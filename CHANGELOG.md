# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

**Última atualização:** 2025-11-03 16:06:33 UTC

## [Unreleased]

### 🔄 Changed

#### `IndicadorComparator`

- **Melhorado:** Agora trata `EntityNotFoundError` de forma tolerante
- **Comportamento:** Quando uma entidade não é encontrada, emite um warning e continua a comparação com entidades válidas
- **Mudado:** Entidades não encontradas são incluídas no resultado com valores `None` em vez de interromper a comparação
- **Benefício:** Permite análises comparativas mesmo quando alguns identificadores são inválidos

```python
# Agora funciona mesmo se alguns identificadores forem inválidos
comparacao = analisador.comparar_indicadores(
    identificadores=['00000000', 'INVALIDO', '11111111'],
    indicadores=[...],
    data=202403
)
# Warning: Entidade(s) não encontrada(s): 'INVALIDO'. Serão incluídas no resultado com valores None.
# Comparação continua normalmente para '00000000' e '11111111'
```

#### `TimeSeriesProvider`

- **Melhorado:** Agora trata `EntityNotFoundError` de forma tolerante em `get_series_temporais_lote()`
- **Comportamento:** Quando uma entidade não é encontrada, emite um warning e ignora requisições para essa entidade
- **Mudado:** Requisições para entidades não encontradas são ignoradas em vez de interromper todo o processamento
- **Benefício:** Permite processamento em lote mesmo quando alguns identificadores são inválidos

```python
# Agora funciona mesmo se alguns identificadores forem inválidos
series = analisador.get_series_temporais_lote([
    {'identificador': '00000000', ...},
    {'identificador': 'INVALIDO', ...},  # Será ignorado com warning
    {'identificador': '11111111', ...}
])
# Warning: Entidade(s) não encontrada(s): 'INVALIDO'. As requisições para essas entidades serão ignoradas.
# Processamento continua normalmente para outras entidades
```

---

## [2.0.1] - 2025-11-03 01:03:55 UTC

### ✨ Added

#### Exportação de Exceções na API Pública

- **Adicionado:** Exceções customizadas agora podem ser importadas diretamente de `bacen_analysis`
- Facilita o tratamento de erros sem precisar importar de módulos internos

```python
from bacen_analysis import (
    AnalisadorBancario,
    InvalidScopeError,
    EntityNotFoundError,
    DataUnavailableError,
    AmbiguousIdentifierError
)
```

### 🔄 Changed

#### `IndicadorComparator`

- **Melhorado:** Agora captura `DataUnavailableError` para permitir comparações parciais
- **Comportamento:** Se um indicador não estiver disponível para uma entidade, a comparação continua com outras entidades
- **Benefício:** Tolerância a falhas - permite análises mesmo quando alguns dados estão faltando
- **Mudado:** Parâmetro `documento_cosif` agora deve ser especificado na configuração do indicador COSIF (removido do método `comparar()`)

```python
# Agora funciona mesmo se alguns dados não estiverem disponíveis
comparacao = analisador.comparar_indicadores(
    identificadores=['00000000', '11111111'],
    indicadores=[
        {
            'nome': 'Ativo Total',
            'tipo': 'COSIF',
            'tipo_cosif': 'prudencial',
            'documento_cosif': 4060  # Agora especificado no indicador
        }
    ],
    data=202403
)
# Se '00000000' não tiver dados, a comparação ainda funciona para '11111111'
```

#### `TimeSeriesProvider`

- **Melhorado:** Tratamento mais robusto de `DataUnavailableError` em `get_series_temporais_lote()`
- **Melhorado:** Validação mais rigorosa de parâmetros obrigatórios (`documento_cosif` e `tipo_cosif` para COSIF)
- **Melhorado:** Ignora requisições inválidas (sem escopo/tipo) em lote, continuando com as válidas
- **Mudado:** Parâmetros `documento_cosif`, `tipo_cosif` e `escopo_ifdata` agora são obrigatórios quando necessário

#### `COSIFDataProvider`

- **Melhorado:** Validação mais robusta de `documento_cosif` obrigatório
- **Melhorado:** Mensagens de erro mais descritivas quando dados não estão disponíveis
- **Adicionado:** Método `_normalize_documentos()` para melhor tratamento de documentos

#### `IFDATADataProvider`

