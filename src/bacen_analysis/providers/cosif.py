"""
Provedor de dados COSIF
"""

import pandas as pd
from typing import List, Union, Optional
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity


class COSIFDataProvider:
    """
    Responsável por consultas específicas de dados COSIF.
    
    Single Responsibility: Consultas e filtragem de dados COSIF.
    """
    
    # Mapeamento de documentos para tipos
    DOC_TO_TIPO_MAP = {
        4060: 'prudencial', 4066: 'prudencial',
        4010: 'individual', 4016: 'individual'
    }
    
    def __init__(self, repository: DataRepository, entity_resolver: EntityIdentifierResolver):
        """
        Inicializa o provedor COSIF.

        Args:
            repository: Instância de DataRepository para acessar dados
            entity_resolver: Instância de EntityIdentifierResolver para resolver identificadores
        """
        self._repository = repository
        self._entity_resolver = entity_resolver
        # Cache local dos DataFrames para evitar acesso via properties em loops
        self._df_cosif_prud: Optional[pd.DataFrame] = None
        self._df_cosif_ind: Optional[pd.DataFrame] = None

    def _get_df_base(self, tipo: str) -> pd.DataFrame:
        """
        Obtém o DataFrame base com cache local.

        Args:
            tipo: 'prudencial' ou 'individual'

        Returns:
            DataFrame correspondente ao tipo
        """
        if tipo == 'prudencial':
            if self._df_cosif_prud is None:
                self._df_cosif_prud = self._repository.df_cosif_prud
            return self._df_cosif_prud
        else:
            if self._df_cosif_ind is None:
                self._df_cosif_ind = self._repository.df_cosif_ind
            return self._df_cosif_ind

    def _select_df_base(self, tipo: str, df_override: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Retorna o DataFrame COSIF base considerando overrides temporários."""
        if df_override is not None:
            return df_override
        return self._get_df_base(tipo)

    def determine_tipo(
        self,
        tipo: str,
        documentos: Optional[Union[int, List[int]]]
    ) -> tuple[str, Optional[List[int]]]:
        """Determina o tipo final (prudencial/individual) e normaliza documentos."""
        tipo_busca = tipo
        documentos_lista: Optional[List[int]] = None

        if documentos is not None:
            if not isinstance(documentos, list):
                documentos_lista = [documentos]
            else:
                documentos_lista = documentos

            if documentos_lista:
                primeiro_doc = documentos_lista[0]
                if primeiro_doc in self.DOC_TO_TIPO_MAP:
                    tipo_definido_pelo_doc = self.DOC_TO_TIPO_MAP[primeiro_doc]
                    if tipo_busca != tipo_definido_pelo_doc:
                        tipo_busca = tipo_definido_pelo_doc
        return tipo_busca, documentos_lista

    def build_subset(
        self,
        tipo: str,
        cnpjs_busca: List[str],
        datas: List[int],
        contas: List[Union[str, int]],
        documentos: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """Constrói um recorte otimizado do DataFrame COSIF para múltiplas requisições."""
        if not cnpjs_busca or not datas:
            return self._get_df_base(tipo).iloc[0:0].copy()

        df_base = self._get_df_base(tipo)

        cnpjs_unique = list(dict.fromkeys(cnpjs_busca))
        datas_unique = list(dict.fromkeys(datas))

        filtro_base = df_base['CNPJ_8'].isin(cnpjs_unique) & df_base['DATA'].isin(datas_unique)

        contas = contas or []
        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, (int, float)) and not pd.isna(c)]

        filtro_conta = None
        if nomes_busca:
            filtro_conta = df_base['NOME_CONTA_COSIF'].isin(list(dict.fromkeys(nomes_busca)))
        if codigos_busca:
            filtro_codigos = df_base['CONTA_COSIF'].isin(list(dict.fromkeys(codigos_busca)))
            filtro_conta = filtro_codigos if filtro_conta is None else (filtro_conta | filtro_codigos)

        filtro_final = filtro_base if filtro_conta is None else (filtro_base & filtro_conta)

        if documentos:
            filtro_final &= df_base['DOCUMENTO_COSIF'].isin(documentos)

        return df_base[filtro_final].copy()
    
    def get_dados(
        self,
        identificador: str,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        tipo: str = 'prudencial',
        documentos: Optional[Union[int, List[int]]] = None,
        df_cosif_override: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Busca dados COSIF. Determina automaticamente o 'tipo' (prudencial/individual)
        se um 'documento' for fornecido, tornando o parâmetro 'tipo' um fallback.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            contas: Lista de nomes ou códigos de contas COSIF
            datas: Data única ou lista de datas no formato YYYYMM
            tipo: Tipo de dados ('prudencial' ou 'individual')
            documentos: Documento único ou lista de documentos COSIF
            
        Returns:
            DataFrame com os dados solicitados, incluindo colunas 'Nome_Entidade' e 'CNPJ_8'
        """
        # Lógica inteligente de seleção de tipo
        tipo_busca, documentos_lista = self.determine_tipo(tipo, documentos)
        
        # Seleciona o DataFrame base usando cache local
        df_base = self._select_df_base(tipo_busca, df_cosif_override)

        # Resolve identificadores canônicos
        cnpj_8 = self._entity_resolver.find_cnpj(identificador)
        if not cnpj_8:
            return self._empty_result_df(df_base)

        info_ent = self._entity_resolver.get_entity_identifiers(cnpj_8)
        nome_entidade_canonico = info_ent.get('nome_entidade', identificador)
        cnpj_busca = info_ent.get('cnpj_reporte_cosif', cnpj_8)
        
        if not cnpj_busca:
            return self._empty_result_df(df_base)
        
        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]
        
        # Aplica filtros
        filtro_base = (df_base['CNPJ_8'] == cnpj_busca) & (df_base['DATA'].isin(datas))
        
        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, (int, float))]
        filtro_nomes = df_base['NOME_CONTA_COSIF'].isin(nomes_busca)
        filtro_codigos = df_base['CONTA_COSIF'].isin(codigos_busca)
        filtro_conta = filtro_nomes | filtro_codigos
        
        filtro_final = filtro_base & filtro_conta
        
        if documentos_lista:
            filtro_final &= df_base['DOCUMENTO_COSIF'].isin(documentos_lista)
        
        temp_df = df_base[filtro_final].copy()
        
        # Padroniza e reordena as colunas de saída
        if not temp_df.empty:
            temp_df.rename(columns={'NOME_INSTITUICAO_COSIF': 'Nome_Entidade'}, inplace=True)
            temp_df['Nome_Entidade'] = nome_entidade_canonico
            
            cols_base = list(temp_df.columns)
            cols_prioritarias = ['Nome_Entidade', 'CNPJ_8']
            cols_restantes = [c for c in cols_base if c not in cols_prioritarias]
            
            ordem_final = cols_prioritarias + cols_restantes
            return temp_df.reset_index(drop=True)[ordem_final]
        else:
            return self._empty_result_df(df_base)

    def get_dados_with_resolved(
        self,
        resolved_entity: ResolvedEntity,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        tipo: str = 'prudencial',
        documentos: Optional[Union[int, List[int]]] = None,
        df_cosif_override: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Busca dados COSIF usando uma entidade já resolvida (otimizado).

        Este método evita a resolução duplicada de identificadores,
        melhorando performance em operações em lote.

        Args:
            resolved_entity: Entidade já resolvida pelo EntityIdentifierResolver
            contas: Lista de nomes ou códigos de contas COSIF
            datas: Data única ou lista de datas no formato YYYYMM
            tipo: Tipo de dados ('prudencial' ou 'individual')
            documentos: Documento único ou lista de documentos COSIF

        Returns:
            DataFrame com os dados solicitados
        """
        # Lógica inteligente de seleção de tipo
        tipo_busca, documentos_lista = self.determine_tipo(tipo, documentos)

        # Seleciona o DataFrame base usando cache local
        df_base = self._select_df_base(tipo_busca, df_cosif_override)

        # Usa entidade já resolvida
        cnpj_8 = resolved_entity.cnpj_interesse
        if not cnpj_8:
            return self._empty_result_df(df_base)

        nome_entidade_canonico = resolved_entity.nome_entidade or resolved_entity.identificador_original
        cnpj_busca = resolved_entity.cnpj_reporte_cosif or cnpj_8

        if not cnpj_busca:
            return self._empty_result_df(df_base)

        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]

        # Aplica filtros
        filtro_base = (df_base['CNPJ_8'] == cnpj_busca) & (df_base['DATA'].isin(datas))

        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, (int, float))]
        filtro_nomes = df_base['NOME_CONTA_COSIF'].isin(nomes_busca)
        filtro_codigos = df_base['CONTA_COSIF'].isin(codigos_busca)
        filtro_conta = filtro_nomes | filtro_codigos

        filtro_final = filtro_base & filtro_conta

        if documentos_lista:
            filtro_final &= df_base['DOCUMENTO_COSIF'].isin(documentos_lista)

        temp_df = df_base[filtro_final].copy()

        # Padroniza e reordena as colunas de saída
        if not temp_df.empty:
            temp_df.rename(columns={'NOME_INSTITUICAO_COSIF': 'Nome_Entidade'}, inplace=True)
            temp_df['Nome_Entidade'] = nome_entidade_canonico

            cols_base = list(temp_df.columns)
            cols_prioritarias = ['Nome_Entidade', 'CNPJ_8']
            cols_restantes = [c for c in cols_base if c not in cols_prioritarias]

            ordem_final = cols_prioritarias + cols_restantes
            return temp_df.reset_index(drop=True)[ordem_final]
        else:
            return self._empty_result_df(df_base)

    def _empty_result_df(self, df_base: pd.DataFrame) -> pd.DataFrame:
        """
        Retorna DataFrame vazio com estrutura padronizada.
        
        Args:
            df_base: DataFrame base para inferir colunas
            
        Returns:
            DataFrame vazio com colunas corretas
        """
        return pd.DataFrame(columns=[
            'Nome_Entidade', 'CNPJ_8'
        ] + [c for c in df_base.columns if c not in ['NOME_INSTITUICAO_COSIF', 'CNPJ_8']])

