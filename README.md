# Análise de Dados Financeiros do Banco Central do Brasil

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.0-green)](https://github.com/enzoomoreira/bacen-data-analysis)

## 1. Visão Geral

Este projeto é um **pacote Python moderno e instalável** que fornece um pipeline completo de dados e ferramentas de análise para os relatórios financeiros de instituições brasileiras, disponibilizados pelo Banco Central do Brasil (BCB).

A versão 2.0.0 representa uma **refatoração completa** da arquitetura do projeto, transformando-o de notebooks simples para um pacote Python profissional com arquitetura modular, otimizações de performance e API simplificada, mantendo **100% de compatibilidade** com a versão anterior.

### O Que Este Projeto Faz

O projeto automatiza o processo de:
- **Extrair**: Download automatizado de dados do BCB (COSIF e IF.DATA)
- **Transformar**: Limpeza, padronização e unificação de dados complexos
- **Carregar**: Armazenamento otimizado em formato Parquet
- **Analisar**: Interface Python intuitiva para consultas e análises avançadas

**Objetivo Principal**: Permitir a extração de insights valiosos dos dados do BCB sem a necessidade de lidar com a complexidade do tratamento e da unificação dos dados brutos.

### Fluxo do Projeto

```
┌─────────────────────────────────────────────────────────────┐
│                      1. PIPELINE ETL                        │
│  notebooks/etl/data_download.ipynb                          │
│  • Download automático dos relatórios BCB                   │
│  • Padronização de colunas e CNPJs                          │
│  • Resolução de inconsistências                             │
│  • Geração de dicionários de referência (Excel)             │
│  • Salvamento otimizado em Parquet                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   2. ANÁLISE DE DADOS                       │
│  from bacen_analysis import AnalisadorBancario              │
│  • Interface Python simples e poderosa                      │
│  • Consultas por nome ou CNPJ                               │
│  • Comparações multi-instituição                            │
│  • Séries temporais e análise de tendências                 │
│  • Notebooks de exemplo com casos de uso práticos           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Novos Recursos v2.0.0

### ✨ Destaques da Versão

- **Pacote Python Instalável**: Instalação via `pip install -e .` com imports simplificados
- **Arquitetura Modular**: Código organizado em camadas com responsabilidades bem definidas
- **Performance Otimizada**:
  - Cache LRU para resoluções de identificadores
  - Novo método `get_series_temporais_lote()` para buscas em massa (significativamente mais rápido)
  - Pré-resolução de entidades em operações em lote
- **Controle Granular de Escopo**: Parâmetro `escopo_ifdata` com opções `'individual'`, `'prudencial'`, `'financeiro'`, `'cascata'`
- **API Simplificada**: Imports diretos sem necessidade de manipular `sys.path`
- **Type Hints Completos**: Código totalmente tipado para melhor IDE support
- **100% Compatível**: API pública mantida idêntica à versão 1.x

### Padrões de Design Aplicados

- **Facade Pattern**: `AnalisadorBancario` como interface unificada
- **Repository Pattern**: Acesso centralizado aos dados
- **Dependency Injection**: Componentes recebem dependências via construtor
- **Single Responsibility**: Cada módulo com responsabilidade única e clara

---

## 3. Estrutura do Projeto

```
bacen-data-analysis/
│
├── src/bacen_analysis/              # Pacote principal
│   ├── __init__.py                  # API pública (exporta AnalisadorBancario)
│   │
│   ├── core/                        # Componentes centrais
│   │   ├── analyser.py              # AnalisadorBancario (Facade principal)
│   │   └── entity_resolver.py       # Resolução de CNPJs e nomes
│   │
│   ├── providers/                   # Provedores de dados por fonte
│   │   ├── cosif.py                 # Provedor de dados COSIF
│   │   ├── ifdata.py                # Provedor de dados IFDATA
│   │   └── cadastro.py              # Provedor de dados cadastrais
│   │
│   ├── data/                        # Camada de acesso a dados
│   │   ├── loader.py                # Carregamento de arquivos Parquet
│   │   └── repository.py            # Repository Pattern para dados
│   │
│   ├── analysis/                    # Módulos de análise
│   │   ├── comparator.py            # Comparação entre instituições
│   │   └── time_series.py           # Geração de séries temporais
│   │
│   └── utils/                       # Utilitários
│       ├── cnpj.py                  # Padronização de CNPJ
│       └── text.py                  # Limpeza de texto
│
├── notebooks/                       # Notebooks organizados
│   ├── etl/
│   │   └── data_download.ipynb      # Pipeline ETL completo
│   └── analysis/
│       ├── example.ipynb            # Tutorial com exemplos práticos
│       └── full_table.ipynb         # Exemplos de tabelas completas
│
├── pyproject.toml                   # Configuração do pacote
├── .gitignore                       # Arquivos ignorados pelo Git
└── README.md                        # Este arquivo
```

### Descrição das Camadas

| Camada | Responsabilidade |
|--------|------------------|
| **core/** | Componentes centrais: Facade principal e resolução de identificadores |
| **providers/** | Consultas especializadas por fonte de dados (COSIF, IFDATA, Cadastro) |
| **data/** | Carregamento e acesso unificado aos arquivos Parquet |
| **analysis/** | Operações de análise: comparações e séries temporais |
| **utils/** | Funções utilitárias de transformação e padronização |

**Nota**: Os diretórios `Input/` e `Output/` são criados automaticamente ao executar o notebook de ETL pela primeira vez.

---

## 4. Instalação e Setup

### Requisitos

- **Python**: 3.12 ou superior
- **Sistema Operacional**: Windows, macOS ou Linux

### Passo a Passo

#### 1. Clone o Repositório

```bash
git clone https://github.com/enzoomoreira/bacen-data-analysis.git
cd bacen-data-analysis
```

#### 2. Instale o Pacote

O projeto usa **pyproject.toml** para gerenciamento de dependências. Escolha a opção de instalação conforme sua necessidade:

**Instalação básica** (apenas dependências principais):
```bash
pip install -e .
```

**Instalação com ferramentas de desenvolvimento** (pytest, black, ruff):
```bash
pip install -e ".[dev]"
```

**Instalação com suporte a notebooks** (jupyter, matplotlib):
```bash
pip install -e ".[notebooks]"
```

**Instalação completa** (todas as dependências):
```bash
pip install -e ".[all]"
```

**Dependências principais instaladas automaticamente**:
- `pandas>=2.0.0` - Manipulação de dados
- `pyarrow>=10.0.0` - Leitura de arquivos Parquet
- `openpyxl>=3.0.0` - Leitura/escrita de arquivos Excel
- `requests>=2.28.0` - Download de dados do BCB

#### 3. Execute o Pipeline de ETL

**PASSO ESSENCIAL** antes de qualquer análise:

1. Abra e execute o notebook `notebooks/etl/data_download.ipynb` do início ao fim
2. O processo pode demorar na primeira execução (downloads completos)
3. Execuções futuras serão mais rápidas (apenas dados novos)
4. Ao final, o diretório `Output/` conterá:
   - Arquivos `.parquet` com dados processados
   - Dicionários de referência em Excel (essenciais para consultas)

#### 4. Explore e Analise

- Abra o notebook `notebooks/analysis/example.ipynb` - Tutorial completo com exemplos práticos
- Consulte os arquivos em `Output/`, especialmente `dicionario_entidades.xlsx` para encontrar nomes e CNPJs corretos
- Crie seus próprios notebooks de análise importando: `from bacen_analysis import AnalisadorBancario`

---

## 5. Guia de Uso Rápido

### Import Simplificado (Novo na v2.0)

```python
# Versão 2.0 - Import direto, sem manipulação de paths
from bacen_analysis import AnalisadorBancario

# Também disponível: função utilitária para padronizar CNPJs
from bacen_analysis import standardize_cnpj_base8
```

### Inicialização

```python
from pathlib import Path
from bacen_analysis import AnalisadorBancario

# Especifique o diretório onde estão os arquivos Parquet processados
output_dir = Path('Output')  # ou caminho absoluto
analisador = AnalisadorBancario(diretorio_output=str(output_dir))
```

### Exemplo Rápido

```python
# Buscar o Ativo Total do Itaú em março de 2024
dados = analisador.get_dados_ifdata(
    identificador='60701190',  # CNPJ ou nome funciona
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

print(dados)
```

**Para exemplos completos e casos de uso avançados**, consulte: `notebooks/analysis/example.ipynb`

---

## 6. API Completa - AnalisadorBancario

A classe `AnalisadorBancario` é sua interface principal para os dados. Após a inicialização, você acessa métodos para consultas complexas de forma intuitiva.

### Padrão de Saída Consistente

**Todos os métodos** que retornam dados sobre entidades incluem as colunas `Nome_Entidade` e `CNPJ_8` no início do DataFrame. Isso garante que você sempre saiba a qual instituição os dados se referem.

### Métodos Principais

#### `get_dados_cosif()`

Busca dados contábeis detalhados (Balanço Patrimonial, DRE) da fonte COSIF.

```python
dados = analisador.get_dados_cosif(
    identificador='00000000',       # CNPJ_8 ou nome da instituição
    contas=['ATIVO TOTAL'],         # Lista de nomes ou códigos de contas
    datas=[202401, 202402, 202403], # Lista de datas (AAAAMM)
    documentos=[4060]               # 4060=Prudencial, 4010=Individual
)
```

**Parâmetros**:
- `identificador` (str): CNPJ de 8 dígitos ou nome da instituição
- `contas` (list): Nomes ou códigos das contas contábeis
- `datas` (list): Datas no formato AAAAMM (ex: 202403 = março/2024)
- `documentos` (list): Códigos de documento (4060=prudencial, 4066=prudencial agregado, 4010=individual, 4016=individual agregado)

**Retorno**: DataFrame com colunas `Nome_Entidade`, `CNPJ_8`, `Data`, `Conta`, `Valor`, etc.

---

#### `get_dados_ifdata()`

Busca indicadores regulatórios (Basileia, liquidez, etc.) da fonte IF.DATA.

```python
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Índice de Basileia'],
    datas=202403,
    escopo='prudencial'  # NOVO: controle granular de escopo
)
```

**Parâmetros**:
- `identificador` (str): CNPJ de 8 dígitos ou nome da instituição
- `contas` (list): Nomes ou códigos dos indicadores
- `datas` (list/int): Data(s) no formato AAAAMM
- `escopo` (str): Controle de escopo da busca:
  - `'individual'`: Apenas dados da instituição individual
  - `'prudencial'`: Apenas dados do conglomerado prudencial
  - `'financeiro'`: Apenas dados do conglomerado financeiro
  - `'cascata'` (padrão): Tenta todas as opções acima em ordem

**Retorno**: DataFrame com colunas `Nome_Entidade`, `CNPJ_8`, `Data`, `Conta`, `Valor`, `ID_BUSCA_USADO` (indica a origem do dado).

---

#### `get_atributos_cadastro()`

Busca informações cadastrais de instituições (Segmento, Situação, Endereço, etc.).

```python
atributos = analisador.get_atributos_cadastro(
    identificadores=['60701190', '00000208', '00416968'],
    atributos=['Segmento', 'Situacao']
)
```

**Parâmetros**:
- `identificadores` (list): Lista de CNPJs ou nomes
- `atributos` (list): Lista de atributos desejados (consulte `dicionario_atributos_cadastro.xlsx`)

**Retorno**: DataFrame com `Nome_Entidade`, `CNPJ_8` e os atributos solicitados.

---

#### `comparar_indicadores()`

Cria uma tabela-resumo "pivotada" para comparar múltiplos indicadores entre várias instituições.

```python
comparacao = analisador.comparar_indicadores(
    identificadores=['00000000', '00000208', '60701190'],
    indicadores=[
        {'nome': 'Ativo Total', 'tipo': 'IFDATA', 'escopo': 'prudencial'},
        {'nome': 'ATIVO TOTAL', 'tipo': 'COSIF', 'documento': 4060},
        {'nome': 'Segmento', 'tipo': 'ATRIBUTO'}
    ],
    datas=202403
)
```

**Parâmetros**:
- `identificadores` (list): Lista de instituições
- `indicadores` (list): Lista de dicionários descrevendo cada indicador:
  - `tipo`: `'COSIF'`, `'IFDATA'`, ou `'ATRIBUTO'`
  - `nome`: Nome ou código da conta/indicador/atributo
  - Parâmetros específicos: `escopo` (IFDATA), `documento` (COSIF)
- `datas` (list/int): Data(s) de referência

**Retorno**: DataFrame pivotado com instituições nas linhas e indicadores nas colunas.

---

#### `get_serie_temporal_indicador()`

Busca a evolução de um único indicador ao longo do tempo para uma instituição.

```python
serie = analisador.get_serie_temporal_indicador(
    identificador='Banco Inter',
    conta='Lucro Líquido',
    fonte='IFDATA',
    data_inicio=202301,
    data_fim=202312,
    drop_na=False,           # Manter linhas com NaN?
    fill_value=0,            # Preencher NaNs com valor específico
    replace_zeros_with_nan=False  # Converter zeros em NaN?
)
```

**Parâmetros**:
- `identificador` (str): Instituição
- `conta` (str/int): Indicador desejado
- `fonte` (str): `'COSIF'` ou `'IFDATA'`
- `data_inicio` / `data_fim` (int): Intervalo de datas (AAAAMM)
- **Controle de dados ausentes**:
  - `drop_na` (bool): Remove linhas com NaN (padrão: True)
  - `fill_value` (float): Preenche NaNs com este valor
  - `replace_zeros_with_nan` (bool): Trata zeros como dados ausentes

**Retorno**: DataFrame com `Data` e `Valor`, pronto para plotagem.

---

#### `get_series_temporais_lote()` ✨ NOVO

Busca **múltiplas séries temporais de forma otimizada** em uma única chamada. **Significativamente mais rápido** que múltiplas chamadas a `get_serie_temporal_indicador()`.

```python
requisicoes = [
    {
        'identificador': '00000000',
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202501, 202502, 202503],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': 'Ativo Total - Itaú'
    },
    {
        'identificador': '00000208',
        'conta': 10000001,  # Código de conta COSIF
        'fonte': 'COSIF',
        'datas': [202501, 202502],
        'documento_cosif': 4060,
        'nome_indicador': 'Caixa - Bradesco'
    }
]

