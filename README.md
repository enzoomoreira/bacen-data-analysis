# Projeto: Análise de Dados Financeiros de Bancos (COSIF & IFDATA)

## Visão Geral

Este projeto automatiza a coleta, processamento, limpeza e unificação de dados contábeis de instituições financeiras brasileiras. Ele combina informações do COSIF (Plano Contábil das Instituições do Sistema Financeiro Nacional) – tanto dados individuais de instituições quanto dados de conglomerados prudenciais – com indicadores de Basiléia, RWA (Risk-Weighted Assets) e informações cadastrais provenientes do IFDATA.

O fluxo principal é orquestrado por dois notebooks Jupyter localizados na pasta `Code/`:

1. **`Code/DataDownload.ipynb`**:

   * Responsável pelo pipeline de ETL (Extração, Transformação e Carga).
   * Efetua o download dos arquivos CSV/ZIP do COSIF Individual e COSIF Prudencial diretamente do site do Banco Central do Brasil (BCB).
   * Realiza requisições à API OData do BCB para obter:

     1. **IfDataValores** (indicadores de Basiléia, RWA etc.) para vários tipos de instituição (1, 2 e 3), usando `Relatorio='T'`.
     2. **IfDataCadastro** (informações cadastrais) para cada período, em base mensal.
   * Processa e limpa os dados brutos: normaliza nomes de colunas, trata datas, corrige encoding de texto (especialmente em dados do IFDATA) e formata CNPJs.
   * Gera diversos arquivos Parquet em estágios (salvos em `Output/`):

     * **Brutos**: Dados como foram baixados, após concatenação inicial.
     * **Intermediários**: Inclui uma versão pivotada (`wide`) do COSIF Individual e merges preliminares.
     * **Corrigidos**: Os arquivos finais prontos para análise (`df_cosif_full_corrigido.parquet` e `df_final_corrigido.parquet`). Nestes arquivos, os dados do **COSIF Individual são mantidos em formato longo** (uma linha por conta contábil), e o IFDATA já inclui tanto valores quanto cadastro.
   * Cria também dicionários de contas em formato Excel para referência (salvos em `Output/`).

2. **`Code/DataCheck.ipynb`**:

   * Carrega os arquivos Parquet finais "corrigidos" da pasta `Output/`.
   * Realiza uma análise exploratória de dados (EDA) básica e verificações de sanidade.

Este pipeline visa fornecer um conjunto de dados consolidado e pronto para análises financeiras, de risco e de capital das instituições.

## Pré-requisitos

* **Python ≥ 3.8**
* Principais bibliotecas Python (podem ser instaladas via `pip install -r requirements.txt` ou individualmente):

  * `pandas`
  * `requests`
  * `openpyxl`
  * (Obs: `pathlib`, `zipfile`, `re` são parte da biblioteca padrão do Python)
* Acesso à internet (para download dos dados do BCB).
* Permissão para criar pastas (`Input/`, `Output/`) e salvar arquivos no sistema.

## Estrutura de Diretórios

O projeto segue a seguinte estrutura de diretórios:

```
b3-analise-bancos/          ← Raiz do projeto
│
├─ .venv/                    ← (Opcional) Ambiente virtual Python
│
├─ Code/                     ← Contém os notebooks Jupyter
│   ├─ DataDownload.ipynb
│   └─ DataCheck.ipynb
│
├─ Input/                    ← Dados brutos baixados
│   ├─ COSIF/
│   │   ├─ individual/       ← Subpastas YYYYMM com CSVs COSIF Individual
│   │   └─ prudencial/       ← Subpastas YYYYMM com CSVs COSIF Prudencial
│   └─ IFDATA/               ← CSVs trimestrais IfDataValores (YYYYMM_{tipo}.csv)
│   └─ IFDATA_Cadastro/      ← CSVs mensais IfDataCadastro (IfDataCadastro_YYYYMM.csv)
│
├─ Output/                   ← Arquivos processados (Parquet e Excel)
│   ├─ df_cosif_individual_full.parquet
│   ├─ df_cosif_prudencial_full.parquet
│   ├─ df_if_prudencial_full.parquet      ← contém IfDataValores + IfDataCadastro unidos
│   ├─ df_cosif_individual_wide.parquet
│   ├─ df_cosif_full.parquet
│   ├─ df_final.parquet
│   ├─ df_cosif_full_corrigido.parquet
│   ├─ df_final_corrigido.parquet
│   ├─ cosif_account_name.xlsx
│   ├─ cosif_prudencial_account_name.xlsx
│   └─ if_account_name.xlsx
│
├─ .gitignore                ← Arquivos e pastas a serem ignorados pelo Git
├─ README.md                 ← Este arquivo
└─ requirements.txt          ← Lista de dependências
```

