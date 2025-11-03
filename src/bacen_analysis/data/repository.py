"""
Repository Pattern para acesso aos dados carregados
"""

import pandas as pd
from typing import Optional
from bacen_analysis.data.loader import DataLoader


class DataRepository:
    """
    Interface de acesso aos dados carregados (Repository Pattern).
    
    Single Responsibility: Prover acesso unificado aos DataFrames carregados.
    """
    
    def __init__(self, data_loader: DataLoader):
        """
        Inicializa o repositório com um DataLoader.

        Args:
            data_loader: Instância de DataLoader para carregar os dados
        """
        self._loader = data_loader
        self._loaded = False
        # Cache direto dos DataFrames (lazy loading)
        self._df_cosif_ind: Optional[pd.DataFrame] = None
        self._df_cosif_prud: Optional[pd.DataFrame] = None
        self._df_ifd_val: Optional[pd.DataFrame] = None
        self._df_ifd_cad: Optional[pd.DataFrame] = None

    def load(self) -> None:
        """Carrega todos os dados em memória."""
        if not self._loaded:
            dados = self._loader.load_all()
            # Armazena como atributos diretos para acesso O(1)
            self._df_cosif_ind = dados['cosif_ind']
            self._df_cosif_prud = dados['cosif_prud']
            self._df_ifd_val = dados['ifd_val']
            self._df_ifd_cad = dados['ifd_cad']
            self._loaded = True

    @property
    def df_cosif_ind(self) -> pd.DataFrame:
        """Retorna DataFrame de COSIF individual."""
        if not self._loaded:
            self.load()
        return self._df_cosif_ind

    @property
    def df_cosif_prud(self) -> pd.DataFrame:
        """Retorna DataFrame de COSIF prudencial."""
        if not self._loaded:
            self.load()
        return self._df_cosif_prud

    @property
    def df_ifd_val(self) -> pd.DataFrame:
        """Retorna DataFrame de IFDATA valores."""
        if not self._loaded:
            self.load()
        return self._df_ifd_val

    @property
    def df_ifd_cad(self) -> pd.DataFrame:
        """Retorna DataFrame de IFDATA cadastro."""
        if not self._loaded:
            self.load()
        return self._df_ifd_cad

    def reload(self) -> None:
        """Recarrega todos os dados (útil após atualizações)."""
        self._loaded = False
        self.load()

    def get_stats(self) -> dict[str, int]:
        """
        Retorna estatísticas sobre os dados carregados.

        Returns:
            Dicionário com número de linhas por fonte
        """
        if not self._loaded:
            self.load()

        return {
            'cosif_ind': len(self._df_cosif_ind),
            'cosif_prud': len(self._df_cosif_prud),
            'ifd_val': len(self._df_ifd_val),
            'ifd_cad': len(self._df_ifd_cad),
        }

