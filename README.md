# Análise de Dados Financeiros do Banco Central

## 1. Visão Geral

Este projeto é um pipeline de dados e uma ferramenta de análise para os relatórios financeiros de instituições brasileiras, disponibilizados pelo Banco Central do Brasil (BCB). Ele automatiza o processo de baixar, limpar, padronizar e conectar dados complexos de múltiplas fontes (COSIF e IF.DATA), tornando-os acessíveis para análise através de uma interface Python simples e poderosa.

O objetivo principal é permitir a extração de insights valiosos dos dados do BCB sem a necessidade de lidar com a complexidade do tratamento e da unificação dos dados brutos.

### Fluxo do Projeto

1.  **ETL (Extração, Transformação e Carga):** O notebook `Code/DataDownload.ipynb` baixa os relatórios, padroniza as colunas, resolve inconsistências e salva os dados limpos em formato Parquet, otimizado para performance.
2.  **Análise de Dados:** Notebooks de exemplo, como o `Analysis/DataAnalysis_example.ipynb`, demonstram como utilizar a classe `AnalisadorBancario` (do arquivo `Code/DataUtils.py`), que é o coração da ferramenta, para realizar consultas de forma intuitiva.

## 2. Estrutura de Arquivos

Ao clonar o repositório, você terá a seguinte estrutura:

```
.
├── Analysis/
│   ├── Banks.csv                     # Lista de bancos para demonstração nos exemplos.
│   ├── DataAnalysis_example.ipynb    # Notebook com exemplos de como usar a ferramenta.
│   └── DataAnalysis.ipynb            # Notebook com exemplo de uma tabela completa.
│
├── Code/
│   ├── DataDownload.ipynb        # Notebook para download e processamento dos dados (ETL).
│   └── DataUtils.py              # Módulo com a classe AnalisadorBancario.
│
├── .gitignore                    # Pastas e arquivos que o Git ignora.
├── README.md                     # Este arquivo.
└── requirements.txt              # Libraries necessárias.
```**Nota:** Os diretórios `Input/` e `Output/` serão criados automaticamente quando você executar o notebook `DataDownload.ipynb`.

## 3. Como Começar

### Passo a Passo

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/enzoomoreira/bacen-data-analysis.git
    cd bacen-data-analysis
    ```

2.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute o Pipeline de ETL (Passo Essencial):**
    -   Abra e execute o notebook `Code/DataDownload.ipynb` do início ao fim.
    -   **Atenção:** A primeira execução pode demorar. Em execuções futuras, ele baixará apenas os dados novos.
    -   Ao final, o diretório `Output/` conterá os arquivos `.parquet` processados e os **dicionários de referência em Excel**, que são cruciais para a análise.

4.  **Explore e Analise:**
    -   Abra o notebook `Analysis/DataAnalysis_example.ipynb`. Ele serve como um tutorial prático e demonstração dos principais recursos.
    -   Consulte os arquivos gerados em `Output/`, especialmente `dicionario_entidades.xlsx`, para encontrar os nomes e identificadores corretos dos bancos.
    -   Crie seu próprio notebook de análise e comece a usar a classe `AnalisadorBancario`!

## 4. Guia de Uso do `AnalisadorBancario`

A classe `AnalisadorBancario` é a sua interface para os dados. Após inicializá-la, você pode usar seus métodos para fazer consultas complexas.

### Inicialização
```python
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Setup do path para encontrar os módulos do projeto
code_dir = Path('.').resolve().parent / 'Code'
if str(code_dir) not in sys.path:
    sys.path.append(str(code_dir))

import DataUtils as du
from DataUtils import AnalisadorBancario