## Notebook: `Code/DataDownload.ipynb`

#### Objetivo

Automatizar o download, a limpeza, a transformação e a unificação dos dados COSIF e IFDATA, gerando arquivos Parquet otimizados para análise na pasta `Output/`.

#### Configuração de Caminhos

O script utiliza `base_dir = Path('..')` para definir o diretório raiz do projeto. A partir disso, `dir_inputs` é definido como `base_dir / 'Input'` e `dir_outputs` como `base_dir / 'Output'`. Isso garante que os caminhos funcionem corretamente quando o notebook é executado de dentro da pasta `Code/`.

#### Seções e Funcionalidades Principais

1. **Configuração Inicial**:

   * Definição dos intervalos de datas (`date_range_monthly`, `date_range_quarterly`) para a coleta.
   * Criação automática dos diretórios `Input/` e `Output/` e suas subpastas necessárias usando `pathlib`.

2. **Pipeline COSIF Individual**:

   * **Download**: Para cada mês no `date_range_monthly`:

     * Tenta baixar arquivos de `https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/Bancos/{YYYYMM}{suffix}`.
     * Testa sufixos: `BANCOS.csv`, `BANCOS.zip`, `BANCOS.csv.zip`.
     * Verifica se o download é um arquivo válido (não HTML de erro) e se já não foi baixado anteriormente.
     * Salva/extrai os CSVs para `Input/COSIF/individual/{YYYYMM}/`.
   * **Leitura e Concatenação**:

     * Lê todos os CSVs individuais (parâmetros: `header=3`, `encoding='unicode_escape'`, `sep=';'`, `decimal=','`, `on_bad_lines='skip'`).
     * Concatena em um DataFrame `df_cosif_individual_full`.
   * **Saída Raw**: Salva `df_cosif_individual_full.parquet` em `Output/`.
   * **Dicionário de Contas**: Gera `cosif_account_name.xlsx` com mapeamento `CONTA` → `NOME_CONTA`, após limpar caracteres ilegais dos nomes.

3. **Pipeline COSIF Prudencial**:

   * **Download**: Similar ao COSIF Individual, mas para `https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/Conglomerados-prudenciais/{YYYYMM}{suffix}` com sufixos `BLOPRUDENCIAL.csv`, etc.
   * Salva/extrai os CSVs para `Input/COSIF/prudencial/{YYYYMM}/`.
   * **Leitura e Concatenação**:

     * Lê todos os CSVs prudenciais (mesmos parâmetros do Individual).
     * Concatena em `df_cosif_prudencial_full`.
   * **Saída Raw**: Salva `df_cosif_prudencial_full.parquet` em `Output/`.
   * **Dicionário de Contas**: Gera `cosif_prudencial_account_name.xlsx`.