- **Melhorado:** Método `build_subset()` agora aceita `str` ou `List[str]` para `ids_para_buscar`
- **Melhorado:** Validação mais clara quando escopo não está disponível para uma entidade

#### `AnalisadorBancario`

- **Melhorado:** Uso de logger em vez de `print()` para melhor controle de logs
- **Atualizado:** Documentação reflete mudanças nos parâmetros obrigatórios

#### Configuração do Projeto

- **Adicionado:** Arquivo `.gitattributes` para normalização consistente de line endings entre plataformas
  - Configuração automática de LF/CRLF baseada no tipo de arquivo
  - Melhora compatibilidade entre diferentes sistemas operacionais
  - Arquivos Python, configuração e documentação usam LF
  - Scripts Windows (.bat, .cmd, .ps1) usam CRLF
- **Melhorado:** `.gitignore` atualizado para ignorar arquivos do Cursor IDE (`.cursor`)

#### Notebooks de Exemplo

- **Atualizado:** `notebooks/analysis/example.ipynb` e `notebooks/analysis/full_table.ipynb` com exemplos atualizados para v2.0.1
  - Refletem novos parâmetros obrigatórios (`escopo`, `tipo`)
  - Incluem exemplos de tratamento de exceções customizadas
  - Atualizados para usar a nova API com imports diretos de `bacen_analysis`
  - Exemplos demonstram uso correto de `escopo_ifdata` e `tipo_cosif` obrigatórios

### 🔧 Fixed

- Corrigida validação de `documento_cosif` em `comparar_indicadores()` - agora deve ser especificado na configuração do indicador
- Corrigido tratamento de requisições sem escopo/tipo em `get_series_temporais_lote()` - agora ignora requisições inválidas graciosamente
- Corrigida documentação no README removendo referências ao escopo `'cascata'` removido
- Melhorado tratamento de casos onde dados não estão disponíveis - não interrompe comparações parciais

### 📚 Documentação

- Atualizado README.md removendo referências ao escopo `'cascata'` que foi removido na v2.0.0
- Adicionados exemplos de uso das exceções na API pública
- Melhoradas docstrings indicando quando parâmetros são obrigatórios

---

## [2.0.0] - 2025-11-03 00:01:59 UTC

### 🔴 Breaking Changes

#### Parâmetros de Escopo e Tipo Agora São Obrigatórios

**IFDATA - Parâmetro `escopo` obrigatório:**
- ❌ **Removido:** Valor padrão `'cascata'` para o parâmetro `escopo` em métodos IFDATA
- ✅ **Agora obrigatório:** O parâmetro `escopo` deve ser especificado explicitamente
- ✅ **Valores válidos:** `'individual'`, `'prudencial'`, `'financeiro'`
- 📍 **Afeta:** `get_dados_ifdata()`, `get_serie_temporal()`, `comparar_indicadores()`

```python
# ❌ ANTES (não funciona mais)
dados = analisador.get_dados_ifdata(
    identificador='00000000',
    contas=['Ativo Total'],
    datas=202403
)

# ✅ AGORA (obrigatório especificar escopo)
dados = analisador.get_dados_ifdata(
    identificador='00000000',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'  # OBRIGATÓRIO
)
```

**COSIF - Parâmetro `tipo` obrigatório:**
- ❌ **Removido:** Valor padrão `'prudencial'` para o parâmetro `tipo` em métodos COSIF
- ✅ **Agora obrigatório:** O parâmetro `tipo` deve ser especificado explicitamente
- ✅ **Valores válidos:** `'prudencial'`, `'individual'`
- 📍 **Afeta:** `get_dados_cosif()`, `get_serie_temporal()`, `comparar_indicadores()`

```python
# ❌ ANTES (não funciona mais)
dados = analisador.get_dados_cosif(
    identificador='00000000',
    contas=['ATIVO TOTAL'],
    datas=202403
)

# ✅ AGORA (obrigatório especificar tipo)
dados = analisador.get_dados_cosif(
    identificador='00000000',
    contas=['ATIVO TOTAL'],
    datas=202403,
    tipo='prudencial'  # OBRIGATÓRIO
)
```

#### Mudança no Comportamento de Retorno de Erros

- ❌ **Antes:** Métodos retornavam DataFrames vazios quando dados não eram encontrados
- ✅ **Agora:** Métodos lançam exceções específicas quando:
  - Entidade não encontrada
  - Escopo/tipo inválido ou não especificado
  - Dados não disponíveis para o contexto especificado
  - Identificador ambíguo (múltiplas correspondências)

