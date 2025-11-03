# Guia de Migração: v1.x → v2.0.1

Este guia detalha o processo de migração do `bacen-data-analysis` da versão 1.x para a versão 2.0.1, incluindo todas as mudanças necessárias e novos recursos disponíveis.

## Índice

- [Visão Geral das Mudanças](#visão-geral-das-mudanças)
- [Compatibilidade](#compatibilidade)
- [Passo a Passo da Migração](#passo-a-passo-da-migração)
- [Mudanças na API](#mudanças-na-api)
- [Novos Recursos Disponíveis](#novos-recursos-disponíveis)
- [Exemplos de Migração](#exemplos-de-migração)

---

## Visão Geral das Mudanças

A versão 2.0.1 representa uma **refatoração completa** da arquitetura do projeto:

### O Que Mudou

- **Estrutura**: Transformado em pacote Python instalável
- **Imports**: Sistema simplificado sem manipulação de `sys.path`
- **Arquitetura**: Código modular com separação clara de responsabilidades
- **Performance**: Otimizações significativas (cache LRU, busca em lote)
- **Type Hints**: Código completamente tipado
- **Exceções**: Sistema customizado de exceções

### O Que NÃO Mudou

- **API Pública**: Métodos mantêm assinaturas idênticas (exceto novo parâmetro `escopo_ifdata`)
- **Dados**: Formato e estrutura dos Parquets permanecem compatíveis
- **Notebooks ETL**: Funcionamento mantido (apenas otimizações internas)

---

## Compatibilidade

A v2.0.1 é **100% compatível** com código da v1.x, com as seguintes exceções:

### Breaking Changes

1. **Sistema de Imports**: Necessário atualizar todos os imports (detalhado abaixo)
2. **Parâmetro `escopo_ifdata`**: Agora **obrigatório** no método `get_dados_ifdata()`
3. **Remoção do escopo `'cascata'`**: Substituído por escopos explícitos

### Migração Recomendada

- **Código de produção**: Atualizar imports obrigatório
- **Notebooks antigos**: Funcionam após atualizar célula de imports
- **Scripts existentes**: Mínima alteração necessária

---

## Passo a Passo da Migração

### Passo 1: Instalar o Pacote

Na raiz do projeto, execute:

```bash
pip install -e .
```

Ou, para instalação completa:

```bash
pip install -e ".[all]"
```

**Nota**: Se já tinha o projeto clonado, apenas execute o comando acima. Não é necessário clonar novamente.

### Passo 2: Atualizar Imports em Todos os Arquivos

#### ANTES (v1.x)

```python
import sys
from pathlib import Path

# Manipulação manual de paths
code_dir = Path('.').resolve().parent / 'Code'
if str(code_dir) not in sys.path:
    sys.path.append(str(code_dir))

import DataUtils as du
from DataUtils import AnalisadorBancario
```

#### DEPOIS (v2.0.1)

```python
# Import direto, sem manipulação de paths
from bacen_analysis import AnalisadorBancario
```

**Benefícios**:
- Código mais limpo (5 linhas → 1 linha)
- Sem preocupação com caminhos relativos
- Funciona de qualquer diretório

### Passo 3: Adicionar Parâmetro `escopo` (IFDATA)

Se você usa `get_dados_ifdata()`, adicione o parâmetro `escopo`:

#### ANTES (v1.x)

```python
# Parâmetro escopo era opcional (padrão: 'cascata')
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403
    # escopo era opcional
)
```

#### DEPOIS (v2.0.1)

```python
# Parâmetro escopo é OBRIGATÓRIO
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'  # OBRIGATÓRIO: 'individual', 'prudencial' ou 'financeiro'
)
```

### Passo 4: Substituir Lógica de Cascata (Se Aplicável)

Se você dependia do comportamento `'cascata'` (tentar prudencial → financeiro → individual):

#### ANTES (v1.x)

```python
# Escopo 'cascata' tentava automaticamente em ordem
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='cascata'  # Tentava: prudencial → financeiro → individual
)
```

#### DEPOIS (v2.0.1)

```python
from bacen_analysis import DataUnavailableError

# Implementar lógica de cascata explicitamente
escopos_para_tentar = ['prudencial', 'financeiro', 'individual']
dados = None

for escopo in escopos_para_tentar:
    try:
        dados = analisador.get_dados_ifdata(
            identificador='60701190',
            contas=['Ativo Total'],
            datas=202403,
            escopo=escopo
        )
        break  # Se encontrou dados, para o loop
    except DataUnavailableError:
        continue  # Tenta próximo escopo

if dados is None:
    print("Dado não disponível em nenhum escopo")
```

### Passo 5: Testar Seu Código

Execute seus scripts/notebooks e verifique se tudo funciona conforme esperado.

---

## Mudanças na API

### Métodos Mantidos (100% Compatíveis)

Os seguintes métodos mantêm **assinatura idêntica**:

- `get_dados_cosif()` - Sem alterações
- `get_atributos_cadastro()` - Sem alterações
- `comparar_indicadores()` - Sem alterações
- `get_serie_temporal_indicador()` - Sem alterações

### Métodos Modificados

#### `get_dados_ifdata()`

**Mudança**: Parâmetro `escopo` agora é **obrigatório** e não aceita mais `'cascata'`.

**Assinatura Antiga (v1.x)**:
```python
def get_dados_ifdata(
    identificador,
    contas,
    datas,
    escopo='cascata'  # Opcional, padrão 'cascata'
)
```

**Assinatura Nova (v2.0.1)**:
```python
def get_dados_ifdata(
    identificador,
    contas,
    datas,
    escopo  # OBRIGATÓRIO: 'individual', 'prudencial', 'financeiro'
)
```

**Opções de `escopo`**:
- `'individual'`: Apenas instituição individual
- `'prudencial'`: Apenas conglomerado prudencial
- `'financeiro'`: Apenas conglomerado financeiro
- ~~`'cascata'`~~: **REMOVIDO** - implementar manualmente se necessário

### Novos Métodos

#### `get_series_temporais_lote()`

**Novo na v2.0.1**: Busca múltiplas séries temporais de forma otimizada.

```python
requisicoes = [
    {
        'identificador': '60701190',
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': 'Ativo Total - Itaú'
    }
]

df_series = analisador.get_series_temporais_lote(requisicoes)
```

**Vantagem**: Significativamente mais rápido que múltiplas chamadas individuais.

#### Métodos Utilitários

```python
# Limpar cache de resoluções (novo)
analisador.clear_cache()

# Recarregar dados (novo)
analisador.reload_data()
```

---

## Novos Recursos Disponíveis

Após migrar, você pode aproveitar os novos recursos:

### 1. Controle Granular de Escopo (IFDATA)

```python
# Buscar apenas dados individuais
individual = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'
)

# Buscar apenas conglomerado prudencial
prudencial = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)
```

### 2. Busca Otimizada em Lote

```python
# Buscar 10 séries de uma vez (muito mais rápido!)
bancos = ['60701190', '60746948', '00000000', ...]

requisicoes = [
    {
        'identificador': cnpj,
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': f'Banco_{cnpj}'
    }
    for cnpj in bancos
]

df_series = analisador.get_series_temporais_lote(requisicoes)
```

### 3. Cache LRU Automático

```python
# Primeira chamada: resolve 'Banco Inter' → CNPJ (lento)
dados1 = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

# Segunda chamada: usa cache (instantâneo)
dados2 = analisador.get_dados_ifdata(
    identificador='Banco Inter',  # Já está no cache!
    contas=['Lucro Líquido'],
    datas=202403,
    escopo='prudencial'
)
```

### 4. Exceções Customizadas

```python
from bacen_analysis import DataUnavailableError, EntityNotFoundError, InvalidScopeError

try:
    dados = analisador.get_dados_ifdata(
        identificador='CNPJ_INEXISTENTE',
        contas=['Ativo Total'],
        datas=202403,
        escopo='prudencial'
    )
except EntityNotFoundError:
    print("Instituição não encontrada nos dados cadastrais")
except DataUnavailableError:
    print("Dado não disponível para esta data/escopo")
except InvalidScopeError:
    print("Escopo inválido - use 'individual', 'prudencial' ou 'financeiro'")
```

---

## Exemplos de Migração

### Exemplo 1: Script Simples

#### ANTES (v1.x)

```python
import sys
from pathlib import Path

code_dir = Path('.').resolve().parent / 'Code'
if str(code_dir) not in sys.path:
    sys.path.append(str(code_dir))

from DataUtils import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar dados (escopo padrão: 'cascata')
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403
)

print(dados)
```

#### DEPOIS (v2.0.1)

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar dados (escopo explícito)
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'  # NOVO: obrigatório
)

print(dados)
```

### Exemplo 2: Notebook de Análise

#### ANTES (v1.x)

```python
# Célula 1: Setup
import sys
from pathlib import Path

code_dir = Path('..') / 'Code'
if str(code_dir.resolve()) not in sys.path:
    sys.path.append(str(code_dir.resolve()))

import DataUtils as du
from DataUtils import AnalisadorBancario

# Célula 2: Análise
analisador = AnalisadorBancario(diretorio_output='../data/output')
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Lucro Líquido'],
    datas=[202401, 202402, 202403]
)
```

#### DEPOIS (v2.0.1)

```python
# Célula 1: Setup
from bacen_analysis import AnalisadorBancario

# Célula 2: Análise
analisador = AnalisadorBancario(diretorio_output='../data/output')
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Lucro Líquido'],
    datas=[202401, 202402, 202403],
    escopo='prudencial'  # NOVO: obrigatório
)
```

### Exemplo 3: Comparação Multi-Instituição

#### ANTES (v1.x)

```python
comparacao = analisador.comparar_indicadores(
    identificadores=['60701190', '60746948', '00000000'],
    indicadores={
        'Ativo Total': {
            'tipo': 'IFDATA',
            'conta': 'Ativo Total'
            # escopo_ifdata não era obrigatório
        },
        'Segmento': {
            'tipo': 'ATRIBUTO',
            'atributo': 'Segmento'
        }
    },
    data=202403
)
```

#### DEPOIS (v2.0.1)

```python
comparacao = analisador.comparar_indicadores(
    identificadores=['60701190', '60746948', '00000000'],
    indicadores={
        'Ativo Total': {
            'tipo': 'IFDATA',
            'conta': 'Ativo Total',
            'escopo_ifdata': 'prudencial'  # NOVO: obrigatório
        },
        'Segmento': {
            'tipo': 'ATRIBUTO',
            'atributo': 'Segmento'
        }
    },
    data=202403
)
```

---

## Checklist de Migração

Use este checklist para garantir uma migração completa:

- [ ] Executar `pip install -e .` (ou `pip install -e ".[all]"`)
- [ ] Atualizar imports em todos os scripts/notebooks
- [ ] Adicionar parâmetro `escopo` em todas as chamadas `get_dados_ifdata()`
- [ ] Substituir lógica `'cascata'` por loops explícitos (se aplicável)
- [ ] Atualizar chamadas `comparar_indicadores()` (adicionar `escopo_ifdata`)
- [ ] Testar todos os scripts e notebooks
- [ ] Remover código antigo de manipulação de `sys.path`
- [ ] Atualizar documentação interna do projeto (se houver)

---

## Suporte

Se encontrar problemas durante a migração:
- [Troubleshooting](../troubleshooting.md) - Soluções para problemas comuns
- [Issues no GitHub](https://github.com/enzoomoreira/bacen-data-analysis/issues) - Reporte bugs ou peça ajuda

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
