"""
Provedor de dados COSIF
"""

import pandas as pd
from typing import List, Union, Optional
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity
from bacen_analysis.exceptions import InvalidScopeError, DataUnavailableError, EntityNotFoundError


class COSIFDataProvider:
    """
    Responsável por consultas específicas de dados COSIF.
    
    Single Responsibility: Consultas e filtragem de dados COSIF.
    """
    
    VALID_TIPOS = {'prudencial', 'individual'}
    
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

    def _validate_tipo(self, tipo: str) -> None:
        """
        Valida se o tipo fornecido é válido.
        
        Args:
            tipo: Tipo a validar
            
        Raises:
            InvalidScopeError: Se o tipo não for válido
        """
        if tipo not in self.VALID_TIPOS:
            raise InvalidScopeError(
                scope_name='tipo',
                value=tipo,
                valid_values=list(self.VALID_TIPOS),
                context='Tipo deve ser explicitamente especificado como "prudencial" ou "individual"'
            )

    def _normalize_documentos(self, documentos: Optional[Union[int, List[int]]]) -> Optional[List[int]]:
        """
        Normaliza documentos para uma lista.
        
        Args:
            documentos: Documento único ou lista de documentos
            
        Returns:
            Lista de documentos ou None
        """
        if documentos is None:
            return None
        if isinstance(documentos, list):
            return documentos
        return [documentos]

    def _check_data_availability(
        self,
        cnpj_busca: str,
        datas: List[int],
        tipo: str,
        df_base: pd.DataFrame
    ) -> None:
        """
        Verifica se os dados estão disponíveis para o contexto especificado.
        
        Args:
            cnpj_busca: CNPJ para buscar
            datas: Lista de datas
            tipo: Tipo de dados
            df_base: DataFrame base
            
        Raises:
            DataUnavailableError: Se os dados não estão disponíveis
        """
        if df_base.empty:
            raise DataUnavailableError(
                entity=cnpj_busca,
                scope_type=tipo,
                reason=f"Nenhum dado disponível no tipo '{tipo}'",
                suggestions=[
                    f"Verifique se há dados para este tipo no repositório",
                    f"Tente usar o outro tipo ({'individual' if tipo == 'prudencial' else 'prudencial'})"
                ]
            )
        
        # Verifica se há dados para o CNPJ e datas especificadas
        filtro_base = (df_base['CNPJ_8'] == cnpj_busca) & (df_base['DATA'].isin(datas))
        dados_existem = filtro_base.any()
        
        if not dados_existem:
            raise DataUnavailableError(
                entity=cnpj_busca,
                scope_type=tipo,
                reason=f"Nenhum dado encontrado para CNPJ {cnpj_busca} nas datas {datas} no tipo '{tipo}'",
                suggestions=[
                    f"Verifique se o CNPJ tem dados no tipo '{tipo}'",
                    f"Verifique se as datas estão disponíveis",
                    f"Tente usar o outro tipo ({'individual' if tipo == 'prudencial' else 'prudencial'})"
                ]
            )

    def _select_df_base(self, tipo: str, df_override: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Retorna o DataFrame COSIF base considerando overrides temporários."""
        if df_override is not None:
            return df_override
        return self._get_df_base(tipo)

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
        tipo: str,
        documentos: Optional[Union[int, List[int]]] = None,
        df_cosif_override: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Busca dados COSIF com tipo obrigatório.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            contas: Lista de nomes ou códigos de contas COSIF
            datas: Data única ou lista de datas no formato YYYYMM
            tipo: Tipo de dados OBRIGATÓRIO ('prudencial' ou 'individual')
            documentos: Documento único ou lista de documentos COSIF
            df_cosif_override: DataFrame override para otimização (uso interno)
            
        Returns:
            DataFrame com os dados solicitados, incluindo colunas 'Nome_Entidade' e 'CNPJ_8'
            
        Raises:
            InvalidScopeError: Se o tipo não for válido
            EntityNotFoundError: Se a entidade não for encontrada
            DataUnavailableError: Se os dados não estiverem disponíveis para o contexto
        """
        # Valida tipo obrigatório
        self._validate_tipo(tipo)
        
        # Normaliza documentos
        documentos_lista = self._normalize_documentos(documentos)
        
        # Seleciona o DataFrame base usando cache local
        df_base = self._select_df_base(tipo, df_cosif_override)

        # Resolve identificadores canônicos (find_cnpj lança exceção se não encontrar)
        cnpj_8 = self._entity_resolver.find_cnpj(identificador)

        info_ent = self._entity_resolver.get_entity_identifiers(cnpj_8)
        nome_entidade_canonico = info_ent.get('nome_entidade', identificador)
        cnpj_busca = info_ent.get('cnpj_reporte_cosif', cnpj_8)
        
        if not cnpj_busca:
            raise DataUnavailableError(
                entity=identificador,
                scope_type=tipo,
                reason="CNPJ de reporte COSIF não encontrado",
                suggestions=["Verifique se a entidade possui dados COSIF"]
            )
        
        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]
        
        # Verifica disponibilidade de dados
        self._check_data_availability(cnpj_busca, datas, tipo, df_base)
        
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
            # Se chegou aqui, os dados existem mas não há correspondência com as contas/documentos
            raise DataUnavailableError(
                entity=identificador,
                scope_type=tipo,
                reason=f"Nenhum dado encontrado para as contas/documentos especificados no tipo '{tipo}'",
                suggestions=[
                    "Verifique se os nomes ou códigos das contas estão corretos",
                    "Verifique se os documentos especificados existem para esta entidade",
                    "Verifique se há dados para as datas especificadas"
                ]
            )

    def get_dados_with_resolved(
        self,
        resolved_entity: ResolvedEntity,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        tipo: str,
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
            tipo: Tipo de dados OBRIGATÓRIO ('prudencial' ou 'individual')
            documentos: Documento único ou lista de documentos COSIF
            df_cosif_override: DataFrame override para otimização (uso interno)

        Returns:
            DataFrame com os dados solicitados
            
        Raises:
            InvalidScopeError: Se o tipo não for válido
            DataUnavailableError: Se os dados não estiverem disponíveis para o contexto
        """
        # Valida tipo obrigatório
        self._validate_tipo(tipo)
        
        # Normaliza documentos
        documentos_lista = self._normalize_documentos(documentos)

        # Seleciona o DataFrame base usando cache local
        df_base = self._select_df_base(tipo, df_cosif_override)

        # Usa entidade já resolvida
        cnpj_8 = resolved_entity.cnpj_interesse
        if not cnpj_8:
            raise DataUnavailableError(
                entity=resolved_entity.identificador_original,
                scope_type=tipo,
                reason="Entidade resolvida não possui CNPJ de interesse",
                suggestions=["Verifique se o identificador foi resolvido corretamente"]
            )

        nome_entidade_canonico = resolved_entity.nome_entidade or resolved_entity.identificador_original
        cnpj_busca = resolved_entity.cnpj_reporte_cosif or cnpj_8

        if not cnpj_busca:
            raise DataUnavailableError(
                entity=resolved_entity.identificador_original,
                scope_type=tipo,
                reason="CNPJ de reporte COSIF não encontrado",
                suggestions=["Verifique se a entidade possui dados COSIF"]
            )

        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]

        # Verifica disponibilidade de dados
        self._check_data_availability(cnpj_busca, datas, tipo, df_base)

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
            # Se chegou aqui, os dados existem mas não há correspondência com as contas/documentos
            raise DataUnavailableError(
                entity=resolved_entity.identificador_original,
                scope_type=tipo,
                reason=f"Nenhum dado encontrado para as contas/documentos especificados no tipo '{tipo}'",
                suggestions=[
                    "Verifique se os nomes ou códigos das contas estão corretos",
                    "Verifique se os documentos especificados existem para esta entidade",
                    "Verifique se há dados para as datas especificadas"
                ]
            )

