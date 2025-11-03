# Análise de Dados Financeiros do Banco Central do Brasil

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.1-green)](https://github.com/enzoomoreira/bacen-data-analysis)

## Visão Geral

**Pipeline completo de dados e ferramentas de análise** para relatórios financeiros de instituições brasileiras, disponibilizados pelo Banco Central do Brasil (BCB).

A versão 2.0.1 representa uma **refatoração completa** da arquitetura, transformando notebooks simples em um **pacote Python profissional e instalável** com arquitetura modular, otimizações de performance e API simplificada, mantendo **100% de compatibilidade** com a versão anterior.

### O Que Este Projeto Faz

Automatiza o processo de **extrair, transformar, carregar e analisar** dados do BCB:

- **Extrair**: Download automatizado de dados (COSIF e IF.DATA)
- **Transformar**: Limpeza, padronização e unificação de dados complexos
- **Carregar**: Armazenamento otimizado em formato Parquet
- **Analisar**: Interface Python intuitiva para consultas e análises avançadas

**Objetivo Principal**: Permitir extração de insights valiosos dos dados do BCB sem lidar com a complexidade do tratamento e unificação dos dados brutos.

---

## Fluxo do Projeto

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
└─────────────────────────────────────────────────────────────┘
```

---

## Instalação Rápida

### 1. Clone o Repositório

```bash
git clone https://github.com/enzoomoreira/bacen-data-analysis.git
cd bacen-data-analysis
```

### 2. Instale o Pacote

```bash
pip install -e .
```

Para instalação completa (com notebooks e ferramentas de desenvolvimento):

```bash
pip install -e ".[all]"
```

### 3. Execute o Pipeline ETL

**PASSO ESSENCIAL** antes de qualquer análise:

1. Abra e execute `notebooks/etl/data_download.ipynb` do início ao fim
2. O processo pode demorar na primeira execução (15-30 minutos)
3. Execuções futuras serão mais rápidas (2-5 minutos, apenas dados novos)

📖 **[Guia completo de instalação](docs/guias/instalacao.md)**

---

## Uso Rápido

### Import Simplificado (Novo na v2.0)

```python
from bacen_analysis import AnalisadorBancario

# Inicializar analisador
analisador = AnalisadorBancario(diretorio_output='data/output')
```

### Exemplo: Consultar Dados

```python
# Buscar Ativo Total do Itaú em março de 2024
dados = analisador.get_dados_ifdata(
    identificador='60701190',  # CNPJ ou nome funciona
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'  # 'individual', 'prudencial' ou 'financeiro'
)

print(dados)
```

**Saída**:
```
  Nome_Entidade              CNPJ_8    Data    Conta        Valor         ID_BUSCA_USADO
0 ITAÚ UNIBANCO HOLDING S.A. 60701190  202403  Ativo Total  2800000000    62144175
```

📖 **[Guia de uso completo](docs/guias/uso-rapido.md)** | **[Exemplos práticos](docs/referencia/exemplos-praticos.md)**

---

## Novos Recursos v2.0.1

### Destaques da Versão

- **Pacote Python Instalável**: Instalação via `pip install -e .` com imports simplificados
- **Arquitetura Modular**: Código organizado em camadas com responsabilidades bem definidas
- **Performance Otimizada**:
  - Cache LRU para resoluções de identificadores (1000x mais rápido)
  - Novo método `get_series_temporais_lote()` para buscas em massa (5-10x mais rápido)
  - Pré-resolução de entidades em operações em lote
- **Controle Granular de Escopo**: Parâmetro de escopo obrigatório para IFDATA (`'individual'`, `'prudencial'`, `'financeiro'`). Use `escopo` em `get_dados_ifdata()`, ou `escopo_ifdata` em dicionários de configuração de métodos de análise (obrigatório na v2.0.1)
- **Type Hints Completos**: Código totalmente tipado para melhor IDE support
- **Sistema de Exceções**: Exceções customizadas para melhor tratamento de erros
- **100% Compatível**: API pública mantida idêntica à versão 1.x

### Padrões de Design Aplicados

- **Facade Pattern**: `AnalisadorBancario` como interface unificada
- **Repository Pattern**: Acesso centralizado aos dados
- **Dependency Injection**: Componentes recebem dependências via construtor
- **Single Responsibility**: Cada módulo com responsabilidade única e clara

📖 **[Changelog completo v2.0.1](docs/arquitetura/novos-recursos-v2.md)**

---

## Documentação

### 📚 Guias

- **[Instalação e Setup](docs/guias/instalacao.md)** - Instalação completa e primeira execução
- **[Uso Rápido](docs/guias/uso-rapido.md)** - Primeiros passos com a API
- **[Migração v1.x → v2.0](docs/guias/migracao-v2.md)** - Guia de migração para usuários da v1.x

### 📖 Referência

- **[API Completa](docs/referencia/api-completa.md)** - Documentação detalhada de todos os métodos
- **[Exemplos Práticos](docs/referencia/exemplos-praticos.md)** - 8 exemplos completos com casos de uso reais
- **[Técnicas Avançadas](docs/referencia/tecnicas-avancadas.md)** - Otimizações, cache e performance

### 🏗️ Arquitetura

- **[Estrutura do Projeto](docs/arquitetura/estrutura-projeto.md)** - Organização de diretórios e módulos
- **[Design Patterns](docs/arquitetura/design-patterns.md)** - Padrões aplicados e decisões arquiteturais
- **[Novos Recursos v2.0.1](docs/arquitetura/novos-recursos-v2.md)** - Changelog detalhado

### 🔧 Suporte

- **[Troubleshooting](docs/troubleshooting.md)** - Soluções para problemas comuns e FAQ

---

## Notebooks Incluídos

### `notebooks/etl/data_download.ipynb`

Pipeline ETL completo:
- Download automático dos dados do BCB
- Limpeza e padronização
- Geração de dicionários de referência
- Salvamento otimizado em Parquet

**Quando executar**: Primeira vez (obrigatório) e mensalmente para atualizar dados.

### `notebooks/analysis/example.ipynb`

Tutorial completo com exemplos práticos:
- Consultas fundamentais (COSIF, IFDATA, Cadastro)
- Análises comparativas entre instituições
- Séries temporais e visualizações
- Técnicas avançadas

### `notebooks/analysis/full_table.ipynb`

Exemplos de construção de tabelas completas:
- Dashboards
- Relatórios comparativos
- Análises de mercado

---

## Estrutura do Projeto

```
bacen-data-analysis/
│
├── src/bacen_analysis/              # Pacote principal
│   ├── core/                        # Componentes centrais (Facade, Resolver)
│   ├── providers/                   # Provedores de dados (COSIF, IFDATA, Cadastro)
│   ├── data/                        # Camada de acesso a dados (Loader, Repository)
│   ├── analysis/                    # Módulos de análise (Comparator, TimeSeries)
│   └── utils/                       # Utilitários (CNPJ, texto, logging)
│
├── notebooks/                       # Notebooks organizados
│   ├── etl/                         # Pipeline ETL
│   └── analysis/                    # Notebooks de análise
│
├── docs/                            # Documentação modular
│   ├── guias/                       # Guias de uso
│   ├── referencia/                  # Referência da API
│   └── arquitetura/                 # Arquitetura e design
│
├── data/                            # Dados (criado pelo ETL)
│   ├── input/                       # Dados brutos
│   └── output/                      # Dados processados (Parquet + dicionários)
│
├── pyproject.toml                   # Configuração do pacote
└── README.md                        # Este arquivo
```

📖 **[Documentação completa da estrutura](docs/arquitetura/estrutura-projeto.md)**

---

## API Principal - AnalisadorBancario

### Métodos de Consulta

```python
# Dados contábeis COSIF
dados = analisador.get_dados_cosif(
    identificador='60701190',
    contas=['ATIVO TOTAL', 'PATRIMÔNIO LÍQUIDO'],
    datas=202403,
    tipo='prudencial',
    documentos=4060
)

# Indicadores regulatórios IFDATA
dados = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Índice de Basileia'],
    datas=202403,
    escopo='prudencial'
)

