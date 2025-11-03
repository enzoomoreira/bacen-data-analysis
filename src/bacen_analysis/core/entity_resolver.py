"""
Resolvedor de identificadores de entidades (CNPJ/nomes)
"""

import pandas as pd
import re
from typing import Dict, Optional
from functools import lru_cache
from dataclasses import dataclass
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.exceptions import EntityNotFoundError, AmbiguousIdentifierError


@dataclass(frozen=True)
class ResolvedEntity:
    """
    Objeto imutável contendo todos os identificadores resolvidos de uma entidade.

    Uso de dataclass frozen=True permite hashability para @lru_cache e
    garante imutabilidade (thread-safe, sem side effects).

    Attributes:
        cnpj_interesse: CNPJ de 8 dígitos da entidade de interesse
        cnpj_reporte_cosif: CNPJ a usar para busca COSIF (pode ser do líder)
        cod_congl_prud: Código do conglomerado prudencial
        nome_entidade: Nome canônico da entidade
        identificador_original: Identificador usado na busca original (para debug)
    """
    cnpj_interesse: Optional[str]
    cnpj_reporte_cosif: Optional[str]
    cod_congl_prud: Optional[str]
    nome_entidade: Optional[str]
    identificador_original: str


class EntityIdentifierResolver:
    """
    Responsável por resolver identificadores (nomes/CNPJs) em CNPJs canônicos
    e metadados de entidades.
    
    Single Responsibility: Mapeamento e resolução de identificadores de entidades.
    """
    
    def __init__(self, repository: DataRepository):
        """
        Inicializa o resolvedor com um repositório de dados.
        
        Args:
            repository: Instância de DataRepository para acessar os dados
        """
        self._repository = repository
        self._mapa_nomes_df: Optional[pd.DataFrame] = None
        self._create_mapping()
    
    def _create_mapping(self) -> None:
        """Cria o mapeamento de nomes para CNPJs a partir dos dados carregados."""
        df_ifd_cad = self._repository.df_ifd_cad
        df_cosif_prud = self._repository.df_cosif_prud
        df_cosif_ind = self._repository.df_cosif_ind
        
        mapa1 = df_ifd_cad[['NOME_INSTITUICAO_IFD_CAD', 'CNPJ_8']].dropna().drop_duplicates()
        mapa2 = df_cosif_prud[['NOME_INSTITUICAO_COSIF', 'CNPJ_8']].dropna().drop_duplicates()
        mapa3 = df_cosif_ind[['NOME_INSTITUICAO_COSIF', 'CNPJ_8']].dropna().drop_duplicates()
        
        mapa1.columns = ['nome', 'cnpj_8']
        mapa2.columns = ['nome', 'cnpj_8']
        mapa3.columns = ['nome', 'cnpj_8']
        
        self._mapa_nomes_df = pd.concat([mapa1, mapa2, mapa3]).drop_duplicates(
            subset='nome', keep='first'
        ).reset_index(drop=True)
        self._mapa_nomes_df['nome_upper'] = self._mapa_nomes_df['nome'].str.strip().str.upper()
    
    @lru_cache(maxsize=256)
    def find_cnpj(self, identificador: str) -> str:
        """
        Encontra o CNPJ_8 a partir de um nome ou de um CNPJ.
        
        Args:
            identificador: Nome da instituição ou CNPJ de 8 dígitos
            
        Returns:
            CNPJ de 8 dígitos
            
        Raises:
            EntityNotFoundError: Se o identificador não for encontrado
            AmbiguousIdentifierError: Se o identificador for ambíguo
        """
        identificador_upper = identificador.strip().upper()
        
        # Se já é um CNPJ de 8 dígitos, retorna diretamente
        if re.fullmatch(r'\d{8}', identificador):
            return identificador
        
        # Busca exata
        match_exato = self._mapa_nomes_df[
            self._mapa_nomes_df['nome_upper'] == identificador_upper
        ]
        if not match_exato.empty:
            return match_exato['cnpj_8'].iloc[0]
        
        # Busca parcial (contains)
        match_contains = self._mapa_nomes_df[
            self._mapa_nomes_df['nome_upper'].str.contains(identificador_upper, na=False)
        ]
        if not match_contains.empty:
            # Se encontrou mais de um, lança exceção sobre a ambiguidade
            if len(match_contains) > 1:
                nomes_encontrados = match_contains['nome'].tolist()
                raise AmbiguousIdentifierError(
                    identifier=identificador,
                    matches=nomes_encontrados,
                    suggestion="Use um nome mais completo ou o CNPJ de 8 dígitos para maior precisão"
                )
            return match_contains['cnpj_8'].iloc[0]
        
        # Não encontrado
        raise EntityNotFoundError(
            identifier=identificador,
            suggestions=[
                "Verifique se o nome ou CNPJ está correto",
                "Use o CNPJ de 8 dígitos para maior precisão",
                "Verifique a grafia do nome da instituição"
            ]
        )
    
    @lru_cache(maxsize=256)
    def get_entity_identifiers(self, cnpj_8: str) -> Dict[str, Optional[str]]:
        """
        Obtém metadados completos da entidade a partir do CNPJ.
        
        Args:
            cnpj_8: CNPJ de 8 dígitos
            
        Returns:
            Dicionário com metadados:
            - 'cnpj_interesse': CNPJ da entidade de interesse
            - 'cnpj_reporte_cosif': CNPJ a usar para busca COSIF (pode ser líder)
            - 'cod_congl_prud': Código do conglomerado prudencial
            - 'nome_entidade': Nome canônico da entidade
        """
        info = {
            'cnpj_interesse': cnpj_8,
            'cnpj_reporte_cosif': cnpj_8,
            'cod_congl_prud': None,
            'nome_entidade': None
        }
        
        if not cnpj_8:
            return info
        
        df_ifd_cad = self._repository.df_ifd_cad
        entry_cad = df_ifd_cad[df_ifd_cad['CNPJ_8'] == cnpj_8].sort_values('DATA', ascending=False)
        
        if entry_cad.empty:
            return info
        
        linha_interesse = entry_cad.iloc[0]
        info['nome_entidade'] = linha_interesse.get('NOME_INSTITUICAO_IFD_CAD')
        
        cod_congl = linha_interesse.get('COD_CONGL_PRUD_IFD_CAD')
        if pd.notna(cod_congl):
            info['cod_congl_prud'] = cod_congl
            df_conglomerado = df_ifd_cad[df_ifd_cad['COD_CONGL_PRUD_IFD_CAD'] == cod_congl]
            df_lideres_potenciais = df_conglomerado.dropna(subset=['CNPJ_LIDER_8_IFD_CAD'])
            
            if not df_lideres_potenciais.empty:
                lider_info = df_lideres_potenciais.sort_values('DATA', ascending=False).iloc[0]
                cnpj_lider = lider_info.get('CNPJ_LIDER_8_IFD_CAD')
                if pd.notna(cnpj_lider):
                    info['cnpj_reporte_cosif'] = cnpj_lider
        
        return info

    @lru_cache(maxsize=256)
    def resolve_full(self, identificador: str) -> ResolvedEntity:
        """
        Resolve completamente um identificador em uma única operação.

        Este método combina find_cnpj() e get_entity_identifiers() para
        evitar chamadas duplicadas. Retorna um objeto imutável com todas
        as informações necessárias.

        Args:
            identificador: Nome da instituição ou CNPJ de 8 dígitos

        Returns:
            ResolvedEntity com todos os identificadores e metadados
            
        Raises:
            EntityNotFoundError: Se o identificador não for encontrado
            AmbiguousIdentifierError: Se o identificador for ambíguo
        """
        # find_cnpj() lança exceção se não encontrar, então cnpj_8 nunca será None
        cnpj_8 = self.find_cnpj(identificador)
        
        info = self.get_entity_identifiers(cnpj_8)

        return ResolvedEntity(
            cnpj_interesse=cnpj_8,
            cnpj_reporte_cosif=info.get('cnpj_reporte_cosif', cnpj_8),
            cod_congl_prud=info.get('cod_congl_prud'),
            nome_entidade=info.get('nome_entidade'),
            identificador_original=identificador
        )

    def clear_cache(self) -> None:
        """Limpa o cache LRU dos métodos com @lru_cache."""
        self.find_cnpj.cache_clear()
        self.get_entity_identifiers.cache_clear()
        self.resolve_full.cache_clear()
    
    def reload_mapping(self) -> None:
        """Recria o mapeamento de nomes (útil após atualizações nos dados)."""
        self._create_mapping()
        self.clear_cache()

