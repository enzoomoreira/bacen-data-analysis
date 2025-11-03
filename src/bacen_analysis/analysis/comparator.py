"""
Comparador de indicadores entre múltiplas entidades
"""

import warnings
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union
from bacen_analysis.providers.cosif import COSIFDataProvider
from bacen_analysis.providers.ifdata import IFDATADataProvider
from bacen_analysis.providers.cadastro import CadastroProvider
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity
from bacen_analysis.exceptions import InvalidScopeError, DataUnavailableError, EntityNotFoundError


class IndicadorComparator:
    """
    Responsável por comparar múltiplos indicadores entre várias instituições.
    
    Single Responsibility: Comparação e agregação de indicadores de múltiplas fontes.
    """
    
    def __init__(
        self,
        cosif_provider: COSIFDataProvider,
        ifdata_provider: IFDATADataProvider,
        cadastro_provider: CadastroProvider,
        entity_resolver: EntityIdentifierResolver
    ):
        """
        Inicializa o comparador de indicadores.
        
        Args:
            cosif_provider: Provedor de dados COSIF
            ifdata_provider: Provedor de dados IFDATA
            cadastro_provider: Provedor de dados de cadastro
            entity_resolver: Resolvedor de identificadores
        """
        self._cosif_provider = cosif_provider
        self._ifdata_provider = ifdata_provider
        self._cadastro_provider = cadastro_provider
        self._entity_resolver = entity_resolver
    
    def comparar(
        self,
        identificadores: List[str],
        indicadores: Dict[str, Dict],
        data: int,
        fillna: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Cria uma tabela comparativa de indicadores, usando a lógica centralizada
        para obter Nome e CNPJ da entidade.
        
        Args:
            identificadores: Lista de identificadores (nomes ou CNPJs) de instituições
            indicadores: Dicionário onde a chave é o nome da coluna e o valor é a configuração do indicador
                        Cada configuração deve ter:
                        - 'tipo' ('COSIF', 'IFDATA', ou 'ATRIBUTO')
                        - 'conta' (para COSIF/IFDATA) ou 'atributo' (para ATRIBUTO)
                        - Para COSIF: 'tipo_cosif' ('prudencial' ou 'individual') e 'documento_cosif' (OBRIGATÓRIO)
                        - Para IFDATA: 'escopo_ifdata' ('individual', 'prudencial' ou 'financeiro')
            data: Data no formato YYYYMM para comparação
            fillna: Valor para preencher NaNs (0, np.nan, ou string 'nan')
            
        Returns:
            DataFrame pivotado com identificadores nas linhas e indicadores nas colunas
            
        Raises:
            KeyError: Se configuração de indicador estiver incompleta
            ValueError: Se tipo de indicador não for reconhecido
            InvalidScopeError: Se documento_cosif não for especificado em indicador COSIF
        """
        
        # OTIMIZAÇÃO: Resolve todos os identificadores uma vez no início
        # Captura EntityNotFoundError para permitir comparações mesmo quando alguns bancos não existem
        resolved_entities = {}
        entidades_nao_encontradas = []
        for ident in identificadores:
            try:
                resolved_entities[ident] = self._entity_resolver.resolve_full(ident)
            except EntityNotFoundError:
                # Cria um ResolvedEntity vazio para identificar não encontrado
                resolved_entities[ident] = ResolvedEntity(
                    cnpj_interesse=None,
                    cnpj_reporte_cosif=None,
                    cod_congl_prud=None,
                    nome_entidade=None,
                    identificador_original=ident
                )
                entidades_nao_encontradas.append(ident)
        
        # Emite warning se houver entidades não encontradas
        if entidades_nao_encontradas:
            warnings.warn(
                f"Entidade(s) não encontrada(s): {', '.join(repr(e) for e in entidades_nao_encontradas)}. "
                f"Serão incluídas no resultado com valores None.",
                category=UserWarning,
                stacklevel=2
            )

        lista_resultados = []

        for ident in identificadores:
            resolved = resolved_entities[ident]

            if not resolved.cnpj_interesse:
                dados_banco = {
                    'Nome_Entidade': f"'{ident}' não encontrado",
                    'CNPJ_8': 'N/A'
                }
                for nome_coluna in indicadores:
                    dados_banco[nome_coluna] = None
                lista_resultados.append(dados_banco)
                continue

            nome_entidade = resolved.nome_entidade or ident

            dados_banco = {'Nome_Entidade': nome_entidade, 'CNPJ_8': resolved.cnpj_interesse}

            for nome_coluna, info_ind in indicadores.items():
                valor = None
                tipo = info_ind.get('tipo', '').upper()
                
                if tipo == 'COSIF':
                    try:
                        conta = info_ind['conta']
                    except KeyError:
                        raise KeyError(
                            f"Indicador '{nome_coluna}' de tipo COSIF precisa da chave 'conta'."
                        )

                    tipo_cosif = info_ind.get('tipo_cosif')
                    if not tipo_cosif:
                        raise InvalidScopeError(
                            scope_name='tipo_cosif',
                            value=None,
                            valid_values=['prudencial', 'individual'],
                            context=f"Indicador '{nome_coluna}' de tipo COSIF precisa da chave 'tipo_cosif' especificada na configuração do indicador"
                        )

                    documento_cosif = info_ind.get('documento_cosif')
                    if documento_cosif is None:
                        raise InvalidScopeError(
                            scope_name='documento_cosif',
                            value=None,
                            valid_values=None,
                            context=f"Indicador '{nome_coluna}' de tipo COSIF precisa da chave 'documento_cosif' especificada na configuração do indicador"
                        )

                    # Usa método otimizado com entidade já resolvida
                    # Captura DataUnavailableError para permitir comparações mesmo quando alguns dados não existem
                    try:
                        df_res = self._cosif_provider.get_dados_with_resolved(
                            resolved,
                            contas=[conta],
                            datas=[data],
                            tipo=tipo_cosif,
                            documentos=[documento_cosif] if documento_cosif else None
                        )

                        if not df_res.empty:
                            valor = df_res.sort_values('DOCUMENTO_COSIF', ascending=False)[
                                'VALOR_CONTA_COSIF'
                            ].iloc[0]
                    except DataUnavailableError:
                        # Dados não disponíveis para esta entidade/indicador - mantém valor como None
                        valor = None

                elif tipo == 'IFDATA':
                    try:
                        conta = info_ind['conta']
                    except KeyError:
                        raise KeyError(
                            f"Indicador '{nome_coluna}' de tipo IFDATA precisa da chave 'conta'."
                        )

                    escopo = info_ind.get('escopo_ifdata')
                    if not escopo:
                        raise KeyError(
                            f"Indicador '{nome_coluna}' de tipo IFDATA precisa da chave 'escopo_ifdata' "
                            f"('individual', 'prudencial' ou 'financeiro')."
                        )

                    # Usa método otimizado com entidade já resolvida
                    # Captura DataUnavailableError para permitir comparações mesmo quando alguns dados não existem
                    try:
                        df_res = self._ifdata_provider.get_dados_with_resolved(
                            resolved,
                            contas=[conta],
                            datas=[data],
                            escopo=escopo
                        )

                        if not df_res.empty:
                            valor = df_res['VALOR_CONTA_IFD_VAL'].iloc[0]
                    except DataUnavailableError:
                        # Dados não disponíveis para esta entidade/indicador - mantém valor como None
                        valor = None

                elif tipo == 'ATRIBUTO':
                    try:
                        atributo = info_ind['atributo']
                    except KeyError:
                        raise KeyError(
                            f"Indicador '{nome_coluna}' de tipo ATRIBUTO precisa da chave 'atributo'."
                        )

                    # Usa método otimizado com entidade já resolvida
                    df_res = self._cadastro_provider.get_atributos_with_resolved(
                        resolved,
                        atributos=[atributo]
                    )

                    if not df_res.empty:
                        valor = df_res[atributo].iloc[0]
                
                else:
                    raise ValueError(
                        f"Tipo de indicador '{info_ind.get('tipo')}' não reconhecido em '{nome_coluna}'."
                    )
                
                dados_banco[nome_coluna] = valor
            
            lista_resultados.append(dados_banco)
        
        if not lista_resultados:
            return pd.DataFrame()
        
        df_final = pd.DataFrame(lista_resultados)
        
        cols_indicadores = list(indicadores.keys())
        cols_numericas = [
            c for c in cols_indicadores
            if c in df_final.columns and pd.api.types.is_numeric_dtype(df_final[c])
        ]
        
        if fillna is not None:
            if fillna == 0:
                df_final[cols_numericas] = df_final[cols_numericas].fillna(0)
            elif pd.isna(fillna) or (isinstance(fillna, str) and fillna.lower() == 'nan'):
                df_final[cols_numericas] = df_final[cols_numericas].replace(0, np.nan)
        
        cols_id = ['Nome_Entidade', 'CNPJ_8']
        ordem_final = cols_id + [
            col for col in cols_indicadores if col in df_final.columns
        ]
        return df_final[ordem_final]

