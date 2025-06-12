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
import numpy as np # Importe para usar np.nan

output_dir = Path('./Output').resolve()
analisador = AnalisadorBancario(diretorio_output=str(output_dir))
```

### Conceitos Fundamentais

#### a. A "Mágica" da Tradução de Identidade

A ferramenta foi projetada para lidar com a complexa estrutura de conglomerados do sistema financeiro.

-   **Entidade Individual:** Uma instituição específica (ex: "Itaú Veículos", com seu próprio CNPJ).
-   **Conglomerado:** O grupo financeiro ao qual a entidade pertence. Os dados consolidados (prudenciais e financeiros) são reportados por uma instituição **líder**.

Quando você pede um dado para "Itaú Veículos", a classe automaticamente descobre a qual conglomerado ele pertence e busca os dados reportados pelo líder. Isso é essencial para análises de risco e porte do grupo.

#### b. Códigos de Documento COSIF

-   **Individuais:** `4010` (Balancete), `4016` (Balanço).
-   **Prudenciais:** `4060` (Balancete Consolidado), `4066` (Balanço Consolidado).

### Métodos Principais de Consulta

Os métodos a seguir são os blocos de construção para suas análises.

-   **`get_dados_cosif(...)`**: Busca dados contábeis (Balanço/DRE).
-   **`get_dados_ifdata(...)`**: Busca indicadores regulatórios (Basileia, etc.).
-   **`get_atributos_cadastro(...)`**: Busca informações cadastrais (Segmento, Situação, etc.).
-   **`get_serie_temporal_indicador(...)`**: Busca a evolução de um indicador ao longo do tempo.
-   **`comparar_indicadores(...)`**: Cria uma tabela-resumo para análise de pares.

### Técnicas Avançadas de Consulta

#### a. Buscando por Nome ou Código de Conta

Todos os métodos que aceitam o parâmetro `contas` são flexíveis. Você pode passar uma lista de nomes (strings), uma lista de códigos (inteiros), ou uma **lista mista**.

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
display(dados_mistos)
```

#### b. Buscando Dados Individuais vs. Prudenciais

Para análises COSIF, você pode especificar se deseja os dados da entidade específica ou do conglomerado consolidado.

```python
# Busca o Ativo Total APENAS da entidade Nu Financeira S.A.
dados_individuais = analisador.get_dados_cosif(
    identificador='NU FINANCEIRA S.A.',
    contas=['TOTAL GERAL DO ATIVO'],
    datas=202403,
    tipo='individual' # A chave é o parâmetro 'tipo'
)

# Busca o Ativo Total do CONGLOMERADO Nubank
dados_prudenciais = analisador.get_dados_cosif(
    identificador='NU FINANCEIRA S.A.',
    contas=['TOTAL GERAL DO ATIVO'],
    datas=202403,
    tipo='prudencial' # Este é o comportamento padrão
)
```

#### c. Tratando Zeros e Dados Ausentes (`fillna`)

Os métodos `comparar_indicadores` e `get_serie_temporal_indicador` possuem um parâmetro `fillna` para controlar a apresentação de dados ausentes (`NaN`) e zeros (`0`).

**Cenário 1: Padrão (Dados Brutos)**
Se você não passar o parâmetro `fillna`, os dados são retornados como estão. Ideal para análise estatística precisa.
- `0` é retornado como `0`.
- Ausente é retornado como `NaN`.

**Cenário 2: Relatório Limpo (Preencher com Zero)**
Para relatórios visuais onde `NaN` não é desejado.
```python
tabela_relatorio = analisador.comparar_indicadores(
    ...,
    fillna=0
)
# Output: Todos os NaN (dados ausentes) são convertidos para 0.
```

**Cenário 3: Análise Estatística Pura (Tratar Zeros como Ausentes)**
Útil quando um `0` pode significar "não aplicável" em vez de um valor real.
```python
tabela_estatistica = analisador.comparar_indicadores(
    ...,
    fillna=np.nan
)
# Output: Todos os 0s e os dados ausentes são representados como NaN.
```

## 5. Manutenção e Depuração

-   **Atualizando os Dados:** Para buscar novos meses, simplesmente execute o notebook `Code/DataDownload.ipynb` novamente.
-   **Consultas sem Resultado?**
    1.  **Consulte os Dicionários:** Use os arquivos `.xlsx` no diretório `Output/`, especialmente `dicionario_entidades.xlsx` e os `dicionario_contas_*.xlsx`, para encontrar os nomes e códigos corretos.
    2.  **Verifique a Data/Documento:** Certifique-se de que os dados para a combinação de data e documento que você pediu existem.
    3.  **Entenda a Lógica de Busca:** Lembre-se que para o `IFDATA`, a ferramenta tenta buscar por 3 chaves (Congl. Prudencial, Congl. Financeiro, e CNPJ Individual), parando na primeira que encontra sucesso. Se um dado não aparece, ele não existe em nenhuma dessas chaves para a data solicitada.
```