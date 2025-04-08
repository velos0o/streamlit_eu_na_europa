# Configuração das Emissões Cartão

Este módulo permite visualizar e analisar os dados da planilha de Emissões Cartão do Google Sheets. Para que o módulo funcione corretamente, é necessário configurar o acesso à planilha.

## Opção 1: Compartilhamento público da planilha (mais simples)

1. **Acesse a planilha do Google Sheets**:
   - Abra a planilha em `https://docs.google.com/spreadsheets/d/1x_LOEGoL4LHHdbCH6OETSTPeHtf24WFLmFTv7_zXPNY/`

2. **Compartilhe publicamente para leitura**:
   - Clique no botão "Compartilhar" no canto superior direito
   - Clique em "Alterar para qualquer pessoa com o link"
   - Selecione "Qualquer pessoa com o link" 
   - Defina permissão como "Leitor"
   - Clique em "Concluído"

3. **Configure a variável de ambiente**:
   - Esta opção não requer credenciais, mas mantenha o caminho do arquivo no `.env` para compatibilidade:
   ```
   GOOGLE_CREDENTIALS_PATH=C:/caminho/qualquer/arquivo.json
   ```

## Opção 2: Usando conta de serviço (mais seguro)

1. **Criar projeto no Google Cloud Platform**:
   - Acesse o [Console do Google Cloud](https://console.cloud.google.com/)
   - Crie um novo projeto
   - Ative a API do Google Sheets e Drive para o projeto

2. **Criar credenciais de serviço**:
   - No console do GCP, vá para "APIs e serviços" > "Credenciais"
   - Clique em "Criar credenciais" > "Conta de serviço"
   - Dê um nome à conta de serviço e clique em "Criar"
   - Atribua o papel "Editor" à conta de serviço
   - Clique em "Continuar" e depois em "Concluído"
   - Clique na conta de serviço recém-criada
   - Vá para a aba "Chaves"
   - Clique em "Adicionar chave" > "Criar nova chave"
   - Selecione o formato JSON e clique em "Criar"
   - O arquivo JSON será baixado para o seu computador

3. **Compartilhar a planilha com a conta de serviço**:
   - Abra a planilha do Google Sheets
   - Clique em "Compartilhar"
   - Adicione o e-mail da conta de serviço (encontrado no arquivo JSON)
   - Dê permissão de "Editor" à conta de serviço
   - Clique em "Enviar"

4. **Configurar a variável de ambiente**:
   - Adicione a seguinte linha ao arquivo `.env` no diretório raiz do projeto:
   ```
   GOOGLE_CREDENTIALS_PATH=/caminho/para/seu/arquivo-de-credenciais.json
   ```
   - Substitua `/caminho/para/seu/arquivo-de-credenciais.json` pelo caminho completo do arquivo JSON baixado

## Estrutura da planilha

A planilha deve conter as seguintes colunas:

- ADM RESPONSAVEL
- NOME DA FAMILIA
- NOME DO REQUERENTE
- CARTÓRIO
- TIPO CERTIDÃO
- LIVRO
- FOLHA
- TERMO
- STATUS EMPRESA
- DATA DE SOLICITAÇÃO
- DATA DE ENTREGA OU ATUALIZAÇÃO DO CARTÓRIO
- STATUS CARTÓRIOS
- OBS - CARTÓRIO
- OBS - EMPRESA
- STATUS DA EMISSÃO
- OBSERVAÇÃO

## Solução de problemas

Se você receber o erro "Não foi possível carregar dados da planilha":

1. Verifique se a planilha está compartilhada publicamente para leitura (Opção 1)
2. Verifique se as credenciais da conta de serviço estão corretas (Opção 2)
3. Verifique se você tem acesso à internet

## Suporte

Em caso de dúvidas ou problemas na configuração, consulte a documentação oficial do [Google Sheets API](https://developers.google.com/sheets/api/guides/concepts). 