df_series = analisador.get_series_temporais_lote(
    requisicoes,
    drop_na=True,
    fill_value=None
)
```

**Parâmetros**:
- `requisicoes` (list): Lista de dicionários, cada um descrevendo uma série temporal:
  - `identificador` (str): Instituição
  - `conta` (str/int): Indicador
  - `fonte` (str): `'COSIF'` ou `'IFDATA'`
  - `datas` (list): Lista de datas
  - `nome_indicador` (str): Identificador único para a série no resultado
  - Parâmetros específicos: `escopo_ifdata`, `documento_cosif`
- `drop_na`, `fill_value`: Controle de dados ausentes (aplicados a todas as séries)

**Retorno**: DataFrame com colunas `Data`, `Indicador`, `Valor` (formato longo para múltiplas séries).

**Vantagem**: Pré-resolve todas as entidades uma vez e usa recortes otimizados de DataFrames.

---

### Métodos Utilitários

```python
# Limpar cache de resoluções
analisador.clear_cache()

# Recarregar arquivos Parquet (após atualização de dados)
analisador.reload_data()
```

---

## 7. Exemplos Práticos

### Exemplo 1: Consulta Básica COSIF

Buscar o Ativo Total e Patrimônio Líquido do **Conglomerado Prudencial** do Bradesco em março de 2024:

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='Output')

dados = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',  # Pode usar nome ou CNPJ
    contas=['ATIVO TOTAL', 'PATRIMÔNIO LÍQUIDO'],
    datas=202403,
    documentos=4060  # Conglomerado Prudencial
)

print(dados)
```

