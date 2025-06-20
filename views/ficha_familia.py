"""
FICHA DA FAMÍLIA - Relatório Individual de Famílias
===================================================

ATUALIZAÇÃO DEZEMBRO 2024 - NOVOS PIPELINES 102 E 104:
- Pipeline 102: Paróquia 
- Pipeline 104: Pesquisa BR

Alterações realizadas:
1. Nova função load_cartorio_data_all_pipelines() para carregar dados dos pipelines 92, 94, 102 e 104
2. Atualização da função simplificar_nome_estagio() em utils.py para incluir mapeamentos dos novos estágios
3. Atualização do map_stage_to_relatorio com categorias dos novos pipelines
4. Ampliação do resumo_status_categorias_temp para incluir as novas categorias
5. Suporte ao novo campo NOME_PIPELINE para identificação do pipeline de origem

Novos Estágios Mapeados:
Pipeline 102 (Paróquia):
- DT1098_102:NEW → SOLICITAR PARÓQUIA DE ORIGEM
- DT1098_102:PREPARATION → AGUARDANDO PARÓQUIA DE ORIGEM  
- DT1098_102:CLIENT → CERTIDÃO EMITIDA
- DT1098_102:UC_45SBLC → DEVOLUÇÃO ADM
- DT1098_102:SUCCESS → CERTIDÃO ENTREGUE
- DT1098_102:FAIL → CANCELADO
- DT1098_102:UC_676WIG → CERTIDÃO DISPENSADA
- DT1098_102:UC_UHPXE8 → CERTIDÃO ENTREGUE

Pipeline 104 (Pesquisa BR):
- DT1098_104:NEW → AGUARDANDO PESQUISADOR
- DT1098_104:PREPARATION → PESQUISA EM ANDAMENTO
- DT1098_104:SUCCESS → PESQUISA PRONTA PARA EMISSÃO
- DT1098_104:FAIL → PESQUISA NÃO ENCONTRADA

LÓGICA DE PRECEDÊNCIA PIPELINE 104:
Quando uma pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104 e também possui
registros nos pipelines superiores (92, 94, 102), o sistema mostra apenas o status 
dos pipelines superiores, pois após a pesquisa estar pronta, o card é duplicado 
para os outros pipelines onde o processo continua.

LÓGICA DE "Pasta C/Emissão Concluída":
Esta é uma MÉTRICA DERIVADA, não um status direto. É calculada quando TODAS as 
certidões ativas de uma família estão no status "Brasileiras Emitida". 
Baseada na mesma lógica do higienizacao_desempenho.py.
"""

import streamlit as st
# importยอด_เยี่ยม_navigation_utils # Comentado por enquanto
import pandas as pd # Adicionado para manipulação de dados
import os # Adicionado para manipulação de caminhos

# Importar data loaders dos módulos
from views.reclamacoes.data_loader import carregar_dados_reclamacoes
from views.cartorio_new.data_loader import carregar_dados_cartorio
# Supondo que o data_loader de comune_new tenha uma função similar
from views.comune_new.data_loader import load_comune_data # CORRIGIDO

# Importar a função central de carregamento do Bitrix
from api.bitrix_connector import load_merged_data

# Importar função de simplificação de estágio
# Tratamento de erro caso o arquivo não exista ou a função não seja encontrada
try:
    from views.cartorio_new.visao_geral import simplificar_nome_estagio
except ImportError as e:
    st.error(f"Erro ao importar 'simplificar_nome_estagio': {e}. A exibição do status da certidão pode falhar.")
    # Definir uma função placeholder para evitar erros fatais
    def simplificar_nome_estagio(nome):
        return str(nome) if nome else "Erro Import"

def load_crm_deal_data(category_id):
    """Carrega dados do CRM Deal (Funil/Categoria especificado) usando a função central load_merged_data."""
    print(f"[INFO] Solicitando dados CRM para category_id: {category_id} via load_merged_data")
    try:
        # Chama a função central passando o category_id desejado
        # Opcional: Passar debug=True se quiser ver os logs detalhados de load_merged_data
        # Opcional: Passar force_reload=True para ignorar o cache durante testes
        df_crm_merged = load_merged_data(category_id=category_id, debug=False, force_reload=False)

        if df_crm_merged is None or df_crm_merged.empty:
            st.warning(f"Nenhum dado encontrado ou erro ao carregar dados para a categoria {category_id}.")
            print(f"[AVISO] load_merged_data retornou vazio para category_id {category_id}")
            return pd.DataFrame() # Retorna DF vazio para consistência
        else:
            print(f"[INFO] Dados para category_id {category_id} carregados com sucesso via load_merged_data ({len(df_crm_merged)} linhas).")
            # Verificar se as colunas essenciais para a busca/ficha existem
            colunas_necessarias = ['ID', 'UF_CRM_1722883482527', 'UF_CRM_1722605592778']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_crm_merged.columns]
            if colunas_faltantes:
                st.error(f"Erro Crítico: As seguintes colunas essenciais estão faltando nos dados carregados: {colunas_faltantes}")
                print(f"[ERRO] Colunas essenciais ausentes após merge: {colunas_faltantes}. Colunas presentes: {list(df_crm_merged.columns)}")
                return pd.DataFrame()
            return df_crm_merged

    except ImportError:
        st.error("Erro Crítico: Não foi possível importar 'load_merged_data' de 'api.bitrix_connector'. Verifique a estrutura do projeto.")
        print("[ERRO CRÍTICO] Falha ao importar load_merged_data")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao chamar load_merged_data: {e}")
        print(f"[ERRO CRÍTICO] Erro inesperado em load_crm_deal_data ao chamar load_merged_data: {e}")
        return pd.DataFrame()

# Função para carregar CSS (pode ser movida para um utilitário depois)
def load_page_specific_css(file_path):
    try:
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado: {file_path}")

