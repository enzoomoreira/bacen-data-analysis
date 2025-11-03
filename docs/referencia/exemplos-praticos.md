# Exemplos Práticos

Este guia apresenta 8 exemplos práticos completos de uso do `bacen-data-analysis`, cobrindo os casos de uso mais comuns na análise de dados bancários.

## Nota Importante sobre Nomenclatura de Colunas

Os métodos de consulta retornam DataFrames com nomes de colunas específicos:

**Métodos de Consulta Direta** (`get_dados_cosif`, `get_dados_ifdata`):
- Retornam colunas com nomes **descritivos e em maiúsculas**: `DATA`, `CONTA_COSIF`, `NOME_CONTA_COSIF`, `VALOR_CONTA_COSIF`, `DOCUMENTO_COSIF`, etc.
- Incluem tanto o código quanto o nome da conta/indicador

**Métodos de Série Temporal** (`get_serie_temporal_indicador`, `get_series_temporais_lote`):
- Retornam colunas **padronizadas e simplificadas**: `DATA`, `Nome_Entidade`, `CNPJ_8`, `Conta`, `Valor`
- Formato otimizado para análise temporal e plotagem

**Métodos de Comparação** (`comparar_indicadores`):
- Retornam colunas pivotadas onde os indicadores são as próprias colunas
- Formato: `Nome_Entidade`, `CNPJ_8`, [nomes dos indicadores]

## Índice