4. **Pipeline IFDATA**:

   1. **IfDataValores (trimestral)**:

      * **Download**: Para cada trimestre em `date_range_quarterly` e para cada `TipoInstituicao ∈ {1,2,3}`:

        * Faz requisição à API OData:

        ```
        https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/
        IfDataValores(AnoMes=@AnoMes,TipoInstituicao=@TipoInstituicao,Relatorio=@Relatorio)?
        @AnoMes={YYYYMM}&@TipoInstituicao={tipo}&@Relatorio='T'&$format=text/csv
        ```

        * Salva o CSV resultante em `Input/IFDATA/{YYYYMM}_{tipo}.csv`.
      * **Leitura e Concatenação**:

        * Lê todos os arquivos `YYYYMM_{tipo}.csv` (parâmetros: `encoding='unicode_escape'`, `sep=','`, `decimal=','`, `on_bad_lines='skip'`).
        * Se a coluna `TipoInstituicao` não vier no CSV, atribui corretamente o valor `{tipo}`.
        * Concatena em `df_if_prudencial_full` (que contém todos os indicadores trimestrais).
   2. **IfDataCadastro (mensal)**:

      * **Download**: Para cada mês em `date_range_monthly`:

        * Faz requisição à API OData:

        ```
        https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/
        IfDataCadastro(AnoMes=@AnoMes)?@AnoMes={YYYYMM}&$format=text/csv
        ```

        * Salva o CSV resultante em `Input/IFDATA_Cadastro/IfDataCadastro_{YYYYMM}.csv`.
      * **Leitura e Concatenação**:

        * Lê todos os arquivos `IfDataCadastro_{YYYYMM}.csv` (parâmetros: `encoding='utf-8'`, `sep=','`, `decimal='.'`, `on_bad_lines='skip'`).
        * Concatena em `df_if_cadastro_full`.
      * **Limpeza e Padronização**:

        * Renomeia colunas: `Data → DATA` e `CodConglomeradoPrudencial → COD_CONGL`.
        * Converte `DATA` para inteiro (YYYYMM) e `COD_CONGL` para string.
        * Remove caracteres não imprimíveis de colunas textuais: `NomeInstituicao`, `SegmentoTb`, `Atividade`, `Uf`, `Municipio`, `Situacao`.
   3. **Merge Valores + Cadastro**:

      * Realiza `df_if_combined = pd.merge(df_if_prudencial_full, df_if_cadastro_full, on=['DATA','COD_CONGL'], how='left', validate='many_to_many')`.
      * Ajusta encoding de texto (`latin1 → utf-8`) em colunas textuais de `df_if_combined`.
      * **Saída Raw**: Salva `df_if_prudencial_full.parquet` em `Output/` (o arquivo agora contém both IfDataValores e IfDataCadastro, renomeado para manter compatibilidade).

5. **Combinações Intermediárias (Arquivos `.parquet` não "\_corrigido")**:

   * Normaliza a coluna `DATA` (originalmente `#DATA_BASE` nos arquivos COSIF) para formato `YYYYMM` (inteiro).
   * Cria `df_prud_mapping` com `['DATA', 'CNPJ', 'COD_CONGL', 'NOME_CONGL']` de `df_cosif_prudencial_full`.
   * **Pivota COSIF Individual**:

     * `df_cosif_individual_wide = df_cosif_individual_full.pivot_table(...)` com `CONTA` nas colunas. Salvo como `df_cosif_individual_wide.parquet`.
   * **Merge Individual (wide) + Prudencial (mapping)**:

     * `df_cosif_full = df_cosif_individual_wide.merge(df_prud_mapping, on=['DATA','CNPJ'], how='left')`. Salvo como `df_cosif_full.parquet`.
   * **Merge COSIF Full (wide) + IFDATA**:

     * `df_final = df_cosif_full.merge(df_if_prudencial_full, on=['DATA','COD_CONGL'], how='left')`. Salvo como `df_final.parquet`.

6. **Geração dos Arquivos "Corrigidos" (Formato Longo para COSIF)**:

   * **Preparação `df_ind_pre`**: A partir de `df_cosif_individual_full` (formato longo):

     * Normaliza `CNPJ` (remove não numéricos).
     * Remove colunas `COD_CONGL`, `NOME_CONGL` (serão adicionadas do mapping).
   * **Preparação `df_prud_mapping_corrigido`**: A partir de `df_cosif_prudencial_full`:

     * Normaliza `CNPJ` e `COD_CONGL` (para string).
     * Seleciona `['DATA', 'CNPJ', 'COD_CONGL', 'NOME_CONGL']` e aplica `drop_duplicates(subset=['DATA', 'CNPJ'])`.
   * **Merge para `df_cosif_full_corrigido.parquet`**:

     * `df_cosif_full_corrigido = pd.merge(df_ind_pre, df_prud_mapping_corrigido, on=['DATA', 'CNPJ'], how='left', validate='many_to_one')`.
     * Este DataFrame contém os dados do COSIF Individual em formato **longo**, enriquecidos com `COD_CONGL` e `NOME_CONGL`.
   * **Preparação `df_if_pre`**: A partir de `df_if_prudencial_full`:

     * Converte `DATA` para `int` e `COD_CONGL` para `str`.
   * **Merge para `df_final_corrigido.parquet`**:

     * `df_final_corrigido = pd.merge(df_cosif_full_corrigido, df_if_pre, on=['DATA', 'COD_CONGL'], how='left', validate='many_to_many')`.
     * Este é o DataFrame final principal, combinando dados COSIF (formato longo) com todos os indicadores IFDATA (valores + cadastro). Cada linha de conta COSIF é replicada para cada indicador IFDATA do mesmo conglomerado/data.