```python
# ❌ ANTES (retornava DataFrame vazio)
dados = analisador.get_dados_cosif(...)
if dados.empty:
    print("Nenhum dado encontrado")

# ✅ AGORA (lança exceção)
try:
    dados = analisador.get_dados_cosif(...)
except EntityNotFoundError as e:
    print(f"Entidade não encontrada: {e}")
except DataUnavailableError as e:
    print(f"Dados não disponíveis: {e}")
```

### ✨ Added

#### Sistema de Exceções Customizadas

Novo módulo `bacen_analysis.exceptions` com as seguintes exceções:

- **`BacenAnalysisError`**: Exceção base para todos os erros da biblioteca
- **`InvalidScopeError`**: Lançada quando escopo ou tipo é inválido ou não especificado
- **`DataUnavailableError`**: Lançada quando dados não estão disponíveis para o contexto
- **`EntityNotFoundError`**: Lançada quando uma entidade não é encontrada
- **`AmbiguousIdentifierError`**: Lançada quando um identificador é ambíguo

Todas as exceções incluem mensagens descritivas e sugestões para o usuário.

```python
from bacen_analysis import (
    BacenAnalysisError,
    InvalidScopeError,
    EntityNotFoundError,
    DataUnavailableError,
    AmbiguousIdentifierError
)

try:
    dados = analisador.get_dados_ifdata(...)
except InvalidScopeError as e:
    print(f"Escopo inválido: {e}")
    print(f"Valores válidos: {e.valid_values}")
except EntityNotFoundError as e:
    print(f"Entidade não encontrada: {e}")
    print(f"Sugestões: {e.suggestions}")
```

#### Sistema de Logging

Novo módulo `bacen_analysis.utils.logger` com logging estruturado:

- Substituição de `print()` por logging em `AnalisadorBancario`
- Formatação consistente de mensagens de log
- Configuração de níveis de logging

```python
from bacen_analysis.utils.logger import set_log_level
import logging

# Configurar nível de log
set_log_level(logging.DEBUG)
```

### 🔄 Changed

#### `COSIFDataProvider`

- **Removido:** Método `determine_tipo()` (lógica simplificada)
- **Removido:** Constante `DOC_TO_TIPO_MAP` (não mais necessário)
- **Adicionado:** Método `_validate_tipo()` para validação de tipo
- **Adicionado:** Método `_normalize_documentos()` para normalização
- **Adicionado:** Método `_check_data_availability()` para verificação de dados
- **Mudado:** Parâmetro `tipo` agora é obrigatório (sem valor padrão)
- **Mudado:** Retorna exceções em vez de DataFrames vazios

#### `IFDATADataProvider`

- **Removido:** Suporte ao escopo `'cascata'`
- **Mudado:** Método `resolve_ids_for_scope()` agora retorna `str` em vez de `List[str]`
- **Adicionado:** Método `_validate_escopo()` para validação de escopo
- **Mudado:** Parâmetro `escopo` agora é obrigatório (sem valor padrão)
- **Mudado:** Lógica simplificada para buscar um único ID por escopo
- **Mudado:** Retorna exceções em vez de DataFrames vazios

#### `EntityIdentifierResolver`

- **Mudado:** `find_cnpj()` agora lança `EntityNotFoundError` em vez de retornar `None`
- **Mudado:** `find_cnpj()` agora lança `AmbiguousIdentifierError` para identificadores ambíguos
- **Removido:** Avisos via `print()` substituídos por exceções

#### `TimeSeriesProvider`

- **Mudado:** Parâmetros `tipo_cosif` e `escopo_ifdata` agora são obrigatórios quando necessários
- **Adicionado:** Validações no início do método `get_serie_temporal()`
- **Adicionado:** Tratamento de requisições sem escopo/tipo no método `get_series_temporais_lote()`

#### `IndicadorComparator`

- **Adicionado:** Validação de `tipo_cosif` obrigatório para indicadores COSIF
- **Adicionado:** Validação de `escopo_ifdata` obrigatório para indicadores IFDATA
- **Mudado:** Uso correto dos novos métodos dos providers

#### `AnalisadorBancario`

