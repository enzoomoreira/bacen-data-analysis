"""
Utilitários para limpeza de texto
"""

import pandas as pd
import re
from typing import Union


def clean_text_column(series: pd.Series) -> pd.Series:
    """
    Limpa colunas de texto removendo caracteres de controle ASCII e normalizando espaços.
    
    Remove caracteres de controle ASCII (0x00-0x1F e 0x7F), normaliza espaços múltiplos
    para um único espaço e remove espaços em branco nas extremidades.
    
    Args:
        series: Pandas Series com valores de texto a serem limpos
        
    Returns:
        Pandas Series com valores limpos
    """
    def _clean_text(text):
        if pd.isna(text):
            return ''
        
        text_str = str(text)
        # Remove caracteres de controle ASCII (0x00-0x1F e 0x7F)
        text_str = re.sub(r'[\x00-\x1F\x7F]', '', text_str)
        # Normaliza espaços múltiplos para um único espaço
        text_str = re.sub(r'\s+', ' ', text_str)
        # Remove espaços em branco nas extremidades
        text_str = text_str.strip()
        
        return text_str
    
    return series.apply(_clean_text)

