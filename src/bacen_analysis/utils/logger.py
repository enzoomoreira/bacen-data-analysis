"""
Configuração de logging para a biblioteca Bacen Data Analysis
"""

import logging
import sys
from typing import Optional


def get_logger(name: str = 'bacen_analysis') -> logging.Logger:
    """
    Retorna um logger configurado para a biblioteca.
    
    Args:
        name: Nome do logger (default: 'bacen_analysis')
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evita adicionar handlers múltiplas vezes
    if logger.handlers:
        return logger
    
    # Configura handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    return logger


def set_log_level(level: int) -> None:
    """
    Define o nível de logging global da biblioteca.
    
    Args:
        level: Nível de logging (logging.DEBUG, logging.INFO, etc.)
    """
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