# Função removida - agora usamos load_data_all_pipelines() do views.cartorio_new.data_loader

def exibir_ficha_familia(familia_serie, emissoes_df):
    # --- NOVO: Injetar CSS para animação do banner se necessário ---
    mapa_inicial_flag = familia_serie.get('UF_CRM_1750454794052', 'NÃO')
    if str(mapa_inicial_flag).strip().upper() == 'SIM':
        st.markdown("""
        <style>
        @keyframes border-pulse-animation {
            0% { box-shadow: 0 0 4px rgba(255, 193, 7, 0.5); }
            50% { box-shadow: 0 0 12px 4px rgba(255, 193, 7, 0.8); }
            100% { box-shadow: 0 0 4px rgba(255, 193, 7, 0.5); }
        }
        .mapa-inicial-banner {
            position: fixed;
            top: 80px;
            right: 0;
            width: 100px;
            height: 100px;
            background-color: #ffc107; /* Amarelo chamativo */
            color: #333; /* Texto escuro para contraste */
            font-size: 1.1em;
            font-weight: bold;
            border-radius: 0; /* Quadrado */
            z-index: 1000;
            animation: border-pulse-animation 2s infinite;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    # Iniciar a string HTML com o contêiner principal
    html_ficha_completa = "<div class='ficha-familia-container' style='width:100%; max-width:100%; margin-right:0; margin-left:0;'>"
    
    # Adicionar o banner se a flag estiver ativa
    if str(mapa_inicial_flag).strip().upper() == 'SIM':
        html_ficha_completa += "<div class='mapa-inicial-banner'>MAPA INICIAL</div>"
    
    # Título principal da ficha
    html_ficha_completa += "<div style='background-color:#0070F2; color:white; text-align:center; padding:10px; margin-bottom:15px; font-size:1.3em; font-weight:bold; border-radius:5px;'>ACOMPANHAMENTO FAMÍLIA</div>"

    # DEBUG: Imprimir colunas disponíveis
    print("[DEBUG] Colunas disponíveis na família:", list(familia_serie.index))
    print("\n[DEBUG] Primeiros 10 campos e seus valores:")
    contador = 0
    for campo, valor in familia_serie.items():
        if contador < 10:
            print(f"[DEBUG] {campo}: {valor}")
            contador += 1
    
    # DEBUG: Listar todos os campos UF_CRM e seus valores
    print("\n[DEBUG] Todos campos UF_CRM e seus valores:")
    for campo, valor in familia_serie.items():
        if str(campo).startswith('UF_CRM'):
            print(f"[DEBUG] {campo}: {valor}")
    
    # --- Coleta todos os dados primeiro ---
    nome_familia = familia_serie.get('UF_CRM_1722883482527', 'N/D')
    
    # Tentar múltiplas alternativas para Data de Venda
    data_venda = None
    # Campos mais prováveis para DATA DE VENDA
    campos_data_venda = [
        'UF_CRM_1746054586042',  # ID informado pelo cliente
        'UF_CRM_1739362935',     # Possível campo de data
        'UF_CRM_1725397957843',  # Campo anterior
        'DATE_CREATE',           # Data de criação do registro
        'BEGINDATE',             # Data de início
        'CLOSEDATE'              # Data de fechamento
    ]
    
    for campo in campos_data_venda:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            data_venda = familia_serie.get(campo)
            print(f"[DEBUG] Data de venda encontrada no campo '{campo}': {data_venda}")
            break
            
    if data_venda is None or data_venda == 'None':
        data_venda = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Data de Venda")
    
    id_familia = familia_serie.get('UF_CRM_1722605592778', 'N/D')
    
    # Tentar múltiplas alternativas para ADM Responsável
    adm_responsavel = None
    # Campos mais prováveis para ADM RESPONSÁVEL
    campos_adm = [
        'UF_CRM_1730730467',    # ID informado pelo cliente
        'ASSIGNED_BY_ID',       # Responsável atribuído
        'ASSIGNED_BY',          # Nome do responsável
        'RESPONSIBLE_ID',       # Outra possibilidade 
        'UF_CRM_1746198853',    # Campo anterior
        'CREATED_BY_ID'         # Criador do registro
    ]
    
    for campo in campos_adm:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            adm_responsavel = familia_serie.get(campo)
            print(f"[DEBUG] ADM Responsável encontrado no campo '{campo}': {adm_responsavel}")
            break
            
    if adm_responsavel is None or adm_responsavel == 'None':
        adm_responsavel = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para ADM Responsável")
    
    # Tentar múltiplas alternativas para Procuração
    procuracao_detalhes = None
    # Campos mais prováveis para PROCURAÇÃO
    campos_proc = [
        'UF_CRM_1746046262136',   # ID correto identificado pelo cliente - PROCURAÇÃO PENDENTE
        'UF_CRM_1744671378914',   # ID anterior
        'UF_CRM_1737561431',      # Possível campo de procuração
        'UF_CRM_1746089520',      # Possível campo de procuração
        'COMMENTS',               # Comentários gerais
        'DESCRIPTION'             # Descrição
    ]
    
    for campo in campos_proc:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            procuracao_detalhes = familia_serie.get(campo)
            print(f"[DEBUG] Procuração encontrada no campo '{campo}': {procuracao_detalhes}")
            break
            
    if procuracao_detalhes is None or procuracao_detalhes == 'None':
        procuracao_detalhes = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Procuração")
    
    # Tentar múltiplas alternativas para Etapa Comune
    etapa_comune = None
    # Campos mais prováveis para ETAPA COMUNE
    campos_comune = [
        'UF_CRM_1746045819198',   # ID informado pelo cliente
        'UF_CRM_1737823612831',   # Campo anterior
        'STAGE_ID',               # ID do estágio
        'STAGE_SEMANTIC_ID',      # Semântica do estágio
        'UF_CRM_1737561431'       # Possível campo de comune
    ]
    
    for campo in campos_comune:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            etapa_comune = familia_serie.get(campo)
            print(f"[DEBUG] Etapa Comune encontrada no campo '{campo}': {etapa_comune}")
            break
            
    if etapa_comune is None or etapa_comune == 'None':
        etapa_comune = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Etapa Comune")
    
    data_solicitacao_comune = familia_serie.get('UF_CRM_1737823552173', 'N/D')
    if data_solicitacao_comune is None or data_solicitacao_comune == 'None': data_solicitacao_comune = 'N/D'
    prazo_comune = familia_serie.get('UF_CRM_1746202791172', 'N/D')
    if prazo_comune is None or prazo_comune == 'None': prazo_comune = 'N/D'
    analise_doc = familia_serie.get('UF_CRM_1746045866262', 'N/D')
    if analise_doc is None or analise_doc == 'None': analise_doc = 'N/D'
    traducao = familia_serie.get('UF_CRM_1746045880601', 'N/D')
    if traducao is None or traducao == 'None': traducao = 'N/D'
    apostilamento = familia_serie.get('UF_CRM_1746045919198', 'N/D')
    if apostilamento is None or apostilamento == 'None': apostilamento = 'N/D'
    drive_link_raw = familia_serie.get('UF_CRM_DRIVE', 'N/D')
    drive_display = f"<a href='{drive_link_raw}' target='_blank' class='ficha-link'>Acessar Link</a>" if str(drive_link_raw).startswith('http') else str(drive_link_raw)
    qnt_familiares = familia_serie.get('UF_CRM_QUANTIDADE_FAMILIARES', 'N/D')
    if qnt_familiares is None or qnt_familiares == 'None': qnt_familiares = 'N/D'
    qnt_requerentes = familia_serie.get('UF_CRM_1743182118', 'N/D')
    if qnt_requerentes is None or qnt_requerentes == 'None': qnt_requerentes = 'N/D'
    emissoes_status_geral = familia_serie.get('UF_CRM_1746459875884', 'N/D')
    if emissoes_status_geral is None or emissoes_status_geral == 'None': emissoes_status_geral = 'N/D'

    # (Lógica de processamento de emissões, agora incluindo a posição na árvore)
    requerentes_data_list_of_dicts = []
    processamento_emissoes_ok = False
    
    # NOVA LÓGICA: Função para determinar categoria baseada em Pipeline + Status
    # Esta correção resolve o problema de chaves duplicadas no mapeamento anterior
    def determinar_categoria_por_pipeline_status(category_id, stage_name_legivel):
            """Determina a categoria do resumo baseada no pipeline (CATEGORY_ID) e status (STAGE_NAME_LEGIVEL)"""
            category_id_str = str(category_id)
            status_upper = str(stage_name_legivel).upper() if pd.notna(stage_name_legivel) else ""
            
            # Pipeline 92 e 94 (Cartórios Casa Verde e Tatuapé)
            if category_id_str in ['92', '94']:
                if status_upper == 'AGUARDANDO DECISÃO CLIENTE':
                    return 'Aguardando Decisão Cliente'
                if status_upper in ["AGUARDANDO CERTIDÃO", "BUSCA - CRC", "DEVOLUTIVA BUSCA - CRC", 
                                  "APENAS ASS. REQ CLIENTE P/MONTAGEM", "MONTAGEM REQUERIMENTO CARTÓRIO", 
                                  "SOLICITAR CARTÓRIO DE ORIGEM", "SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
                                  "DEVOLUÇÃO ADM", "DEVOLVIDO REQUERIMENTO"]:
                    return "Brasileiras Pendências"
                elif status_upper == "PESQUISA - BR":
                    return "Brasileiras Pesquisas"
                elif status_upper == "AGUARDANDO CARTÓRIO ORIGEM":
                    return "Brasileiras Solicitadas"
                elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
                    return "Brasileiras Emitida"  # CORRIGIDO: Era "Pasta C/Emissão Concluída"
                elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
                    return "Brasileiras Dispensada"  # Não contabilizada no resumo ativo
                    
            # Pipeline 102 (Paróquia)
            elif category_id_str == '102':
                if status_upper in ["SOLICITAR PARÓQUIA DE ORIGEM", "DEVOLUÇÃO ADM"]:
                    return "Paróquia Pendências"
                elif status_upper == "AGUARDANDO PARÓQUIA DE ORIGEM":
                    return "Paróquia Solicitadas"
                elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
                    return "Paróquia Emitida"  # CORRIGIDO: Consistente com a lógica
                elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
                    return "Paróquia Dispensada"  # Não contabilizada no resumo ativo
                    
            # Pipeline 104 (Pesquisa BR)
            elif category_id_str == '104':
                if status_upper == "AGUARDANDO PESQUISADOR":
                    return "Pesquisa BR Pendências"
                elif status_upper == "PESQUISA EM ANDAMENTO":
                    return "Pesquisa BR Em Andamento"
                elif status_upper == "PESQUISA PRONTA PARA EMISSÃO":
                    return "Pesquisa BR Concluída"
                elif status_upper == "PESQUISA NÃO ENCONTRADA":
                    return "Pesquisa BR Não Encontrada"
            
            # Default para casos não mapeados
            return "Outros"

    if emissoes_df is not None and not emissoes_df.empty:
        col_stage_para_simplificar = None
        if 'STAGE_ID' in emissoes_df.columns: col_stage_para_simplificar = 'STAGE_ID'
        elif 'STAGE_NAME' in emissoes_df.columns: col_stage_para_simplificar = 'STAGE_NAME'
        if col_stage_para_simplificar:
            try:
                emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar].apply(simplificar_nome_estagio)
                processamento_emissoes_ok = True
                # DEBUG ADICIONADO
                print("\n[DEBUG ANTES DO LOOP DE REQUERENTES] Primeiras 20 linhas de emissoes_df com STAGE_NAME_LEGIVEL:")
                if not emissoes_df.empty and col_stage_para_simplificar in emissoes_df.columns :
                    print(emissoes_df[['TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', col_stage_para_simplificar, 'STAGE_NAME_LEGIVEL']].head(20))
                else:
                    print("[DEBUG ANTES DO LOOP DE REQUERENTES] emissoes_df vazio ou coluna de stage ausente.")
            except Exception: emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar]; processamento_emissoes_ok = True
        else: processamento_emissoes_ok = False
        if processamento_emissoes_ok:
            map_tipo_certidao = {'NASCIMENTO': 'Nascimento', 'CASAMENTO': 'Casamento', 'ÓBITO': 'Óbito'}
            # Adicionando UF_CRM_34_POSICAO_ARVORE à lista de colunas necessárias
            cols_req = ['UF_CRM_34_ID_REQUERENTE', 'TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', 'STAGE_NAME_LEGIVEL', 'UF_CRM_34_POSICAO_ARVORE']
            
            # Verificamos se todas as colunas necessárias existem
            colunas_faltantes = [col for col in cols_req if col not in emissoes_df.columns]
            
            if colunas_faltantes:
                print(f"[AVISO] Colunas ausentes nos dados: {colunas_faltantes}")
                if 'UF_CRM_34_POSICAO_ARVORE' in colunas_faltantes:
                    # Criar coluna com valor padrão se ela estiver faltando
                    emissoes_df['UF_CRM_34_POSICAO_ARVORE'] = "N/D"
                    colunas_faltantes.remove('UF_CRM_34_POSICAO_ARVORE')
            
            if not colunas_faltantes:  # Se todas as colunas obrigatórias estiverem presentes
                emissoes_df[cols_req[0]] = emissoes_df[cols_req[0]].fillna('ID Requerente N/D').astype(str)
                emissoes_df[cols_req[1]] = emissoes_df[cols_req[1]].fillna('Nome N/D').astype(str)
                emissoes_df[cols_req[2]] = emissoes_df[cols_req[2]].fillna('Tipo N/D').astype(str)
                emissoes_df[cols_req[3]] = emissoes_df[cols_req[3]].fillna('Status N/D').astype(str)
                emissoes_df[cols_req[4]] = emissoes_df[cols_req[4]].fillna('Não informado').astype(str)
                
                grouped_by_requerente = emissoes_df.groupby(cols_req[0])
                if grouped_by_requerente.ngroups > 0:
                    for id_req, grupo in grouped_by_requerente:
                        nome_req_bruto = grupo[cols_req[1]].iloc[0] if not grupo[cols_req[1]].empty else "Req. Desconhecido"
                        posicao_arvore = grupo[cols_req[4]].iloc[0] if not grupo[cols_req[4]].empty else "N/D"

                        if id_req == 'ID Requerente N/D':
                            nome_req_bruto = grupo[cols_req[1]].iloc[0] if not grupo[cols_req[1]].empty else "Req. (ID N/D)"

                        # --- Limpar prefixos do nome ---
                        nome_limpo = str(nome_req_bruto) # Garantir que é string
                        prefixes_to_remove = ["NASCIMENTO - ", "CASAMENTO - ", "ÓBITO - "]
                        for prefix in prefixes_to_remove:
                            if nome_limpo.startswith(prefix):
                                nome_limpo = nome_limpo[len(prefix):]
                                break # Remover apenas o primeiro prefixo encontrado
                        nome_req_disp = nome_limpo.strip() # Nome final limpo
                        # --- Fim da limpeza ---

                        cert_status = {v: 'Dispensado' for k, v in map_tipo_certidao.items() if v}
                        
                        # NOVA LÓGICA: Precedência de pipelines
                        # Se a pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104,
                        # devemos verificar se ela tem registros nos pipelines superiores (92, 94, 102)
                        pipeline_104_pronto = False
                        registros_pipelines_superiores = []
                        
                        # Verificar se há registro no pipeline 104 com status "PESQUISA PRONTA PARA EMISSÃO"
                        for _, row in grupo.iterrows():
                            if 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) == '104':
                                if row[cols_req[3]] == 'PESQUISA PRONTA PARA EMISSÃO':
                                    pipeline_104_pronto = True
                            elif 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) in ['92', '94', '102']:
                                registros_pipelines_superiores.append(row)
                        
                        # Aplicar lógica de precedência
                        if pipeline_104_pronto and registros_pipelines_superiores:
                            # Se tem pipeline 104 pronto E registros nos superiores,
                            # processar apenas os registros dos pipelines superiores
                            print(f"[DEBUG PRECEDÊNCIA] ID_REQUERENTE {id_req}: Pipeline 104 pronto, usando status dos pipelines superiores")
                            for row in registros_pipelines_superiores:
                                tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                                if tipo_l: 
                                    cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]
                        else:
                            # Lógica normal: processar todos os registros
                            for _, row in grupo.iterrows():
                                tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                                if tipo_l: 
                                    cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]

                        # Incluir a posição na árvore nos dados a serem exibidos
                        requerentes_data_list_of_dicts.append({
                            'Requerente': nome_req_disp, # Usar o nome limpo
                            'Posição': posicao_arvore,
                            **cert_status
                        })
                else: processamento_emissoes_ok = False
            else: processamento_emissoes_ok = False
    # (FIM DA LÓGICA DE PROCESSAMENTO DE EMISSÕES)

    # Ordenar requerentes_data_list_of_dicts por posição na ordem: ITALIANO, FAMILIAR, REQUERENTE
    if requerentes_data_list_of_dicts:
        def ordem_posicao(item):
            posicao = item.get('Posição', '').upper()
            if posicao == 'ITALIANO': return 1
            elif posicao in ['FAMILIAR', 'FAMILIA']: 
                item['Posição'] = 'FAMILIAR'
                return 2
            elif posicao == 'REQUERENTE': return 3
            else: return 4
        
        requerentes_data_list_of_dicts.sort(key=ordem_posicao)

    # --- Montar a Tabela HTML Única --- 
    html_ficha_completa += "<div class='ficha-secao dados-consolidado-tabela-secao'>"
    html_ficha_completa += "<table class='ficha-info-tabela' style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
    
    td_style = "border:1px solid #ddd; padding:8px;"
    td_label_style = f"{td_style} color:#0070F2; font-weight:bold; width:20%;"
    td_data_style = f"{td_style} width:30%;"
    
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Nome da Família:</td><td style='{td_data_style}'>{nome_familia}</td><td style='{td_label_style}'>ID da Família:</td><td style='{td_data_style}'>{id_familia}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Data de Venda:</td><td style='{td_data_style}'>{data_venda}</td><td style='{td_label_style}'>ADM Responsável:</td><td style='{td_data_style}'>{adm_responsavel}</td></tr>"

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>PROCURAÇÃO</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Detalhes Procuração:</td><td colspan='3' style='{td_style}'>{procuracao_detalhes}</td></tr>" 

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>COMUNE</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Etapa Comune:</td><td style='{td_data_style}'>{etapa_comune}</td><td style='{td_label_style}'>Data Solicitação Comune:</td><td style='{td_data_style}'>{data_solicitacao_comune}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Prazo Comune:</td><td style='{td_data_style}'>{prazo_comune}</td><td style='{td_label_style}'></td><td style='{td_data_style}'></td></tr>"

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>DOCUMENTAÇÃO E SERVIÇOS</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Análise Documental:</td><td style='{td_data_style}'>{analise_doc}</td><td style='{td_label_style}'>Tradução:</td><td style='{td_data_style}'>{traducao}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Apostilamento:</td><td style='{td_data_style}'>{apostilamento}</td><td style='{td_label_style}'>Drive:</td><td style='{td_data_style}'>{drive_display}</td></tr>"

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>DETALHES</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Qnt. Familiares:</td><td style='{td_data_style}'>{qnt_familiares}</td><td style='{td_label_style}'>Qnt. Requerentes:</td><td style='{td_data_style}'>{qnt_requerentes}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Emissões (Status Geral):</td><td style='{td_data_style}'>{emissoes_status_geral}</td><td style='{td_label_style}'></td><td style='{td_data_style}'></td></tr>"

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>STATUS EMISSÕES BRASILEIRAS</h4></td></tr>"
    
    empty_cell_style = "text-align:center; border:1px solid #ddd; padding:8px; font-style:italic; color:#666;"
    
    if processamento_emissoes_ok and requerentes_data_list_of_dicts:
        html_ficha_completa += f"<tr><td colspan='4' style='padding:0; border:0;'>"
        html_ficha_completa += "<table style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
        
        html_ficha_completa += "<tr class='emissoes-header-row'>"
        html_ficha_completa += "<th style='color:#0070F2; width:15%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Posição</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:25%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Requerente</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Nascimento</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Casamento</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Óbito</th>"
        html_ficha_completa += "</tr>"
        
        for req_data in requerentes_data_list_of_dicts:
            html_ficha_completa += "<tr class='emissoes-data-row'>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{req_data['Posição']}</td>"
            html_ficha_completa += f"<td style='text-align:left; border:1px solid #ddd; padding:8px;'>{req_data['Requerente']}</td>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{req_data['Nascimento']}</td>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{req_data['Casamento']}</td>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{req_data['Óbito']}</td>"
            html_ficha_completa += "</tr>"
        
        html_ficha_completa += "</table>"
        html_ficha_completa += "</td></tr>"
        
        # --- NOVA LÓGICA PARA POPULAR resumo_status_categorias --- 
        # 1. Definir df_emissoes_ativas (usando emissoes_df que é o df_emissoes_filtradas com STAGE_NAME_LEGIVEL)
        df_emissoes_ativas = pd.DataFrame() 
        total_certidoes_reais_para_exibicao = 0

        if emissoes_df is not None and not emissoes_df.empty and 'STAGE_NAME_LEGIVEL' in emissoes_df.columns:
            status_de_dispensa_reais = ["SOLICITAÇÃO DUPLICADA", "CANCELADO"] # Status que indicam dispensa real
            # Garante que estamos comparando strings com strings e lidando com NaNs em STAGE_NAME_LEGIVEL
            emissoes_df_valid_stages = emissoes_df[pd.notna(emissoes_df['STAGE_NAME_LEGIVEL'])].copy()
            emissoes_df_valid_stages['STAGE_NAME_LEGIVEL_UPPER'] = emissoes_df_valid_stages['STAGE_NAME_LEGIVEL'].astype(str).str.upper()
            
            df_emissoes_ativas = emissoes_df_valid_stages[
                ~emissoes_df_valid_stages['STAGE_NAME_LEGIVEL_UPPER'].isin(status_de_dispensa_reais)
            ].copy()
            total_certidoes_reais_para_exibicao = len(df_emissoes_ativas)

        elif emissoes_df is not None and not emissoes_df.empty: # Fallback se STAGE_NAME_LEGIVEL não existir ou for problemático
            df_emissoes_ativas = emissoes_df.copy() 
            total_certidoes_reais_para_exibicao = len(df_emissoes_ativas)

        # 2. Reinicializar e popular resumo_status_categorias com base em df_emissoes_ativas
        # Usando o map_stage_to_relatorio definido anteriormente
        # ATUALIZADO: Incluindo categorias dos novos pipelines 102 e 104
        resumo_status_categorias_temp = { # Renomeado para evitar conflito de escopo se existir antes
            # Pipelines 92 e 94 (Cartórios)
            'Brasileiras Pendências': 0,
            'Aguardando Decisão Cliente': 0,
            'Brasileiras Pesquisas': 0,
            'Brasileiras Solicitadas': 0,
            'Brasileiras Emitida': 0,  # CORRIGIDO: Status direto de emissão
            # Pipeline 102 (Paróquia)
            'Paróquia Pendências': 0,
            'Paróquia Solicitadas': 0,
            'Paróquia Emitida': 0,  # CORRIGIDO: Consistente com a lógica
            # Pipeline 104 (Pesquisa BR)
            'Pesquisa BR Pendências': 0,
            'Pesquisa BR Em Andamento': 0,
            'Pesquisa BR Concluída': 0,
            'Pesquisa BR Não Encontrada': 0,
            # 'Brasileiras Dispensada': 0, # Não incluímos aqui, pois df_emissoes_ativas já as exclui
            # 'Paróquia Dispensada': 0, # Não incluímos aqui, pois df_emissoes_ativas já as exclui
            'Outros': 0
        }

        if not df_emissoes_ativas.empty:
            # NOVA LÓGICA: Aplicar precedência de pipelines também no resumo
            # Criar DataFrame para processar precedência
            df_processado = df_emissoes_ativas.copy()
            
            # Identificar pessoas que têm "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104
            # e também têm registros nos pipelines superiores (92, 94, 102)
            if 'UF_CRM_34_ID_REQUERENTE' in df_processado.columns and 'CATEGORY_ID' in df_processado.columns:
                # Agrupar por ID_REQUERENTE para aplicar a lógica de precedência
                requerentes_para_remover_104 = []
                
                for id_requerente, grupo_req in df_processado.groupby('UF_CRM_34_ID_REQUERENTE'):
                    # Verificar se tem pipeline 104 com "PESQUISA PRONTA PARA EMISSÃO"
                    tem_104_pronto = False
                    tem_pipelines_superiores = False
                    
                    for _, row in grupo_req.iterrows():
                        if str(row['CATEGORY_ID']) == '104' and row['STAGE_NAME_LEGIVEL'] == 'PESQUISA PRONTA PARA EMISSÃO':
                            tem_104_pronto = True
                        elif str(row['CATEGORY_ID']) in ['92', '94', '102']:
                            tem_pipelines_superiores = True
                    
                    # Se tem 104 pronto E pipelines superiores, remover registros do 104 do resumo
                    if tem_104_pronto and tem_pipelines_superiores:
                        requerentes_para_remover_104.append(id_requerente)
                        print(f"[DEBUG PRECEDÊNCIA RESUMO] ID_REQUERENTE {id_requerente}: Removendo pipeline 104 do resumo (precedência)")
                
                # Remover registros do pipeline 104 para os requerentes identificados
                if requerentes_para_remover_104:
                    mask_remover = (df_processado['UF_CRM_34_ID_REQUERENTE'].isin(requerentes_para_remover_104)) & (df_processado['CATEGORY_ID'].astype(str) == '104')
                    df_processado = df_processado[~mask_remover].copy()
                    print(f"[DEBUG PRECEDÊNCIA RESUMO] Removidos {mask_remover.sum()} registros do pipeline 104 devido à precedência")
            
            # Continuar com a lógica normal de resumo usando df_processado
            for _idx, certidao_ativa_row in df_processado.iterrows():
                status_legivel = certidao_ativa_row['STAGE_NAME_LEGIVEL']
                category_id = certidao_ativa_row.get('CATEGORY_ID', '')
                
                # USAR A NOVA FUNÇÃO em vez do mapeamento antigo
                categoria_para_resumo = determinar_categoria_por_pipeline_status(category_id, status_legivel)
                
                # Só contar se não for uma categoria "Dispensada"
                if not categoria_para_resumo.endswith("Dispensada"):
                    if categoria_para_resumo in resumo_status_categorias_temp:
                        resumo_status_categorias_temp[categoria_para_resumo] += 1
                    else:
                        # Para categorias não mapeadas, contar como 'Outros'
                        resumo_status_categorias_temp['Outros'] += 1
            
            # Atualizar total com o DataFrame processado
            total_certidoes_reais_para_exibicao = len(df_processado)
            
            # ADICIONAR LÓGICA DE "Pasta C/Emissão Concluída" (métrica derivada)
            # Calcular se a família tem TODAS as certidões ativas como "Brasileiras Emitida"
            total_ativas = (resumo_status_categorias_temp['Brasileiras Pendências'] + 
                           resumo_status_categorias_temp['Brasileiras Pesquisas'] + 
                           resumo_status_categorias_temp['Brasileiras Solicitadas'] + 
                           resumo_status_categorias_temp['Brasileiras Emitida'])
            
            if total_ativas > 0 and total_ativas == resumo_status_categorias_temp['Brasileiras Emitida']:
                resumo_status_categorias_temp['Pasta C/Emissão Concluída'] = 1
            else:
                resumo_status_categorias_temp['Pasta C/Emissão Concluída'] = 0
        
        # Atribuir o resultado calculado ao nome da variável que o HTML do resumo espera
        resumo_status_categorias = resumo_status_categorias_temp
        # --- FIM DA NOVA LÓGICA --- 

        html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>RESUMO EMISSÕES</h4></td></tr>"
        
        html_ficha_completa += f"<tr><td colspan='4' style='padding:0; border:0;'>"
        html_ficha_completa += "<table style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
        
        html_ficha_completa += "<tr class='resumo-header-row'>"
        html_ficha_completa += "<th style='color:#0070F2; width:30%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Status</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Quantidade</th>"
        html_ficha_completa += "</tr>"
        
        for status, quantidade in resumo_status_categorias.items():
            if quantidade > 0 or status == 'Outros': 
                html_ficha_completa += "<tr class='resumo-data-row'>"
                html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px; font-weight:bold;'>{status}</td>"
                html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{quantidade}</td>"
                html_ficha_completa += "</tr>"
        
        html_ficha_completa += "<tr class='resumo-total-row' style='background-color:#f0f0f0;'>"
        html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px; font-weight:bold;'>TOTAL</td>"
        html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px; font-weight:bold;'>{total_certidoes_reais_para_exibicao}</td>"
        html_ficha_completa += "</tr>"
        
        html_ficha_completa += "</table>"
        html_ficha_completa += "</td></tr>"
        
    elif emissoes_df is not None and not emissoes_df.empty:
        html_ficha_completa += f"<tr><td colspan='4' style='{empty_cell_style}'>Aviso: Não foi possível processar os detalhes das emissões.</td></tr>"
    else:
        html_ficha_completa += f"<tr><td colspan='4' style='{empty_cell_style}'>Nenhuma emissão detalhada encontrada para esta família.</td></tr>"

    html_ficha_completa += "</table>"
    html_ficha_completa += "</div>" # Fecha dados-consolidado-tabela-secao
    html_ficha_completa += "</div>" # Fecha ficha-familia-container

    # Para garantir que a ficha ocupe todo o espaço disponível,
    # vamos incluir CSS adicional diretamente na página
    css_fullwidth = '''
    <style>
    .ficha-familia-container {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        padding: 20px !important;
    }
    /* Tentativa de forçar o container pai do Streamlit a ter largura total */
    div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        flex: 0 1 100% !important;
    }
    </style>
    '''
    
    # Primeiro injetamos o CSS, depois o HTML da ficha
    st.markdown(css_fullwidth, unsafe_allow_html=True)
    st.markdown(html_ficha_completa, unsafe_allow_html=True)

def exibir_metricas_macro():
    st.markdown("### Métricas Macro")
    st.info("Seção de métricas gerais ainda em desenvolvimento.")
    pass

def show_ficha_familia():
    # REMOVIDO: Configuração do layout da página (já feita em main.py)
    # Comentado para evitar conflito: st.set_page_config() deve ser chamado apenas uma vez
    # try:
    #     st.set_page_config(layout="wide")
    # except st.errors.StreamlitAPIException as e:
    #     # st.toast(f"Nota: st.set_page_config(layout=\"wide\") já foi chamado anteriormente. {e}")
    #     pass # Ignora o erro se já foi configurado

    st.markdown("<h1 class='page-title initial-page-title'>Ficha da Família</h1>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Busque por uma família para ver detalhes ou visualize métricas gerais.</p>", unsafe_allow_html=True)

    # Garantir que toda a página use a largura máxima disponível
    st.markdown('''
    <style>
    .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Estilos para a tabela de resultados de busca */
    .search-results-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
        font-size: 14px;
    }
    .search-results-table th {
        background-color: #f0f0f0;
        padding: 8px 12px;
        text-align: left;
        border: 1px solid #ddd;
        font-weight: 600;
    }
    .search-results-table td {
        padding: 8px 12px;
        border: 1px solid #ddd;
        vertical-align: top;
    }
    .search-results-table tr:hover {
        background-color: #f9f9f9;
        cursor: pointer;
    }
    .search-results-table tr.selected {
        background-color: #e0f0ff;
    }
    /* Estilos para o contador de resultados */
    .results-count {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 10px;
        font-style: italic;
    }
    </style>
    ''', unsafe_allow_html=True)

    # Carregar os dados das famílias antecipadamente para agilizar a busca
    df_crm_deals_full = load_crm_deal_data(category_id=46)
    
    # Preparar estado para armazenar família selecionada
    if "familia_selecionada_id" not in st.session_state:
        st.session_state.familia_selecionada_id = None
    if "resultados_busca" not in st.session_state:
        st.session_state.resultados_busca = pd.DataFrame()
    
    # Função para atualizar o ID da família selecionada
    def selecionar_familia(id_familia):
        st.session_state.familia_selecionada_id = id_familia

    # Container para busca e resultados
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            campo_busca_familia_principal = 'UF_CRM_1722883482527'
            termo_busca = st.text_input(
                "Busca Nome da Família",
                placeholder="Digite o nome da família...",
                key="busca_familia_principal_input"
            ).strip()
        
        # Botão de pesquisa avançada (opcional)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento para alinhar com o campo de busca
            busca_avancada = st.button("🔍 Busca Avançada", help="Abre opções de busca avançada")

    # Processamento da busca
    familia_selecionada_data = pd.Series(dtype=object)
    df_emissoes_filtradas = pd.DataFrame()
    
    if df_crm_deals_full is not None and not df_crm_deals_full.empty:
        if campo_busca_familia_principal in df_crm_deals_full.columns:
            # Preparar colunas para exibição nos resultados da busca
            df_crm_deals_full[campo_busca_familia_principal] = df_crm_deals_full[campo_busca_familia_principal].astype(str).fillna('')
            
            # Se houver termo de busca, filtrar resultados
            if termo_busca:
                resultados_busca_df = df_crm_deals_full[
                    df_crm_deals_full[campo_busca_familia_principal].str.contains(termo_busca, case=False, na=False)
                ].copy()
                
                # Limitar a 10 resultados para performance
                resultados_busca_df = resultados_busca_df.head(10)
                
                # Armazenar os resultados da busca na sessão
                st.session_state.resultados_busca = resultados_busca_df
                
                # Exibir resultados da busca
                if not resultados_busca_df.empty:
                    st.markdown(f"<div class='results-count'>Encontrados {len(resultados_busca_df)} resultados para '{termo_busca}'</div>", unsafe_allow_html=True)
                    
                    # Preparar dados para exibição em tabela amigável
                    dados_para_exibicao = []
                    
                    # Loop para gerar linhas da tabela
                    for idx, row in resultados_busca_df.iterrows():
                        nome_familia = row.get(campo_busca_familia_principal, "")
                        id_familia = row.get('UF_CRM_1722605592778', "N/D")
                        
                        # Tentar encontrar o nome de um requerente, se disponível
                        nome_requerente = "Não informado"
                        if 'UF_CRM_1723029889441' in row and row['UF_CRM_1723029889441']:
                            nome_requerente = row['UF_CRM_1723029889441']
                        elif 'TITLE' in row and row['TITLE']:
                            nome_requerente = row['TITLE']
                        
                        # Adicionar à lista de resultados para exibição
                        dados_para_exibicao.append({
                            "Nome da Família": nome_familia,
                            "ID da Família": id_familia,
                            "Requerente": nome_requerente
                        })
                    
                    # Criar DataFrame para exibição
                    df_resultados = pd.DataFrame(dados_para_exibicao)
                    
                    # Exibir resultados como uma tabela interativa
                    st.dataframe(
                        df_resultados,
                        column_config={
                            "Nome da Família": st.column_config.TextColumn("Nome da Família", width="large"),
                            "ID da Família": st.column_config.TextColumn("ID da Família", width="medium"),
                            "Requerente": st.column_config.TextColumn("Requerente", width="large")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Adicionar seletor na interface do Streamlit para capturar a seleção do usuário
                    familia_ids = resultados_busca_df['UF_CRM_1722605592778'].astype(str).tolist() if 'UF_CRM_1722605592778' in resultados_busca_df.columns else []
                    familia_nomes = resultados_busca_df[campo_busca_familia_principal].astype(str).tolist()
                    
                    # Criar opções para o seletor: "ID - Nome Família"
                    opcoes_selecao = []
                    for idx, id_familia in enumerate(familia_ids):
                        nome = familia_nomes[idx] if idx < len(familia_nomes) else "Família"
                        opcoes_selecao.append(f"{id_familia} - {nome}")
                    
                    if opcoes_selecao:
                        familia_selecionada_option = st.selectbox(
                            "👇 Selecione uma família para ver detalhes completos:",
                            options=["Selecione..."] + opcoes_selecao,
                            key="family_selector"
                        )
                        
                        if familia_selecionada_option != "Selecione...":
                            # Extrair o ID da família da opção selecionada
                            id_familia_selecionada = familia_selecionada_option.split(" - ")[0]
                            # DEBUG ADICIONADO
                            print(f"[DEBUG FILTRO EMISSOES] ID da Família Selecionada para filtrar emissões: '{id_familia_selecionada}' (Tipo: {type(id_familia_selecionada)})")
                            
                            # Obter os dados da família selecionada
                            familia_selecionada_data = resultados_busca_df[
                                resultados_busca_df['UF_CRM_1722605592778'].astype(str) == id_familia_selecionada
                            ].iloc[0]
                            
                            # Buscar emissões relacionadas à família selecionada
                            # ATUALIZADO: Usar nova função que carrega todos os pipelines
                            from views.cartorio_new.data_loader import load_data_all_pipelines
                            df_cartorio_completo = load_data_all_pipelines()
                            
                            campo_ligacao_emissoes = 'UF_CRM_34_ID_FAMILIA'
                            
                            if df_cartorio_completo is not None and not df_cartorio_completo.empty and campo_ligacao_emissoes in df_cartorio_completo.columns:
                                df_cartorio_completo[campo_ligacao_emissoes] = df_cartorio_completo[campo_ligacao_emissoes].astype(str).fillna('')
                                df_emissoes_filtradas = df_cartorio_completo[
                                    df_cartorio_completo[campo_ligacao_emissoes] == id_familia_selecionada
                                ].copy()
                            # DEBUG ADICIONADO
                            print(f"[DEBUG FILTRO EMISSOES] Número de emissões encontradas para a família ID '{id_familia_selecionada}': {len(df_emissoes_filtradas)}")
                            if not df_emissoes_filtradas.empty:
                                print("[DEBUG FILTRO EMISSOES] Primeiras 5 emissões filtradas (colunas relevantes):")
                                print(df_emissoes_filtradas[['TITLE', 'UF_CRM_34_ID_REQUERENTE', 'STAGE_ID', 'UF_CRM_34_ID_FAMILIA', 'NOME_PIPELINE']].head())
                            else:
                                print(f"[DEBUG FILTRO EMISSOES] Nenhuma emissão encontrada para o ID de família '{id_familia_selecionada}'. Verifique se este ID existe na coluna 'UF_CRM_34_ID_FAMILIA'.")
                                if df_cartorio_completo is not None and not df_cartorio_completo.empty and 'UF_CRM_34_ID_FAMILIA' in df_cartorio_completo.columns:
                                    print("[DEBUG FILTRO EMISSOES] Alguns IDs de família presentes:")
                                    print(df_cartorio_completo['UF_CRM_34_ID_FAMILIA'].unique()[:20]) # Mostra até 20 IDs únicos
                            
                            st.success(f"Família selecionada: {familia_selecionada_data.get(campo_busca_familia_principal, '')}")
                else:
                    st.info(f"Nenhuma família encontrada para '{termo_busca}'.")
        else:
            st.error(f"Coluna de busca '{campo_busca_familia_principal}' não existe nos dados do CRM.")
    elif df_crm_deals_full is None:
        st.error("Falha ao carregar dados do CRM.")
    
    st.markdown("---")
    
    if not familia_selecionada_data.empty:
        exibir_ficha_familia(familia_selecionada_data, df_emissoes_filtradas)
    else:
        if not termo_busca:
            exibir_metricas_macro()

# Para testar isoladamente (opcional)
if __name__ == '__main__':
    # Simular st.session_state se necessário para testes
    if 'pagina_atual' not in st.session_state:
        st.session_state['pagina_atual'] = "Ficha da Família"
    if 'emissao_subpagina' not in st.session_state:
        st.session_state.emissao_subpagina = 'Visão Geral'
    if 'comune_subpagina' not in st.session_state:
        st.session_state.comune_subpagina = 'Visão Geral'
        
    show_ficha_familia() 