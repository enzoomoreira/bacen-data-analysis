# Troubleshooting

Guia de solução de problemas comuns ao usar o `bacen-data-analysis`.

## Índice

- [Atualizando os Dados](#atualizando-os-dados)
- [Consultas Sem Resultado](#consultas-sem-resultado)
- [Erros Comuns](#erros-comuns)
- [FAQ](#faq)

---

## Atualizando os Dados

### Como Atualizar para Novos Meses

Para buscar dados de meses recentes:

1. Abra o notebook `notebooks/etl/data_download.ipynb`
2. Execute todas as células (o processo é incremental)
3. Recarregue os dados no analisador se já estiver rodando:

```python
analisador.reload_data()
```

**Nota**: O ETL baixa apenas dados novos, não reprocessa tudo.

---

## Consultas Sem Resultado

Se uma consulta não retornar dados, siga este checklist:

### 1. Consultar Dicionários de Referência

Use os arquivos Excel em `data/output/` para encontrar identificadores corretos:

| Arquivo | Conteúdo |
|---------|----------|
| `dicionario_entidades.xlsx` | Nomes oficiais e CNPJs de instituições |
| `dicionario_contas_cosif_individual.xlsx` | Contas COSIF individual |
| `dicionario_contas_cosif_prudencial.xlsx` | Contas COSIF prudencial |
| `dicionario_contas_ifdata_valores.xlsx` | Indicadores IFDATA |

### 2. Verificar Escopo/Documento

Certifique-se de que os dados existem para a combinação de:
- **Data**: BCB publica com 1-2 meses de atraso
- **Escopo** (IFDATA): Nem todas as instituições têm dados consolidados
- **Documento** (COSIF): Existem diferentes tipos

**Exemplo**: Tentar múltiplos escopos

```python
from bacen_analysis import DataUnavailableError

escopos = ['prudencial', 'financeiro', 'individual']
for escopo in escopos:
    try:
        dados = analisador.get_dados_ifdata(
            identificador='60701190',
            contas=['Ativo Total'],
            datas=202403,
            escopo=escopo
        )
        print(f"Dados encontrados no escopo: {escopo}")
        break
    except DataUnavailableError:
        print(f"Escopo {escopo} não disponível")
```

### 3. Usar Coluna ID_BUSCA_USADO (IFDATA)

Para consultas IFDATA, verifique qual ID foi usado:

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
- Se `ID_BUSCA_USADO != CNPJ_8`: Dado veio de conglomerado

### 4. Verificar Grafia do Nome

Nomes devem corresponder aos dicionários:

```python
# ❌ Pode não encontrar (nome impreciso e conta inexata)
dados = analisador.get_dados_cosif(
    identificador='Bradesco',
    contas=['Ativo'],
    datas=202403,
    tipo='prudencial',  # tipo é obrigatório
    documentos=4060
)

# ✅ Use CNPJ ou nome completo com nomes exatos
dados = analisador.get_dados_cosif(
    identificador='60746948',  # CNPJ é mais preciso
    contas=['ATIVO TOTAL'],    # Nome exato da conta
    datas=202403,
    tipo='prudencial',
    documentos=4060
)
```

### 5. Verificar Disponibilidade dos Dados

Nem todos os dados existem para todas as instituições em todas as datas.

```python
# Verificar se dados existem
try:
    dados = analisador.get_dados_ifdata(...)
    print("Dados encontrados!")
except DataUnavailableError:
    print("Dados não disponíveis para esta combinação de parâmetros")
```

---

## Erros Comuns

### FileNotFoundError: Arquivo Parquet não encontrado

**Causa**: Pipeline ETL não foi executado.

**Solução**:
1. Execute `notebooks/etl/data_download.ipynb` do início ao fim
2. Verifique se `data/output/` foi criado com arquivos `.parquet`

---

### EntityNotFoundError

**Causa**: Identificador (CNPJ ou nome) não encontrado nos dados cadastrais.

**Solução**:
1. Consulte `dicionario_entidades.xlsx` para nomes corretos
2. Use CNPJ de 8 dígitos em vez de nome
3. Verifique se a instituição está ativa

```python
# Listar todas as entidades disponíveis
# Acessa o DataFrame de cadastro exposto publicamente
cnpjs_disponiveis = analisador.df_ifd_cad['CNPJ_8'].unique().tolist()
atributos = analisador.get_atributos_cadastro(
    identificador=cnpjs_disponiveis[:10],  # Primeiros 10 como exemplo
    atributos=['Segmento']
)
print(atributos[['Nome_Entidade', 'CNPJ_8']])
```

---

### DataUnavailableError

**Causa**: Dados não disponíveis para a combinação de parâmetros.

**Soluções**:
1. Tente escopo diferente (IFDATA)
2. Tente documento diferente (COSIF)
3. Verifique se a data é muito recente (aguardar publicação BCB)
4. Verifique se a conta/indicador existe para esta instituição

---

### KeyError: Nome de coluna não encontrado

**Causa**: Nome de conta/indicador incorreto.

**Solução**:
1. Consulte dicionários para nomes exatos
2. Use códigos numéricos em vez de nomes
3. Verifique capitalização (ex: `'ATIVO TOTAL'` vs `'Ativo Total'`)

---

### MemoryError ou "Kernel died"

**Causa**: RAM insuficiente para processar dados.

**Soluções**:
1. Feche outros programas
2. Filtre dados antes de carregar (use datas específicas)
3. Use `drop_na=True` para reduzir tamanho dos DataFrames
4. Processe em lotes menores

---

### ModuleNotFoundError: No module named 'bacen_analysis'

**Causa**: Pacote não foi instalado.

**Solução**:
```bash
cd /caminho/para/bacen-data-analysis
pip install -e .
```

---

### ImportError: DLL load failed (Windows)

**Causa**: Dependências do PyArrow/Pandas não instaladas corretamente.

**Solução**:
```bash
pip uninstall pyarrow pandas
pip install --upgrade pyarrow pandas
```

---

## FAQ

### P: Como sei qual escopo usar (IFDATA)?

**R**: Depende do que você quer analisar:
- **Individual**: Para análise da instituição específica
- **Prudencial**: Para análise do conglomerado prudencial (mais comum)
- **Financeiro**: Para análise do conglomerado financeiro

Em caso de dúvida, tente `'prudencial'` primeiro.

---

### P: Por que minha consulta retorna DataFrame vazio?

**R**: Possíveis causas (em ordem de probabilidade):
1. Nome/código da conta incorreto → Consulte dicionários
2. Data muito recente → BCB publica com atraso
3. Escopo incorreto → Tente outros escopos
4. Instituição não reporta este dado → Consulte outras instituições

---

### P: Qual a diferença entre COSIF e IFDATA?

**R**:
- **COSIF**: Dados contábeis detalhados (Balanço, DRE) - milhares de contas
- **IFDATA**: Indicadores regulatórios agregados (Basileia, liquidez, etc.) - centenas de indicadores

Use COSIF para análises contábeis detalhadas, IFDATA para indicadores regulatórios.

---

### P: Como listar todas as contas disponíveis?

**R**: Consulte os dicionários Excel:
```python
import pandas as pd

# COSIF Prudencial
contas_cosif = pd.read_excel('data/output/dicionario_contas_cosif_prudencial.xlsx')
print(contas_cosif[['Codigo', 'Nome']])

# IFDATA
contas_ifdata = pd.read_excel('data/output/dicionario_contas_ifdata_valores.xlsx')
print(contas_ifdata[['Codigo', 'Nome']])
```

---

### P: Como fazer busca parcial de instituição?

**R**: Use nome parcial no identificador:
```python
# Funciona (busca case-insensitive parcial)
dados = analisador.get_dados_ifdata(identificador='Inter', ...)
dados = analisador.get_dados_ifdata(identificador='Bradesco', ...)
```

Mas CNPJ é sempre mais preciso:
```python
dados = analisador.get_dados_ifdata(identificador='00416968', ...)
```

---

### P: Posso usar CNPJ de 14 dígitos?

**R**: Sim, é automaticamente convertido para 8 dígitos:
```python
# Todos funcionam
dados = analisador.get_dados_ifdata(identificador='60701190', ...)
dados = analisador.get_dados_ifdata(identificador='60701190000104', ...)
dados = analisador.get_dados_ifdata(identificador='60.701.190/0001-04', ...)
```

---

### P: Como limpar o cache?

**R**:
```python
analisador.clear_cache()
```

Útil quando:
- Dados cadastrais foram atualizados
- Suspeita de resoluções incorretas cacheadas

---

### P: Quanto tempo leva o ETL inicial?

**R**:
- **Primeira execução**: 15-30 minutos (download completo)
- **Execuções subsequentes**: 2-5 minutos (apenas dados novos)

---

### P: Posso executar o ETL em produção?

**R**: Sim, mas considere:
- Agendar execução mensal (após publicação BCB)
- Monitorar espaço em disco (~2GB)
- Usar ambiente virtual
- Implementar retry logic para downloads

---

### P: Como reportar um bug?

**R**: Abra uma issue no GitHub:
1. Vá para https://github.com/enzoomoreira/bacen-data-analysis/issues
2. Clique em "New Issue"
3. Inclua:
   - Código que reproduz o problema
   - Mensagem de erro completa
   - Versão do Python e do pacote
   - Sistema operacional

---

## Suporte Adicional

Se você não encontrou solução aqui:

- **GitHub Issues**: https://github.com/enzoomoreira/bacen-data-analysis/issues
- **Documentação**:
  - [Guia de Instalação](guias/instalacao.md)
  - [Guia de Uso Rápido](guias/uso-rapido.md)
  - [API Completa](referencia/api-completa.md)

---

**Versão**: 2.0.1 | **Última atualização**: Novembro 2025
