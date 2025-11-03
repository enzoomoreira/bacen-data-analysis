"""
Provedor de dados de cadastro
"""

import pandas as pd
from typing import List, Union, Optional
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver, ResolvedEntity
from bacen_analysis.exceptions import EntityNotFoundError


class CadastroProvider:
    """
    Responsável por consultas de dados cadastrais (IFDATA cadastro).
    
    Single Responsibility: Consultas de atributos cadastrais de entidades.
    """
    
    def __init__(self, repository: DataRepository, entity_resolver: EntityIdentifierResolver):
        """
        Inicializa o provedor de cadastro.

        Args:
            repository: Instância de DataRepository para acessar dados
            entity_resolver: Instância de EntityIdentifierResolver para resolver identificadores
        """
        self._repository = repository
        self._entity_resolver = entity_resolver
        # Cache local do DataFrame para evitar acesso via property em loops
        self._df_ifd_cad: Optional[pd.DataFrame] = None

    def _get_df_ifd_cad(self) -> pd.DataFrame:
        """Obtém DataFrame IFDATA cadastro com cache local."""
        if self._df_ifd_cad is None:
            self._df_ifd_cad = self._repository.df_ifd_cad
        return self._df_ifd_cad
    
    def get_atributos(
        self,
        identificador: Union[str, List[str]],
        atributos: List[str]
    ) -> pd.DataFrame:
        """
        Busca atributos (colunas) específicos do cadastro IFDATA,
        com colunas de identificação padronizadas.
        
        Args:
            identificador: Nome, CNPJ ou lista de identificadores de instituições
            atributos: Lista de nomes de atributos (colunas) do cadastro a serem retornados
            
        Returns:
            DataFrame com os atributos solicitados, incluindo colunas 'Nome_Entidade' e 'CNPJ_8'
        """
        if not isinstance(identificador, list):
            identificador = [identificador]

        resultados = []
        df_ifd_cad = self._get_df_ifd_cad()

        for ident in identificador:
            try:
                # find_cnpj lança exceção se não encontrar
                cnpj_8 = self._entity_resolver.find_cnpj(ident)
            except EntityNotFoundError:
                # Se não encontrar, continua com o próximo identificador
                continue
            
            info_ent = self._entity_resolver.get_entity_identifiers(cnpj_8)
            nome_entidade = info_ent.get('nome_entidade') or ident
            
            entry = df_ifd_cad[df_ifd_cad['CNPJ_8'] == cnpj_8]
            if not entry.empty:
                linha = entry.sort_values('DATA', ascending=False).iloc[0]
                
                # Constrói um dicionário com a saída padronizada
                dados_linha = {
                    'Nome_Entidade': nome_entidade,
                    'CNPJ_8': cnpj_8
                }
                for atr in atributos:
                    # Usa .get() para evitar erro se o atributo não existir na linha
                    dados_linha[atr] = linha.get(atr, None)
                
                resultados.append(dados_linha)
        
        if not resultados:
            # Retorna DF vazio com a estrutura de colunas correta
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + atributos)
        
        df_final = pd.DataFrame(resultados)
        
        # Garante a ordem das colunas
        ordem_final = ['Nome_Entidade', 'CNPJ_8'] + [
            atr for atr in atributos if atr in df_final.columns
        ]
        return df_final[ordem_final]

    def get_atributos_with_resolved(
        self,
        resolved_entities: Union[ResolvedEntity, List[ResolvedEntity]],
        atributos: List[str]
    ) -> pd.DataFrame:
        """
        Busca atributos usando entidades já resolvidas (otimizado).

        Este método evita a resolução duplicada de identificadores,
        melhorando performance em operações em lote.

        Args:
            resolved_entities: Entidade ou lista de entidades já resolvidas
            atributos: Lista de nomes de atributos (colunas) do cadastro

        Returns:
            DataFrame com os atributos solicitados
        """
        if not isinstance(resolved_entities, list):
            resolved_entities = [resolved_entities]

        resultados = []
        df_ifd_cad = self._get_df_ifd_cad()

        for resolved_entity in resolved_entities:
            cnpj_8 = resolved_entity.cnpj_interesse
            if not cnpj_8:
                continue

            nome_entidade = resolved_entity.nome_entidade or resolved_entity.identificador_original

            entry = df_ifd_cad[df_ifd_cad['CNPJ_8'] == cnpj_8]
            if not entry.empty:
                linha = entry.sort_values('DATA', ascending=False).iloc[0]

                # Constrói um dicionário com a saída padronizada
                dados_linha = {
                    'Nome_Entidade': nome_entidade,
                    'CNPJ_8': cnpj_8
                }
                for atr in atributos:
                    dados_linha[atr] = linha.get(atr, None)

                resultados.append(dados_linha)

        if not resultados:
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + atributos)

        df_final = pd.DataFrame(resultados)

        # Garante a ordem das colunas
        ordem_final = ['Nome_Entidade', 'CNPJ_8'] + [
            atr for atr in atributos if atr in df_final.columns
        ]
        return df_final[ordem_final]

