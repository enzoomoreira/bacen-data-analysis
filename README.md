# Análise de Dados Financeiros do Banco Central

## 1. Visão Geral

Este projeto é um pipeline completo de dados e uma ferramenta de análise para os relatórios financeiros de instituições brasileiras, disponibilizados pelo Banco Central do Brasil (BCB). Ele automatiza o processo de baixar, limpar, padronizar e conectar dados complexos de múltiplas fontes (COSIF e IFDATA), tornando-os acessíveis para análise através de uma interface Python simples e poderosa.

O objetivo principal é permitir que analistas, estudantes e pesquisadores possam extrair insights valiosos dos dados do BCB sem a necessidade de lidar com a complexidade do tratamento e da unificação dos dados brutos.

### Fluxo do Projeto

1.  **ETL (Extração, Transformação e Carga):** O notebook `Code/DataDownload.ipynb` baixa os relatórios, padroniza as colunas, resolve inconsistências e salva os dados limpos em formato Parquet, otimizado para performance.
2.  **Análise de Dados:** Notebooks de exemplo, `Analysis/DataAnalysis_example.ipynb` e `Analysis/DataAnalysis_example_2.ipynb`, demonstram como utilizar a classe `AnalisadorBancario` (do arquivo `Code/DataUtils.py`), que é o coração da ferramenta, para realizar consultas de forma intuitiva.

## 2. Estrutura de Arquivos

Ao clonar o repositório, você terá a seguinte estrutura:

```
.
├── Analysis/
│   ├── DataAnalysis_example.ipynb  # Notebook com exemplos de como usar a ferramenta.
│   └── DataAnalysis_example_2.ipynb  # Notebook com exemplos de como usar a ferramenta.
│
├── Code/
│   ├── DataDownload.ipynb        # Notebook para download e processamento dos dados (ETL).
│   └── DataUtils.py              # Módulo com a classe AnalisadorBancario.
│
└── README.md                     # Este arquivo.
```
**Nota:** Os diretórios `Input/` e `Output/` serão criados automaticamente quando você executar o notebook `DataDownload.ipynb`.

## 3. Como Começar

### Passo a Passo

1.  **Clone o Repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DO_REPOSITORIO]
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
    -   Abra o notebook `Analysis/DataAnalysis_example.ipynb` ou `Analysis/DataAnalysis_example_2.ipynb`. Eles servem como tutoriais práticos.
    -   Consulte os arquivos gerados em `Output/`, especialmente `dicionario_entidades.xlsx`, para encontrar os nomes e identificadores corretos dos bancos.
    -   Crie seu próprio notebook de análise e comece a usar a classe `AnalisadorBancario`!

## 4. Guia de Uso do `AnalisadorBancario`

A classe `AnalisadorBancario` é a sua interface para os dados. Após inicializá-la, você pode usar seus métodos para fazer consultas complexas.

### Inicialização
```python
from Code.DataUtils import AnalisadorBancario
from pathlib import Path
import numpy as np # Importe o numpy para usar np.nan

output_dir = Path('./Output').resolve()
analisador = AnalisadorBancario(diretorio_output=str(output_dir))
```

### Conceitos Fundamentais

#### a. A "Mágica" da Tradução de Identidade

A ferramenta foi projetada para lidar com a complexa estrutura de conglomerados do sistema financeiro.

-   **Entidade Individual:** Uma instituição específica (ex: "Itaú Veículos", com seu próprio CNPJ).
-   **Conglomerado:** O grupo financeiro ao qual a entidade pertence (ex: Itaú Unibanco). Os dados consolidados são reportados por uma entidade **líder**.

Quando você pede um dado prudencial para "Itaú Veículos", a classe automaticamente:
1.  Encontra o CNPJ da entidade.
2.  Descobre a qual conglomerado ela pertence.
3.  Identifica o CNPJ da entidade líder do conglomerado.
4.  Busca os dados usando o CNPJ do líder.