## Principais Arquivos de Saída em `Output/`

1. **Parquets Brutos / Intermediários**:

   * `df_cosif_individual_full.parquet`
     COSIF Individual raw, formato longo.
   * `df_cosif_prudencial_full.parquet`
     COSIF Prudencial raw, formato longo.
   * `df_if_prudencial_full.parquet`
     IFDATA raw – contém IfDataValores (trimestral) + IfDataCadastro (mensal), unidos e com encoding corrigido.
   * `df_cosif_individual_wide.parquet`
     COSIF Individual pivotado (contas como colunas).
   * `df_cosif_full.parquet`
     Individual pivotado + Prudencial mapping.
   * `df_final.parquet`
     Individual pivotado + Prudencial mapping + IFDATA (valores + cadastro).

2. **Parquets "Corrigidos" (Principais para Análise)**:

   * **`df_cosif_full_corrigido.parquet`**

     * Contém os dados do COSIF Individual (saldos por conta) em **formato longo**.
     * Enriquecido com `COD_CONGL` e `NOME_CONGL` do COSIF Prudencial.
     * Ideal para análises focadas apenas nos dados contábeis COSIF com identificação do conglomerado.
   * **`df_final_corrigido.parquet`**

     * O DataFrame mais completo. Contém todas as informações de `df_cosif_full_corrigido` (COSIF Individual em formato longo + Prudencial).
     * Faz um `left join` com os dados do IFDATA (valores + cadastro) usando `DATA` e `COD_CONGL`. Isso significa que para cada linha de conta/saldo do COSIF, são adicionadas colunas com os diversos indicadores IFDATA (Tier 1, RWA etc.) e as informações cadastrais correspondentes.
     * Se um conglomerado tiver múltiplos indicadores IFDATA no mesmo período, a linha COSIF correspondente será replicada para cada indicador.
     * Ideal para análises que cruzam saldos contábeis COSIF com indicadores de capital, risco e dados cadastrais do IFDATA.

3. **Dicionários de Contas (Excel)**:

   * `cosif_account_name.xlsx`
     Mapeamento `CONTA` ↔ `NOME_CONTA` do COSIF Individual.
   * `cosif_prudencial_account_name.xlsx`
     Mapeamento `CONTA` ↔ `NOME_CONTA` do COSIF Prudencial.
   * `if_account_name.xlsx`
     Mapeamento `Conta` (código IFDATA) ↔ `NomeColuna` (nome do indicador, ex: "Tier\_1").

## Notebook: `Code/DataCheck.ipynb`

#### Objetivo

Realizar uma análise exploratória de dados (EDA) básica e verificações de sanidade nos DataFrames finais gerados pelo `DataDownload.ipynb` e salvos na pasta `Output/`.

#### Configuração de Caminhos

No início do script, os caminhos para os arquivos Parquet na pasta `Output/` são definidos de forma relativa:

```python
from pathlib import Path
# ...
notebook_parent_dir = Path('..') # Aponta para a raiz do projeto ('b3-analise-bancos/')
output_dir = notebook_parent_dir / 'Output'
parquet_path = output_dir / 'df_final_corrigido.parquet'
parquet_cosif_full_path = output_dir / 'df_cosif_full_corrigido.parquet'
```

Isso permite que o notebook localize os arquivos corretamente quando executado de dentro da pasta `Code/`.

#### Estrutura de Células e Verificações

1. **Carregamento de Dados**:

   * Lê o arquivo `df_final_corrigido.parquet` (e opcionalmente `df_cosif_full_corrigido.parquet`).

