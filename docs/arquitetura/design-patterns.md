# Design Patterns e Arquitetura

Este documento detalha os padrões de design implementados no projeto e as decisões arquiteturais que tornam o código modular, testável e escalável.

## Índice

- [Padrões de Design Implementados](#padrões-de-design-implementados)
- [Princípios SOLID](#princípios-solid)
- [Otimizações de Performance](#otimizações-de-performance)
- [Diagrama de Arquitetura](#diagrama-de-arquitetura)

---

## Padrões de Design Implementados

### 1. Facade Pattern

**Implementação**: `AnalisadorBancario` (core/analyser.py)

**Propósito**: Fornecer uma interface unificada e simplificada para um subsistema complexo.

**Como funciona**:
```python
# Sem Facade: usuário precisa conhecer múltiplos componentes
repository = DataRepository(...)
resolver = EntityResolver(...)
provider = IFDATAProvider(...)
cnpj = resolver.resolve(identificador)
dados = provider.get_dados(cnpj, ...)

# Com Facade: interface simples e unificada
analisador = AnalisadorBancario(diretorio_output='data/output')
dados = analisador.get_dados_ifdata(identificador='Itaú', ...)
```

**Benefícios**:
- API pública limpa e intuitiva
- Usuário não precisa conhecer componentes internos
- Facilita refatorações internas sem quebrar código do usuário
- Ponto único de entrada para toda a funcionalidade

---

### 2. Repository Pattern

**Implementação**: `DataRepository` (data/repository.py)

**Propósito**: Encapsular a lógica de acesso aos dados, abstraindo a camada de persistência.

**Como funciona**:
```python
class DataRepository:
    def __init__(self, data_loader: DataLoader):
        self._loader = data_loader
        self._loaded = False
        # Cache interno dos DataFrames (lazy loading)
        self._df_cosif_ind = None
        self._df_cosif_prud = None
        self._df_ifd_val = None
        self._df_ifd_cad = None

    @property
    def df_cosif_ind(self) -> pd.DataFrame:
        """Retorna DataFrame de COSIF individual com lazy loading."""
        if not self._loaded:
            self.load()
        return self._df_cosif_ind

    def load(self) -> None:
        """Carrega todos os dados em memória."""
        if not self._loaded:
            dados = self._loader.load_all()
            self._df_cosif_ind = dados['cosif_ind']
            # ... outros DataFrames
            self._loaded = True
```

**Benefícios**:
- Separação entre lógica de negócio e acesso a dados
- Facilita testes (mock do repository)
- Mudanças no formato de armazenamento (ex: Parquet → SQL) são isoladas
- Caching transparente

---

### 3. Dependency Injection

**Implementação**: Todos os componentes principais

**Propósito**: Componentes recebem dependências via construtor, não as criam.

**Como funciona**:
```python
class AnalisadorBancario:
    def __init__(self, diretorio_output: str):
        # Injetar dependências (não criar internamente)
        self.repository = DataRepository(diretorio_output)
        self.resolver = EntityResolver(self.repository)
        self.cosif_provider = COSIFProvider(self.repository)
        self.ifdata_provider = IFDATAProvider(self.repository, self.resolver)
        # ...

# Facilita testes com mocks
class TestAnalisadorBancario:
    def test_get_dados_ifdata(self):
        mock_repository = MockRepository()
        analisador = AnalisadorBancario(repository=mock_repository)
        # ...
```

**Benefícios**:
- Testabilidade (fácil criar mocks)
- Flexibilidade (trocar implementações)
- Baixo acoplamento entre componentes
- Facilita refatorações

---

### 4. Strategy Pattern (Implícito)

**Implementação**: Providers (COSIF, IFDATA, Cadastro)

**Propósito**: Diferentes estratégias de consulta para diferentes fontes de dados.

**Como funciona**:
```python
# Cada provider implementa estratégia específica
class COSIFProvider:
    def get_dados(self, cnpj, contas, datas, tipo, documentos):
        # Estratégia para COSIF
        ...

class IFDATAProvider:
    def get_dados(self, cnpj, contas, datas, escopo):
        # Estratégia para IFDATA
        ...

# Facade escolhe estratégia baseada na fonte
class AnalisadorBancario:
    def get_dados_cosif(self, ...):
        return self.cosif_provider.get_dados(...)

    def get_dados_ifdata(self, ...):
        return self.ifdata_provider.get_dados(...)
```

**Benefícios**:
- Fácil adicionar novas fontes de dados
- Lógica específica isolada por fonte
- Cada provider tem implementação otimizada

---

### 5. Cache Pattern (LRU)

**Implementação**: `EntityIdentifierResolver` com `@lru_cache`

**Propósito**: Evitar resoluções repetidas de identificadores.

**Como funciona**:
```python
from functools import lru_cache
from dataclasses import dataclass

@dataclass(frozen=True)
class ResolvedEntity:
    """Objeto imutável (hashable) para permitir cache."""
    cnpj_interesse: str
    cnpj_reporte_cosif: str
    cod_congl_prud: str
    nome_entidade: str
    identificador_original: str

class EntityIdentifierResolver:
    @lru_cache(maxsize=256)
    def find_cnpj(self, identificador: str) -> str:
        # Busca CNPJ a partir de nome ou CNPJ
        ...

    @lru_cache(maxsize=256)
    def get_entity_identifiers(self, identificador: str) -> dict:
        # Retorna todos os metadados da entidade
        ...

    @lru_cache(maxsize=256)
    def resolve_full(self, identificador: str) -> ResolvedEntity:
        # Resolução completa em uma operação
        ...

# Primeira chamada: lenta (~100ms)
resolved = resolver.resolve_full('Banco Inter')

# Chamadas subsequentes: instantâneas (~0.1ms)
resolved = resolver.resolve_full('Banco Inter')
```

**Benefícios**:
- Performance: reduz tempo de consultas repetidas em ~1000x
- Transparente: funciona automaticamente
- Gerenciamento automático de memória (LRU)
- Três métodos cacheados para diferentes níveis de detalhe

---

## Princípios SOLID

### S - Single Responsibility Principle

Cada módulo tem uma responsabilidade única:

| Módulo | Responsabilidade Única |
|--------|------------------------|
| `entity_resolver.py` | Apenas resolução de identificadores |
| `cosif.py` | Apenas consultas COSIF |
| `ifdata.py` | Apenas consultas IFDATA |
| `comparator.py` | Apenas comparações |
| `time_series.py` | Apenas séries temporais |

### O - Open/Closed Principle

Aberto para extensão, fechado para modificação:

```python
# Adicionar novo provider sem modificar código existente
class NovoProvider:
    def __init__(self, repository: DataRepository):
        self.repository = repository

    def get_dados(self, ...):
        # Nova implementação
        ...

# Estender AnalisadorBancario
class AnalisadorBancario:
    def __init__(self, ...):
        # ...
        self.novo_provider = NovoProvider(self.repository)

    def get_dados_nova_fonte(self, ...):
        return self.novo_provider.get_dados(...)
```

### L - Liskov Substitution Principle

Providers são substituíveis:

```python
# Todos os providers seguem interface similar
def get_dados(self, cnpj, contas, datas, **kwargs) -> pd.DataFrame:
    ...
```

### I - Interface Segregation Principle

Interfaces pequenas e específicas:

```python
# Usuário usa apenas os métodos necessários
analisador.get_dados_ifdata(...)  # Não precisa conhecer COSIF
analisador.get_dados_cosif(...)   # Não precisa conhecer IFDATA
```

### D - Dependency Inversion Principle

Dependências apontam para abstrações:

```python
# Alto nível depende de abstração, não de implementação concreta
class AnalisadorBancario:
    def __init__(self, repository: DataRepository):  # Abstração
        self.repository = repository
        # Não depende diretamente de DataLoader ou arquivos Parquet
```

---

## Otimizações de Performance

### 1. Cache LRU (Least Recently Used)

**Onde**: `EntityIdentifierResolver` (3 métodos cacheados)

**Impacto**:
- Primeira resolução: ~100ms
- Resoluções cacheadas: ~0.1ms
- **Speedup**: ~1000x

**Configuração**:
```python
@lru_cache(maxsize=256)  # Armazena até 256 resoluções
# Aplicado em: find_cnpj(), get_entity_identifiers(), resolve_full()
```

### 2. Pré-resolução em Lote

**Onde**: `TimeSeriesProvider.get_series_temporais_lote()`

**Como funciona**:
```python
# Resolver todos os identificadores UMA VEZ no início
identificadores_unicos = set(req['identificador'] for req in requisicoes)
cnpjs_resolvidos = {id: resolver.resolve(id) for id in identificadores_unicos}

# Usar resoluções cacheadas em loop
for requisicao in requisicoes:
    cnpj = cnpjs_resolvidos[requisicao['identificador']]  # Instantâneo
    # ...
```

**Impacto**: Busca de 100 séries temporais: 30s → 3s (~10x mais rápido)

**Observação**: Esta otimização funciona em conjunto com os **métodos `*_with_resolved()`** dos providers, que aceitam objetos `ResolvedEntity` já resolvidos, evitando resoluções repetidas:

```python
# Providers possuem métodos otimizados para entidades já resolvidas
class COSIFDataProvider:
    def get_dados_with_resolved(self, resolved: ResolvedEntity, ...):
        # Usa entidade já resolvida, não resolve novamente
        ...

class IFDATADataProvider:
    def get_dados_with_resolved(self, resolved: ResolvedEntity, ...):
        # Usa entidade já resolvida, não resolve novamente
        ...

class CadastroProvider:
    def get_atributos_with_resolved(self, resolved: ResolvedEntity, ...):
        # Usa entidade já resolvida, não resolve novamente
        ...

# TimeSeriesProvider usa estes métodos internamente em operações em lote
```

### 3. Recortes Otimizados de DataFrames

**Onde**: Providers (COSIFDataProvider, IFDATADataProvider)

**Como funciona**:
```python
# Método build_subset() nos providers
def build_subset(self, df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    # Usar máscaras booleanas eficientes
    mask = pd.Series([True] * len(df))
    for coluna, valores in filters.items():
        mask &= df[coluna].isin(valores)
    return df[mask]
```

**Impacto**: Filtragem 2-3x mais rápida que queries iterativas

**Uso**: Este método permite construir subconjuntos otimizados em operações em lote, aplicando filtros múltiplos de forma eficiente usando operações vetorizadas do Pandas.

### 4. Cache Local em Loops

**Onde**: Providers

**Como funciona**:
```python
# Evitar acessar repository em loop
df_cosif = self.repository.get_cosif_prudencial()  # Uma vez

for conta in contas:
    # Usar DataFrame local (não chamar repository repetidamente)
    resultado = df_cosif[df_cosif['Conta'] == conta]
```

### 5. Lazy Loading

**Onde**: `DataLoader`

**Como funciona**:
```python
class DataLoader:
    def __init__(self, diretorio_output: str):
        self._cache = {}  # DataFrames carregados

    def load_parquet(self, filename: str) -> pd.DataFrame:
        if filename not in self._cache:
            # Carregar apenas quando necessário
            self._cache[filename] = pd.read_parquet(...)
        return self._cache[filename]
```

**Impacto**: Reduz uso de memória, carrega apenas dados necessários

---

## Diagrama de Arquitetura

### Arquitetura em Camadas

```
┌──────────────────────────────────────────────────────┐
│              Camada de Apresentação                  │
│         (Notebooks Jupyter, Scripts Python)          │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              Facade (AnalisadorBancario)             │
│         Interface unificada e simplificada           │
│         • get_dados_cosif()                          │
│         • get_dados_ifdata()                         │
│         • comparar_indicadores()                     │
│         • get_series_temporais_lote()                │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│        Camada de Análise (analysis/)                 │
│   • Comparação de indicadores                        │
│   • Geração de séries temporais                      │
│   • Otimizações de performance                       │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│      Provedores de Dados (providers/)                │
│   • COSIF: Dados contábeis                           │
│   • IFDATA: Indicadores regulatórios                 │
│   • Cadastro: Dados cadastrais                       │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│       Camada de Dados (data/)                        │
│   • Repository Pattern                               │
│   • Loader de arquivos Parquet                       │
│   • Cache e gerenciamento de memória                 │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│       Camada de Persistência                         │
│   • Arquivos Parquet (data/output/)                  │
│   • Dicionários Excel                                │
└──────────────────────────────────────────────────────┘
```

### Fluxo de Dependências

```
AnalisadorBancario (Facade)
    ↓
    ├── EntityResolver
    │   └── DataRepository
    │
    ├── COSIFProvider
    │   └── DataRepository
    │
    ├── IFDATAProvider
    │   ├── DataRepository
    │   └── EntityResolver
    │
    ├── CadastroProvider
    │   └── DataRepository
    │
    └── TimeSeriesProvider
        ├── COSIFProvider
        ├── IFDATAProvider
        └── EntityResolver

DataRepository
    └── DataLoader
        └── Arquivos Parquet
```

**Observações**:
- Dependências sempre apontam "para baixo" (camadas superiores dependem de inferiores)
- Nenhuma dependência circular
- Componentes de mesmo nível não dependem entre si

---

## Comparação: v1.x vs v2.0.1

| Aspecto | v1.x | v2.0.1 |
|---------|------|--------|
| **Estrutura** | Funções soltas em módulo único | Arquitetura em camadas |
| **Imports** | Manipulação manual de sys.path | Pacote instalável |
| **Padrões** | Nenhum padrão formal | Facade, Repository, DI |
| **Cache** | Sem cache | LRU cache (256 entradas) |
| **Performance** | Baseline | 5-10x mais rápido (lote) |
| **Type Hints** | Parcial | Completo |
| **Testes** | Difícil (código acoplado) | Fácil (DI, mocks) |
| **Extensibilidade** | Modificação direta | Extensão sem modificação |

---

## Referências Adicionais

- [Estrutura do Projeto](estrutura-projeto.md) - Detalhes da organização do código
- [Novos Recursos v2.0.1](novos-recursos-v2.md) - Mudanças na v2.0
- [Técnicas Avançadas](../referencia/tecnicas-avancadas.md) - Otimizações de performance

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
