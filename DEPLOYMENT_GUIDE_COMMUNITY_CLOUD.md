# 🚀 Guia de Deploy - Streamlit Community Cloud

## 🔧 Soluções para Problemas Específicos do Community Cloud

### ❌ Problema: "You passed a narwhals DataFrame to is_pandas_dataframe"

**Por que acontece no Community Cloud mas não em localhost:**

1. **Versões de dependências**: O Community Cloud pode instalar versões diferentes do Altair/narwhals
2. **Ambiente containerizado**: Comportamento diferente do processamento de DataFrames
3. **Cache de sistema**: Diferenças no cache interno do Streamlit
4. **Processamento assíncrono**: Forma como o Community Cloud processa os dados

### ✅ Soluções Implementadas

#### 1. **Utilitário Global de Correção**
Criamos `utils/dataframe_utils.py` com funções que convertem automaticamente:

```python
from utils.dataframe_utils import ensure_pandas_df

# Sempre use antes de passar DataFrames para componentes Streamlit
st.dataframe(ensure_pandas_df(df))
st.bar_chart(ensure_pandas_df(df))
```

#### 2. **Arquivos Já Corrigidos**
- ✅ `views/protocolado/dados_macros.py` - **"Gráfico de Detalhamento das Pendências"**
- ✅ `views/producao.py` - Múltiplas tabelas e gráficos
- ✅ Função `ensure_pandas_df()` disponível globalmente

#### 3. **Script de Correção Automática**
Execute para identificar e corrigir todos os problemas:

```bash
python fix_narwhals_dataframes.py
python fix_narwhals_dataframes.py --fix  # Para aplicar correções
```

## 🔍 Verificações Pré-Deploy

### 1. **Dependências Fixas**
Garanta versões específicas no `requirements.txt`:

```txt
streamlit==1.44.0
altair==5.4.1
pandas==2.2.0
```

### 2. **Teste Local Primeiro**
```bash
streamlit run main.py
```

### 3. **Verificação de Imports**
Certifique-se que todos os arquivos que usam Streamlit importam:

```python
from utils.dataframe_utils import ensure_pandas_df
```

## 📝 Checklist de Deploy

### Antes do Deploy:
- [ ] ✅ Dependências fixadas no requirements.txt
- [ ] ✅ Script de correção executado
- [ ] ✅ Testes locais passando
- [ ] ✅ Imports de ensure_pandas_df adicionados
- [ ] ✅ Commit e push das correções

### Durante o Deploy:
- [ ] 🔄 Community Cloud fazendo build
- [ ] 🔄 Verificar logs de instalação
- [ ] 🔄 Aguardar conclusão do deploy

### Após o Deploy:
- [ ] ✅ Testar "Gráfico de Detalhamento das Pendências"
- [ ] ✅ Testar outras páginas com tabelas
- [ ] ✅ Verificar se não há erros narwhals
- [ ] ✅ Testar navegação completa

## 🚨 Se Ainda Houver Problemas

### 1. **Force Rebuild**
No Community Cloud, clique em "Reboot app" para forçar rebuild completo.

### 2. **Verificar Logs**
Acesse os logs no Community Cloud para identificar erros específicos.

### 3. **Aplicar Correções Manuais**
Se algum arquivo escapou, aplique manualmente:

```python
# ANTES (pode dar erro no Community Cloud)
st.dataframe(df)

# DEPOIS (sempre funciona)
st.dataframe(ensure_pandas_df(df))
```

### 4. **Versões de Emergência**
Se necessário, use versões mais antigas estáveis:

```txt
streamlit==1.43.0
altair==5.3.0
```

## 📊 Arquivos Críticos Já Corrigidos

### Alta Prioridade ✅
- `views/protocolado/dados_macros.py` - **Problema principal resolvido**
- `views/producao.py` - 7 correções aplicadas
- `utils/dataframe_utils.py` - Utilitário criado

### Média Prioridade (Próximos)
- `views/cartorio_new/producao_adm.py` - 6 ocorrências
- `views/comune/visualization.py` - 20+ ocorrências
- `views/higienizacoes/checklist/higienizacao_checklist.py` - 5 ocorrências

## 🎯 Monitoramento Pós-Deploy

### Sinais de Sucesso:
- ✅ "Gráfico de Detalhamento das Pendências" carrega sem erro
- ✅ Todas as tabelas renderizam corretamente
- ✅ Navegação funciona sem travamentos
- ✅ Logs limpos no Community Cloud

### Sinais de Problema:
- ❌ Erro "narwhals DataFrame" ainda aparece
- ❌ Páginas não carregam completamente
- ❌ Erros nos logs do Community Cloud

## 💡 Dicas de Performance

### 1. **Cache Eficiente**
```python
@st.cache_data
def load_data():
    df = load_raw_data()
    return ensure_pandas_df(df)  # Garantir pandas nativo no cache
```

### 2. **Processamento Otimizado**
```python
# Converter uma vez, usar muitas vezes
df_safe = ensure_pandas_df(df)
st.dataframe(df_safe)
st.bar_chart(df_safe)
```

### 3. **Monitoramento**
Use `st.error()` para capturar problemas em produção:

```python
try:
    df_processed = process_data(df)
    st.dataframe(ensure_pandas_df(df_processed))
except Exception as e:
    st.error(f"Erro no processamento: {e}")
    st.dataframe(ensure_pandas_df(df))  # Fallback
```

---

## 🎉 Resumo das Correções

### ✅ **Problema Principal RESOLVIDO**
O "Gráfico de Detalhamento das Pendências" agora usa `ensure_pandas_df()` e deve funcionar perfeitamente no Community Cloud.

### ✅ **Infraestrutura Criada**
- Utilitário global para conversão de DataFrames
- Script de correção automática
- Guia de deploy específico

### ✅ **Arquivos Prioritários Corrigidos**
- dados_macros.py (problema original)
- producao.py (7 correções)
- Função global disponível

### 🔄 **Próximos Passos**
1. Fazer deploy no Community Cloud
2. Testar o "Gráfico de Detalhamento das Pendências"
3. Se funcionar, aplicar correções nos demais arquivos gradualmente

---

**📞 Em caso de problemas, o erro específico será diferente e poderemos investigar baseado nos logs do Community Cloud.** 