**Saída**:
```
  Nome_Entidade        CNPJ_8    Data             Conta         Valor
0 BANCO BRADESCO S.A.  60746948  202403  ATIVO TOTAL       2500000000
1 BANCO BRADESCO S.A.  60746948  202403  PATRIMÔNIO LÍQUIDO 150000000
```

---

### Exemplo 2: Consulta Básica IFDATA

Buscar o Índice de Basileia do Banco Inter em março de 2024:

```python
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Índice de Basileia'],
    datas=202403,
    escopo='prudencial'
)

print(dados)
```

---

### Exemplo 3: Controle de Escopo (Individual vs Prudencial)

Comparar o **Ativo Total** no nível **individual** vs **conglomerado prudencial** do Itaú:

```python
# Nível Individual
ativo_individual = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'
)

# Nível Prudencial (Conglomerado)
ativo_prudencial = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

print("Individual:", ativo_individual['Valor'].values[0])
print("Prudencial:", ativo_prudencial['Valor'].values[0])
```

**Opções de escopo**:
- `'individual'`: Apenas a instituição individual
- `'prudencial'`: Conglomerado prudencial (se existir)
- `'financeiro'`: Conglomerado financeiro (se existir)
- `'cascata'` (padrão): Tenta prudencial → financeiro → individual

