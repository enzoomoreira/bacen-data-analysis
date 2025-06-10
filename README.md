Excelente ideia. Um bom `README.md` é o que transforma um projeto pessoal em uma ferramenta útil para outras pessoas (ou para o seu "eu" do futuro). Ele serve como documentação, guia de usuário e manual de manutenção, tudo em um só lugar.

Preparei uma estrutura de `README.md` completa, seguindo as melhores práticas. Ela é detalhada, cheia de exemplos de código e explica tanto o "o quê" quanto o "porquê" do projeto.

Você pode copiar e colar o conteúdo abaixo diretamente em um arquivo `README.md` na raiz do seu repositório.

---

# Análise de Dados Financeiros do Banco Central

## 1. Visão Geral do Projeto

Este projeto consiste em um pipeline de dados completo para baixar, processar e analisar informações financeiras de instituições brasileiras, utilizando as APIs e os arquivos de dados públicos do Banco Central do Brasil (BCB).

O objetivo é transformar dados brutos e complexos, provenientes de diferentes fontes (COSIF, IFDATA), em uma estrutura de dados limpa, padronizada e pronta para análise. Para facilitar a extração de insights, o projeto inclui uma poderosa classe de análise em Python (`AnalisadorBancario`) que abstrai toda a complexidade de conectar e consultar esses dados.

O fluxo do projeto é dividido em duas etapas principais:

1.  **ETL (Extração, Transformação e Carga):** Realizado pelo notebook `DataDownload.ipynb`. Ele automatiza o download dos relatórios COSIF (Individual e Prudencial) e IFDATA (Cadastro e Valores), limpa-os, padroniza os nomes das colunas e os salva em formato Parquet, otimizado para performance.
2.  **Análise de Dados:** Realizada no notebook `DataAnalysis2.ipynb`, que utiliza a classe `AnalisadorBancario` (definida em `Code/DataUtils.py`) para realizar consultas complexas de forma simples e intuitiva.

## 2. Estrutura de Arquivos

```
.
├── Analysis/
│   ├── DataAnalysis2.ipynb       # Notebook principal para análise de dados.
│   └── referencia_nomes_consulta.xlsx # Arquivo gerado com nomes para consulta.
│
├── Code/
│   ├── DataDownload.ipynb        # Notebook para download e processamento dos dados (ETL).
│   └── DataUtils.py              # Módulo com a classe AnalisadorBancario e funções de utilidade.
│
├── Input/                        # Diretório para os dados brutos baixados (criado automaticamente).
│
├── Output/                       # Diretório para os dados processados (criado automaticamente).
│
└── README.md                     # Este arquivo.
```

## 3. Como Começar

### Pré-requisitos

-   Python 3.9+
-   Bibliotecas listadas em `requirements.txt` (sugestão: `pandas`, `requests`, `openpyxl`, `matplotlib`).

### Passo a Passo

1.  **Clone o Repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DO_REPOSITORIO]
    ```

2.  **Instale as Dependências:**
    ```bash
    pip install pandas requests openpyxl matplotlib
    ```

3.  **Execute o Pipeline de ETL:**
    *   Abra e execute o notebook `Code/DataDownload.ipynb` do início ao fim.
    *   Este processo pode demorar, pois ele irá baixar todos os arquivos necessários do BCB.
    *   Ao final, os diretórios `Input/` e `Output/` estarão populados com os dados brutos e os arquivos Parquet processados, respectivamente.

4.  **Inicie a Análise:**
    *   Abra o notebook `Analysis/DataAnalysis2.ipynb`.
    *   A primeira célula irá inicializar o `AnalisadorBancario`, carregando todos os dados processados em memória.
    *   A segunda célula irá gerar o arquivo `referencia_nomes_consulta.xlsx`, que é um guia essencial com os nomes exatos de bancos e contas para usar nas suas consultas.
    *   A partir daí, você está pronto para usar os métodos do `AnalisadorBancario` para criar suas próprias análises.

## 4. Guia de Uso do `AnalisadorBancario`

A principal ferramenta deste projeto é a classe `AnalisadorBancario`, localizada em `Code/DataUtils.py`. Ela simplifica drasticamente a interação com os dados.

### Inicialização

Primeiro, crie uma instância da classe, apontando para o diretório onde os arquivos Parquet foram salvos.

```python
from DataUtils import AnalisadorBancario
from pathlib import Path

