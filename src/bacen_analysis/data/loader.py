"""
Carregador de dados Parquet
"""

import pandas as pd
from pathlib import Path
from typing import Optional


class DataLoader:
    """
    Responsável por carregar arquivos Parquet do diretório de output.
    
    Single Responsibility: Carregamento e validação de arquivos Parquet.
    """
    
    def __init__(self, diretorio_output: str):
        """
        Inicializa o carregador com o diretório de output.
        
        Args:
            diretorio_output: Caminho para o diretório contendo os arquivos .parquet
            
        Raises:
            FileNotFoundError: Se algum arquivo necessário não for encontrado
        """
        self.base_path = Path(diretorio_output)
        
    def load_all(self) -> dict[str, pd.DataFrame]:
        """
        Carrega todos os arquivos Parquet necessários.
        
        Returns:
            Dicionário com os DataFrames carregados:
            - 'cosif_ind': DataFrame de COSIF individual
            - 'cosif_prud': DataFrame de COSIF prudencial
            - 'ifd_val': DataFrame de IFDATA valores
            - 'ifd_cad': DataFrame de IFDATA cadastro
            
        Raises:
            FileNotFoundError: Se algum arquivo não for encontrado
        """
        arquivos = {
            'cosif_ind': 'df_cosif_individual.parquet',
            'cosif_prud': 'df_cosif_prudencial.parquet',
            'ifd_val': 'df_ifdata_valores.parquet',
            'ifd_cad': 'df_ifdata_cadastro.parquet',
        }
        
        dados = {}
        for key, arquivo in arquivos.items():
            caminho = self.base_path / arquivo
            if not caminho.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {caminho}\n"
                    f"Verifique o caminho do diretório de output."
                )
            dados[key] = pd.read_parquet(caminho)
        
        return dados
    
    def get_file_path(self, arquivo: str) -> Path:
        """
        Retorna o caminho completo para um arquivo.
        
        Args:
            arquivo: Nome do arquivo (ex: 'df_cosif_individual.parquet')
            
        Returns:
            Path completo para o arquivo
        """
        return self.base_path / arquivo

