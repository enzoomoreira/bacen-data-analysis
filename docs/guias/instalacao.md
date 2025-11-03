# Guia de Instalação e Setup

Este guia detalha o processo completo de instalação do pacote `bacen-data-analysis`, desde os requisitos até a execução do pipeline ETL inicial.

## Índice

- [Requisitos](#requisitos)
- [Instalação do Pacote](#instalação-do-pacote)
- [Pipeline de ETL](#pipeline-de-etl)
- [Próximos Passos](#próximos-passos)
- [Troubleshooting de Instalação](#troubleshooting-de-instalação)

---

## Requisitos

### Requisitos de Sistema

- **Python**: 3.12 ou superior
- **Sistema Operacional**: Windows, macOS ou Linux
- **Espaço em Disco**: ~2GB para dados processados (após ETL)
- **Memória RAM**: Mínimo 4GB recomendado (8GB+ ideal para grandes análises)

### Verificar Versão do Python

```bash
python --version
```

Se a versão for inferior a 3.12, atualize o Python antes de continuar.

---

## Instalação do Pacote

### 1. Clone o Repositório

```bash
git clone https://github.com/enzoomoreira/bacen-data-analysis.git
cd bacen-data-analysis
```

### 2. Escolha o Tipo de Instalação

O projeto usa **pyproject.toml** para gerenciamento de dependências. Escolha a opção conforme sua necessidade:

#### Instalação Básica

Apenas dependências principais para análise de dados:

```bash
pip install -e .
```

**Inclui**:
- `pandas>=2.0.0` - Manipulação de dados
- `pyarrow>=10.0.0` - Leitura de arquivos Parquet
- `openpyxl>=3.0.0` - Leitura/escrita de arquivos Excel
- `requests>=2.28.0` - Download de dados do BCB

#### Instalação com Ferramentas de Desenvolvimento

Para desenvolvedores que desejam contribuir com o projeto:

```bash
pip install -e ".[dev]"
```

**Inclui**: Dependências básicas + pytest, black, ruff (linting e formatação)

#### Instalação com Suporte a Notebooks

Para usuários que executarão análises em Jupyter notebooks:

```bash
pip install -e ".[notebooks]"
```

**Inclui**: Dependências básicas + jupyter, matplotlib, seaborn (visualização)

#### Instalação Completa

Todas as dependências (análise + desenvolvimento + notebooks):

```bash
pip install -e ".[all]"
```

**Recomendado para**: Usuários que querem experiência completa e desenvolvedores

---

## Pipeline de ETL

### Passo Essencial: Executar o ETL

**ANTES de qualquer análise**, você DEVE executar o pipeline de ETL para baixar e processar os dados do Banco Central.

#### 1. Abrir o Notebook de ETL

Navegue até o notebook:

```
notebooks/etl/data_download.ipynb
```

Abra-o no Jupyter Notebook, JupyterLab ou VSCode.

#### 2. Executar Todas as Células

Execute o notebook **do início ao fim** (Run All Cells).

#### 3. O Que o ETL Faz

O notebook realizará as seguintes operações:

1. **Download Automático**: Baixa dados COSIF e IFDATA do site do BCB
2. **Padronização**: Limpa e padroniza colunas, CNPJs e nomes
3. **Resolução de Inconsistências**: Unifica dados de múltiplas fontes
4. **Geração de Dicionários**: Cria arquivos Excel de referência
5. **Salvamento Otimizado**: Salva dados em formato Parquet (compacto e rápido)

#### 4. Tempo de Execução

- **Primeira execução**: 15-30 minutos (download completo de todos os dados históricos)
- **Execuções subsequentes**: 2-5 minutos (apenas dados novos/atualizados)

#### 5. Verificar Sucesso

Ao final do ETL, verifique se o diretório `data/output/` foi criado com os seguintes arquivos:

```
data/output/
├── df_cosif_individual.parquet
├── df_cosif_prudencial.parquet
├── df_ifdata_valores.parquet
├── df_ifdata_cadastro.parquet
├── df_mapeamento_cnpj_conglomerado.parquet
├── dicionario_entidades.xlsx
├── dicionario_contas_cosif_individual.xlsx
├── dicionario_contas_cosif_prudencial.xlsx
├── dicionario_contas_ifdata_valores.xlsx
├── info_dataframe_cosif_individual.xlsx
├── info_dataframe_cosif_prudencial.xlsx
├── info_dataframe_ifdata_valores.xlsx
└── info_dataframe_ifdata_cadastro.xlsx
```

**Arquivos importantes**:
- **`.parquet`**: Dados processados e otimizados
  - `df_cosif_*.parquet`: Dados contábeis COSIF
  - `df_ifdata_*.parquet`: Indicadores regulatórios e cadastro
  - `df_mapeamento_*.parquet`: Mapeamento de CNPJs para conglomerados
- **`dicionario_*.xlsx`**: Dicionários de referência (essenciais para consultas)
- **`info_dataframe_*.xlsx`**: Metadados e perfis dos DataFrames

---

## Próximos Passos

### 1. Explorar o Tutorial

Abra o notebook de exemplos:

```
notebooks/analysis/example.ipynb
```

Este notebook contém:
- Exemplos práticos de todas as funcionalidades
- Casos de uso comuns
- Técnicas avançadas

### 2. Consultar Dicionários

Abra os arquivos Excel em `data/output/` para encontrar:
- Nomes oficiais de instituições (`dicionario_entidades.xlsx`)
- Códigos e nomes de contas COSIF
- Indicadores disponíveis no IFDATA

### 3. Começar Suas Análises

Crie seu próprio notebook ou script Python:

```python
from bacen_analysis import AnalisadorBancario
from pathlib import Path

# Inicializar analisador
output_dir = Path('data/output')
analisador = AnalisadorBancario(diretorio_output=str(output_dir))

# Começar a analisar!
```

📖 **Próximos guias recomendados**:
- [Guia de Uso Rápido](uso-rapido.md) - Primeiros passos com a API
- [Exemplos Práticos](../referencia/exemplos-praticos.md) - Casos de uso detalhados

---

## Troubleshooting de Instalação

### Erro: "Python version < 3.12"

**Problema**: Versão do Python incompatível.

**Solução**: Atualize para Python 3.12 ou superior:
- Windows: Baixe de [python.org](https://www.python.org/downloads/)
- macOS: Use Homebrew (`brew install python@3.12`)
- Linux: Use o gerenciador de pacotes da sua distribuição

### Erro: "pip: command not found"

**Problema**: pip não está instalado ou não está no PATH.

**Solução**:
```bash
# Verificar se pip está instalado
python -m pip --version

# Se não estiver, instalar pip
python -m ensurepip --upgrade
```

### Erro: "No module named 'pandas'" (Após Instalação)

**Problema**: Dependências não foram instaladas corretamente.

**Solução**: Reinstale o pacote:
```bash
pip uninstall bacen-analysis
pip install -e ".[all]"
```

### Erro: "Permission denied" (Linux/macOS)

**Problema**: Permissões insuficientes para instalar pacotes.

**Solução**: Use ambiente virtual ou `--user`:
```bash
# Opção 1: Ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
pip install -e .

# Opção 2: Instalação de usuário
pip install --user -e .
```

### Erro no ETL: "Connection timeout"

**Problema**: Falha ao baixar dados do BCB (timeout de rede).

**Solução**:
1. Verifique sua conexão com a internet
2. Tente novamente (o notebook retomará de onde parou)
3. Se persistir, aguarde alguns minutos e tente novamente

### Erro no ETL: "Memory error" ou "Kernel died"

**Problema**: RAM insuficiente para processar todos os dados.

**Solução**:
1. Feche outros programas para liberar memória
2. Execute o notebook em partes menores (comentar células pesadas temporariamente)
3. Se possível, aumente a RAM disponível para Jupyter

### Jupyter Notebook Não Abre

**Problema**: Jupyter não instalado ou não no PATH.

**Solução**: Instale com suporte a notebooks:
```bash
pip install -e ".[notebooks]"

# Ou instalar Jupyter separadamente
pip install jupyter

# Iniciar Jupyter
jupyter notebook
```

### Arquivos Parquet Não Criados

**Problema**: ETL falhou silenciosamente ou foi interrompido.

**Solução**:
1. Execute o notebook ETL novamente do início ao fim
2. Verifique logs no notebook para erros específicos
3. Certifique-se de que tem espaço em disco suficiente (~2GB)

---

## Suporte Adicional

Se você encontrar problemas não listados aqui, consulte:
- [Troubleshooting Geral](../troubleshooting.md) - Problemas durante o uso
- [Issues no GitHub](https://github.com/enzoomoreira/bacen-data-analysis/issues) - Reporte bugs ou peça ajuda

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