---

### Exemplo 4: Comparação Entre Múltiplas Instituições

Comparar indicadores-chave dos 3 maiores bancos:

```python
comparacao = analisador.comparar_indicadores(
    identificadores=['60701190', '60746948', '00000000'],  # Itaú, Bradesco, BB
    indicadores=[
        {'nome': 'Ativo Total', 'tipo': 'IFDATA', 'escopo': 'prudencial'},
        {'nome': 'Índice de Basileia', 'tipo': 'IFDATA', 'escopo': 'prudencial'},
        {'nome': 'Segmento', 'tipo': 'ATRIBUTO'}
    ],
    datas=202403
)

print(comparacao)
```

**Saída** (formato pivotado):
```
  Nome_Entidade         CNPJ_8    Ativo Total  Índice de Basileia  Segmento
0 ITAÚ UNIBANCO...     60701190   2800000000   15.2                S1
1 BANCO BRADESCO...    60746948   2500000000   14.8                S1
2 BANCO DO BRASIL...   00000000   2900000000   16.1                S1
```

---

### Exemplo 5: Série Temporal Individual

Buscar a evolução do **Lucro Líquido** do Banco Inter em 2023:

```python
serie = analisador.get_serie_temporal_indicador(
    identificador='Banco Inter',
    conta='Lucro Líquido',
    fonte='IFDATA',
    data_inicio=202301,
    data_fim=202312
)

# Plotar com matplotlib
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(serie['Data'], serie['Valor'], marker='o')
plt.title('Evolução do Lucro Líquido - Banco Inter (2023)')
plt.xlabel('Data')
plt.ylabel('Valor (R$)')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

---

### Exemplo 6: Séries Temporais em Lote (Otimizado) ✨

Buscar séries de **Ativo Total** para 10 bancos simultaneamente de forma otimizada:

```python
bancos = ['60701190', '60746948', '00000000', '00416968', '00000208',
          '02318507', '00360305', '00394460', '04902979', '17298092']

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

