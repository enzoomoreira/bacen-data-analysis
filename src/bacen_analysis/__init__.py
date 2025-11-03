"""
Bacen Data Analysis - Análise de dados financeiros do Banco Central do Brasil
"""

from bacen_analysis.core.analyser import AnalisadorBancario
from bacen_analysis.utils.cnpj import standardize_cnpj_base8

__all__ = [
    'AnalisadorBancario',
    'standardize_cnpj_base8',
]

__version__ = '2.0.0'