2. **Inspeção Inicial**:

   * `df.shape`: Exibe o número de linhas e colunas.
   * `df.columns`: Lista os nomes das colunas.
   * `df.info()`: Mostra tipos de dados por coluna e uso de memória.
   * `df.isnull().sum()`: Contagem de valores nulos por coluna.
   * `display(df.head(10))`: Visualiza as primeiras 10 linhas.

3. **Análise de Colunas Categóricas**:

   * Para colunas do tipo `object` ou `string`:

     * Exibe o tipo de dado.
     * Lista até 10 valores únicos.
     * Conta o número total de valores únicos.

4. **Verificação de Duplicatas**:

   * `df.duplicated().sum()`: Conta o número de linhas completamente idênticas.

5. **Amostragem Aleatória**:

   * `display(df.sample(n=5, random_state=42))`: Visualiza 5 linhas aleatórias.

6. **(Opcional) Comparação e Amplitude**:

   * Carrega `df_cosif_full_corrigido.parquet` para comparar dimensões e colunas.
   * Verifica o número de períodos (`DATA`) e instituições (`CNPJ`) únicos nos DataFrames.

Este notebook não inclui exemplos complexos de consultas, mas serve como um ponto de partida para entender a estrutura e a qualidade dos dados consolidados.

## Conceitos-Chave e Lógica de Merge (Arquivos Corrigidos)

1. **COSIF Individual (em `..._corrigido.parquet`)**:

   * Os dados são mantidos em **formato longo**: cada linha representa um único `SALDO` para uma `CONTA` contábil específica de um `CNPJ` em uma `DATA`.
   * Colunas chave: `DATA`, `CNPJ`, `NOME_INSTITUICAO`, `CONTA`, `NOME_CONTA`, `SALDO`, `DOCUMENTO`, `TAXONOMIA`.

2. **COSIF Prudencial (usado para `df_prud_mapping_corrigido`)**:

   * Fornece o mapeamento de `CNPJ` para `COD_CONGL` (código do conglomerado) e `NOME_CONGL`.
   * É usado para enriquecer os dados do COSIF Individual.

3. **IFDATA (valores + cadastro)**:

   * Fornece indicadores de capital e risco (Tier 1, Tier 2, Índice de Basiléia, RWA etc.) por `COD_CONGL` e `DATA`, além de informações cadastrais.
   * Cada indicador (`NomeColuna`) para um `(DATA, COD_CONGL)` é uma linha no `df_if_pre`.
   * O cadastro traz campos como `NomeInstituicao`, `SegmentoTb`, `Atividade`, `Uf`, `Municipio`, `Situacao`, `CodConglomeradoFinanceiro` etc., que enriquecem o perfil do conglomerado.

4. **Lógica de Merge para Arquivos "\_corrigido"**:

   * **`df_cosif_full_corrigido.parquet`**:

     * `df_ind_pre` (COSIF Individual longo) `LEFT JOIN df_prud_mapping_corrigido`
     * Chaves: `['DATA', 'CNPJ']`.
     * Resultado: Cada linha de conta/saldo do COSIF Individual é associada ao seu respectivo `COD_CONGL` e `NOME_CONGL`, se existir. Linhas do COSIF Individual sem mapeamento para conglomerado terão `COD_CONGL` e `NOME_CONGL` como `NaN`.
   * **`df_final_corrigido.parquet`**:

     * `df_cosif_full_corrigido` `LEFT JOIN df_if_pre`
     * Chaves: `['DATA', 'COD_CONGL']`.
     * Resultado: Cada linha de `df_cosif_full_corrigido` (que já representa uma conta/saldo COSIF com info de conglomerado) é replicada para cada indicador IFDATA e cada linha de cadastro correspondente àquele `DATA` e `COD_CONGL`.
     * Se um `(DATA, COD_CONGL)` não tiver dados no IFDATA, as colunas provenientes do IFDATA serão `NaN`.
     * Se um `(DATA, COD_CONGL)` tiver múltiplos indicadores no IFDATA, a linha original do COSIF será duplicada para cada um desses indicadores.