# Busca otimizada em uma chamada
df_series = analisador.get_series_temporais_lote(requisicoes)

# Pivotar para análise
df_pivot = df_series.pivot(index='Data', columns='Indicador', values='Valor')
print(df_pivot)
```

**Vantagem**: Este método é **muito mais rápido** que fazer 10 chamadas separadas a `get_serie_temporal_indicador()`.

---

### Exemplo 7: Tratamento de Dados Ausentes

Buscar uma série temporal completa, **preenchendo lacunas com zero**:

```python
serie = analisador.get_serie_temporal_indicador(
    identificador='00000208',
    conta='Lucro Líquido',
    fonte='IFDATA',
    data_inicio=202301,
    data_fim=202312,
    drop_na=False,      # NÃO remover linhas com NaN
    fill_value=0        # Preencher NaNs com 0
)

print(serie)
# Resultado terá todas as 12 datas, com zeros onde não havia dados
```

**Opções de controle**:
- `drop_na=True` (padrão): Remove linhas com valores ausentes
- `drop_na=False`: Mantém linhas com NaN (útil para visualizar lacunas)
- `fill_value=0`: Preenche NaNs com valor específico
- `replace_zeros_with_nan=True`: Converte zeros em NaN (trata zeros como ausentes)

---

### Exemplo 8: Consultas com Códigos e Nomes Mistos

Buscar dados usando uma **mistura de nomes e códigos** de contas:

```python
contas_mistas = [
    'ATIVO TOTAL',      # Busca por nome
    60000002,           # Busca por código (PATRIMÔNIO LÍQUIDO)
    'LUCRO LÍQUIDO'     # Busca por nome
]