# Inicialização do Analisador
output_dir = Path('.').resolve().parent / 'Output'
analisador = AnalisadorBancario(diretorio_output=str(output_dir))
```

### **O Padrão de Saída: Consistência é Chave**

Um dos principais recursos da classe é a **consistência da saída**. Todos os métodos que retornam dados sobre uma ou mais entidades sempre incluirão as colunas `Nome_Entidade` e `CNPJ_8` no início do DataFrame. Isso garante que você sempre saiba a qual instituição os dados se referem, usando seu nome oficial e CNPJ padronizado.

### Métodos Principais de Consulta

-   `get_dados_cosif(...)`: Busca dados contábeis detalhados (Balanço/DRE) da fonte COSIF.
-   `get_dados_ifdata(...)`: Busca indicadores regulatórios (Basileia, etc.) da fonte IF.DATA.
-   `get_atributos_cadastro(...)`: Busca informações cadastrais de uma entidade (Segmento, Situação, etc.).
-   `comparar_indicadores(...)`: Cria uma tabela-resumo "pivotada" para comparar múltiplos indicadores entre várias instituições.
-   `get_serie_temporal_indicador(...)`: Busca a evolução de um único indicador ao longo do tempo, retornando uma série temporal pronta para plotagem.

### Exemplos de Uso e Técnicas Avançadas

#### a. Controle de Escopo da Busca (Individual vs. Conglomerado)

A classe oferece controle granular sobre qual nível de dados você deseja analisar.

-   **Para dados COSIF**, use o parâmetro `documentos` (ex: `4010` para individual, `4060` para prudencial). A classe infere o tipo automaticamente.
-   **Para dados IF.DATA**, use o novo parâmetro `escopo_ifdata`, que aceita `'individual'`, `'prudencial'`, `'financeiro'` ou `'cascata'` (padrão).

```python
# Exemplo 1: Buscando o Ativo Total do CONGLOMERADO PRUDENCIAL do Itaú
dados_prudenciais = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial' # A chave é o parâmetro 'escopo'
)

# Exemplo 2: Buscando o mesmo dado, mas APENAS da instituição individual
dados_individuais = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'
)
```

#### b. Controle Explícito de Dados Ausentes e Zeros

O método `get_serie_temporal_indicador` possui parâmetros claros para lidar com dados ausentes e zeros, oferecendo total controle sobre o resultado.

-   `drop_na=True` (Padrão): Remove as linhas onde o valor do indicador é `NaN` (ausente).
-   `drop_na=False`: Mantém as linhas com `NaN`, útil para visualizar lacunas em séries temporais.
-   `fill_value=...`: Preenche os valores `NaN` com um número específico (ex: `fill_value=0`).
-   `replace_zeros_with_nan=True`: Converte todos os valores `0` para `NaN`, tratando-os como dados ausentes.

```python
# Exemplo: Gerar uma série temporal completa, preenchendo lacunas com 0
serie_completa = analisador.get_serie_temporal_indicador(
    identificador='Banco Inter',
    conta='Lucro Líquido',
    fonte='IFDATA',
    data_inicio=202301,
    data_fim=202312,
    drop_na=False,     # Não remove as linhas com NaN
    fill_value=0       # Preenche os NaNs com 0
)
```

#### c. Flexibilidade na Consulta de Contas

Os métodos que aceitam o parâmetro `contas` são flexíveis. Você pode passar uma lista de nomes (strings), códigos (inteiros), ou uma **lista mista**.

```python
# Exemplo de consulta mista para o Bradesco
contas_mistas = [
    'ATIVO TOTAL', # Busca por nome
    60000002       # Busca pelo código do 'PATRIMÔNIO LÍQUIDO'
]

dados_mistos = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',
    contas=contas_mistas,
    datas=202403,
    documentos=4060
)```

## 5. Manutenção e Depuração

-   **Atualizando os Dados:** Para buscar novos meses, simplesmente execute o notebook `Code/DataDownload.ipynb` novamente.
-   **Consultas sem Resultado?**
    1.  **Consulte os Dicionários:** Use os arquivos `.xlsx` no diretório `Output/`, especialmente `dicionario_entidades.xlsx` e os `dicionario_contas_*.xlsx`, para encontrar os nomes e códigos corretos.
    2.  **Verifique o Escopo/Documento:** Certifique-se de que os dados para a combinação de data, escopo e documento que você pediu existem. Nem todas as instituições reportam todos os dados em todos os níveis.
    3.  **Entenda a Origem do Dado (IF.DATA):** O método `get_dados_ifdata` retorna a coluna `ID_BUSCA_USADO`. Ela informa qual chave encontrou o dado (o CNPJ da própria entidade, o código do conglomerado prudencial ou o código do conglomerado financeiro). Isso é uma ferramenta poderosa para entender a origem do dado. Se um valor não aparece, ele não existe em nenhuma das chaves aplicáveis para a data solicitada.