Isso garante que você sempre obtenha os dados consolidados corretos, que são os mais importantes para análise de risco e porte.

#### b. Códigos de Documento COSIF

-   **Individuais:** `4010` (Balancete), `4016` (Balanço).
-   **Prudenciais:** `4060` (Balancete Consolidado), `4066` (Balanço Consolidado).

### Métodos de Consulta

#### `get_serie_temporal_indicador(...)`

Busca a evolução de um indicador ao longo do tempo. Ideal para gráficos.

**Parâmetros Adicionais:**
-   `fillna` (opcional): Controla como tratar dados ausentes ou zeros.
    -   `None` (padrão): Retorna os dados como estão (`0` é `0`, ausente é `NaN`).
    -   `0`: Preenche todos os valores ausentes (`NaN`) com `0`.
    -   `np.nan`: Converte os `0`s da fonte em `NaN`, unificando todos os dados não-positivos como "ausentes".

**Exemplo:**
```python
# Obter a série do Patrimônio Líquido do Itaú, tratando zeros como dados ausentes
serie_pl_itau = analisador.get_serie_temporal_indicador(
    identificador='ITAU UNIBANCO S.A.',
    conta='PATRIMÔNIO LÍQUIDO',
    data_inicio=202301,
    data_fim=202403,
    fonte='COSIF',
    documento_cosif=4060,
    fillna=np.nan # Trata zeros como ausentes
)
serie_pl_itau.plot(title='Evolução do Patrimônio Líquido - Itaú');
```

#### `comparar_indicadores(...)`

A ferramenta mais poderosa para análise de pares. Cria uma tabela-resumo com múltiplos indicadores de diferentes fontes.

**Parâmetros Adicionais:**
-   `fillna` (opcional): Mesma lógica da função de série temporal, aplicada a toda a tabela.

**Exemplo:**
```python
# Dicionário que define os indicadores desejados
indicadores = {
    'Patrimônio Líquido': {'tipo': 'COSIF', 'conta': 'PATRIMÔNIO LÍQUIDO'},
    'Índice de Basileia': {'tipo': 'IFDATA', 'conta': 'Índice de Basileia'},
    'Situação Cadastral': {'tipo': 'Atributo', 'atributo': 'SITUACAO_IFD_CAD'}
}

# Lista de bancos (use nomes do dicionario_entidades.xlsx para precisão)
bancos = ['ITAU UNIBANCO S.A.', 'BANCO BRADESCO S.A.', 'NU FINANCEIRA S.A. - SOCIEDADE DE CRÉDITO, FINANCIAMENTO E INVESTIMENTO']

# Gerar um relatório limpo, preenchendo dados ausentes com 0
tabela_relatorio = analisador.comparar_indicadores(
    identificadores=bancos,
    indicadores=indicadores,
    data=202403,
    documento_cosif=4060,
    fillna=0
)
display(tabela_relatorio)
```
*Outros métodos como `get_dados_cosif`, `get_dados_ifdata`, e `get_atributos_cadastro` também estão disponíveis para consultas mais granulares.*

## 5. Manutenção e Depuração

-   **Atualizando os Dados:** Para buscar novos meses, simplesmente execute o notebook `Code/DataDownload.ipynb` novamente.
-   **Consultas sem Resultado?**
    1.  **Consulte os Dicionários:** Use os arquivos `.xlsx` no diretório `Output/`, especialmente `dicionario_entidades.xlsx`, para encontrar os nomes e contas corretos.
    2.  **Verifique a Data/Documento:** Certifique-se de que os dados para a combinação de data e documento que você pediu existem.
    3.  **Entenda a Lógica de Busca:** Lembre-se que para o `IFDATA`, a ferramenta tenta buscar por 3 chaves (Congl. Prudencial, Congl. Financeiro, e CNPJ Individual), parando na primeira que encontra sucesso. Se um dado não aparece, ele não existe em nenhuma dessas chaves para a data solicitada.
```