dados = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',
    contas=contas_mistas,  # Lista mista
    datas=202403,
    documentos=4060
)

print(dados)
```

---

## 8. Técnicas Avançadas

### Controle Granular de Escopo no IFDATA

O parâmetro `escopo` no método `get_dados_ifdata()` oferece controle preciso sobre qual nível de dados você deseja:

```python
# 1. CASCATA (padrão): Tenta Prudencial → Financeiro → Individual
dados_cascata = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='cascata'  # ou omita o parâmetro
)

# 2. INDIVIDUAL: Apenas a instituição individual
dados_individual = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'
)

# 3. PRUDENCIAL: Apenas o conglomerado prudencial
dados_prudencial = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

# 4. FINANCEIRO: Apenas o conglomerado financeiro
dados_financeiro = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='financeiro'
)
```

**Coluna `ID_BUSCA_USADO`**: Indica qual chave encontrou o dado (CNPJ individual, código do conglomerado prudencial ou código do conglomerado financeiro). Use-a para rastrear a origem exata dos dados.

---

### Busca Otimizada em Lote

Quando você precisa buscar **muitas séries temporais**, sempre use `get_series_temporais_lote()` em vez de múltiplas chamadas individuais:

```python
# ❌ EVITE: Múltiplas chamadas (lento)
series = []
for banco in lista_bancos:
    serie = analisador.get_serie_temporal_indicador(
        identificador=banco,
        conta='Ativo Total',
        fonte='IFDATA',
        datas=[202401, 202402, 202403]
    )
    series.append(serie)

# ✅ PREFIRA: Busca em lote (muito mais rápido)
requisicoes = [
    {
        'identificador': banco,
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': f'Banco_{banco}'
    }
    for banco in lista_bancos
]
df_series = analisador.get_series_temporais_lote(requisicoes)
```

**Por que é mais rápido?**
- Resolve todos os identificadores **uma única vez** no início
- Usa recortes otimizados de DataFrames (`build_subset()`)
- Minimiza operações duplicadas de busca e filtragem

---

### Cache e Performance

A classe `AnalisadorBancario` usa **cache LRU** (Least Recently Used) para otimizar resoluções de identificadores:

```python
# Primeira chamada: Resolve 'Banco Inter' → CNPJ (lento)
dados1 = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Ativo Total'],
    datas=202403
)

# Segunda chamada com mesmo nome: Usa cache (instantâneo)
dados2 = analisador.get_dados_ifdata(
    identificador='Banco Inter',  # Já está no cache!
    contas=['Lucro Líquido'],
    datas=202403
)

