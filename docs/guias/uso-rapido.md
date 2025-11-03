# Guia de Uso Rápido

Este guia apresenta os conceitos básicos e primeiros passos para usar o `bacen-data-analysis`. Após ler este guia, você será capaz de realizar consultas básicas aos dados do Banco Central.

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Import Simplificado](#import-simplificado)
- [Inicialização](#inicialização)
- [Exemplos Básicos](#exemplos-básicos)
- [Próximos Passos](#próximos-passos)
- [Tratamento de Erros](#tratamento-de-erros)

---

## Pré-requisitos

Antes de começar, certifique-se de que:

1. O pacote foi instalado: `pip install -e .`
2. O pipeline ETL foi executado: `notebooks/etl/data_download.ipynb`
3. Os arquivos Parquet existem em: `data/output/`

Se ainda não fez isso, consulte: [Guia de Instalação](instalacao.md)

---

## Import Simplificado

A versão 2.0 do projeto introduz imports diretos, sem necessidade de manipular `sys.path`:

```python
from bacen_analysis import AnalisadorBancario
```

Também está disponível uma função utilitária para padronizar CNPJs:

```python
from bacen_analysis import standardize_cnpj_base8
```

---

## Inicialização

Para começar a usar o analisador, você precisa especificar o diretório onde estão os arquivos Parquet processados:

```python
from pathlib import Path
from bacen_analysis import AnalisadorBancario

# Especificar diretório com arquivos Parquet
output_dir = Path('data/output')  # Caminho relativo ou absoluto

# Inicializar o analisador
analisador = AnalisadorBancario(diretorio_output=str(output_dir))
```

**Nota**: Use caminho relativo se estiver na raiz do projeto, ou caminho absoluto se estiver em outro diretório.

---

## Exemplos Básicos

### Exemplo 1: Consultar Dados IFDATA

Buscar o **Ativo Total** do Itaú em março de 2024:

```python
# Buscar por CNPJ ou nome da instituição
dados = analisador.get_dados_ifdata(
    identificador='60701190',  # String única ou lista de identificadores
    contas=['Ativo Total'],
    datas=202403,  # Formato: AAAAMM
    escopo='prudencial'  # 'individual', 'prudencial' ou 'financeiro'
)

print(dados)
```

**Saída esperada** (valores ilustrativos):
```
  Nome_Entidade              CNPJ_8    Data    Conta        Valor         ID_BUSCA_USADO
0 ITAÚ UNIBANCO HOLDING S.A. 60701190  202403  Ativo Total  2800000000    62144175
```

**Explicação**:
- `identificador`: CNPJ de 8 dígitos, nome da instituição, ou lista de identificadores
- `contas`: Lista de indicadores desejados
- `datas`: Data(s) no formato AAAAMM
- `escopo`: Nível de dados (**obrigatório na v2.0.1**)

### Exemplo 2: Consultar Dados COSIF

Buscar **Ativo Total** e **Patrimônio Líquido** do Bradesco:

```python
dados = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',  # String única ou lista de identificadores
    contas=['ATIVO TOTAL', 'PATRIMÔNIO LÍQUIDO'],
    datas=202403,
    tipo='prudencial',  # 'prudencial' ou 'individual' (OBRIGATÓRIO)
    documentos=4060  # Código do documento (opcional)
)

print(dados)
```

**Saída esperada** (valores ilustrativos):
```
  Nome_Entidade        CNPJ_8    Data    Conta                   Valor
0 BANCO BRADESCO S.A.  60746948  202403  ATIVO TOTAL             2500000000
1 BANCO BRADESCO S.A.  60746948  202403  PATRIMÔNIO LÍQUIDO      150000000
```

### Exemplo 3: Consultar Atributos Cadastrais

Buscar o **Segmento** e **Situação** de uma instituição:

```python
atributos = analisador.get_atributos_cadastro(
    identificador='60701190',  # String única ou lista de identificadores
    atributos=['Segmento', 'Situacao']
)

print(atributos)
```

**Saída esperada** (valores ilustrativos):
```
  Nome_Entidade              CNPJ_8    Segmento  Situacao
0 ITAÚ UNIBANCO HOLDING S.A. 60701190  S1        ATIVA
```

### Exemplo 4: Múltiplas Datas

Buscar dados de **vários meses** de uma vez:

```python
# Buscar dados de janeiro a março de 2024
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Lucro Líquido'],
    datas=[202401, 202402, 202403],  # Lista de datas
    escopo='prudencial'
)

print(dados)
```

**Saída esperada** (valores ilustrativos):
```
  Nome_Entidade  CNPJ_8    Data    Conta          Valor         ID_BUSCA_USADO
0 BANCO INTER    00416968  202401  Lucro Líquido  50000000      62331143
1 BANCO INTER    00416968  202402  Lucro Líquido  55000000      62331143
2 BANCO INTER    00416968  202403  Lucro Líquido  60000000      62331143
```

### Exemplo 5: Múltiplas Instituições

Buscar dados de **várias instituições** simultaneamente:

```python
# Comparar Ativo Total de múltiplos bancos
dados = analisador.get_dados_ifdata(
    identificador=['60701190', '60746948', '00416968'],  # Lista de CNPJs
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

print(dados)
```

**Saída esperada** (valores ilustrativos):
```
  Nome_Entidade              CNPJ_8    Data    Conta        Valor         ID_BUSCA_USADO
0 ITAÚ UNIBANCO HOLDING S.A. 60701190  202403  Ativo Total  2800000000    62144175
1 BANCO BRADESCO S.A.        60746948  202403  Ativo Total  2500000000    60746948
2 BANCO INTER                00416968  202403  Ativo Total  180000000     62331143
```

---

## Próximos Passos

Agora que você conhece o básico, explore recursos mais avançados:

### Consulte os Dicionários

Para encontrar nomes exatos de instituições e indicadores, abra os arquivos Excel em `data/output/`:

- **`dicionario_entidades.xlsx`**: Nomes e CNPJs de todas as instituições
- **`dicionario_contas_ifdata_valores.xlsx`**: Todos os indicadores IFDATA disponíveis
- **`dicionario_contas_cosif_prudencial.xlsx`**: Contas COSIF prudencial
- **`dicionario_contas_cosif_individual.xlsx`**: Contas COSIF individual

### Documentação Adicional

- **[API Completa](../referencia/api-completa.md)**: Documentação detalhada de todos os métodos
- **[Exemplos Práticos](../referencia/exemplos-praticos.md)**: 8 exemplos completos com casos de uso reais
- **[Técnicas Avançadas](../referencia/tecnicas-avancadas.md)**: Otimizações, cache, busca em lote

### Notebooks de Exemplo

Explore os notebooks incluídos:

- **`notebooks/analysis/example.ipynb`**: Tutorial completo com múltiplos exemplos
- **`notebooks/analysis/full_table.ipynb`**: Construção de tabelas comparativas

---

## Principais Conceitos

### Padrão de Saída

Todos os métodos retornam DataFrames com **colunas padrão no início**:
- `Nome_Entidade`: Nome oficial da instituição
- `CNPJ_8`: CNPJ de 8 dígitos

Isso garante que você sempre saiba a qual instituição os dados se referem.

### Escopo (IFDATA)

O parâmetro `escopo` é **obrigatório** na v2.0.1 e controla o nível dos dados:
- `'individual'`: Apenas a instituição individual
- `'prudencial'`: Conglomerado prudencial (se existir)
- `'financeiro'`: Conglomerado financeiro (se existir)

**Coluna ID_BUSCA_USADO**: Presente apenas em consultas IFDATA, esta coluna indica o CNPJ exato usado para buscar o dado. Isso é útil para identificar se o valor veio do nível individual, prudencial ou financeiro da hierarquia de conglomerados.

### Tipo e Documento (COSIF)

Para COSIF, você deve especificar:
- `tipo`: `'prudencial'` ou `'individual'` (**obrigatório**)
- `documentos`: Código do documento (opcional, mas recomendado)
  - `4060`: Prudencial
  - `4066`: Prudencial agregado
  - `4010`: Individual
  - `4016`: Individual agregado

### Identificadores Flexíveis

Você pode consultar instituições usando:
- **CNPJ de 8 dígitos**: `'60701190'` ou `60701190`
- **Nome completo**: `'ITAÚ UNIBANCO HOLDING S.A.'`
- **Nome parcial**: `'Itaú'`, `'Bradesco'`, `'Inter'`
- **Lista de identificadores**: `['60701190', '60746948']` ou `['Itaú', 'Bradesco']`

O analisador resolve automaticamente para o CNPJ correto. Use listas quando quiser consultar múltiplas instituições de uma vez.

---

## Dicas Importantes

1. **Sempre consulte os dicionários** para encontrar nomes exatos de contas e indicadores
2. **Use CNPJs** quando possível - são mais precisos que nomes
3. **Especifique o escopo explicitamente** para evitar ambiguidade
4. **Verifique a coluna `ID_BUSCA_USADO`** (IFDATA) para saber a origem exata do dado
5. **Consulte o Troubleshooting** se uma consulta não retornar resultados

---

## Tratamento de Erros

O `bacen-data-analysis` fornece exceções específicas para facilitar o tratamento de erros:

```python
from bacen_analysis import (
    AnalisadorBancario,
    EntityNotFoundError,
    DataUnavailableError,
    InvalidScopeError,
    AmbiguousIdentifierError
)

analisador = AnalisadorBancario(diretorio_output='data/output')

try:
    dados = analisador.get_dados_ifdata(
        identificador='Banco Inexistente',
        contas=['Ativo Total'],
        datas=202403,
        escopo='prudencial'
    )
except EntityNotFoundError as e:
    print(f"Instituição não encontrada: {e}")
except DataUnavailableError as e:
    print(f"Dados não disponíveis: {e}")
except InvalidScopeError as e:
    print(f"Escopo inválido: {e}")
```

**Exceções disponíveis**:
- `EntityNotFoundError`: Identificador de instituição não encontrado
- `DataUnavailableError`: Dados solicitados não estão disponíveis
- `InvalidScopeError`: Escopo ou tipo inválido fornecido
- `AmbiguousIdentifierError`: Identificador ambíguo (múltiplas correspondências)

Para mais detalhes, consulte: [Troubleshooting](../troubleshooting.md)

---

## Suporte

Se tiver dúvidas ou problemas:
- [Troubleshooting](../troubleshooting.md) - Soluções para problemas comuns
- [Issues no GitHub](https://github.com/enzoomoreira/bacen-data-analysis/issues) - Reporte bugs ou peça ajuda

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
