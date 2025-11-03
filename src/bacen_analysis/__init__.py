"""
Bacen Data Analysis - Análise de dados financeiros do Banco Central do Brasil
"""

from bacen_analysis.core.analyser import AnalisadorBancario
from bacen_analysis.utils.cnpj import standardize_cnpj_base8
from bacen_analysis.exceptions import (
    BacenAnalysisError,
    InvalidScopeError,
    DataUnavailableError,
    EntityNotFoundError,
    AmbiguousIdentifierError
)

__all__ = [
    'AnalisadorBancario',
    'standardize_cnpj_base8',
    'BacenAnalysisError',
    'InvalidScopeError',
    'DataUnavailableError',
    'EntityNotFoundError',
    'AmbiguousIdentifierError',
]

__version__ = '2.0.1'