5. **Duplicatas e Documentos (COSIF)**:

   * Os arquivos COSIF podem conter dados de diferentes tipos de `DOCUMENTO` (ex: 4010 - Balancete Mensal, 4016 - Balanço Semestral).
   * Em meses de balanço (junho, dezembro), uma mesma conta pode ter seu saldo reportado em ambos os documentos, muitas vezes com o mesmo valor. Isso pode levar a linhas que parecem duplicadas se não se considerar a coluna `DOCUMENTO`.
   * Para obter um valor de saldo único por `(DATA, CNPJ, CONTA)`, pode ser necessário agrupar ou usar `drop_duplicates(subset=['DATA','CNPJ','CONTA','SALDO'])`.

## Como Executar

1. **Clone o Repositório e Configure o Ambiente**:

   * Certifique-se de ter Python instalado.
   * Navegue até a raiz do projeto (`b3-analise-bancos/`).
   * (Recomendado) Crie e ative um ambiente virtual:

     ```bash
     python -m venv .venv
     source .venv/bin/activate  # Linux/macOS
     # .venv\Scripts\activate    # Windows
     ```
   * Instale as bibliotecas necessárias (se houver um `requirements.txt`):

     ```bash
     pip install -r requirements.txt
     ```

     Ou individualmente:

     ```bash
     pip install pandas requests openpyxl jupyter
     ```

2. **Execute `Code/DataDownload.ipynb`**:

   * Abra o notebook (ex: `jupyter lab Code/DataDownload.ipynb` ou via interface do VS Code).
   * O notebook está configurado para encontrar as pastas `Input/` e `Output/` corretamente a partir da pasta `Code/`.
   * Execute todas as células em sequência.
   * Aguarde o download e processamento. Verifique a pasta `Output/` pela geração dos arquivos.

3. **Execute `Code/DataCheck.ipynb`**:

   * Abra o notebook (ex: `jupyter lab Code/DataCheck.ipynb`).
   * Os caminhos para os arquivos Parquet já estão configurados de forma relativa.
   * Execute as células para realizar as verificações e a EDA básica.

## Dicas para Análises com os Arquivos Corrigidos (Formato Longo)

1. **Arquivos Principais**:

   * `df_final_corrigido.parquet`: Use para análises que cruzam saldos contábeis COSIF com indicadores IFDATA (valores + cadastro).
   * `df_cosif_full_corrigido.parquet`: Use se precisar apenas dos dados COSIF (Individual + Prudencial) sem a “explosão” de linhas causada pelo join com IFDATA.

2. **Filtrando Contas COSIF (Formato Longo)**:
   Como as contas COSIF estão em formato longo, você filtrará pela coluna `CONTA` ou `NOME_CONTA`. Exemplo:

   ```python
   # df é o DataFrame carregado de df_final_corrigido.parquet
   cnpj_especifico = "00000000000191"  # Exemplo
   data_especifica = 202412
   nome_conta_desejada = "Operações de Crédito - Carteira Comercial - Pessoas Jurídicas"  # Exemplo

   resultado = df[
       (df['CNPJ'] == cnpj_especifico) &
       (df['DATA'] == data_especifica) &
       (df['NOME_CONTA'] == nome_conta_desejada)
   ]
   # 'resultado' pode ter múltiplas linhas se houver vários indicadores IFDATA para esse CNPJ/Data
   # O saldo COSIF estará na coluna 'SALDO'
   if not resultado.empty:
       saldo_cosif = resultado['SALDO'].iloc[0]  # Pega o primeiro, pois o saldo COSIF será o mesmo
       print(f"Saldo COSIF: {saldo_cosif}")
       # Para ver os indicadores IFDATA associados (coluna 'Saldo' do IFDATA):
       # display(resultado[['NomeColuna', 'Saldo']])
   ```

3. **Obtendo Indicadores IFDATA**:
   Filtre por `NomeColuna` para um indicador específico. Exemplo:

   ```python
   # df é o DataFrame carregado de df_final_corrigido.parquet
   cod_congl_especifico = "C0080738"  # Exemplo
   data_especifica = 202412

   rwa_data = df[
       (df['COD_CONGL'] == cod_congl_especifico) &
       (df['DATA'] == data_especifica) &
       (df['NomeColuna'] == 'RWA')
   ]
   # rwa_data conterá todas as contas COSIF para aquele COD_CONGL/Data
   # que foram cruzadas com o indicador RWA.
   if not rwa_data.empty:
       valor_rwa = rwa_data['Saldo'].iloc[0]  # Coluna 'Saldo' do IFDATA
       print(f"RWA: {valor_rwa}")
   ```

