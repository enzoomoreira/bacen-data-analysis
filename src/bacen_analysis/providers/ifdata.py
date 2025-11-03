"""
Provedor de dados IFDATA
"""

import pandas as pd
from typing import List, Union, Optional
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity
from bacen_analysis.exceptions import InvalidScopeError, DataUnavailableError, EntityNotFoundError


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

    VALID_ESCOPOS = {'individual', 'prudencial', 'financeiro'}

    def _select_df_ifd_val(self, df_override: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Retorna o DataFrame IFDATA valores considerando overrides temporários."""
        if df_override is not None:
            return df_override
        return self._get_df_ifd_val()

    def _validate_escopo(self, escopo: str) -> None:
        """
        Valida se o escopo fornecido é válido.
        
        Args:
            escopo: Escopo a validar
            
        Raises:
            InvalidScopeError: Se o escopo não for válido
        """
        if escopo not in self.VALID_ESCOPOS:
            raise InvalidScopeError(
                scope_name='escopo',
                value=escopo,
                valid_values=list(self.VALID_ESCOPOS),
                context='Escopo deve ser explicitamente especificado como "individual", "prudencial" ou "financeiro"'
            )

    def resolve_ids_for_scope(self, resolved_entity: ResolvedEntity, escopo: str) -> str:
        """
        Resolve o identificador de busca necessário para o escopo informado.
        
        Args:
            resolved_entity: Entidade já resolvida
            escopo: Escopo OBRIGATÓRIO ('individual', 'prudencial', 'financeiro')
            
        Returns:
            ID único para busca (string)
            
        Raises:
            InvalidScopeError: Se o escopo não for válido
            DataUnavailableError: Se o escopo não estiver disponível para a entidade
        """
        # Valida escopo obrigatório
        self._validate_escopo(escopo)
        
        cnpj_8 = resolved_entity.cnpj_interesse
        if not cnpj_8:
            raise DataUnavailableError(
                entity=resolved_entity.identificador_original,
                scope_type=escopo,
                reason="Entidade não possui CNPJ de interesse",
                suggestions=["Verifique se o identificador foi resolvido corretamente"]
            )

        df_ifd_cad = self._get_df_ifd_cad()
        entry_cad = df_ifd_cad[df_ifd_cad['CNPJ_8'] == cnpj_8].sort_values('DATA', ascending=False)

        if escopo == 'individual':
            return cnpj_8
        elif escopo == 'prudencial':
            cod_congl_prud = resolved_entity.cod_congl_prud
            if not cod_congl_prud or pd.isna(cod_congl_prud):
                raise DataUnavailableError(
                    entity=resolved_entity.identificador_original,
                    scope_type=escopo,
                    reason="Entidade não possui código de conglomerado prudencial",
                    suggestions=[
                        "Esta entidade pode não fazer parte de um conglomerado prudencial",
                        "Tente usar escopo 'individual'"
                    ]
                )
            return str(cod_congl_prud)
        elif escopo == 'financeiro':
            if entry_cad.empty:
                raise DataUnavailableError(
                    entity=resolved_entity.identificador_original,
                    scope_type=escopo,
                    reason="Entidade não possui registro no cadastro IFDATA",
                    suggestions=["Verifique se a entidade possui dados cadastrais"]
                )
            cod_congl_fin = entry_cad.iloc[0].get('COD_CONGL_FIN_IFD_CAD')
            if not cod_congl_fin or pd.isna(cod_congl_fin):
                raise DataUnavailableError(
                    entity=resolved_entity.identificador_original,
                    scope_type=escopo,
                    reason="Entidade não possui código de conglomerado financeiro",
                    suggestions=[
                        "Esta entidade pode não fazer parte de um conglomerado financeiro",
                        "Tente usar escopo 'individual' ou 'prudencial'"
                    ]
                )
            return str(cod_congl_fin)
        
        # Não deveria chegar aqui devido à validação, mas por segurança:
        raise InvalidScopeError(
            scope_name='escopo',
            value=escopo,
            valid_values=list(self.VALID_ESCOPOS)
        )

    def build_subset(
        self,
        ids_para_buscar: Union[str, List[str]],
        datas: List[int],
        contas: List[Union[str, int]]
    ) -> pd.DataFrame:
        """Constrói um recorte otimizado do DataFrame IFDATA Valores."""
        # Normaliza ids_para_buscar para lista
        if isinstance(ids_para_buscar, str):
            ids_para_buscar = [ids_para_buscar]
        
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
        escopo: str,
        df_ifd_val_override: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Busca dados IFDATA com escopo obrigatório.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            contas: Lista de nomes ou códigos de contas IFDATA
            datas: Data única ou lista de datas no formato YYYYMM
            escopo: Escopo OBRIGATÓRIO da busca ('individual', 'prudencial', 'financeiro')
            df_ifd_val_override: DataFrame override para otimização (uso interno)
            
        Returns:
            DataFrame com os dados solicitados, incluindo colunas 'Nome_Entidade', 'CNPJ_8' e 'ID_BUSCA_USADO'
            
        Raises:
            InvalidScopeError: Se o escopo não for válido
            EntityNotFoundError: Se a entidade não for encontrada
            DataUnavailableError: Se os dados não estiverem disponíveis para o contexto
        """
        # Resolve identificadores canônicos (find_cnpj lança exceção se não encontrar)
        cnpj_8 = self._entity_resolver.find_cnpj(identificador)
        
        resolved = self._entity_resolver.resolve_full(identificador)
        nome_entidade_canonico = resolved.nome_entidade or identificador
        
        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]
        
        # Resolve ID único para o escopo especificado
        id_busca = self.resolve_ids_for_scope(resolved, escopo)

        # Busca dados usando o ID específico
        df_ifd_val = self._select_df_ifd_val(df_ifd_val_override)
        
        filtro_base = (df_ifd_val['COD_INST_IFD_VAL'] == id_busca) & (df_ifd_val['DATA'].isin(datas))
        
        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, (int, float))]
        
        filtro_nomes = df_ifd_val['NOME_CONTA_IFD_VAL'].isin(nomes_busca)
        filtro_codigos = df_ifd_val['CONTA_IFD_VAL'].isin(codigos_busca)
        filtro_conta = filtro_nomes | filtro_codigos
        
        df_resultado = df_ifd_val[filtro_base & filtro_conta].copy()
        
        if df_resultado.empty:
            raise DataUnavailableError(
                entity=identificador,
                scope_type=escopo,
                reason=f"Nenhum dado encontrado para ID {id_busca} nas datas {datas} com escopo '{escopo}'",
                suggestions=[
                    "Verifique se há dados para o escopo especificado",
                    "Verifique se as datas estão disponíveis",
                    "Verifique se os nomes ou códigos das contas estão corretos"
                ]
            )
        
        df_resultado['ID_BUSCA_USADO'] = id_busca
        df_resultado['Nome_Entidade'] = nome_entidade_canonico
        df_resultado['CNPJ_8'] = resolved.cnpj_interesse
        
        # Remove duplicatas
        df_resultado.drop_duplicates(inplace=True)
        
        # Reordena colunas
        cols_base = list(df_resultado.columns)
        cols_prioritarias = ['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO']
        cols_restantes = [c for c in cols_base if c not in cols_prioritarias]
        
        ordem_final = cols_prioritarias + cols_restantes
        return df_resultado.reset_index(drop=True)[ordem_final]

    def get_dados_with_resolved(
        self,
        resolved_entity: ResolvedEntity,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        escopo: str,
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
            escopo: Escopo OBRIGATÓRIO da busca ('individual', 'prudencial', 'financeiro')
            df_ifd_val_override: DataFrame override para otimização (uso interno)

        Returns:
            DataFrame com os dados solicitados

        Raises:
            InvalidScopeError: Se o escopo não for válido
            DataUnavailableError: Se os dados não estiverem disponíveis para o contexto
        """
        # Usa entidade já resolvida
        cnpj_8 = resolved_entity.cnpj_interesse
        if not cnpj_8:
            raise DataUnavailableError(
                entity=resolved_entity.identificador_original,
                scope_type=escopo,
                reason="Entidade resolvida não possui CNPJ de interesse",
                suggestions=["Verifique se o identificador foi resolvido corretamente"]
            )

        nome_entidade_canonico = resolved_entity.nome_entidade or resolved_entity.identificador_original

        # Normaliza datas
        if not isinstance(datas, list):
            datas = [datas]

        # Resolve ID único para o escopo especificado
        id_busca = self.resolve_ids_for_scope(resolved_entity, escopo)

        # Busca dados usando o ID específico
        df_ifd_val = self._select_df_ifd_val(df_ifd_val_override)

        filtro_base = (df_ifd_val['COD_INST_IFD_VAL'] == id_busca) & (df_ifd_val['DATA'].isin(datas))

        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, (int, float))]

        filtro_nomes = df_ifd_val['NOME_CONTA_IFD_VAL'].isin(nomes_busca)
        filtro_codigos = df_ifd_val['CONTA_IFD_VAL'].isin(codigos_busca)
        filtro_conta = filtro_nomes | filtro_codigos

        df_resultado = df_ifd_val[filtro_base & filtro_conta].copy()

        if df_resultado.empty:
            raise DataUnavailableError(
                entity=resolved_entity.identificador_original,
                scope_type=escopo,
                reason=f"Nenhum dado encontrado para ID {id_busca} nas datas {datas} com escopo '{escopo}'",
                suggestions=[
                    "Verifique se há dados para o escopo especificado",
                    "Verifique se as datas estão disponíveis",
                    "Verifique se os nomes ou códigos das contas estão corretos"
                ]
            )

        df_resultado['ID_BUSCA_USADO'] = id_busca
        df_resultado['Nome_Entidade'] = nome_entidade_canonico
        df_resultado['CNPJ_8'] = cnpj_8

        # Remove duplicatas
        df_resultado.drop_duplicates(inplace=True)

        # Reordena colunas
        cols_base = list(df_resultado.columns)
        cols_prioritarias = ['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO']
        cols_restantes = [c for c in cols_base if c not in cols_prioritarias]

        ordem_final = cols_prioritarias + cols_restantes
        return df_resultado.reset_index(drop=True)[ordem_final]

