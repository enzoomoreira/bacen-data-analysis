"""
Provedor de séries temporais de indicadores
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Union, Dict, Any
from pandas.tseries.offsets import MonthEnd
from bacen_analysis.providers.cosif import COSIFDataProvider
from bacen_analysis.providers.ifdata import IFDATADataProvider
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity
from bacen_analysis.exceptions import EntityNotFoundError, InvalidScopeError, DataUnavailableError


class TimeSeriesProvider:
    """
    Responsável por gerar séries temporais de indicadores.
    
    Single Responsibility: Construção e manipulação de séries temporais de indicadores.
    """
    
    def __init__(
        self,
        cosif_provider: COSIFDataProvider,
        ifdata_provider: IFDATADataProvider,
        entity_resolver: EntityIdentifierResolver
    ):
        """
        Inicializa o provedor de séries temporais.
        
        Args:
            cosif_provider: Provedor de dados COSIF
            ifdata_provider: Provedor de dados IFDATA
            entity_resolver: Resolvedor de identificadores
        """
        self._cosif_provider = cosif_provider
        self._ifdata_provider = ifdata_provider
        self._entity_resolver = entity_resolver
    
    def get_serie_temporal(
        self,
        identificador: str,
        conta: Union[str, int],
        fonte: str = 'COSIF',
        documento_cosif: Optional[int] = None,
        tipo_cosif: Optional[str] = None,
        escopo_ifdata: Optional[str] = None,
        fill_value: Optional[Union[int, float]] = None,
        replace_zeros_with_nan: bool = False,
        drop_na: bool = True,
        data_inicio: Optional[int] = None,
        data_fim: Optional[int] = None,
        datas: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Busca a série temporal de um indicador, com controle de escopo obrigatório.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            conta: Nome ou código da conta/indicador
            fonte: Fonte dos dados ('COSIF' ou 'IFDATA')
            documento_cosif: Documento COSIF a usar (OBRIGATÓRIO se fonte='COSIF')
            tipo_cosif: Tipo OBRIGATÓRIO para COSIF ('prudencial' ou 'individual')
            escopo_ifdata: Escopo OBRIGATÓRIO para IFDATA ('individual', 'prudencial', 'financeiro')
            fill_value: Valor para preencher NaNs
            replace_zeros_with_nan: Se True, converte zeros em NaN
            drop_na: Se True, remove linhas com NaN
            data_inicio: Data inicial no formato YYYYMM (use com data_fim)
            data_fim: Data final no formato YYYYMM (use com data_inicio)
            datas: Lista de datas específicas (alternativa a data_inicio/data_fim)
            
        Returns:
            DataFrame com colunas: DATA, Nome_Entidade, CNPJ_8, Conta, Valor
            
        Raises:
            ValueError: Se parâmetros de data inválidos
            InvalidScopeError: Se escopo/tipo não for especificado ou inválido
            EntityNotFoundError: Se identificador não encontrado
        """
        # OTIMIZAÇÃO: Resolve identificador uma única vez
        resolved = self._entity_resolver.resolve_full(identificador)
        if not resolved.cnpj_interesse:
            raise EntityNotFoundError(
                identifier=identificador,
                suggestions=[
                    "Verifique se o nome ou CNPJ está correto",
                    "Use o CNPJ de 8 dígitos para maior precisão"
                ]
            )

        nome_entidade = resolved.nome_entidade or identificador
        
        # Gera lista de datas
        datas_yyyymm = []
        if datas:
            datas_yyyymm = datas
        elif data_inicio and data_fim:
            start_date_str = f'{data_inicio // 100}-{data_inicio % 100:02d}-01'
            end_date_ts = pd.to_datetime(f'{data_fim}', format='%Y%m') + MonthEnd(0)
            datas_yyyymm = pd.date_range(
                start=start_date_str,
                end=end_date_ts,
                freq='ME'
            ).strftime('%Y%m').astype(int).tolist()
        else:
            raise ValueError(
                "Deve ser fornecido 'datas' ou ambos 'data_inicio' e 'data_fim'."
            )
        
        if not datas_yyyymm:
            return pd.DataFrame(columns=['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor'])
        
        # Valida e prepara parâmetros de escopo
        fonte_upper = fonte.upper()
        if fonte_upper == 'COSIF':
            if not tipo_cosif:
                raise ValueError(
                    "Para fonte 'COSIF', o parâmetro 'tipo_cosif' é obrigatório. "
                    "Use 'prudencial' ou 'individual'."
                )
            if documento_cosif is None:
                raise InvalidScopeError(
                    scope_name='documento_cosif',
                    value=None,
                    valid_values=None,
                    context="Para fonte 'COSIF', o parâmetro 'documento_cosif' é obrigatório"
                )
        elif fonte_upper == 'IFDATA':
            if not escopo_ifdata:
                raise ValueError(
                    "Para fonte 'IFDATA', o parâmetro 'escopo_ifdata' é obrigatório. "
                    "Use 'individual', 'prudencial' ou 'financeiro'."
                )
        else:
            raise ValueError(f"Fonte '{fonte}' inválida. Use 'COSIF' ou 'IFDATA'.")

        # Busca dados brutos usando métodos otimizados
        df_bruto = pd.DataFrame()
        valor_col = ''

        if fonte_upper == 'COSIF':
            # Usa método otimizado com entidade já resolvida
            df_bruto = self._cosif_provider.get_dados_with_resolved(
                resolved,
                contas=[conta],
                datas=datas_yyyymm,
                tipo=tipo_cosif,
                documentos=[documento_cosif] if documento_cosif else None
            )
            valor_col = 'VALOR_CONTA_COSIF'
        elif fonte_upper == 'IFDATA':
            # Usa método otimizado com entidade já resolvida
            df_bruto = self._ifdata_provider.get_dados_with_resolved(
                resolved,
                contas=[conta],
                datas=datas_yyyymm,
                escopo=escopo_ifdata
            )
            valor_col = 'VALOR_CONTA_IFD_VAL'
        
        # Os providers sempre lançam DataUnavailableError quando não há dados,
        # então se chegamos aqui, df_bruto não está vazio
        
        # Limpeza de duplicatas por data
        coluna_temp_isna = '_valor_is_na'
        df_bruto[coluna_temp_isna] = df_bruto[valor_col].isna()
        df_bruto.sort_values(by=['DATA', coluna_temp_isna], inplace=True)
        df_bruto.drop(columns=[coluna_temp_isna], inplace=True)
        
        df_pivot = df_bruto.pivot_table(
            index='DATA',
            values=valor_col,
            aggfunc='first',
            dropna=False
        )
        
        # Reindexa com todas as datas do período
        datas_periodo_dt = pd.to_datetime(datas_yyyymm, format='%Y%m') + MonthEnd(0)
        df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y%m') + MonthEnd(0)
        df_pivot = df_pivot.reindex(datas_periodo_dt)
        
        # Converte para formato longo
        df_long = df_pivot.reset_index().rename(columns={'index': 'DATA', valor_col: 'Valor'})
        df_long['Nome_Entidade'] = nome_entidade
        df_long['CNPJ_8'] = resolved.cnpj_interesse
        df_long['Conta'] = str(conta)
        
        # Aplica transformações
        if replace_zeros_with_nan:
            df_long['Valor'] = df_long['Valor'].replace(0, np.nan)
        
        if fill_value is not None:
            df_long['Valor'] = df_long['Valor'].fillna(fill_value)
        
        if drop_na:
            df_long.dropna(subset=['Valor'], inplace=True)

        return df_long[['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor']].reset_index(drop=True)

    def get_series_temporais_lote(
        self,
        requisicoes: List[Dict[str, Any]],
        fill_value: Optional[Union[int, float]] = None,
        replace_zeros_with_nan: bool = False,
        drop_na: bool = True
    ) -> pd.DataFrame:
        """
        Busca múltiplas séries temporais em um único lote otimizado.

        Esta função é significativamente mais rápida que chamar get_serie_temporal()
        múltiplas vezes, pois resolve todos os identificadores de uma só vez e
        usa métodos otimizados *_with_resolved().

        Args:
            requisicoes: Lista de dicionários com:
                - identificador: str (nome ou CNPJ da instituição)
                - conta: str | int (nome ou código da conta/indicador)
                - fonte: 'COSIF' | 'IFDATA'
                - datas: List[int] (datas no formato YYYYMM)
                - documento_cosif: Optional[int] (para COSIF, default: 4060)
                - escopo_ifdata: str (OBRIGATÓRIO para IFDATA: 'individual', 'prudencial' ou 'financeiro')
                - nome_indicador: str (para identificação na coluna 'Conta')
            fill_value: Valor para preencher NaNs (aplicado a todos)
            replace_zeros_with_nan: Se True, converte zeros em NaN (aplicado a todos)
            drop_na: Se True, remove linhas com NaN (aplicado a todos)

        Returns:
            DataFrame consolidado com colunas:
            ['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor']

        Example:
            >>> requisicoes = [
            ...     {
            ...         'identificador': '00000000',
            ...         'conta': 'Ativo Total',
            ...         'fonte': 'IFDATA',
            ...         'datas': [202501, 202502, 202503],
            ...         'escopo_ifdata': 'prudencial',
            ...         'nome_indicador': 'Ativo Total'
            ...     },
            ...     {
            ...         'identificador': '00000208',
            ...         'conta': '10000001',
            ...         'fonte': 'COSIF',
            ...         'datas': [202501, 202502],
            ...         'documento_cosif': 4060,
            ...         'nome_indicador': 'Caixa'
            ...     }
            ... ]
            >>> df = provider.get_series_temporais_lote(requisicoes)
        """
        if not requisicoes:
            return pd.DataFrame(columns=['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor'])

        # OTIMIZAÇÃO CRÍTICA: Pré-resolve TODOS os identificadores únicos UMA VEZ
        identificadores_unicos = list(set(req['identificador'] for req in requisicoes))
        mapa_entidades = {}

        for identificador in identificadores_unicos:
            resolved = self._entity_resolver.resolve_full(identificador)
            mapa_entidades[identificador] = resolved

        # Pré-processamento: agrupa requisitos por fonte para montar recortes otimizados
        requisicoes_expandidas: List[Dict[str, Any]] = []
        ifdata_ids: set[str] = set()
        ifdata_datas: set[int] = set()
        ifdata_contas: set[Union[str, int]] = set()
        cosif_union: Dict[str, Dict[str, set]] = {}

        for req in requisicoes:
            identificador = req['identificador']
            conta = req['conta']
            fonte = req['fonte']
            datas_yyyymm = req['datas']

            resolved = mapa_entidades[identificador]
            if not resolved.cnpj_interesse:
                continue

            if not datas_yyyymm:
                continue

            fonte_upper = fonte.upper()
            nome_indicador = req.get('nome_indicador', str(conta))

            requisicao_exp = {
                'resolved': resolved,
                'identificador': identificador,
                'conta': conta,
                'fonte': fonte_upper,
                'datas_yyyymm': datas_yyyymm,
                'nome_indicador': nome_indicador,
            }

            if fonte_upper == 'IFDATA':
                escopo_ifdata = req.get('escopo_ifdata')
                if not escopo_ifdata:
                    continue  # Ignora requisições sem escopo
                requisicao_exp['escopo_ifdata'] = escopo_ifdata

                id_busca = self._ifdata_provider.resolve_ids_for_scope(resolved, escopo_ifdata)
                ifdata_ids.add(id_busca)
                ifdata_datas.update(datas_yyyymm)
                if isinstance(conta, (str, int, float)):
                    ifdata_contas.add(conta)

            elif fonte_upper == 'COSIF':
                documento_cosif = req.get('documento_cosif')
                tipo_cosif = req.get('tipo_cosif')
                if not tipo_cosif:
                    continue  # Ignora requisições sem tipo
                documentos_lista = [documento_cosif] if documento_cosif else None

                requisicao_exp['tipo_cosif'] = tipo_cosif
                requisicao_exp['documentos_lista'] = documentos_lista

                cosif_info = cosif_union.setdefault(tipo_cosif, {
                    'cnpjs': set(),
                    'datas': set(),
                    'contas': set(),
                    'documentos': set()
                })
                cnpj_busca = resolved.cnpj_reporte_cosif or resolved.cnpj_interesse
                if cnpj_busca:
                    cosif_info['cnpjs'].add(cnpj_busca)
                cosif_info['datas'].update(datas_yyyymm)
                if isinstance(conta, (str, int, float)):
                    cosif_info['contas'].add(conta)
                if documentos_lista:
                    cosif_info['documentos'].update(documentos_lista)
            else:
                continue

            requisicoes_expandidas.append(requisicao_exp)

        df_ifdata_subset: Optional[pd.DataFrame] = None
        if ifdata_ids and ifdata_datas:
            # Converte sets para listas antes de passar para build_subset
            # (ifdata_ids, ifdata_datas e ifdata_contas são sets para eliminar duplicatas)
            df_ifdata_subset = self._ifdata_provider.build_subset(
                ids_para_buscar=list(ifdata_ids),
                datas=list(ifdata_datas),
                contas=list(ifdata_contas)
            )

        cosif_subsets: Dict[str, pd.DataFrame] = {}
        for tipo_cosif, info in cosif_union.items():
            cnpjs_lista = [cnpj for cnpj in info['cnpjs'] if pd.notna(cnpj)]
            if not cnpjs_lista:
                continue
            datas_lista = list(info['datas']) if info['datas'] else []
            contas_lista = list(info['contas']) if info['contas'] else []
            documentos_lista = list(info['documentos']) if info['documentos'] else None

            cosif_subsets[tipo_cosif] = self._cosif_provider.build_subset(
                tipo=tipo_cosif,
                cnpjs_busca=cnpjs_lista,
                datas=datas_lista,
                contas=contas_lista,
                documentos=documentos_lista
            )

        dfs_coletados = []

        for req in requisicoes_expandidas:
            resolved = req['resolved']
            conta = req['conta']
            nome_indicador = req['nome_indicador']
            datas_yyyymm = req['datas_yyyymm']
            fonte_upper = req['fonte']

            df_bruto = pd.DataFrame()
            valor_col = ''

            try:
                if fonte_upper == 'IFDATA':
                    escopo_ifdata = req.get('escopo_ifdata')
                    if not escopo_ifdata:
                        continue  # Ignora requisições sem escopo
                    df_bruto = self._ifdata_provider.get_dados_with_resolved(
                        resolved,
                        contas=[conta],
                        datas=datas_yyyymm,
                        escopo=escopo_ifdata,
                        df_ifd_val_override=df_ifdata_subset
                    )
                    valor_col = 'VALOR_CONTA_IFD_VAL'
                elif fonte_upper == 'COSIF':
                    tipo_cosif = req['tipo_cosif']
                    documentos_lista = req.get('documentos_lista')
                    df_bruto = self._cosif_provider.get_dados_with_resolved(
                        resolved,
                        contas=[conta],
                        datas=datas_yyyymm,
                        tipo=tipo_cosif,
                        documentos=documentos_lista,
                        df_cosif_override=cosif_subsets.get(tipo_cosif)
                    )
                    valor_col = 'VALOR_CONTA_COSIF'
                else:
                    continue

                # Salvaguarda defensiva para casos extremos onde um DataFrame vazio possa passar
                if df_bruto.empty:
                    continue

            except DataUnavailableError:
                # Dados não disponíveis para esta requisição - continua para a próxima
                continue

            nome_entidade = resolved.nome_entidade or req['identificador']

            # Limpeza de duplicatas por data
            coluna_temp_isna = '_valor_is_na'
            df_bruto[coluna_temp_isna] = df_bruto[valor_col].isna()
            df_bruto.sort_values(by=['DATA', coluna_temp_isna], inplace=True)
            df_bruto.drop(columns=[coluna_temp_isna], inplace=True)

            df_pivot = df_bruto.pivot_table(
                index='DATA',
                values=valor_col,
                aggfunc='first',
                dropna=False
            )

            datas_periodo_dt = pd.to_datetime(datas_yyyymm, format='%Y%m') + MonthEnd(0)
            df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y%m') + MonthEnd(0)
            df_pivot = df_pivot.reindex(datas_periodo_dt)

            df_long = df_pivot.reset_index().rename(columns={'index': 'DATA', valor_col: 'Valor'})
            df_long['Nome_Entidade'] = nome_entidade
            df_long['CNPJ_8'] = resolved.cnpj_interesse
            df_long['Conta'] = nome_indicador

            dfs_coletados.append(df_long[['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor']])

        # Consolida todos os resultados
        if not dfs_coletados:
            return pd.DataFrame(columns=['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor'])

        df_consolidado = pd.concat(dfs_coletados, ignore_index=True)

        # Aplica transformações globais
        if replace_zeros_with_nan:
            df_consolidado['Valor'] = df_consolidado['Valor'].replace(0, np.nan)

        if fill_value is not None:
            df_consolidado['Valor'] = df_consolidado['Valor'].fillna(fill_value)

        if drop_na:
            df_consolidado.dropna(subset=['Valor'], inplace=True)

        return df_consolidado.reset_index(drop=True)

