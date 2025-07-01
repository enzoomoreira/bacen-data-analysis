# Análise de Dados Financeiros do Banco Central

## 1. Visão Geral

Este projeto é um pipeline completo de dados e uma ferramenta de análise para os relatórios financeiros de instituições brasileiras, disponibilizados pelo Banco Central do Brasil (BCB). Ele automatiza o processo de baixar, limpar, padronizar e conectar dados complexos de múltiplas fontes (COSIF e IFDATA), tornando-os acessíveis para análise através de uma interface Python simples e poderosa.

O objetivo principal é permitir a extração de insights valiosos dos dados do BCB sem a necessidade de lidar com a complexidade do tratamento e da unificação dos dados brutos.

### Fluxo do Projeto

1.  **ETL (Extração, Transformação e Carga):** O notebook `Code/DataDownload.ipynb` baixa os relatórios, padroniza as colunas, resolve inconsistências e salva os dados limpos em formato Parquet, otimizado para performance.
2.  **Análise de Dados:** Notebooks de exemplo, `Analysis/DataAnalysis.ipynb` e `Analysis/DataAnalysis_example.ipynb`, demonstram como utilizar a classe `AnalisadorBancario` (do arquivo `Code/DataUtils.py`), que é o coração da ferramenta, para realizar consultas de forma intuitiva.

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
```
**Nota:** Os diretórios `Input/` e `Output/` serão criados automaticamente quando você executar o notebook `DataDownload.ipynb`.

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
    -   Abra o notebook `Analysis/DataAnalysis.ipynb` ou `Analysis/DataAnalysis_example.ipynb` . Eles servem como tutoriais práticos.
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

```
# Exemplo da estrutura de saída padrão
  Nome_Entidade            CNPJ_8    ... (outras colunas de dados)
0 BANCO BRADESCO S.A.      60746948  ...
1 NU FINANCEIRA S.A. ...   30680829  ...
```

### Métodos Principais de Consulta

-   `get_dados_cosif(...)`: Busca dados contábeis detalhados (Balanço/DRE) da fonte COSIF. Retorna a tabela de dados brutos da fonte, enriquecida com `Nome_Entidade` e `CNPJ_8`.

-   `get_dados_ifdata(...)`: Busca indicadores regulatórios (Basileia, etc.) da fonte IF.DATA. Além de `Nome_Entidade` e `CNPJ_8`, este método também retorna a coluna `ID_BUSCA_USADO`, útil para depuração (veja a seção de Manutenção).

-   `get_atributos_cadastro(...)`: Busca informações cadastrais de uma entidade (Segmento, Situação, etc.).

-   `comparar_indicadores(...)`: Cria uma tabela-resumo "pivotada" para comparar múltiplos indicadores entre várias instituições lado a lado. Ideal para análise de pares.

-   `get_serie_temporal_indicador(...)`: Busca a evolução de um indicador ao longo do tempo. Retorna uma série temporal que pode ser formatada como `'wide'` (padrão, para plotagem) ou `'long'` (ideal para ferramentas de BI e concatenação de dados).

### Exemplos de Uso e Técnicas Avançadas

#### a. Buscando por Nome ou Código de Conta

Todos os métodos que aceitam o parâmetro `contas` são flexíveis. Você pode passar uma lista de nomes (strings), códigos (inteiros), ou uma **lista mista**.

```python
# Exemplo de consulta mista para o Bradesco
contas_mistas = [
    'TOTAL GERAL DO ATIVO', # Busca por nome
    60000002              # Busca pelo código do 'PATRIMÔNIO LÍQUIDO'
]

dados_mistos = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',
    contas=contas_mistas,
    datas=202403
)

# O resultado sempre mostrará o nome da conta, independentemente de como foi buscada.
display(dados_mistos[['Nome_Entidade', 'CONTA_COSIF', 'NOME_CONTA_COSIF', 'VALOR_CONTA_COSIF']])
```

#### b. Buscando Dados Individuais vs. Prudenciais

Para análises COSIF, você pode especificar se deseja os dados da entidade específica ou do conglomerado consolidado, usando o parâmetro `tipo`.

```python
# Busca o Ativo Total do CONGLOMERADO Nubank (comportamento padrão)
dados_prudenciais = analisador.get_dados_cosif(
    identificador='NU FINANCEIRA S.A.',
    contas=['TOTAL GERAL DO ATIVO'],
    datas=202403,
    tipo='prudencial' # ou omitindo o parâmetro 'tipo'
)

