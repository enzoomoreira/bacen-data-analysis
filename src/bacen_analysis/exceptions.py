"""
Exceções customizadas para a biblioteca Bacen Data Analysis
"""


class BacenAnalysisError(Exception):
    """
    Exceção base para todos os erros na biblioteca Bacen Data Analysis.
    
    Esta classe serve como base para todas as exceções específicas,
    permitindo que usuários capturem qualquer erro da biblioteca
    usando `except BacenAnalysisError:`.
    """
    pass


class InvalidScopeError(BacenAnalysisError):
    """
    Exceção levantada quando um escopo ou tipo é inválido ou não especificado.
    
    Args:
        scope_name: Nome do parâmetro de escopo (ex: 'tipo', 'escopo')
        value: Valor fornecido (ou None se não fornecido)
        valid_values: Lista de valores válidos
        context: Contexto adicional para ajudar na mensagem de erro
    """
    def __init__(self, scope_name: str, value=None, valid_values=None, context=None):
        self.scope_name = scope_name
        self.value = value
        self.valid_values = valid_values or []
        
        if value is None:
            msg = f"O parâmetro '{scope_name}' é obrigatório e deve ser especificado."
        elif valid_values and value not in valid_values:
            msg = (
                f"O valor '{value}' é inválido para o parâmetro '{scope_name}'. "
                f"Valores válidos: {', '.join(repr(v) for v in valid_values)}."
            )
        else:
            msg = f"O parâmetro '{scope_name}' tem um valor inválido: {value}."
        
        if context:
            msg += f" Contexto: {context}"
        
        super().__init__(msg)


class DataUnavailableError(BacenAnalysisError):
    """
    Exceção levantada quando os dados solicitados não estão disponíveis
    para o contexto especificado.
    
    Args:
        entity: Identificador da entidade (nome ou CNPJ)
        scope_type: Tipo de escopo que foi solicitado
        reason: Razão pela qual os dados não estão disponíveis
        suggestions: Lista de sugestões para o usuário
    """
    def __init__(self, entity: str, scope_type: str, reason: str = None, suggestions=None):
        self.entity = entity
        self.scope_type = scope_type
        self.reason = reason
        self.suggestions = suggestions or []
        
        msg = (
            f"Dados não disponíveis para a entidade '{entity}' "
            f"com escopo/tipo '{scope_type}'."
        )
        
        if reason:
            msg += f" Razão: {reason}"
        
        if self.suggestions:
            msg += f" Sugestões: {', '.join(self.suggestions)}"
        
        super().__init__(msg)


class EntityNotFoundError(BacenAnalysisError):
    """
    Exceção levantada quando uma entidade não é encontrada no mapeamento.
    
    Args:
        identifier: Identificador usado na busca
        suggestions: Lista de sugestões para o usuário
    """
    def __init__(self, identifier: str, suggestions=None):
        self.identifier = identifier
        self.suggestions = suggestions or []
        
        msg = f"Entidade não encontrada para o identificador '{identifier}'."
        
        if self.suggestions:
            msg += f" Sugestões: {', '.join(self.suggestions)}"
        
        super().__init__(msg)


class AmbiguousIdentifierError(BacenAnalysisError):
    """
    Exceção levantada quando um identificador é ambíguo,
    resultando em múltiplas correspondências.
    
    Args:
        identifier: Identificador usado na busca
        matches: Lista de correspondências encontradas
        suggestion: Sugestão para resolver a ambiguidade
    """
    def __init__(self, identifier: str, matches=None, suggestion=None):
        self.identifier = identifier
        self.matches = matches or []
        self.suggestion = suggestion
        
        msg = (
            f"O identificador '{identifier}' é ambíguo. "
            f"Encontradas {len(self.matches)} correspondências."
        )
        
        if self.matches:
            matches_str = ', '.join(repr(m) for m in self.matches[:5])
            if len(self.matches) > 5:
                matches_str += f" (e mais {len(self.matches) - 5})"
            msg += f" Correspondências: {matches_str}"
        
        if self.suggestion:
            msg += f" Sugestão: {self.suggestion}"
        
        super().__init__(msg)

