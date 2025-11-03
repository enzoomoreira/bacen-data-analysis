# API Completa - AnalisadorBancario

Esta é a documentação completa da API pública da classe `AnalisadorBancario`, a interface principal para consulta de dados do Banco Central.

## Índice

- [Inicialização](#inicialização)
- [Padrão de Saída](#padrão-de-saída)
- [Métodos de Consulta](#métodos-de-consulta)
  - [get_dados_cosif()](#get_dados_cosif)
  - [get_dados_ifdata()](#get_dados_ifdata)
  - [get_atributos_cadastro()](#get_atributos_cadastro)
- [Métodos de Análise](#métodos-de-análise)
  - [comparar_indicadores()](#comparar_indicadores)
  - [get_serie_temporal_indicador()](#get_serie_temporal_indicador)
  - [get_series_temporais_lote()](#get_series_temporais_lote)
- [Métodos Utilitários](#métodos-utilitários)

---

## Inicialização

### `AnalisadorBancario(diretorio_output)`

Inicializa o analisador bancário com acesso aos dados processados.

**Parâmetros**:
- `diretorio_output` (str): Caminho para o diretório contendo os arquivos Parquet processados

**Retorno**: Instância de `AnalisadorBancario`

**Exemplo**:
```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')
```

**Exceções**:
- `FileNotFoundError`: Se o diretório ou arquivos Parquet não existirem

---

## Padrão de Saída

**Todos os métodos** que retornam dados sobre entidades incluem as seguintes colunas no início do DataFrame:

- `Nome_Entidade` (str): Nome oficial da instituição
- `CNPJ_8` (str): CNPJ de 8 dígitos da instituição

Isso garante que você sempre saiba a qual instituição os dados se referem.

---

## Métodos de Consulta

### `get_dados_cosif()`

Busca dados contábeis detalhados (Balanço Patrimonial, DRE) da fonte COSIF.

**Assinatura**:
```python
def get_dados_cosif(
    identificador: str | list[str],
    contas: list[str | int],
    datas: int | list[int],
    tipo: str,
    documentos: int | list[int] | None = None
) -> pd.DataFrame
```

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `identificador` | str ou list[str] | Sim | CNPJ de 8 dígitos ou nome da instituição. Aceita string única ou lista de strings |
| `contas` | list[str ou int] | Sim | Lista de nomes ou códigos das contas contábeis |
| `datas` | int ou list[int] | Sim | Data(s) no formato AAAAMM (ex: 202403 = março/2024) |
| `tipo` | str | Sim | Tipo de dados: `'prudencial'` ou `'individual'` |
| `documentos` | int ou list[int] ou None | Não | Código(s) de documento. Opções: `4060` (prudencial), `4066` (prudencial agregado), `4010` (individual), `4016` (individual agregado) |

**Retorno**: `pd.DataFrame` com colunas:
- `Nome_Entidade` (str): Nome oficial da instituição
- `CNPJ_8` (str): CNPJ de 8 dígitos
- `DATA` (int): Data no formato AAAAMM
- `CONTA_COSIF` (int): Código numérico da conta
- `NOME_CONTA_COSIF` (str): Nome descritivo da conta
- `VALOR_CONTA_COSIF` (float): Valor da conta
- `DOCUMENTO_COSIF` (int): Código do documento
- Outras colunas como `TAXONOMIA_COSIF`, `COD_CONGL_PRUD_COSIF`, `NOME_CONGL_PRUD_COSIF`, etc.

**Exceções**:
- `EntityNotFoundError`: Se o identificador não for encontrado
- `DataUnavailableError`: Se os dados não estiverem disponíveis

**Exemplo**:
```python
dados = analisador.get_dados_cosif(
    identificador='BANCO BRADESCO S.A.',
    contas=['ATIVO TOTAL', 'PATRIMÔNIO LÍQUIDO'],
    datas=[202401, 202402, 202403],
    tipo='prudencial',
    documentos=4060
)
```

---

### `get_dados_ifdata()`

Busca indicadores regulatórios (Basileia, liquidez, etc.) da fonte IF.DATA.

**Assinatura**:
```python
def get_dados_ifdata(
    identificador: str | list[str],
    contas: list[str | int],
    datas: int | list[int],
    escopo: str
) -> pd.DataFrame
```

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `identificador` | str ou list[str] | Sim | CNPJ de 8 dígitos ou nome da instituição |
| `contas` | list[str ou int] | Sim | Lista de nomes ou códigos dos indicadores |
| `datas` | int ou list[int] | Sim | Data(s) no formato AAAAMM |
| `escopo` | str | Sim | Escopo da busca: `'individual'`, `'prudencial'` ou `'financeiro'` |

**Opções de `escopo`**:
- `'individual'`: Apenas dados da instituição individual
- `'prudencial'`: Apenas dados do conglomerado prudencial
- `'financeiro'`: Apenas dados do conglomerado financeiro

**Retorno**: `pd.DataFrame` com colunas:
- `Nome_Entidade` (str): Nome oficial da instituição
- `CNPJ_8` (str): CNPJ de 8 dígitos da instituição base
- `ID_BUSCA_USADO` (str): ID usado na busca (CNPJ individual ou código do conglomerado)
- `DATA` (int): Data no formato AAAAMM
- `CONTA_IFD_VAL` (int): Código numérico do indicador
- `NOME_CONTA_IFD_VAL` (str): Nome descritivo do indicador
- `VALOR_IFD_VAL` (float): Valor do indicador
- Outras colunas como `COD_INST_IFD_VAL`, `PERIODICIDADE_IFD_VAL`, etc.

**Exceções**:
- `EntityNotFoundError`: Se o identificador não for encontrado
- `DataUnavailableError`: Se os dados não estiverem disponíveis para o escopo especificado
- `InvalidScopeError`: Se o escopo for inválido

**Exemplo**:
```python
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Índice de Basileia', 'Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

# Verificar origem dos dados
print(dados['ID_BUSCA_USADO'])
```

**Nota importante**: Na v2.0.1, o parâmetro `escopo` é **obrigatório** e não aceita mais o valor `'cascata'`. Se você precisa tentar múltiplos escopos, implemente a lógica explicitamente (veja [Guia de Migração](../guias/migracao-v2.md)).

---

### `get_atributos_cadastro()`

Busca informações cadastrais de instituições (Segmento, Situação, Endereço, etc.).

**Assinatura**:
```python
def get_atributos_cadastro(
    identificador: str | list[str],
    atributos: list[str]
) -> pd.DataFrame
```

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `identificador` | str ou list[str] | Sim | CNPJ de 8 dígitos ou nome da instituição. Aceita string única ou lista |
| `atributos` | list[str] | Sim | Lista de nomes dos atributos desejados |

**Atributos comuns disponíveis**:
- `'Segmento'`: Segmento da instituição (S1, S2, S3, S4, S5)
- `'Situacao'`: Situação atual (ATIVA, LIQUIDADA, etc.)
- `'Endereco'`: Endereço completo
- `'Municipio'`: Município da sede
- `'UF'`: Estado da sede

**Nota**: Para ver todos os atributos disponíveis, acesse o DataFrame de cadastro diretamente: `analisador.df_ifd_cad.columns` ou consulte `info_dataframe_ifdata_cadastro.xlsx` em `data/output/`.

**Retorno**: `pd.DataFrame` com colunas:
- `Nome_Entidade` (str)
- `CNPJ_8` (str)
- Colunas adicionais para cada atributo solicitado

**Exceções**:
- `EntityNotFoundError`: Se o identificador não for encontrado
- `KeyError`: Se um atributo não existir nos dados

**Exemplo**:
```python
atributos = analisador.get_atributos_cadastro(
    identificador=['60701190', '00000208', '00416968'],
    atributos=['Segmento', 'Situacao', 'Municipio']
)

print(atributos)
```

---

## Métodos de Análise

### `comparar_indicadores()`

Cria uma tabela-resumo "pivotada" para comparar múltiplos indicadores entre várias instituições.

**Assinatura**:
```python
def comparar_indicadores(
    identificadores: list[str],
    indicadores: dict,
    data: int,
    fillna: int | float | str | None = None
) -> pd.DataFrame
```

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `identificadores` | list[str] | Sim | Lista de CNPJs ou nomes de instituições |
| `indicadores` | dict | Sim | Dicionário de indicadores a comparar (veja estrutura abaixo) |
| `data` | int | Sim | Data de referência no formato AAAAMM |
| `fillna` | int, float, str ou None | Não | Controle de valores ausentes: `0` preenche NaNs com zero, `'nan'` ou `None` mantém NaNs (padrão: None) |

**Estrutura do parâmetro `indicadores`**:

O dicionário deve ter a seguinte estrutura:

```python
{
    'Nome_da_Coluna': {
        'tipo': 'COSIF' | 'IFDATA' | 'ATRIBUTO',
        # Parâmetros específicos por tipo (veja abaixo)
    }
}
```

**Para tipo `'COSIF'`**:
- `'conta'` (str ou int): Nome ou código da conta
- `'tipo_cosif'` (str): `'prudencial'` ou `'individual'`
- `'documento_cosif'` (int): Código do documento (obrigatório)

**Para tipo `'IFDATA'`**:
- `'conta'` (str ou int): Nome ou código do indicador
- `'escopo_ifdata'` (str): `'individual'`, `'prudencial'` ou `'financeiro'` (obrigatório)

**Para tipo `'ATRIBUTO'`**:
- `'atributo'` (str): Nome do atributo cadastral

**Retorno**: `pd.DataFrame` pivotado com:
- Instituições nas linhas
- Indicadores nas colunas
- Colunas `Nome_Entidade` e `CNPJ_8` no início

**Comportamento com entidades não encontradas**:
- Se um identificador não for encontrado, o método emite um `UserWarning` e continua a comparação
- Entidades não encontradas são incluídas no resultado com valores `None` para todos os indicadores
- Isso permite análises comparativas mesmo quando alguns identificadores são inválidos

**Exemplo completo**:
```python
comparacao = analisador.comparar_indicadores(
    identificadores=['60701190', '60746948', '00000000'],  # Itaú, Bradesco, BB
    indicadores={
        'Ativo Total (IFDATA)': {
            'tipo': 'IFDATA',
            'conta': 'Ativo Total',
            'escopo_ifdata': 'prudencial'
        },
        'Ativo Total (COSIF)': {
            'tipo': 'COSIF',
            'conta': 'ATIVO TOTAL',
            'tipo_cosif': 'prudencial',
            'documento_cosif': 4060
        },
        'Índice de Basileia': {
            'tipo': 'IFDATA',
            'conta': 'Índice de Basileia',
            'escopo_ifdata': 'prudencial'
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

**Saída esperada**:
```
  Nome_Entidade         CNPJ_8    Ativo Total (IFDATA)  Ativo Total (COSIF)  Índice de Basileia  Segmento
0 ITAÚ UNIBANCO...     60701190   2800000000            2800000000           15.2                S1
1 BANCO BRADESCO...    60746948   2500000000            2500000000           14.8                S1
2 BANCO DO BRASIL...   00000000   2900000000            2900000000           16.1                S1
```

---

### `get_serie_temporal_indicador()`

Busca a evolução de um único indicador ao longo do tempo para uma instituição.

**Assinatura**:
```python
def get_serie_temporal_indicador(
    identificador: str,
    conta: str | int,
    fonte: str = 'COSIF',
    documento_cosif: int | None = None,
    tipo_cosif: str | None = None,
    escopo_ifdata: str | None = None,
    fill_value: float | None = None,
    replace_zeros_with_nan: bool = False,
    drop_na: bool = True,
    data_inicio: int | None = None,
    data_fim: int | None = None,
    datas: list[int] | None = None
) -> pd.DataFrame
```

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `identificador` | str | Sim | CNPJ ou nome da instituição |
| `conta` | str ou int | Sim | Nome ou código do indicador |
| `fonte` | str | Não | Fonte dos dados: `'COSIF'` ou `'IFDATA'` (padrão: `'COSIF'`) |
| `documento_cosif` | int ou None | Condicional | **Obrigatório para COSIF**: Código do documento |
| `tipo_cosif` | str ou None | Condicional | **Obrigatório para COSIF**: `'prudencial'` ou `'individual'` |
| `escopo_ifdata` | str ou None | Condicional | **Obrigatório para IFDATA**: `'individual'`, `'prudencial'` ou `'financeiro'` |
| `fill_value` | float ou None | Não | Preenche NaNs com valor específico |
| `replace_zeros_with_nan` | bool | Não | Converte zeros em NaN (padrão: False) |
| `drop_na` | bool | Não | Remove linhas com NaN (padrão: True) |
| `data_inicio` | int ou None | Condicional | Data inicial no formato AAAAMM (alternativa a `datas`) |
| `data_fim` | int ou None | Condicional | Data final no formato AAAAMM (alternativa a `datas`) |
| `datas` | list[int] ou None | Condicional | Lista de datas específicas (alternativa a `data_inicio`/`data_fim`) |

**Retorno**: `pd.DataFrame` com colunas:
- `DATA` (int): Data no formato AAAAMM
- `Nome_Entidade` (str): Nome oficial da instituição
- `CNPJ_8` (str): CNPJ de 8 dígitos
- `Conta` (str): Nome ou código da conta/indicador
- `Valor` (float): Valor do indicador

**Controle de dados ausentes**:
- `drop_na=True`: Remove linhas com valores NaN
- `drop_na=False`: Mantém linhas com NaN (útil para visualizar lacunas)
- `fill_value=0`: Preenche NaNs com zero (ou outro valor)
- `replace_zeros_with_nan=True`: Trata zeros como dados ausentes

**Exemplo (IFDATA)**:
```python
serie = analisador.get_serie_temporal_indicador(
    identificador='Banco Inter',
    conta='Lucro Líquido',
    fonte='IFDATA',
    escopo_ifdata='prudencial',
    data_inicio=202301,
    data_fim=202312
)

# Plotar série
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(serie['Data'], serie['Valor'], marker='o')
plt.title('Evolução do Lucro Líquido - Banco Inter (2023)')
plt.xlabel('Data')
plt.ylabel('Valor (R$)')
plt.grid(True)
plt.show()
```

**Exemplo (COSIF)**:
```python
serie = analisador.get_serie_temporal_indicador(
    identificador='00000208',
    conta='ATIVO TOTAL',
    fonte='COSIF',
    tipo_cosif='prudencial',
    documento_cosif=4060,
    data_inicio=202301,
    data_fim=202312,
    drop_na=False,
    fill_value=0  # Preencher lacunas com zero
)
```

---

### `get_series_temporais_lote()`

Busca **múltiplas séries temporais de forma otimizada** em uma única chamada. **Novo na v2.0.1**.

**Assinatura**:
```python
def get_series_temporais_lote(
    requisicoes: list[dict],
    drop_na: bool = True,
    fill_value: float | None = None
) -> pd.DataFrame
```

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `requisicoes` | list[dict] | Sim | Lista de dicionários, cada um descrevendo uma série temporal |
| `drop_na` | bool | Não | Remove linhas com NaN (aplicado a todas as séries) |
| `fill_value` | float ou None | Não | Preenche NaNs com valor específico (aplicado a todas as séries) |

**Estrutura de cada requisição**:

```python
{
    'identificador': str,         # CNPJ ou nome
    'conta': str | int,           # Indicador
    'fonte': 'COSIF' | 'IFDATA',  # Fonte
    'datas': list[int],           # Lista de datas
    'nome_indicador': str,        # Identificador único para a série

    # Parâmetros condicionais:
    'escopo_ifdata': str,         # Para IFDATA: 'individual', 'prudencial', 'financeiro'
    'tipo_cosif': str,            # Para COSIF: 'prudencial', 'individual'
    'documento_cosif': int        # Para COSIF: código do documento
}
```

**Retorno**: `pd.DataFrame` com colunas:
- `DATA` (int): Data no formato AAAAMM
- `Nome_Entidade` (str): Nome oficial da instituição
- `CNPJ_8` (str): CNPJ de 8 dígitos
- `Conta` (str): Nome do indicador (valor de `nome_indicador`)
- `Valor` (float): Valor do indicador

**Formato de saída**: Formato "longo" adequado para plotagem de múltiplas séries.

**Vantagens**:
- **Muito mais rápido** que múltiplas chamadas individuais
- Pré-resolve todas as entidades uma vez
- Usa recortes otimizados de DataFrames

**Comportamento com entidades não encontradas**:
- Se um identificador não for encontrado, o método emite um `UserWarning` e ignora requisições para essa entidade
- Requisições para entidades válidas continuam sendo processadas normalmente
- Isso permite processamento em lote mesmo quando alguns identificadores são inválidos

**Exemplo completo**:
```python
# Buscar Ativo Total de 5 bancos em 3 meses
bancos = ['60701190', '60746948', '00000000', '00416968', '00000208']

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
df_pivot = df_series.pivot(index='DATA', columns='Conta', values='Valor')
print(df_pivot)
```

**Exemplo misto (COSIF + IFDATA)**:
```python
requisicoes = [
    {
        'identificador': '60701190',
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202501, 202502, 202503],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': 'Ativo Total - Itaú (IFDATA)'
    },
    {
        'identificador': '60701190',
        'conta': 10000001,  # Código COSIF
        'fonte': 'COSIF',
        'datas': [202501, 202502, 202503],
        'tipo_cosif': 'prudencial',
        'documento_cosif': 4060,
        'nome_indicador': 'Caixa - Itaú (COSIF)'
    }
]

df_series = analisador.get_series_temporais_lote(requisicoes)
```

---

## Métodos Utilitários

### `clear_cache()`

Limpa o cache LRU de resoluções de identificadores.

**Assinatura**:
```python
def clear_cache() -> None
```

**Uso**:
```python
analisador.clear_cache()
```

**Quando usar**: Após atualizar dados cadastrais ou quando suspeitar de resoluções incorretas cacheadas.

---

### `reload_data()`

Recarrega todos os arquivos Parquet do diretório de output.

**Assinatura**:
```python
def reload_data() -> None
```

**Uso**:
```python
analisador.reload_data()
```

**Quando usar**: Após executar o pipeline ETL para atualizar os dados, sem precisar reinicializar o analisador.

---

## Funções Auxiliares

### `standardize_cnpj_base8()`

Padroniza um CNPJ para o formato de 8 dígitos (raiz).

**Assinatura**:
```python
def standardize_cnpj_base8(cnpj_input: str | pd.Series) -> str | pd.Series
```

**Parâmetros**:
- `cnpj_input` (str ou pd.Series): CNPJ em qualquer formato (8, 14 dígitos, com ou sem pontuação), ou uma Series do pandas

**Retorno**: str com 8 dígitos (raiz do CNPJ), ou pd.Series se a entrada for uma Series

**Exemplo**:
```python
from bacen_analysis import standardize_cnpj_base8
import pandas as pd

# String - retorna '60701190'
print(standardize_cnpj_base8('60701190'))
print(standardize_cnpj_base8('60.701.190/0001-04'))
print(standardize_cnpj_base8('60701190000104'))

# Series - retorna pd.Series
cnpjs = pd.Series(['60701190', '60.746.948/0001-12', '00000000'])
print(standardize_cnpj_base8(cnpjs))
# Output: 0    60701190
#         1    60746948
#         2    00000000
```

---

## Exceções Customizadas

A biblioteca define exceções customizadas para melhor tratamento de erros:

### `EntityNotFoundError`

Lançada quando um identificador (CNPJ ou nome) não é encontrado nos dados cadastrais.

**Nota importante**: Os métodos `comparar_indicadores()` e `get_series_temporais_lote()` são **tolerantes** a entidades não encontradas:
- Eles não lançam `EntityNotFoundError`
- Em vez disso, emitem `UserWarning` e continuam o processamento
- Isso permite análises mesmo quando alguns identificadores são inválidos

**Exemplo de tratamento**:
```python
from bacen_analysis import EntityNotFoundError

try:
    dados = analisador.get_dados_ifdata(
        identificador='CNPJ_INEXISTENTE',
        contas=['Ativo Total'],
        datas=202403,
        escopo='prudencial'
    )
except EntityNotFoundError as e:
    print(f"Instituição não encontrada: {e}")
```

### `DataUnavailableError`

Lançada quando os dados solicitados não estão disponíveis para a combinação de parâmetros especificada.

**Exemplo de tratamento**:
```python
from bacen_analysis import DataUnavailableError

try:
    dados = analisador.get_dados_ifdata(
        identificador='60701190',
        contas=['Indicador Inexistente'],
        datas=202403,
        escopo='prudencial'
    )
except DataUnavailableError as e:
    print(f"Dados não disponíveis: {e}")
```

### `InvalidScopeError`

Lançada quando um parâmetro de escopo é inválido ou não especificado quando obrigatório.

**Exemplo de tratamento**:
```python
from bacen_analysis import InvalidScopeError

try:
    dados = analisador.get_dados_ifdata(
        identificador='60701190',
        contas=['Ativo Total'],
        datas=202403,
        escopo='invalido'  # Escopo inválido
    )
except InvalidScopeError as e:
    print(f"Escopo inválido: {e}")
```

---

## Referências Adicionais

- [Exemplos Práticos](exemplos-praticos.md) - Casos de uso detalhados
- [Técnicas Avançadas](tecnicas-avancadas.md) - Otimizações e recursos avançados
- [Troubleshooting](../troubleshooting.md) - Soluções para problemas comuns

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
