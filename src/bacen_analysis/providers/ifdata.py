"""
Provedor de dados IFDATA
"""

import pandas as pd
from typing import List, Union, Optional
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity


class IFDATADataProvider:
    """
    Responsável por consultas específicas de dados IFDATA.
    
    Single Responsibility: Consultas e filtragem de dados IFDATA com controle de escopo.
    """
    
    def __init__(self, repository: DataRepository, entity_resolver: EntityIdentifierResolver):
        """
        Inicializa o provedor IFDATA.

        Args:
            repository: Instância de DataRepository para acessar dados
            entity_resolver: Instância de EntityIdentifierResolver para resolver identificadores
        """
        self._repository = repository
        self._entity_resolver = entity_resolver
        # Cache local dos DataFrames para evitar acesso via properties em loops
        self._df_ifd_val: Optional[pd.DataFrame] = None
        self._df_ifd_cad: Optional[pd.DataFrame] = None

    def _get_df_ifd_val(self) -> pd.DataFrame:
        """Obtém DataFrame IFDATA valores com cache local."""
        if self._df_ifd_val is None:
            self._df_ifd_val = self._repository.df_ifd_val
        return self._df_ifd_val

    def _get_df_ifd_cad(self) -> pd.DataFrame:
        """Obtém DataFrame IFDATA cadastro com cache local."""
        if self._df_ifd_cad is None:
            self._df_ifd_cad = self._repository.df_ifd_cad
        return self._df_ifd_cad

    def _select_df_ifd_val(self, df_override: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Retorna o DataFrame IFDATA valores considerando overrides temporários."""
        if df_override is not None:
            return df_override
        return self._get_df_ifd_val()

    def resolve_ids_for_scope(self, resolved_entity: ResolvedEntity, escopo: str = 'cascata') -> List[str]:
        """Resolve os identificadores de busca necessários para o escopo informado."""
        cnpj_8 = resolved_entity.cnpj_interesse
        if not cnpj_8:
            return []

        df_ifd_cad = self._get_df_ifd_cad()
        entry_cad = df_ifd_cad[df_ifd_cad['CNPJ_8'] == cnpj_8].sort_values('DATA', ascending=False)

        cod_congl_prud_busca = resolved_entity.cod_congl_prud
        cod_congl_fin_busca = entry_cad.iloc[0].get('COD_CONGL_FIN_IFD_CAD') if not entry_cad.empty else None

        ids_para_buscar: List[str] = []
        if escopo == 'individual':
            ids_para_buscar = [cnpj_8]
        elif escopo == 'prudencial':
            ids_para_buscar = [cod_congl_prud_busca]
        elif escopo == 'financeiro':
            ids_para_buscar = [cod_congl_fin_busca]
        elif escopo == 'cascata':
            ids_para_buscar = [cnpj_8, cod_congl_prud_busca, cod_congl_fin_busca]
        else:
            raise ValueError(
                f"Escopo '{escopo}' inválido. Use 'cascata', 'individual', 'prudencial', ou 'financeiro'."
            )

        ids_para_buscar = [str(i) for i in ids_para_buscar if pd.notna(i)]
        return list(dict.fromkeys(ids_para_buscar))

    def build_subset(
        self,
        ids_para_buscar: List[str],
        datas: List[int],
        contas: List[Union[str, int]]
    ) -> pd.DataFrame:
        """Constrói um recorte otimizado do DataFrame IFDATA Valores."""
        if not ids_para_buscar or not datas:
            return self._get_df_ifd_val().iloc[0:0].copy()

        df_ifd_val = self._get_df_ifd_val()

        ids_uniques = list(dict.fromkeys(str(i) for i in ids_para_buscar))
        datas_unique = list(dict.fromkeys(datas))

        filtro_base = df_ifd_val['COD_INST_IFD_VAL'].isin(ids_uniques) & df_ifd_val['DATA'].isin(datas_unique)

        contas = contas or []
        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, (int, float)) and not pd.isna(c)]

        filtro_conta = None
        if nomes_busca:
            filtro_conta = df_ifd_val['NOME_CONTA_IFD_VAL'].isin(list(dict.fromkeys(nomes_busca)))
        if codigos_busca:
            filtro_codigos = df_ifd_val['CONTA_IFD_VAL'].isin(list(dict.fromkeys(codigos_busca)))
            filtro_conta = filtro_codigos if filtro_conta is None else (filtro_conta | filtro_codigos)

        if filtro_conta is not None:
            filtro_final = filtro_base & filtro_conta
        else:
            filtro_final = filtro_base

        return df_ifd_val[filtro_final].copy()
    
    def get_dados(
        self,
        identificador: str,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        escopo: str = 'cascata',
        df_ifd_val_override: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Busca dados IFDATA com controle de escopo.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            contas: Lista de nomes ou códigos de contas IFDATA
            datas: Data única ou lista de datas no formato YYYYMM
            escopo: Escopo da busca ('cascata', 'individual', 'prudencial', 'financeiro')
            
        Returns:
            DataFrame com os dados solicitados, incluindo colunas 'Nome_Entidade', 'CNPJ_8' e 'ID_BUSCA_USADO'
            
        Raises:
            ValueError: Se o escopo for inválido
        """
        # Resolve identificadores canônicos
        cnpj_8 = self._entity_resolver.find_cnpj(identificador)
        if not cnpj_8:
            return self._empty_result_df()
        
        resolved = self._entity_resolver.resolve_full(identificador)
        nome_entidade_canonico = resolved.nome_entidade or identificador
        
        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]
        
        ids_para_buscar = self.resolve_ids_for_scope(resolved, escopo)

        if not ids_para_buscar:
            return self._empty_result_df()

        # Itera e coleta todos os resultados usando cache
        resultados_coletados = []
        df_ifd_val = self._select_df_ifd_val(df_ifd_val_override)
        
        for id_busca in ids_para_buscar:
            filtro_base = (df_ifd_val['COD_INST_IFD_VAL'] == id_busca) & (df_ifd_val['DATA'].isin(datas))
            
            nomes_busca = [c for c in contas if isinstance(c, str)]
            codigos_busca = [c for c in contas if isinstance(c, int)]
            
            filtro_nomes = df_ifd_val['NOME_CONTA_IFD_VAL'].isin(nomes_busca)
            filtro_codigos = df_ifd_val['CONTA_IFD_VAL'].isin(codigos_busca)
            filtro_conta = filtro_nomes | filtro_codigos
            
            df_resultado_parcial = df_ifd_val[filtro_base & filtro_conta].copy()
            
            if not df_resultado_parcial.empty:
                df_resultado_parcial['ID_BUSCA_USADO'] = id_busca
                resultados_coletados.append(df_resultado_parcial)
        
        if not resultados_coletados:
            return self._empty_result_df()
        
        df_final = pd.concat(resultados_coletados, ignore_index=True)
        df_final.drop_duplicates(inplace=True)
        
        df_final['Nome_Entidade'] = nome_entidade_canonico
        df_final['CNPJ_8'] = resolved.cnpj_interesse
        
        # Reordena colunas
        cols_base = list(df_final.columns)
        cols_prioritarias = ['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO']
        cols_restantes = [c for c in cols_base if c not in cols_prioritarias]
        
        ordem_final = cols_prioritarias + cols_restantes
        return df_final.reset_index(drop=True)[ordem_final]

    def get_dados_with_resolved(
        self,
        resolved_entity: ResolvedEntity,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        escopo: str = 'cascata',
        df_ifd_val_override: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Busca dados IFDATA usando uma entidade já resolvida (otimizado).

        Este método evita a resolução duplicada de identificadores,
        melhorando performance em operações em lote.

        Args:
            resolved_entity: Entidade já resolvida pelo EntityIdentifierResolver
            contas: Lista de nomes ou códigos de contas IFDATA
            datas: Data única ou lista de datas no formato YYYYMM
            escopo: Escopo da busca ('cascata', 'individual', 'prudencial', 'financeiro')

        Returns:
            DataFrame com os dados solicitados

        Raises:
            ValueError: Se o escopo for inválido
        """
        # Usa entidade já resolvida
        cnpj_8 = resolved_entity.cnpj_interesse
        if not cnpj_8:
            return self._empty_result_df()

        nome_entidade_canonico = resolved_entity.nome_entidade or resolved_entity.identificador_original

        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]

        ids_para_buscar = self.resolve_ids_for_scope(resolved_entity, escopo)

        if not ids_para_buscar:
            return self._empty_result_df()

        # Itera e coleta todos os resultados usando cache
        resultados_coletados = []
        df_ifd_val = self._select_df_ifd_val(df_ifd_val_override)

        for id_busca in ids_para_buscar:
            filtro_base = (df_ifd_val['COD_INST_IFD_VAL'] == id_busca) & (df_ifd_val['DATA'].isin(datas))

            nomes_busca = [c for c in contas if isinstance(c, str)]
            codigos_busca = [c for c in contas if isinstance(c, int)]

            filtro_nomes = df_ifd_val['NOME_CONTA_IFD_VAL'].isin(nomes_busca)
            filtro_codigos = df_ifd_val['CONTA_IFD_VAL'].isin(codigos_busca)
            filtro_conta = filtro_nomes | filtro_codigos

            df_resultado_parcial = df_ifd_val[filtro_base & filtro_conta].copy()

            if not df_resultado_parcial.empty:
                df_resultado_parcial['ID_BUSCA_USADO'] = id_busca
                resultados_coletados.append(df_resultado_parcial)

        if not resultados_coletados:
            return self._empty_result_df()

        df_final = pd.concat(resultados_coletados, ignore_index=True)
        df_final.drop_duplicates(inplace=True)

        df_final['Nome_Entidade'] = nome_entidade_canonico
        df_final['CNPJ_8'] = cnpj_8

        # Reordena colunas
        cols_base = list(df_final.columns)
        cols_prioritarias = ['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO']
        cols_restantes = [c for c in cols_base if c not in cols_prioritarias]

        ordem_final = cols_prioritarias + cols_restantes
        return df_final.reset_index(drop=True)[ordem_final]

    def _empty_result_df(self) -> pd.DataFrame:
        """
        Retorna DataFrame vazio com estrutura padronizada.

        Returns:
            DataFrame vazio com colunas corretas
        """
        df_ifd_val = self._get_df_ifd_val()
        return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO'] + list(df_ifd_val.columns))