# Limpar cache manualmente (se necessário)
analisador.clear_cache()
```

---

### Flexibilidade em Consultas

Você pode consultar por:
- **Nome completo**: `'BANCO BRADESCO S.A.'`
- **Nome parcial**: `'Bradesco'`, `'Inter'`
- **CNPJ de 8 dígitos**: `'60746948'`, `60746948` (string ou int)
- **Códigos de conta**: `10000001` (COSIF), `'Ativo Total'` (IFDATA)
- **Listas mistas**: `['ATIVO TOTAL', 60000002, 'Lucro Líquido']`

A classe normaliza automaticamente os inputs e busca as correspondências corretas.

---

## 9. Arquitetura e Design

### Visão Geral da Arquitetura

O projeto segue uma **arquitetura em camadas** com separação clara de responsabilidades:

```
┌──────────────────────────────────────────────────────┐
│              Camada de Apresentação                  │
│         (Notebooks Jupyter, Scripts Python)          │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              Facade (AnalisadorBancario)             │
│         Interface unificada e simplificada           │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│        Camada de Análise (analysis/)                 │
│   • Comparação de indicadores                        │
│   • Geração de séries temporais                      │
│   • Otimizações de performance                       │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│      Provedores de Dados (providers/)                │
│   • COSIF: Dados contábeis                           │
│   • IFDATA: Indicadores regulatórios                 │
│   • Cadastro: Dados cadastrais                       │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│       Camada de Dados (data/)                        │
│   • Repository Pattern                               │
│   • Loader de arquivos Parquet                       │
│   • Cache e gerenciamento de memória                 │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│       Camada de Persistência                         │
│   • Arquivos Parquet (Input/, Output/)               │
│   • Dicionários Excel                                │
└──────────────────────────────────────────────────────┘
```

### Padrões de Design Implementados

#### 1. Facade Pattern
`AnalisadorBancario` atua como uma fachada que unifica a complexidade de múltiplos componentes em uma interface simples.

#### 2. Repository Pattern
`DataRepository` encapsula a lógica de acesso aos dados, abstraindo a camada de persistência.

#### 3. Dependency Injection
Componentes recebem suas dependências via construtor, facilitando testes e manutenção.

#### 4. Single Responsibility Principle
Cada módulo tem uma responsabilidade única:
- `entity_resolver.py`: Apenas resolução de identificadores
- `cosif.py`: Apenas consultas COSIF
- `ifdata.py`: Apenas consultas IFDATA
- `comparator.py`: Apenas comparações
- `time_series.py`: Apenas séries temporais

### Otimizações de Performance

1. **Cache LRU**: Resoluções de identificadores são cached (256 entradas)
2. **Pré-resolução em Lote**: Métodos de análise resolvem todos os IDs uma vez
3. **Recortes Otimizados**: `build_subset()` cria views eficientes de DataFrames
4. **Cache Local**: Providers mantêm referências locais aos DataFrames em loops
5. **Lazy Loading**: Dados só são carregados quando necessários

---

## 10. Notebooks Incluídos

### `notebooks/etl/data_download.ipynb`

**Pipeline completo de ETL** para download e processamento dos dados do BCB.

**O que faz**:
- Download automático dos arquivos COSIF e IFDATA do site do BCB
- Limpeza e padronização de dados brutos
- Unificação de múltiplas fontes
- Geração de dicionários de referência (Excel)
- Salvamento otimizado em formato Parquet

**Quando executar**:
- Primeira vez (obrigatório)
- Mensalmente ou quando novos dados forem publicados
- Após mudanças na estrutura de dados do BCB

---

### `notebooks/analysis/example.ipynb`

**Tutorial completo** com exemplos práticos de uso do `AnalisadorBancario`.

**Conteúdo**:
- **Seção 1**: Consultas fundamentais (COSIF, IFDATA, Cadastro)
- **Seção 2**: Análises comparativas entre instituições
- **Seção 3**: Séries temporais e visualizações
- **Seção 4**: Técnicas avançadas (escopo, tratamento de NaNs, otimizações)

**Para quem**: Iniciantes e usuários intermediários.

---

### `notebooks/analysis/full_table.ipynb`

**Exemplos de construção de tabelas completas** com múltiplos indicadores e instituições.

**Casos de uso**:
- Construção de dashboards
- Relatórios comparativos
- Análises de mercado

---

## 11. Migrando da Versão 1.x

A v2.0.0 é **100% compatível** com código da v1.x, exceto pelos imports. Siga estes passos:

### Passo 1: Instalar o Pacote

```bash
# Na raiz do projeto
pip install -e .
```

### Passo 2: Atualizar Imports

**ANTES (v1.x)**:
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

**DEPOIS (v2.0)**:
```python
# Import direto, sem manipulação de paths
from bacen_analysis import AnalisadorBancario
```

### Passo 3: Usar Normalmente

Todos os métodos mantêm a **mesma assinatura**:

```python
# Código v1.x funciona sem alterações (após atualizar imports)
analisador = AnalisadorBancario(diretorio_output='Output')

dados = analisador.get_dados_cosif(
    identificador='60701190',
    contas=['ATIVO TOTAL'],
    datas=202403,
    documentos=4060
)
```

### Novos Recursos Disponíveis (Opcionais)

Após a migração, você pode aproveitar os novos recursos:

```python
# 1. Controle de escopo no IFDATA
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'  # NOVO parâmetro
)