output_dir = Path('..').resolve() / 'Output'
analisador = AnalisadorBancario(diretorio_output=str(output_dir))
```

### Métodos Principais para Consulta

A classe oferece métodos de alto nível para buscar diferentes tipos de dados. O `identificador` pode ser o nome do banco (parcial ou completo) ou um CNPJ de 8 dígitos.

#### a. `get_dados_cosif(...)`

Busca dados contábeis dos relatórios COSIF. É ideal para informações de balanço e DRE.

```python
# Exemplo: Buscar o Ativo Total e o Patrimônio Líquido do Itaú em Mar/2024
dados_cosif = analisador.get_dados_cosif(
    identificador='ITAU UNIBANCO',
    contas=['TOTAL GERAL DO ATIVO', 'PATRIMÔNIO LÍQUIDO'],
    datas=202403,
    tipo='prudencial', # 'prudencial' (padrão) ou 'individual'
    documentos=[4060]  # Opcional: filtra pelo código do documento (ex: 4060, 4066)
)
display(dados_cosif)
```

#### b. `get_dados_ifdata(...)`

Busca dados dos relatórios IFDATA, que contêm indicadores regulatórios como Índice de Basileia, Imobilização, etc.

```python
# Exemplo: Buscar o Índice de Basileia do Bradesco
dados_ifdata = analisador.get_dados_ifdata(
    identificador='BRADESCO',
    contas=['Índice de Basileia'],
    datas=202403 # IFDATA é geralmente trimestral
)
display(dados_ifdata)
```

#### c. `get_atributos_cadastro(...)`

Busca informações cadastrais que são colunas diretas no `df_ifdata_cadastro`, como segmento, situação, etc.

```python
# Exemplo: Ver o segmento e a situação do Nubank
atributos_nubank = analisador.get_atributos_cadastro(
    identificador='NU FINANCEIRA',
    atributos=['SEGMENTOTB_IFD_CAD', 'SITUACAO_IFD_CAD']
)
display(atributos_nubank)
```

#### d. `get_serie_temporal_indicador(...)`

Uma função poderosa para analisar a evolução de um indicador ao longo do tempo, pronta para ser plotada.

```python
# Exemplo: Obter a série temporal do Lucro Líquido do BTG Pactual
serie_lucro_btg = analisador.get_serie_temporal_indicador(
    identificador='BTG PACTUAL',
    conta='RESULTADO LÍQUIDO',
    data_inicio=202301,
    data_fim=202403,
    fonte='COSIF', # 'COSIF' ou 'IFDATA'
    documento_cosif=4060
)
# Plotar o resultado
serie_lucro_btg.plot(title='Evolução do Lucro Líquido - BTG Pactual');
```

#### e. `comparar_indicadores(...)`

A função mais completa. Cria uma tabela comparativa para múltiplos bancos e múltiplos indicadores de diferentes fontes, ideal para relatórios e análises de pares.

```python
# Dicionário que define os indicadores desejados
indicadores = {
    'Patrimônio Líquido': {'tipo': 'COSIF', 'conta': 'PATRIMÔNIO LÍQUIDO'},
    'Índice de Basileia': {'tipo': 'IFDATA', 'conta': 'Índice de Basileia'},
    'Situação': {'tipo': 'Atributo', 'atributo': 'SITUACAO_IFD_CAD'}
}

# Lista de bancos para comparar
bancos = ['ITAU', 'BRADESCO', 'NUBANK', 'BCO DO BRASIL S.A.']

# Gerar a tabela para uma data e documento específicos
tabela_comparativa = analisador.comparar_indicadores(
    identificadores=bancos,
    indicadores=indicadores,
    data=202403,
    documento_cosif=4060
)
display(tabela_comparativa)
```

## 5. Manutenção e Debug

### Atualizando os Dados
Para obter os dados mais recentes, basta executar novamente o notebook `Code/DataDownload.ipynb`. Ele irá baixar apenas os arquivos dos meses que ainda não existem localmente.

### Depurando Consultas
Se uma consulta em `DataAnalysis2.ipynb` não retornar o resultado esperado (ex: uma tabela vazia ou valores `None`), siga estes passos:

1.  **Verifique os Nomes:** Consulte o arquivo `referencia_nomes_consulta.xlsx` para garantir que você está usando os nomes exatos do banco e da conta. A busca por nome parcial (`'ITAU'`) é flexível, mas pode falhar se houver ambiguidades.
2.  **Verifique a Data e o Documento:** Certifique-se de que os dados para a data e o documento solicitados existem. Lembre-se que dados IFDATA são geralmente trimestrais (ex: 202303, 202306, 202309, 202312).
3.  **Use o Modo Debug:** O método `get_dados_cosif` possui um parâmetro `debug`. Ativá-lo fornecerá um output detalhado sobre o processo de busca, mostrando qual CNPJ foi usado e quantos registros foram encontrados em cada etapa do filtro.

    ```python
    # Exemplo de uso do modo debug
    dados = analisador.get_dados_cosif(
        identificador='NUBANK',
        contas=['PATRIMÔNIO LÍQUIDO'],
        datas=202403,
        debug=True # Ativa a depuração
    )
    ```

### Entendendo a "Mágica" por Trás da Classe
A principal complexidade que o `AnalisadorBancario` resolve é a "tradução de identidade". Um banco pode ser conhecido por um CNPJ (ex: Nu Financeira), mas reportar seus dados consolidados sob o CNPJ do líder do conglomerado (ex: Nu Pagamentos).

-   O método interno `_find_cnpj` traduz um nome de banco para o seu CNPJ de 8 dígitos.
-   O método interno `_get_entity_identifiers` pega esse CNPJ e, usando o `df_ifdata_cadastro`, descobre qual é o CNPJ do líder do conglomerado (`cnpj_reporte_cosif`) e o código do conglomerado (`cod_congl_prud`).
-   Os métodos públicos (`get_dados_*`) usam esses identificadores corretos para filtrar os DataFrames, garantindo que você sempre obtenha os dados certos, independentemente do identificador que usou na consulta.

---