- [Exemplo 1: Consulta Básica COSIF](#exemplo-1-consulta-básica-cosif)
- [Exemplo 2: Consulta Básica IFDATA](#exemplo-2-consulta-básica-ifdata)
- [Exemplo 3: Controle de Escopo (Individual vs Prudencial)](#exemplo-3-controle-de-escopo-individual-vs-prudencial)
- [Exemplo 4: Comparação Entre Múltiplas Instituições](#exemplo-4-comparação-entre-múltiplas-instituições)
- [Exemplo 5: Série Temporal Individual](#exemplo-5-série-temporal-individual)
- [Exemplo 6: Séries Temporais em Lote (Otimizado)](#exemplo-6-séries-temporais-em-lote-otimizado)
- [Exemplo 7: Tratamento de Dados Ausentes](#exemplo-7-tratamento-de-dados-ausentes)
- [Exemplo 8: Consultas com Códigos e Nomes Mistos](#exemplo-8-consultas-com-códigos-e-nomes-mistos)

---

## Exemplo 1: Consulta Básica COSIF

### Objetivo
Buscar o **Ativo Total** e **Patrimônio Líquido** do Conglomerado Prudencial do Bradesco em março de 2024.

### Código

```python
from bacen_analysis import AnalisadorBancario

# Inicializar analisador
analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar dados contábeis COSIF
dados = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',  # Pode usar nome ou CNPJ
    contas=['ATIVO TOTAL', 'PATRIMÔNIO LÍQUIDO'],
    datas=202403,
    tipo='prudencial',  # OBRIGATÓRIO: 'prudencial' ou 'individual'
    documentos=4060     # Opcional: Código do documento
)

print(dados)
```

### Saída Esperada

```
  Nome_Entidade        CNPJ_8    DATA    CONTA_COSIF  NOME_CONTA_COSIF      VALOR_CONTA_COSIF  DOCUMENTO_COSIF
0 BANCO BRADESCO S.A.  60746948  202403  10000000     ATIVO TOTAL           2500000000         4060
1 BANCO BRADESCO S.A.  60746948  202403  60000002     PATRIMÔNIO LÍQUIDO    150000000          4060
```

**Nota sobre as colunas:**
- `DATA`: Data no formato AAAAMM
- `CONTA_COSIF`: Código numérico da conta COSIF
- `NOME_CONTA_COSIF`: Nome descritivo da conta
- `VALOR_CONTA_COSIF`: Valor da conta em reais
- `DOCUMENTO_COSIF`: Código do documento COSIF

Para acessar os valores:
```python
valor_ativo = dados['VALOR_CONTA_COSIF'].iloc[0]
nome_conta = dados['NOME_CONTA_COSIF'].iloc[0]
```

### Pontos-Chave

- Pode usar **nome completo** ou **CNPJ** no identificador
- Parâmetro `tipo` é **obrigatório** para COSIF
- `documentos` filtra por tipo de relatório específico
- Retorna múltiplas contas em um único DataFrame
- As colunas incluem tanto o **código** quanto o **nome** da conta

---

## Exemplo 2: Consulta Básica IFDATA

### Objetivo
Buscar o **Índice de Basileia** do Banco Inter (conglomerado prudencial) em março de 2024.

### Código

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar indicador regulatório IFDATA
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',  # Pode usar nome parcial
    contas=['Índice de Basileia'],
    datas=202403,
    escopo='prudencial'  # OBRIGATÓRIO: 'individual', 'prudencial' ou 'financeiro'
)

print(dados)
```

### Saída Esperada

```
  Nome_Entidade  CNPJ_8    ID_BUSCA_USADO  DATA    CONTA_IFD_VAL  NOME_CONTA_IFD_VAL  VALOR_CONTA_IFD_VAL
0 BANCO INTER    00416968  62331143        202403  1018           Índice de Basileia  18.5
```

**Nota sobre as colunas:**
- `DATA`: Data no formato AAAAMM
- `CONTA_IFD_VAL`: Código numérico da conta IFDATA
- `NOME_CONTA_IFD_VAL`: Nome descritivo do indicador
- `VALOR_CONTA_IFD_VAL`: Valor do indicador
- `ID_BUSCA_USADO`: Identificador usado na busca (CNPJ ou código de conglomerado)

Para acessar os valores:
```python
valor_basileia = dados['VALOR_CONTA_IFD_VAL'].iloc[0]
nome_indicador = dados['NOME_CONTA_IFD_VAL'].iloc[0]
```

### Pontos-Chave

- `escopo` é **obrigatório** na v2.0.1
- `ID_BUSCA_USADO` mostra de onde o dado veio (conglomerado ou individual)
- Aceita **nomes parciais** de instituições
- Ideal para indicadores regulatórios (Basileia, liquidez, etc.)
- As colunas incluem tanto o **código** quanto o **nome** do indicador

---

## Exemplo 3: Controle de Escopo (Individual vs Prudencial)

### Objetivo
Comparar o **Ativo Total** no nível **individual** vs **conglomerado prudencial** do Itaú.

### Código

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar dados no nível individual
ativo_individual = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'
)

# Buscar dados no nível prudencial (conglomerado)
ativo_prudencial = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

# Comparar valores (usar o nome correto da coluna)
print(f"Individual: R$ {ativo_individual['VALOR_CONTA_IFD_VAL'].values[0]:,.0f}")
print(f"Prudencial: R$ {ativo_prudencial['VALOR_CONTA_IFD_VAL'].values[0]:,.0f}")
print(f"Diferença:  R$ {ativo_prudencial['VALOR_CONTA_IFD_VAL'].values[0] - ativo_individual['VALOR_CONTA_IFD_VAL'].values[0]:,.0f}")
```

### Saída Esperada

```
Individual: R$ 2,650,000,000,000
Prudencial: R$ 2,800,000,000,000
Diferença:  R$ 150,000,000,000
```

### Pontos-Chave

- **Individual**: Dados apenas da instituição específica
- **Prudencial**: Dados consolidados do conglomerado prudencial
- **Financeiro**: Dados consolidados do conglomerado financeiro (se existir)
- Útil para entender o tamanho real do grupo econômico

---

## Exemplo 4: Comparação Entre Múltiplas Instituições

### Objetivo
Comparar indicadores-chave dos **3 maiores bancos** do Brasil (Itaú, Bradesco, Banco do Brasil).

### Código

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Comparar múltiplos indicadores
comparacao = analisador.comparar_indicadores(
    identificadores=['60701190', '60746948', '00000000'],  # Itaú, Bradesco, BB
    indicadores={
        'Ativo Total': {
            'tipo': 'IFDATA',
            'conta': 'Ativo Total',
            'escopo_ifdata': 'prudencial'
        },
        'Índice de Basileia': {
            'tipo': 'IFDATA',
            'conta': 'Índice de Basileia',
            'escopo_ifdata': 'prudencial'
        },
        'Patrimônio Líquido': {
            'tipo': 'COSIF',
            'conta': 'PATRIMÔNIO LÍQUIDO',
            'tipo_cosif': 'prudencial',
            'documento_cosif': 4060
        },
        'Segmento': {
            'tipo': 'ATRIBUTO',
            'atributo': 'Segmento'
        }
    },
    data=202403
)

print(comparacao)
```

### Saída Esperada

```
  Nome_Entidade         CNPJ_8    Ativo Total    Índice de Basileia  Patrimônio Líquido  Segmento
0 ITAÚ UNIBANCO...     60701190   2800000000000  15.2                220000000000        S1
1 BANCO BRADESCO...    60746948   2500000000000  14.8                150000000000        S1
2 BANCO DO BRASIL...   00000000   2900000000000  16.1                180000000000        S1
```

### Pontos-Chave

- Combina dados de **três fontes**: COSIF, IFDATA e Cadastro
- Formato **pivotado**: instituições nas linhas, indicadores nas colunas
- Ideal para criar **tabelas comparativas** e **rankings**
- Cada indicador pode ter configuração independente

---

## Exemplo 5: Série Temporal Individual

### Objetivo
Buscar a evolução do **Lucro Líquido** do Banco Inter ao longo de 2023 e plotar um gráfico.

### Código

```python
from bacen_analysis import AnalisadorBancario
import matplotlib.pyplot as plt

analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar série temporal
serie = analisador.get_serie_temporal_indicador(
    identificador='Banco Inter',
    conta='Lucro Líquido',
    fonte='IFDATA',
    escopo_ifdata='prudencial',  # OBRIGATÓRIO para IFDATA
    data_inicio=202301,
    data_fim=202312
)

# Plotar gráfico (usar nomes corretos das colunas)
plt.figure(figsize=(12, 6))
plt.plot(serie['DATA'], serie['Valor'], marker='o', linewidth=2, markersize=8)
plt.title('Evolução do Lucro Líquido - Banco Inter (2023)', fontsize=14, fontweight='bold')
plt.xlabel('Data (AAAAMM)', fontsize=12)
plt.ylabel('Valor (R$ milhões)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Estatísticas básicas
print(f"Lucro Médio: R$ {serie['Valor'].mean():,.0f}")
print(f"Lucro Máximo: R$ {serie['Valor'].max():,.0f}")
print(f"Lucro Mínimo: R$ {serie['Valor'].min():,.0f}")
```

### Saída Esperada (Estatísticas)

```
Lucro Médio: R$ 650,000,000
Lucro Máximo: R$ 800,000,000
Lucro Mínimo: R$ 500,000,000
```

### Pontos-Chave

- Ideal para **análise de tendências** ao longo do tempo
- Retorna DataFrame com colunas: `DATA`, `Nome_Entidade`, `CNPJ_8`, `Conta`, `Valor`
- Use `DATA` (maiúsculo) para acessar as datas
- Use `Valor` para acessar os valores numéricos
- Pode usar `drop_na`, `fill_value` para controlar dados ausentes
- Funciona com **COSIF** ou **IFDATA**

---

## Exemplo 6: Séries Temporais em Lote (Otimizado)

### Objetivo
Buscar séries de **Ativo Total** para **10 bancos** simultaneamente de forma otimizada.

### Código

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Lista dos 10 maiores bancos
bancos = [
    '60701190',  # Itaú
    '60746948',  # Bradesco
    '00000000',  # Banco do Brasil
    '00416968',  # Banco Inter
    '00000208',  # BTG Pactual
    '02318507',  # Santander
    '00360305',  # Caixa Econômica
    '00394460',  # Safra
    '04902979',  # Original
    '17298092'   # Stone
]

# Criar requisições para busca em lote
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

# NOTA: Para usar fonte='COSIF', adicione obrigatoriamente:
# - 'tipo_cosif': 'prudencial' ou 'individual'
# - 'documento_cosif': código do documento (ex: 4060)
# Exemplo:
# {
#     'identificador': '00000208',
#     'conta': '10000001',
#     'fonte': 'COSIF',
#     'datas': [202401, 202402],
#     'tipo_cosif': 'prudencial',
#     'documento_cosif': 4060,
#     'nome_indicador': 'Caixa'
# }

# Busca otimizada em uma única chamada
df_series = analisador.get_series_temporais_lote(requisicoes)

# Pivotar para análise (usar nomes corretos das colunas)
df_pivot = df_series.pivot(index='DATA', columns='Conta', values='Valor')

print(df_pivot)

# Calcular taxa de crescimento
crescimento = ((df_pivot.loc[202403] - df_pivot.loc[202401]) / df_pivot.loc[202401] * 100)
print("\nCrescimento Q1 2024 (%):")
print(crescimento.sort_values(ascending=False))
```

### Saída Esperada

```
Conta          Banco_60701190  Banco_60746948  Banco_00000000  ...
DATA
202401         2750000000000   2480000000000   2850000000000   ...
202402         2770000000000   2490000000000   2870000000000   ...
202403         2800000000000   2500000000000   2900000000000   ...

Crescimento Q1 2024 (%):
Banco_04902979    5.2
Banco_00416968    4.8
Banco_17298092    4.3
...
```

**Nota:** A coluna `Conta` contém o valor de `nome_indicador` especificado em cada requisição.

### Pontos-Chave

- **Muito mais rápido** que 10 chamadas individuais
- Pré-resolve todos os identificadores uma vez
- Ideal para **análises comparativas** em escala
- Formato "longo" facilita pivotagem e visualização

---

## Exemplo 7: Tratamento de Dados Ausentes

### Objetivo
Buscar uma série temporal completa, **preenchendo lacunas com zero** e tratando dados ausentes.

### Código

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Buscar série com controle de dados ausentes
serie = analisador.get_serie_temporal_indicador(
    identificador='00000208',
    conta='Lucro Líquido',
    fonte='IFDATA',
    escopo_ifdata='prudencial',
    data_inicio=202301,
    data_fim=202312,
    drop_na=False,      # NÃO remover linhas com NaN
    fill_value=0        # Preencher NaNs com 0
)

print(serie)

# Identificar meses com dados ausentes (preenchidos com 0)
meses_ausentes = serie[serie['Valor'] == 0]['DATA'].tolist()
print(f"\nMeses sem dados (preenchidos com zero): {meses_ausentes}")
```

### Saída Esperada

```
    Data         Valor
0   202301  500000000
1   202302  520000000
2   202303          0  <- Dado ausente, preenchido
3   202304  550000000
4   202305  560000000
5   202306          0  <- Dado ausente, preenchido
...

Meses sem dados (preenchidos com zero): [202303, 202306]
```

### Opções de Controle

```python
# Opção 1: Remover linhas com NaN (padrão)
serie = analisador.get_serie_temporal_indicador(..., drop_na=True)

# Opção 2: Manter NaNs para visualizar lacunas
serie = analisador.get_serie_temporal_indicador(..., drop_na=False)

# Opção 3: Preencher NaNs com valor específico
serie = analisador.get_serie_temporal_indicador(..., drop_na=False, fill_value=0)

# Opção 4: Tratar zeros como dados ausentes
serie = analisador.get_serie_temporal_indicador(..., replace_zeros_with_nan=True)
```

### Pontos-Chave

- `drop_na=True` (padrão): Remove linhas com valores ausentes
- `drop_na=False`: Mantém linhas com NaN (útil para identificar lacunas)
- `fill_value`: Preenche NaNs com valor específico
- `replace_zeros_with_nan`: Converte zeros em NaN (útil quando zero não é válido)

---

## Exemplo 8: Consultas com Códigos e Nomes Mistos

### Objetivo
Buscar dados usando uma **mistura de nomes e códigos** de contas COSIF.

### Código

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# Lista mista: nomes e códigos de contas
contas_mistas = [
    'ATIVO TOTAL',      # Busca por nome
    60000002,           # Busca por código (PATRIMÔNIO LÍQUIDO)
    'LUCRO LÍQUIDO',    # Busca por nome
    10000001            # Busca por código (CAIXA)
]

# Buscar com lista mista
dados = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',
    contas=contas_mistas,  # Lista mista
    datas=202403,
    tipo='prudencial',
    documentos=4060
)

print(dados)

# Agrupar por conta
resumo = dados.groupby('Conta')['Valor'].sum()
print("\nResumo por Conta:")
print(resumo)
```

### Saída Esperada

```
  Nome_Entidade        CNPJ_8    Data    Conta                Valor
0 BANCO BRADESCO S.A.  60746948  202403  ATIVO TOTAL          2500000000000
1 BANCO BRADESCO S.A.  60746948  202403  PATRIMÔNIO LÍQUIDO   150000000000
2 BANCO BRADESCO S.A.  60746948  202403  LUCRO LÍQUIDO        12000000000
3 BANCO BRADESCO S.A.  60746948  202403  CAIXA                50000000000

Resumo por Conta:
Conta
ATIVO TOTAL           2500000000000
CAIXA                   50000000000
LUCRO LÍQUIDO           12000000000
PATRIMÔNIO LÍQUIDO     150000000000
```

### Pontos-Chave

- Aceita **nomes** e **códigos** na mesma lista
- Flexibilidade para trabalhar com dados de diferentes origens
- Útil quando você tem **parte dos códigos** memorizados
- Consulte `dicionario_contas_cosif_*.xlsx` para encontrar códigos

---

## Dicas Gerais

### 1. Sempre Consulte os Dicionários

Antes de fazer consultas, abra os arquivos Excel em `data/output/`:
- `dicionario_entidades.xlsx` - Nomes e CNPJs corretos
- `dicionario_contas_cosif_*.xlsx` - Códigos e nomes de contas COSIF
- `dicionario_contas_ifdata_valores.xlsx` - Indicadores IFDATA

### 2. Use CNPJs Para Precisão

```python
# Preferível
dados = analisador.get_dados_ifdata(identificador='60701190', ...)

# Funciona, mas pode ser ambíguo
dados = analisador.get_dados_ifdata(identificador='Itaú', ...)
```

### 3. Verifique ID_BUSCA_USADO (IFDATA)

```python
dados = analisador.get_dados_ifdata(...)
print(dados['ID_BUSCA_USADO'])  # Mostra de onde o dado veio
```

### 4. Combine Múltiplas Fontes

```python
# Combinar COSIF, IFDATA e Cadastro em uma análise
comparacao = analisador.comparar_indicadores(
    identificadores=[...],
    indicadores={
        'Indicador COSIF': {'tipo': 'COSIF', ...},
        'Indicador IFDATA': {'tipo': 'IFDATA', ...},
        'Atributo': {'tipo': 'ATRIBUTO', ...}
    },
    data=202403
)
```

---

## Próximos Passos

- [Técnicas Avançadas](tecnicas-avancadas.md) - Otimizações e recursos avançados
- [API Completa](api-completa.md) - Documentação detalhada de todos os métodos
- [Troubleshooting](../troubleshooting.md) - Soluções para problemas comuns

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