4. **Lidando com Replicação de Linhas (devido ao IFDATA)**:
   Se você precisa de um valor único para uma conta COSIF (`DATA`, `CNPJ`, `CONTA`) e não quer a repetição causada pelos múltiplos indicadores IFDATA, pode usar `drop_duplicates` no subconjunto de colunas do COSIF antes de analisar os indicadores IFDATA separadamente ou agregar:

   ```python
   # df é o DataFrame carregado de df_final_corrigido.parquet
   colunas_chave_cosif = [
       'DATA', 'CNPJ', 'NOME_INSTITUICAO', 'CONTA', 'NOME_CONTA', 'SALDO',
       'DOCUMENTO', 'TAXONOMIA', 'COD_CONGL', 'NOME_CONGL'
   ]
   df_cosif_unico = df.drop_duplicates(subset=colunas_chave_cosif)
   # Agora df_cosif_unico tem uma linha por evento COSIF, mas perdeu a granularidade dos múltiplos indicadores IFDATA.
   # Use com cautela dependendo da análise.
   ```

5. **Agregação**:

   * Para somar saldos COSIF (se houver múltiplas entradas por `DOCUMENTO` que você queira consolidar), use `df_cosif_full_corrigido.parquet`:

     ```python
     # df_cfc é df_cosif_full_corrigido
     df_agregado_cosif = df_cfc.groupby(
         ['DATA', 'CNPJ', 'NOME_INSTITUICAO', 'CONTA', 'NOME_CONTA', 'COD_CONGL', 'NOME_CONGL']
     )['SALDO'].sum().reset_index()
     ```

6. **Análises que Requerem Formato "Wide" (Contas como Colunas)**:
   Se sua análise específica se beneficia muito de ter contas COSIF como colunas (ex: cálculos de ratios complexos envolvendo múltiplas contas diretamente como colunas), você pode:

   * Usar os arquivos Parquet intermediários como `Output/df_cosif_individual_wide.parquet` ou `Output/df_cosif_full.parquet`.
   * Pivotar `df_cosif_full_corrigido.parquet` (ou uma versão filtrada/agregada de `df_final_corrigido.parquet`) conforme necessário:

     ```python
     # Exemplo de pivotagem em df_cosif_full_corrigido
     # df_cfc é df_cosif_full_corrigido
     df_cosif_wide_analise = df_cfc.pivot_table(
         index=['DATA', 'CNPJ', 'NOME_INSTITUICAO', 'COD_CONGL', 'NOME_CONGL', 'DOCUMENTO', 'TAXONOMIA'],  
         # Adicione outras colunas de índice conforme necessário
         columns='NOME_CONTA',  # ou 'CONTA'
         values='SALDO'
     ).reset_index()
     ```

7. **Interpretação de `DOCUMENTO` e `TAXONOMIA`**:

   * `DOCUMENTO`: Indica a origem do dado contábil (ex: 4010 Balancete, 4016 Balanço).
   * `TAXONOMIA`: Refere-se à taxonomia XBRL (ex: COSIF, IFRS). Se houver dados de múltiplas taxonomias, filtre conforme a necessidade.

## Objetivos e Utilidades

* **Armazenamento Centralizado e Eficiente**: Dados brutos e processados são salvos em formato Parquet, otimizado para performance com pandas.
* **Pipeline de Dados Automatizado**: Facilita a atualização dos dados com novas divulgações mensais/trimestrais.
* **Rastreabilidade**: Mantém informações de origem como `DOCUMENTO` e `TAXONOMIA`.
* **Base para Análises Financeiras**:

  * Extração de saldos de contas contábeis específicas (carteira de crédito, depósitos, provisões, etc.).
  * Acompanhamento de indicadores de capital e risco (Tier 1, Tier 2, Índice de Basiléia, RWA) e perfil cadastral das instituições (Segmento, Atividade, UF, Município, Situação etc.).
  * Cálculo de indicadores financeiros e de risco personalizados.
  * Análise comparativa entre instituições e ao longo do tempo.