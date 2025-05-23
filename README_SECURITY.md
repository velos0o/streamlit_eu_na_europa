# 🔒 Guia de Segurança - Projeto Eu na Europa

## ⚠️ IMPORTANTE: Configuração de Credenciais

### 📋 Arquivo secrets.toml
O arquivo `.streamlit/secrets.toml` contém credenciais sensíveis e **NUNCA** deve ser commitado no Git.

### 🛡️ Configuração Segura

1. **Copie o template:**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Preencha com suas credenciais reais:**
   - Bitrix24: Webhook URL, tokens
   - Google Sheets: Service Account JSON
   - Supabase: URLs e chaves de API

3. **Verifique o .gitignore:**
   O arquivo já está configurado para ignorar `secrets.toml`

### 🚨 Se Credenciais Foram Expostas

1. **Regenerar imediatamente:**
   - [ ] Bitrix24: Revogar e gerar novos tokens
   - [ ] Google Cloud: Deletar e criar nova Service Account Key
   - [ ] Supabase: Regenerar anon_key e service_key

2. **Monitorar:**
   - Verifique logs de acesso suspeitos
   - Monitor uso das APIs

### 🌐 Deploy Seguro

**Streamlit Cloud:**
- Use a aba "Secrets" no dashboard
- Cole o conteúdo do `secrets.toml` lá
- Nunca inclua secrets no código

**Outras plataformas:**
- Use variáveis de ambiente
- Serviços de gestão de secrets (AWS Secrets Manager, etc.)

### 📞 Em Caso de Comprometimento

1. Regenerar todas as credenciais
2. Verificar logs de acesso
3. Atualizar senhas relacionadas
4. Notificar equipe de segurança

---

**Lembre-se:** Segurança é responsabilidade de todos! 🛡️ 