# Busca o Ativo Total APENAS da entidade Nu Financeira S.A.
dados_individuais = analisador.get_dados_cosif(
    identificador='NU FINANCEIRA S.A.',
    contas=['TOTAL GERAL DO ATIVO'],
    datas=202403,
    tipo='individual' # A chave é o parâmetro 'tipo'
)
```

#### c. Tratando Zeros e Dados Ausentes (`fillna`)

Os métodos `comparar_indicadores` e `get_serie_temporal_indicador` possuem um parâmetro `fillna` para controlar a apresentação de dados ausentes (`NaN`) e zeros (`0`).

-   **`fillna=None` (Padrão):** Retorna os dados como estão. `0` é `0`, ausente é `NaN`.
-   **`fillna=0`:** Converte todos os `NaN` (ausentes) para `0`. Ideal para relatórios visuais.
-   **`fillna=np.nan`:** Converte todos os `0` para `NaN`. Útil quando `0` pode significar "não aplicável".

```python
# Exemplo: Tratar zeros como ausentes na tabela comparativa
tabela_estatistica = analisador.comparar_indicadores(
    ...,
    fillna=np.nan
)
```

#### d. Escolhendo o Formato da Série Temporal (Long vs. Wide)

O método `get_serie_temporal_indicador` possui o parâmetro `formato_saida` para maior flexibilidade.

-   **`formato_saida='wide'` (Padrão):** Retorna um DataFrame com as datas como índice e o valor do indicador como coluna. Ideal para plotar um gráfico rapidamente.
-   **`formato_saida='long'`:** Retorna um DataFrame com as colunas `DATA`, `Nome_Entidade`, `CNPJ_8`, `Conta` e `Valor`. Este formato é perfeito para ser usado em ferramentas de Business Intelligence (como Power BI e Tableau) ou para empilhar várias séries temporais em uma única tabela.

```python
# Exemplo: Buscar o Patrimônio Líquido do Itaú em formato 'long'
serie_longa = analisador.get_serie_temporal_indicador(
    identificador='ITAÚ UNIBANCO',
    conta='Patrimônio Líquido',
    data_inicio=202301,
    data_fim=202312,
    fonte='IFDATA',
    formato_saida='long'
)

display(serie_longa.head())

# Saída esperada (estrutura):
#          DATA   Nome_Entidade    CNPJ_8             Conta         Valor
# 0  2023-03-31  ITAÚ UNIBANCO...  60701190  Patrimônio Líquido  1.67...e+08
# 1  2023-06-30  ITAÚ UNIBANCO...  60701190  Patrimônio Líquido  1.71...e+08
# 2  2023-09-30  ITAÚ UNIBANCO...  60701190  Patrimônio Líquido  1.74...e+08
# 3  2023-12-31  ITAÚ UNIBANCO...  60701190  Patrimônio Líquido  1.77...e+08
```

## 5. Manutenção e Depuração

-   **Atualizando os Dados:** Para buscar novos meses, simplesmente execute o notebook `Code/DataDownload.ipynb` novamente.
-   **Consultas sem Resultado?**
    1.  **Consulte os Dicionários:** Use os arquivos `.xlsx` no diretório `Output/`, especialmente `dicionario_entidades.xlsx` e os `dicionario_contas_*.xlsx`, para encontrar os nomes e códigos corretos.
    2.  **Verifique a Data/Documento:** Certifique-se de que os dados para a combinação de data e documento que você pediu existem.
    3.  **Entenda a Lógica de Busca (IF.DATA):** O método `get_dados_ifdata` possui uma busca em múltiplos estágios. A coluna `ID_BUSCA_USADO` na saída informa qual chave encontrou o dado (o CNPJ da própria entidade, o código do conglomerado prudencial ou o código do conglomerado financeiro). Isso é uma ferramenta poderosa para entender a origem do dado. Se um valor não aparece, ele não existe em nenhuma dessas chaves para a data solicitada.