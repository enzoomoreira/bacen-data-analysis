# Técnicas Avançadas

Este guia apresenta técnicas avançadas e otimizações para maximizar a performance e flexibilidade do `bacen-data-analysis`.

## Índice

- [Controle Granular de Escopo no IFDATA](#controle-granular-de-escopo-no-ifdata)
- [Busca Otimizada em Lote](#busca-otimizada-em-lote)
- [Cache e Performance](#cache-e-performance)
- [Flexibilidade em Consultas](#flexibilidade-em-consultas)
- [Tratamento Avançado de Erros](#tratamento-avançado-de-erros)

---

## Controle Granular de Escopo no IFDATA

O parâmetro `escopo` no método `get_dados_ifdata()` oferece controle preciso sobre qual nível de dados você deseja. **Na v2.0.1, este parâmetro é obrigatório**.

### Opções de Escopo

```python
from bacen_analysis import AnalisadorBancario

analisador = AnalisadorBancario(diretorio_output='data/output')

# INDIVIDUAL: Apenas a instituição individual
dados_individual = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='individual'
)

# PRUDENCIAL: Apenas o conglomerado prudencial
dados_prudencial = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

# FINANCEIRO: Apenas o conglomerado financeiro
dados_financeiro = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='financeiro'
)
```

### Lógica de Cascata Explícita

Na v2.0.1, o escopo `'cascata'` foi removido. Se você precisa tentar múltiplos escopos em ordem (comportamento anterior do `'cascata'`), implemente explicitamente:

```python
from bacen_analysis import DataUnavailableError

def buscar_com_cascata(analisador, identificador, contas, datas, escopos=None):
    """
    Busca dados tentando múltiplos escopos em ordem.

    Args:
        escopos: Lista de escopos para tentar (padrão: ['prudencial', 'financeiro', 'individual'])
    """
    if escopos is None:
        escopos = ['prudencial', 'financeiro', 'individual']

    for escopo in escopos:
        try:
            dados = analisador.get_dados_ifdata(
                identificador=identificador,
                contas=contas,
                datas=datas,
                escopo=escopo
            )
            print(f"Dados encontrados no escopo: {escopo}")
            return dados
        except DataUnavailableError:
            continue

    raise DataUnavailableError(f"Dados não disponíveis em nenhum escopo: {escopos}")

# Usar função de cascata
dados = buscar_com_cascata(
    analisador,
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403
)
```

### Coluna ID_BUSCA_USADO

A coluna `ID_BUSCA_USADO` indica qual chave encontrou o dado:

```python
dados = analisador.get_dados_ifdata(
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

print(dados[['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO']])
```

**Interpretação**:
- Se `ID_BUSCA_USADO == CNPJ_8`: Dado veio da instituição individual
- Se `ID_BUSCA_USADO != CNPJ_8`: Dado veio de um conglomerado (prudencial/financeiro)

---

## Busca Otimizada em Lote

Quando você precisa buscar **muitas séries temporais**, sempre use `get_series_temporais_lote()` em vez de múltiplas chamadas individuais.

### Comparação de Performance

```python
import time

# ❌ EVITE: Múltiplas chamadas individuais (LENTO)
inicio = time.time()
series = []
for banco in lista_bancos:
    serie = analisador.get_serie_temporal_indicador(
        identificador=banco,
        conta='Ativo Total',
        fonte='IFDATA',
        escopo_ifdata='prudencial',
        data_inicio=202401,
        data_fim=202403
    )
    series.append(serie)
tempo_individual = time.time() - inicio
print(f"Tempo com chamadas individuais: {tempo_individual:.2f}s")

# ✅ PREFIRA: Busca em lote (MUITO MAIS RÁPIDO)
inicio = time.time()
requisicoes = [
    {
        'identificador': banco,
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': f'Banco_{banco}'
    }
    for banco in lista_bancos
]
df_series = analisador.get_series_temporais_lote(requisicoes)
tempo_lote = time.time() - inicio
print(f"Tempo com busca em lote: {tempo_lote:.2f}s")
print(f"Speedup: {tempo_individual/tempo_lote:.1f}x")
```

**Resultado típico**: Speedup de 5-10x dependendo do número de séries.

### Por Que É Mais Rápido?

1. **Resolução única**: Todos os identificadores são resolvidos uma vez no início
2. **Recortes otimizados**: Usa `build_subset()` para criar views eficientes
3. **Menos operações de busca**: Minimiza operações duplicadas de filtragem

### Exemplo Avançado: Múltiplas Fontes

```python
# Combinar COSIF e IFDATA em uma busca em lote
requisicoes = [
    # Indicadores IFDATA
    {
        'identificador': '60701190',
        'conta': 'Ativo Total',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': 'Ativo Total - Itaú (IFDATA)'
    },
    {
        'identificador': '60701190',
        'conta': 'Índice de Basileia',
        'fonte': 'IFDATA',
        'datas': [202401, 202402, 202403],
        'escopo_ifdata': 'prudencial',
        'nome_indicador': 'Basileia - Itaú'
    },
    # Contas COSIF
    {
        'identificador': '60701190',
        'conta': 10000001,  # Código COSIF: CAIXA
        'fonte': 'COSIF',
        'datas': [202401, 202402, 202403],
        'tipo_cosif': 'prudencial',
        'documento_cosif': 4060,
        'nome_indicador': 'Caixa - Itaú (COSIF)'
    },
    {
        'identificador': '60701190',
        'conta': 'PATRIMÔNIO LÍQUIDO',
        'fonte': 'COSIF',
        'datas': [202401, 202402, 202403],
        'tipo_cosif': 'prudencial',
        'documento_cosif': 4060,
        'nome_indicador': 'PL - Itaú (COSIF)'
    }
]

df_series = analisador.get_series_temporais_lote(requisicoes)

# Pivotar para análise
df_pivot = df_series.pivot(index='DATA', columns='Conta', values='Valor')
print(df_pivot)
```

---

## Cache e Performance

A classe `AnalisadorBancario` usa **cache LRU** (Least Recently Used) para otimizar resoluções de identificadores.

### Como o Cache Funciona

```python
# Primeira chamada: Resolve 'Banco Inter' → CNPJ (lento ~0.1s)
dados1 = analisador.get_dados_ifdata(
    identificador='Banco Inter',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

# Segunda chamada com mesmo nome: Usa cache (instantâneo ~0.001s)
dados2 = analisador.get_dados_ifdata(
    identificador='Banco Inter',  # Já está no cache!
    contas=['Lucro Líquido'],
    datas=202403,
    escopo='prudencial'
)
```

### Tamanho do Cache

- **Capacidade**: 256 entradas (configurado via LRU)
- **Escopo**: Por instância do `AnalisadorBancario`
- **Política**: Least Recently Used (remove entradas menos usadas quando cheio)

### Gerenciar Cache Manualmente

```python
# Limpar cache (útil após atualização de dados cadastrais)
analisador.clear_cache()

# Recarregar dados (após executar ETL)
analisador.reload_data()
```

### Dica de Performance: Pre-warming

Para análises com muitas instituições, "aqueça" o cache antecipadamente:

```python
# Pre-warming: Resolver todos os CNPJs antecipadamente
lista_bancos = ['60701190', '60746948', '00000000', ...]

for banco in lista_bancos:
    try:
        analisador.get_atributos_cadastro(
            identificador=banco,
            atributos=['Segmento']
        )
    except:
        pass  # Ignora erros, apenas popula o cache

# Agora todas as consultas subsequentes serão mais rápidas
```

---

## Flexibilidade em Consultas

O analisador aceita identificadores em múltiplos formatos.

### Formatos de CNPJ Aceitos

```python
# Todos funcionam e retornam os mesmos dados
identificadores_validos = [
    '60701190',              # String 8 dígitos
    60701190,                # Int 8 dígitos
    '60.701.190/0001-04',    # String formatada 14 dígitos
    '60701190000104',        # String 14 dígitos sem formatação
]

for identificador in identificadores_validos:
    dados = analisador.get_dados_ifdata(
        identificador=identificador,
        contas=['Ativo Total'],
        datas=202403,
        escopo='prudencial'
    )
    print(f"{identificador} -> {dados['Nome_Entidade'].values[0]}")
```

### Busca por Nome (Parcial ou Completo)

```python
# Todas essas formas funcionam:
nomes_validos = [
    'ITAÚ UNIBANCO HOLDING S.A.',  # Nome completo oficial
    'Itaú Unibanco',                # Nome parcial
    'Itaú',                          # Nome muito parcial
    'itau'                           # Case-insensitive
]
```

**Nota**: Busca por nome usa **matching parcial case-insensitive**. Se houver ambiguidade, use CNPJ.

### Contas: Nomes vs Códigos

```python
# COSIF: Aceita nomes e códigos
contas_cosif = [
    'ATIVO TOTAL',      # Nome
    60000002,           # Código (PATRIMÔNIO LÍQUIDO)
    'LUCRO LÍQUIDO',    # Nome
    10000001            # Código (CAIXA)
]

# IFDATA: Aceita nomes e códigos
contas_ifdata = [
    'Ativo Total',              # Nome
    'Índice de Basileia',       # Nome
    20001,                      # Código (se aplicável)
]
```

### Datas: Único ou Lista

```python
# Data única (int)
dados = analisador.get_dados_ifdata(..., datas=202403, ...)

# Lista de datas
dados = analisador.get_dados_ifdata(..., datas=[202401, 202402, 202403], ...)

# Range de datas (usando série temporal)
serie = analisador.get_serie_temporal_indicador(
    ...,
    data_inicio=202301,
    data_fim=202312
)
```

---

## Tratamento Avançado de Erros

Use exceções customizadas para tratamento robusto de erros.

### Exceções Disponíveis

```python
from bacen_analysis import EntityNotFoundError, DataUnavailableError
```

### Padrão Try-Except Específico

```python
from bacen_analysis import EntityNotFoundError, DataUnavailableError

def buscar_com_tratamento(analisador, identificador, contas, datas, escopo):
    """Busca dados com tratamento robusto de erros."""
    try:
        dados = analisador.get_dados_ifdata(
            identificador=identificador,
            contas=contas,
            datas=datas,
            escopo=escopo
        )
        return dados, None  # Sucesso

    except EntityNotFoundError as e:
        return None, f"Instituição não encontrada: {identificador}"

    except DataUnavailableError as e:
        return None, f"Dados não disponíveis para {identificador} em {datas}"

    except Exception as e:
        return None, f"Erro inesperado: {e}"

# Usar função
dados, erro = buscar_com_tratamento(
    analisador,
    identificador='60701190',
    contas=['Ativo Total'],
    datas=202403,
    escopo='prudencial'
)

if erro:
    print(f"Erro: {erro}")
else:
    print(dados)
```

### Busca Resiliente em Lote

```python
def buscar_multiplas_instituicoes_resiliente(analisador, identificadores, conta, data, escopo):
    """Busca dados de múltiplas instituições, continuando mesmo com erros."""
    resultados = []
    erros = []

    for identificador in identificadores:
        try:
            dados = analisador.get_dados_ifdata(
                identificador=identificador,
                contas=[conta],
                datas=data,
                escopo=escopo
            )
            resultados.append(dados)
        except (EntityNotFoundError, DataUnavailableError) as e:
            erros.append({'identificador': identificador, 'erro': str(e)})

    # Combinar resultados bem-sucedidos
    if resultados:
        df_final = pd.concat(resultados, ignore_index=True)
    else:
        df_final = pd.DataFrame()

    return df_final, erros

# Usar função
bancos = ['60701190', 'CNPJ_INVALIDO', '60746948', '00000000']
dados, erros = buscar_multiplas_instituicoes_resiliente(
    analisador,
    identificadores=bancos,
    conta='Ativo Total',
    data=202403,
    escopo='prudencial'
)

print(f"Sucessos: {len(dados)}, Erros: {len(erros)}")
if erros:
    print("Erros encontrados:")
    for erro in erros:
        print(f"  - {erro['identificador']}: {erro['erro']}")
```

---

## Dicas de Otimização

### 1. Reutilize Instâncias do Analisador

```python
# ❌ EVITE: Criar nova instância a cada consulta
for banco in lista_bancos:
    analisador = AnalisadorBancario(...)  # Lento!
    dados = analisador.get_dados_ifdata(...)

# ✅ PREFIRA: Reutilizar mesma instância
analisador = AnalisadorBancario(...)  # Uma vez
for banco in lista_bancos:
    dados = analisador.get_dados_ifdata(...)  # Rápido!
```

### 2. Use CNPJs Para Performance

```python
# Mais rápido (busca direta)
dados = analisador.get_dados_ifdata(identificador='60701190', ...)

# Mais lento (busca + matching)
dados = analisador.get_dados_ifdata(identificador='Itaú', ...)
```

### 3. Filtre Datas no Nível da Query

```python
# ❌ Menos eficiente
serie = analisador.get_serie_temporal_indicador(..., data_inicio=202201, data_fim=202412)
serie_filtrada = serie[serie['Data'] >= 202301]

# ✅ Mais eficiente
serie = analisador.get_serie_temporal_indicador(..., data_inicio=202301, data_fim=202412)
```

### 4. Use drop_na Apropriadamente

```python
# Para plotagem limpa (sem lacunas)
serie = analisador.get_serie_temporal_indicador(..., drop_na=True)

# Para análise de completude dos dados
serie = analisador.get_serie_temporal_indicador(..., drop_na=False)
```

---

## Referências Adicionais

- [API Completa](api-completa.md) - Documentação detalhada de todos os métodos
- [Exemplos Práticos](exemplos-praticos.md) - Casos de uso detalhados
- [Troubleshooting](../troubleshooting.md) - Soluções para problemas comuns

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