# 2. Busca otimizada em lote
requisicoes = [...]  # Lista de requisições
df_series = analisador.get_series_temporais_lote(requisicoes)  # NOVO método
```

---

## 12. Manutenção e Troubleshooting

### Atualizando os Dados

Para buscar novos meses de dados:

1. Abra e execute `notebooks/etl/data_download.ipynb` novamente
2. O notebook baixará apenas os dados novos (incremental)
3. Recarregue os dados no analisador (se já estiver instanciado):

```python
analisador.reload_data()
```

---

### Consultas Sem Resultado?

Se uma consulta não retornar dados, siga este checklist:

#### 1. Consulte os Dicionários de Referência

Use os arquivos Excel no diretório `Output/` para encontrar os identificadores corretos:

- **`dicionario_entidades.xlsx`**: Nomes oficiais e CNPJs de instituições
- **`dicionario_contas_cosif_individual.xlsx`**: Contas COSIF individual
- **`dicionario_contas_cosif_prudencial.xlsx`**: Contas COSIF prudencial
- **`dicionario_contas_ifdata.xlsx`**: Indicadores IFDATA
- **`dicionario_atributos_cadastro.xlsx`**: Atributos cadastrais disponíveis

#### 2. Verifique o Escopo/Documento

Certifique-se de que os dados existem para a combinação de:
- **Data**: O BCB publica dados com 1-2 meses de atraso
- **Escopo**: Nem todas as instituições têm dados consolidados (prudencial/financeiro)
- **Documento**: COSIF tem diferentes tipos (4010, 4016, 4060, 4066)

Exemplo:
```python
# Se não encontrar no prudencial, tente individual
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'  # Tente diferentes escopos
)
```

#### 3. Use a Coluna `ID_BUSCA_USADO` (IFDATA)

Para consultas IFDATA, verifique qual ID foi usado para encontrar o dado:

```python
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='cascata'
)

# Verificar de onde o dado veio
print(dados['ID_BUSCA_USADO'])
# Saída: '62144175' (conglomerado prudencial)
```

**Interpretação**:
- Se `ID_BUSCA_USADO == CNPJ_8 da entidade`: Dado veio da instituição individual
- Se `ID_BUSCA_USADO != CNPJ_8`: Dado veio de um conglomerado

#### 4. Verifique a Grafia do Nome

Nomes de instituições e contas devem corresponder aos dicionários:

```python
# ❌ Pode não encontrar
dados = analisador.get_dados_cosif(
    identificador='Bradesco',  # Nome parcial
    contas=['Ativo'],          # Nome incompleto
    datas=202403
)

# ✅ Melhor: Use CNPJ ou nome completo
dados = analisador.get_dados_cosif(
    identificador='60746948',    # CNPJ sempre funciona
    contas=['ATIVO TOTAL'],      # Nome completo da conta
    datas=202403,
    documentos=4060
)
```

#### 5. Verifique Disponibilidade dos Dados

Nem todos os dados existem para todas as instituições em todas as datas. Use o escopo `'cascata'` (padrão) para buscar automaticamente em múltiplos níveis:

```python
dados = analisador.get_dados_ifdata(
    identificador='00000208',
    contas=['Índice de Basileia'],
    datas=202403,
    escopo='cascata'  # Tenta prudencial → financeiro → individual
)

if dados.empty:
    print("Dado não disponível para esta data/instituição")
```

---

### Erros Comuns

#### `FileNotFoundError: Arquivo Parquet não encontrado`

**Causa**: Pipeline de ETL não foi executado.

**Solução**: Execute `notebooks/etl/data_download.ipynb` primeiro.

---

#### `KeyError` ou valores vazios

**Causa**: Nome de conta/indicador incorreto ou dado não existe.

**Solução**: Consulte os dicionários Excel em `Output/` para encontrar os nomes corretos.

---

## 13. Licença e Créditos

### Licença

Este projeto está licenciado sob a [Licença MIT](https://opensource.org/licenses/MIT).

### Fonte dos Dados

Todos os dados financeiros são de **domínio público** e foram obtidos do:
- **Banco Central do Brasil (BCB)**
- Sistema COSIF
- Sistema IF.DATA

### Autor

**Enzo Moreira**

### Contribuições

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request


**Versão**: 2.0.0 | **Última atualização**: Novembro 2025
