# Estrutura do Projeto

Este documento detalha a arquitetura de diretórios e responsabilidades de cada módulo do projeto `bacen-data-analysis`.

## Índice

- [Visão Geral](#visão-geral)
- [Árvore de Diretórios](#árvore-de-diretórios)
- [Descrição das Camadas](#descrição-das-camadas)
- [Fluxo de Dados](#fluxo-de-dados)

---

## Visão Geral

O projeto segue uma **arquitetura em camadas** com separação clara de responsabilidades, transformando notebooks simples em um pacote Python profissional, instalável e modular.

---

## Árvore de Diretórios

```
bacen-data-analysis/
│
├── src/bacen_analysis/              # Pacote principal
│   ├── __init__.py                  # API pública (exporta AnalisadorBancario)
│   ├── exceptions.py                # Exceções customizadas da biblioteca
│   │
│   ├── core/                        # Componentes centrais
│   │   ├── __init__.py
│   │   ├── analyser.py              # AnalisadorBancario (Facade principal)
│   │   └── entity_resolver.py       # Resolução de CNPJs e nomes
│   │
│   ├── providers/                   # Provedores de dados por fonte
│   │   ├── __init__.py
│   │   ├── cosif.py                 # Provedor de dados COSIF
│   │   ├── ifdata.py                # Provedor de dados IFDATA
│   │   └── cadastro.py              # Provedor de dados cadastrais
│   │
│   ├── data/                        # Camada de acesso a dados
│   │   ├── __init__.py
│   │   ├── loader.py                # Carregamento de arquivos Parquet
│   │   └── repository.py            # Repository Pattern para dados
│   │
│   ├── analysis/                    # Módulos de análise
│   │   ├── __init__.py
│   │   ├── comparator.py            # Comparação entre instituições
│   │   └── time_series.py           # Geração de séries temporais
│   │
│   └── utils/                       # Utilitários
│       ├── __init__.py
│       ├── cnpj.py                  # Padronização de CNPJ
│       ├── text.py                  # Limpeza de texto
│       └── logger.py                # Sistema de logging
│
├── notebooks/                       # Notebooks organizados
│   ├── etl/
│   │   └── data_download.ipynb      # Pipeline ETL completo
│   └── analysis/
│       ├── example.ipynb            # Tutorial com exemplos práticos
│       ├── full_table.ipynb         # Exemplos de tabelas completas
│       └── Banks.csv                # Lista auxiliar de bancos para exemplos
│
├── data/                            # Dados (criado pelo ETL)
│   ├── input/                       # Dados brutos baixados do BCB
│   ├── output/                      # Dados processados (Parquet + dicionários Excel)
│   └── results/                     # Relatórios e análises exportadas (não versionado)
│
├── docs/                            # Documentação modular
│   ├── guias/
│   │   ├── instalacao.md
│   │   ├── uso-rapido.md
│   │   └── migracao-v2.md
│   ├── referencia/
│   │   ├── api-completa.md
│   │   ├── exemplos-praticos.md
│   │   └── tecnicas-avancadas.md
│   ├── arquitetura/
│   │   ├── estrutura-projeto.md     # Este arquivo
│   │   ├── design-patterns.md
│   │   └── novos-recursos-v2.md
│   └── troubleshooting.md
│
├── pyproject.toml                   # Configuração do pacote Python
├── .gitignore                       # Arquivos ignorados pelo Git
├── LICENSE                          # Licença MIT
└── README.md                        # Documentação principal (simplificada)
```

**Nota**: Os diretórios `data/input/`, `data/output/` e `data/results/` são criados automaticamente conforme necessário. O diretório `results/` armazena relatórios e análises exportadas (não versionados no Git).

---

## Descrição das Camadas

### 1. Camada Core (`src/bacen_analysis/core/`)

**Responsabilidade**: Componentes centrais da biblioteca.

#### `analyser.py` - AnalisadorBancario

**Descrição**: Classe principal que implementa o **Facade Pattern**, fornecendo uma interface unificada e simplificada para todas as funcionalidades do sistema.

**Responsabilidades**:
- Orquestrar chamadas entre provedores, analisadores e repositório
- Gerenciar cache de resoluções de identificadores
- Fornecer API pública consistente

**Métodos principais**:
- `get_dados_cosif()`
- `get_dados_ifdata()`
- `get_atributos_cadastro()`
- `comparar_indicadores()`
- `get_serie_temporal_indicador()`
- `get_series_temporais_lote()`

#### `entity_resolver.py` - EntityIdentifierResolver

**Descrição**: Responsável por resolver identificadores (nomes ou CNPJs) para CNPJs de 8 dígitos únicos.

**Responsabilidades**:
- Matching case-insensitive de nomes parciais
- Padronização de CNPJs (8, 14 dígitos, formatados)
- Cache LRU de resoluções (256 entradas)
- Tratamento de ambiguidades

---

### 2. Camada Providers (`src/bacen_analysis/providers/`)

**Responsabilidade**: Consultas especializadas por fonte de dados.

#### `cosif.py` - COSIFProvider

**Descrição**: Provedor de dados contábeis COSIF (Balanço Patrimonial, DRE).

**Responsabilidades**:
- Consultas por CNPJ, conta, data, tipo e documento
- Suporte a nomes e códigos de contas
- Filtragem por tipo (prudencial/individual)

#### `ifdata.py` - IFDATAProvider

**Descrição**: Provedor de indicadores regulatórios IF.DATA (Basileia, liquidez, etc.).

**Responsabilidades**:
- Consultas por CNPJ, conta, data e escopo
- Lógica de escopo (individual/prudencial/financeiro)
- Retorna coluna `ID_BUSCA_USADO` para rastreamento de origem

#### `cadastro.py` - CadastroProvider

**Descrição**: Provedor de dados cadastrais de instituições.

**Responsabilidades**:
- Consultas de atributos (Segmento, Situação, Endereço, etc.)
- Suporte a múltiplas instituições
- Retorna dados sempre com `Nome_Entidade` e `CNPJ_8`

---

### 3. Camada Data (`src/bacen_analysis/data/`)

**Responsabilidade**: Acesso e carregamento de dados.

#### `loader.py` - DataLoader

**Descrição**: Carregamento de arquivos Parquet do diretório de output.

**Responsabilidades**:
- Lazy loading de arquivos Parquet
- Validação de existência de arquivos
- Caching de DataFrames em memória

#### `repository.py` - DataRepository

**Descrição**: Implementa **Repository Pattern** para acesso centralizado aos dados.

**Responsabilidades**:
- Interface unificada para acesso aos DataFrames
- Encapsulamento da camada de persistência
- Gerenciamento de múltiplas fontes de dados

---

### 4. Camada Analysis (`src/bacen_analysis/analysis/`)

**Responsabilidade**: Operações de análise avançada.

#### `comparator.py` - Comparador

**Descrição**: Comparações entre múltiplas instituições.

**Responsabilidades**:
- Criação de tabelas pivotadas
- Combinação de COSIF, IFDATA e Cadastro
- Formatação consistente de resultados

#### `time_series.py` - TimeSeriesAnalyzer

**Descrição**: Geração de séries temporais.

**Responsabilidades**:
- Séries temporais individuais
- Busca otimizada em lote
- Controle de dados ausentes (drop_na, fill_value)
- Pré-resolução de entidades

---

### 5. Camada Utils (`src/bacen_analysis/utils/`)

**Responsabilidade**: Funções utilitárias de suporte.

#### `cnpj.py`

**Funções**:
- `standardize_cnpj_base8()`: Padroniza CNPJ para 8 dígitos

#### `text.py`

**Funções**:
- `clean_text()`: Remove acentos, caracteres especiais
- `normalize_name()`: Normaliza nomes para matching

#### `logger.py`

**Funções**:
- `setup_logger()`: Configuração de logging
- Níveis: DEBUG, INFO, WARNING, ERROR

---

### 6. Notebooks (`notebooks/`)

#### `etl/data_download.ipynb`

**Descrição**: Pipeline ETL completo.

**Responsabilidades**:
- Download automático dos dados do BCB
- Limpeza e padronização
- Resolução de inconsistências
- Geração de dicionários de referência
- Salvamento em Parquet

**Quando executar**: Primeira vez (obrigatório) e mensalmente para atualizar dados.

#### `analysis/example.ipynb`

**Descrição**: Tutorial completo com exemplos práticos.

**Conteúdo**:
- Consultas fundamentais (COSIF, IFDATA, Cadastro)
- Análises comparativas
- Séries temporais e visualizações
- Técnicas avançadas

#### `analysis/full_table.ipynb`

**Descrição**: Exemplos de tabelas completas.

**Conteúdo**:
- Construção de dashboards
- Relatórios comparativos
- Análises de mercado

---

## Fluxo de Dados

### Fluxo Completo: ETL → Análise

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
                   data/output/*.parquet
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

### Fluxo Interno: Consulta de Dados

```
1. Usuário faz chamada
   analisador.get_dados_ifdata(identificador='Itaú', ...)
                    ↓
2. AnalisadorBancario (Facade)
   • Recebe requisição
   • Verifica cache
                    ↓
3. EntityIdentifierResolver
   • Resolve 'Itaú' → '60701190' (CNPJ_8)
   • Armazena em cache LRU
                    ↓
4. IFDATAProvider
   • Recebe CNPJ_8 resolvido
   • Consulta DataRepository
                    ↓
5. DataRepository
   • Acessa DataFrame via DataLoader
   • Retorna dados filtrados
                    ↓
6. IFDATAProvider
   • Aplica filtros de escopo
   • Formata resultado (adiciona Nome_Entidade, CNPJ_8)
                    ↓
7. AnalisadorBancario
   • Retorna DataFrame ao usuário
```

---

## Princípios de Design

### 1. Separação de Responsabilidades

Cada camada tem uma responsabilidade única e bem definida:
- **Core**: Orquestração e interface pública
- **Providers**: Lógica de negócio por fonte
- **Data**: Acesso aos dados
- **Analysis**: Operações analíticas
- **Utils**: Funções auxiliares

### 2. Dependency Injection

Componentes recebem dependências via construtor:

```python
class AnalisadorBancario:
    def __init__(self, diretorio_output: str):
        # Injetar dependências
        self.repository = DataRepository(diretorio_output)
        self.resolver = EntityIdentifierResolver(self.repository)
        self.cosif_provider = COSIFProvider(self.repository)
        # ...
```

### 3. Encapsulamento

Detalhes de implementação são ocultos:
- Usuário interage apenas com `AnalisadorBancario`
- Providers, Repository e Resolver são internos
- Formato de armazenamento (Parquet) é transparente

### 4. Extensibilidade

Fácil adicionar novos recursos:
- Novo provider: Implementar interface base
- Novo tipo de análise: Criar módulo em `analysis/`
- Novo utilitário: Adicionar em `utils/`

---

## Referências Adicionais

- [Design Patterns](design-patterns.md) - Padrões de design implementados
- [Novos Recursos v2.0.1](novos-recursos-v2.md) - Mudanças na v2.0
- [API Completa](../referencia/api-completa.md) - Documentação da API pública

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