# Atributos cadastrais
atributos = analisador.get_atributos_cadastro(
    identificador=['60701190', '00000208'],
    atributos=['Segmento', 'Situacao']
)
```

### Métodos de Análise

```python
# Comparar múltiplas instituições
comparacao = analisador.comparar_indicadores(
    identificadores=['60701190', '60746948', '00000000'],
    indicadores={
        'Ativo Total': {'tipo': 'IFDATA', 'conta': 'Ativo Total', 'escopo_ifdata': 'prudencial'},
        'Segmento': {'tipo': 'ATRIBUTO', 'atributo': 'Segmento'}
    },
    data=202403
)

# Série temporal individual
serie = analisador.get_serie_temporal_indicador(
    identificador='Banco Inter',
    conta='Lucro Líquido',
    fonte='IFDATA',
    escopo_ifdata='prudencial',
    data_inicio=202301,
    data_fim=202312
)

# Séries temporais em lote (OTIMIZADO - Novo na v2.0.1)
requisicoes = [
    {
        'identificador': '60701190',
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': 'Ativo Total - Itaú'
    }
]
df_series = analisador.get_series_temporais_lote(requisicoes)
```

📖 **[API completa](docs/referencia/api-completa.md)**

---

## Comparação: v1.x vs v2.0.1

| Aspecto | v1.x | v2.0.1 |
|---------|------|--------|
| **Instalação** | Manual (sys.path) | `pip install -e .` |
| **Imports** | 5 linhas | 1 linha |
| **Arquitetura** | Módulo único | 6 camadas modulares |
| **Performance (lote)** | Baseline | 5-10x mais rápido |
| **Cache** | Sem cache | LRU cache (1000x) |
| **Type Hints** | Parcial | Completo |
| **Padrões de Design** | Nenhum | Facade, Repository, DI |

📖 **[Guia de migração](docs/guias/migracao-v2.md)**

---

## Licença e Créditos

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

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