- **Mudado:** Substituição de `print()` por `logger.info()` para mensagens informativas
- **Mudado:** Documentação atualizada para refletir parâmetros obrigatórios
- **Mudado:** Métodos delegam corretamente para providers com novos parâmetros

### 🔧 Fixed

- Corrigidas referências remanescentes ao escopo `'cascata'` que não foram removidas durante a refatoração
- Corrigida documentação que ainda mencionava valores padrão removidos
- Corrigido comportamento inconsistente entre métodos públicos e privados

### 📝 Migration Guide

#### Atualizar Chamadas de `get_dados_ifdata()`

```python
# ❌ ANTES
dados = analisador.get_dados_ifdata(
    identificador='00000000',
    contas=['Ativo Total'],
    datas=202403
)

# ✅ AGORA
dados = analisador.get_dados_ifdata(
    identificador='00000000',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'  # OBRIGATÓRIO: 'individual', 'prudencial' ou 'financeiro'
)
```

#### Atualizar Chamadas de `get_dados_cosif()`

```python
# ❌ ANTES
dados = analisador.get_dados_cosif(
    identificador='00000000',
    contas=['ATIVO TOTAL'],
    datas=202403
)

# ✅ AGORA
dados = analisador.get_dados_cosif(
    identificador='00000000',
    contas=['ATIVO TOTAL'],
    datas=202403,
    tipo='prudencial'  # OBRIGATÓRIO: 'prudencial' ou 'individual'
)
```

#### Atualizar Chamadas de `get_serie_temporal()`

```python
# ❌ ANTES - COSIF
serie = analisador.get_serie_temporal(
    identificador='00000000',
    conta='ATIVO TOTAL',
    fonte='COSIF'
)

# ✅ AGORA - COSIF
serie = analisador.get_serie_temporal(
    identificador='00000000',
    conta='ATIVO TOTAL',
    fonte='COSIF',
    tipo_cosif='prudencial'  # OBRIGATÓRIO
)

# ❌ ANTES - IFDATA
serie = analisador.get_serie_temporal(
    identificador='00000000',
    conta='Ativo Total',
    fonte='IFDATA'
)

# ✅ AGORA - IFDATA
serie = analisador.get_serie_temporal(
    identificador='00000000',
    conta='Ativo Total',
    fonte='IFDATA',
    escopo_ifdata='prudencial'  # OBRIGATÓRIO
)
```

#### Atualizar Tratamento de Erros

```python
# ❌ ANTES
dados = analisador.get_dados_cosif(...)
if dados.empty:
    print("Nenhum dado encontrado")

# ✅ AGORA
from bacen_analysis import (
    EntityNotFoundError,
    DataUnavailableError,
    InvalidScopeError
)

try:
    dados = analisador.get_dados_cosif(...)
except EntityNotFoundError as e:
    print(f"Entidade não encontrada: {e}")
    # Usar sugestões: e.suggestions
except DataUnavailableError as e:
    print(f"Dados não disponíveis: {e}")
    # Verificar: e.entity, e.scope_type, e.reason
except InvalidScopeError as e:
    print(f"Escopo inválido: {e}")
    # Ver valores válidos: e.valid_values
```

#### Atualizar `comparar_indicadores()`

```python
# ❌ ANTES
comparacao = analisador.comparar_indicadores(
    identificadores=['00000000'],
    indicadores=[
        {'nome': 'Ativo Total', 'tipo': 'IFDATA'},  # Sem escopo
        {'nome': 'ATIVO TOTAL', 'tipo': 'COSIF'}    # Sem tipo
    ],
    datas=202403
)

# ✅ AGORA
comparacao = analisador.comparar_indicadores(
    identificadores=['00000000'],
    indicadores=[
        {
            'nome': 'Ativo Total',
            'tipo': 'IFDATA',
            'escopo_ifdata': 'prudencial'  # OBRIGATÓRIO
        },
        {
            'nome': 'ATIVO TOTAL',
            'tipo': 'COSIF',
            'tipo_cosif': 'prudencial',     # OBRIGATÓRIO
            'conta': 'ATIVO TOTAL'          # Também obrigatório
        }
    ],
    datas=202403
)
```

### 📚 Documentação

- Adicionadas docstrings atualizadas em todos os métodos modificados
- Documentadas exceções customizadas e seus usos
- Atualizadas informações sobre parâmetros obrigatórios

---

## [1.x.x] - Versões Anteriores

Versões anteriores não utilizavam este changelog estruturado.

