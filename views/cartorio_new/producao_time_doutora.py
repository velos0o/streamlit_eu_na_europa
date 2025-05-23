import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Funções que podem ser úteis de utils.py (a serem importadas ou adaptadas)
# from .utils import simplificar_nome_estagio, fetch_supabase_producao_data, carregar_dados_usuarios_bitrix

# Temporariamente, vamos definir funções placeholder se não estiverem disponíveis em utils imediatamente
# ou se precisarmos de adaptações locais.

def carregar_dados_usuarios_bitrix_placeholder():
    # Placeholder: Retorna um DataFrame vazio ou com dados de exemplo
    # Idealmente, esta função virá de .utils
    print("[Placeholder] carregar_dados_usuarios_bitrix_placeholder chamada")
    return pd.DataFrame(columns=['ID', 'FULL_NAME'])

def fetch_supabase_producao_data_placeholder(data_inicio, data_fim):
    # Placeholder: Retorna um DataFrame vazio ou com dados de exemplo
    # Idealmente, esta função virá de .utils
    print(f"[Placeholder] fetch_supabase_producao_data_placeholder chamada com {data_inicio} a {data_fim}")
    # Colunas esperadas do Supabase, com base na descrição e no producao_adm.py
    # 'id', 'timestamp' (ou 'data_criacao'), 'id_card', 'id_familia', 
    # 'id_requerente', 'previous_stage_id', 'stage_id', 'movido_por_id'
    # SEMPRE RETORNAR UM DATAFRAME, MESMO QUE VAZIO
    return pd.DataFrame(columns=[
        'id', 'data_criacao', 'id_card', 'id_familia', 'id_requerente', 
        'previous_stage_id', 'stage_id', 'movido_por_id'
    ])

def simplificar_nome_estagio_placeholder(stage_id_completo, mapa_estagios_time_doutora):
    # Placeholder: Tenta simplificar o nome do estágio.
    # Idealmente, esta função virá de .utils ou será mais robusta.
    print(f"[Placeholder] simplificar_nome_estagio_placeholder chamada com {stage_id_completo}")
    if not isinstance(stage_id_completo, str):
        return "DESCONHECIDO"
    
    # Tenta encontrar no mapa fornecido
    if stage_id_completo in mapa_estagios_time_doutora:
        return mapa_estagios_time_doutora[stage_id_completo]

    # Lógica de fallback simples (pode ser expandida)
    parts = stage_id_completo.split(':')
    if len(parts) > 1:
        simplified_id = parts[-1]
        # Tenta encontrar a parte simplificada no mapa (se os valores do mapa forem simplificados)
        for key, value in mapa_estagios_time_doutora.items():
            if key.endswith(simplified_id):
                return value
        return simplified_id # Retorna a parte após ':' se não houver mapeamento direto
    return stage_id_completo

# --- FUNÇÃO DE SIMPLIFICAÇÃO LOCAL PARA TIME DOUTORA ---
def simplificar_nome_estagio_time_doutora(stage_id_completo, mapa_estagios_especifico):
    """ Simplifica o nome do estágio usando um mapa específico. """
    if not isinstance(stage_id_completo, str):
        return "DESCONHECIDO"
    
    # Tenta encontrar no mapa fornecido
    if stage_id_completo in mapa_estagios_especifico:
        return mapa_estagios_especifico[stage_id_completo]

    # Lógica de fallback simples (pode ser expandida)
    parts = stage_id_completo.split(':')
    if len(parts) > 1:
        simplified_id = parts[-1]
        # Tenta encontrar a parte simplificada no mapa (se os valores do mapa forem simplificados)
        for key, value in mapa_estagios_especifico.items():
            if key.endswith(simplified_id):
                return value
        return simplified_id # Retorna a parte após ':' se não houver mapeamento direto
    return stage_id_completo
# --- FIM FUNÇÃO DE SIMPLIFICAÇÃO LOCAL ---


# --- Constantes Específicas para o Time Doutora ---

# IDs dos usuários do "Time Doutora" (como strings)
IDS_USUARIOS_TIME_DOUTORA = [
    "178",  # Fernanda Santicioli
    "260",  # Nadya Pedroso
    "262",  # Stefany Valentin
    "270",  # Layla Lopes
    "286",  # Juliane Gonçalves
    "612",  # Bianca Lima
    "630",  # Felipe Paulino
    "632",  # Danyelle Santos
    "652"   # Angelica Santos
]
# Adicionar prefixo "user_" para compatibilidade com alguns formatos de ID
IDS_USUARIOS_TIME_DOUTORA_COM_PREFIXO = IDS_USUARIOS_TIME_DOUTORA + [f"user_{id_user}" for id_user in IDS_USUARIOS_TIME_DOUTORA]


# Estágio Inicial de onde a produção é medida
# MONTAGEM REQUERIMENTO CARTÓRIO - com base nos nomes reais do Supabase
STAGE_INICIAL_MONTAGEM_NOMES = [
    "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO",
    "EMISSÕES TATUAPÉ/MONTAGEM REQUERIMENTO CARTÓRIO"
]
# Nome simplificado para este estágio
NOME_SIMPLIFICADO_STAGE_INICIAL = "MONTAGEM REQUERIMENTO CARTÓRIO"

# Estágios de Ganho (Produção Positiva) - com base nos nomes reais do Supabase
STAGES_GANHO_NOMES = [
    "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
    "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM",
    "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE",
    "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE",
    "EMISSÕES CASA VERDE/AGUARDANDO CARTÓRIO ORIGEM",
    "EMISSÕES TATUAPÉ/AGUARDANDO CARTÓRIO ORIGEM",
    "EMISSÕES CASA VERDE/CERTIDÃO EMITIDA",
    "EMISSÕES TATUAPÉ/CERTIDÃO EMITIDA",
    "EMISSÕES CASA VERDE/CERTIDÃO ENTREGUE",
    "EMISSÕES TATUAPÉ/CERTIDÃO ENTREGUE"
]

# Mapeamento de nomes de ganho para simplificação
STAGES_GANHO_MAPEAMENTO = {
    "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM": "SOLICITAR CARTÓRIO DE ORIGEM",
    "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM": "SOLICITAR CARTÓRIO DE ORIGEM", 
    "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE": "SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE",
    "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE": "SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE",
    "EMISSÕES CASA VERDE/AGUARDANDO CARTÓRIO ORIGEM": "AGUARDANDO CARTÓRIO ORIGEM",
    "EMISSÕES TATUAPÉ/AGUARDANDO CARTÓRIO ORIGEM": "AGUARDANDO CARTÓRIO ORIGEM",
    "EMISSÕES CASA VERDE/CERTIDÃO EMITIDA": "CERTIDÃO EMITIDA",
    "EMISSÕES TATUAPÉ/CERTIDÃO EMITIDA": "CERTIDÃO EMITIDA",
    "EMISSÕES CASA VERDE/CERTIDÃO ENTREGUE": "CERTIDÃO ENTREGUE",
    "EMISSÕES TATUAPÉ/CERTIDÃO ENTREGUE": "CERTIDÃO ENTREGUE"
}
NOMES_STAGES_GANHO = list(set(STAGES_GANHO_MAPEAMENTO.values()))

# Estágios de Perca (Produção Negativa/Devolução) - com base nos nomes reais do Supabase
STAGES_PERCA_NOMES = [
    "EMISSÕES CASA VERDE/DEVOLUÇÃO ADM",
    "EMISSÕES TATUAPÉ/DEVOLUÇÃO ADM",
    "EMISSÕES CASA VERDE/DEVOLVIDO REQUERIMENTO",
    "EMISSÕES TATUAPÉ/DEVOLVIDO REQUERIMENTO"
]

# Mapeamento de nomes de perca para simplificação
STAGES_PERCA_MAPEAMENTO = {
    "EMISSÕES CASA VERDE/DEVOLUÇÃO ADM": "DEVOLUÇÃO ADM",
    "EMISSÕES TATUAPÉ/DEVOLUÇÃO ADM": "DEVOLUÇÃO ADM",
    "EMISSÕES CASA VERDE/DEVOLVIDO REQUERIMENTO": "DEVOLVIDO REQUERIMENTO",
    "EMISSÕES TATUAPÉ/DEVOLVIDO REQUERIMENTO": "DEVOLVIDO REQUERIMENTO"
}
NOMES_STAGES_PERCA = list(set(STAGES_PERCA_MAPEAMENTO.values()))

# Mapa Geral para simplificação (incluindo o inicial) - com base nos nomes reais do Supabase
MAPA_ESTAGIOS_TIME_DOUTORA = {
    # Estágios iniciais
    **{nome: NOME_SIMPLIFICADO_STAGE_INICIAL for nome in STAGE_INICIAL_MONTAGEM_NOMES},
    # Estágios de ganho
    **STAGES_GANHO_MAPEAMENTO,
    # Estágios de perca
    **STAGES_PERCA_MAPEAMENTO
}


# --- Configurações de Diretório e CSS (similar ao producao_adm.py) ---
_PRODUCAO_TIME_DOUTORA_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.join(_PRODUCAO_TIME_DOUTORA_DIR, '..', '..', 'assets')
_CSS_PATH = os.path.join(_ASSETS_DIR, 'styles', 'css', 'main.css') # Reutilizar o CSS principal

# Importar as funções reais de utils.py quando disponíveis
# Substituindo os placeholders. É importante que utils.py esteja no mesmo diretório
# ou que o Python path esteja configurado corretamente.
try:
    from .utils import simplificar_nome_estagio, fetch_supabase_producao_data, carregar_dados_usuarios_bitrix
    print("[Info] Funções de .utils carregadas com sucesso.")
except ImportError:
    print("[Alerta] Não foi possível importar de .utils. Usando placeholders.")
    simplificar_nome_estagio = simplificar_nome_estagio_placeholder
    fetch_supabase_producao_data = fetch_supabase_producao_data_placeholder
    carregar_dados_usuarios_bitrix = carregar_dados_usuarios_bitrix_placeholder


def exibir_producao_time_doutora(df_cartorio_original):
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
    
    st.markdown('<div class="cartorio-container cartorio-container--info">', unsafe_allow_html=True)
    st.title("Produção do Time da Doutora")

    # --- Carregar Mapa de Usuários ---
    df_usuarios = carregar_dados_usuarios_bitrix()
    mapa_nomes_usuarios_global = {}
    if not df_usuarios.empty and 'ID' in df_usuarios.columns and 'FULL_NAME' in df_usuarios.columns:
        df_usuarios['ID'] = df_usuarios['ID'].astype(str)
        mapa_nomes_usuarios_global = pd.Series(df_usuarios.FULL_NAME.values, index=df_usuarios.ID).to_dict()
        # Adicionar com prefixo "user_" para IDs do Supabase, se necessário
        for user_id_str, full_name in list(mapa_nomes_usuarios_global.items()):
            mapa_nomes_usuarios_global[f"user_{user_id_str}"] = full_name
            mapa_nomes_usuarios_global[user_id_str] = full_name # Garantir que o ID sem prefixo também mapeie
    else:
        st.warning("Mapeamento de nomes de usuário não disponível ou DataFrame de usuários inválido. IDs serão exibidos.")
        # Criar mapa com IDs para os usuários do time Doutora como fallback
        mapa_nomes_usuarios_global = {id_user: f"Usuário {id_user}" for id_user in IDS_USUARIOS_TIME_DOUTORA}
        mapa_nomes_usuarios_global.update({f"user_{id_user}": f"Usuário {id_user}" for id_user in IDS_USUARIOS_TIME_DOUTORA})


    # --- Filtros ---
    st.subheader("🗓️ Filtros para Análise de Produção")
    col_data1, col_data2 = st.columns(2)
    with col_data1:
        # Usar um período maior por padrão para capturar mais dados de teste
        data_inicio_analise = st.date_input("Data Inicial", value=datetime.now().date() - pd.Timedelta(days=30), key="doutora_data_inicio")
    with col_data2:
        data_fim_analise = st.date_input("Data Final", value=datetime.now().date(), key="doutora_data_fim")

    if data_inicio_analise > data_fim_analise:
        st.warning("A data inicial não pode ser posterior à data final.")
        return

    # Filtro por usuário do Time Doutora
    nomes_time_doutora_para_filtro = sorted([mapa_nomes_usuarios_global.get(id_user, f"ID {id_user}") for id_user in IDS_USUARIOS_TIME_DOUTORA])
    usuario_selecionado_nome = st.selectbox(
        "Filtrar por Usuário do Time Doutora",
        options=['Todos os Usuários'] + nomes_time_doutora_para_filtro,
        index=0,
        key="doutora_usuario_select"
    )

    st.info(f"""
    **Filtros Aplicados:**
    - Período: {data_inicio_analise.strftime('%d/%m/%Y')} a {data_fim_analise.strftime('%d/%m/%Y')}
    - Usuário: {usuario_selecionado_nome}
    """)
    st.markdown("---")

    # --- Carregar Dados do Supabase ---
    with st.spinner("Buscando registros de produção no Supabase..."):
        df_supabase_raw = fetch_supabase_producao_data(
            data_inicio_analise.strftime('%Y-%m-%d'),
            data_fim_analise.strftime('%Y-%m-%d')
        )

    if df_supabase_raw is None or df_supabase_raw.empty:
        st.warning("Nenhum dado de movimentação encontrado no Supabase para o período selecionado.")
        return

    df_movimentacoes = df_supabase_raw.copy()

    # --- Processamento dos Dados ---
    # Garantir que as colunas necessárias existem com verificação flexível
    cols_necessarias_base = ['data_criacao', 'id_card', 'movido_por_id']
    colunas_faltando = []

    # Verificar colunas básicas obrigatórias
    for col in cols_necessarias_base:
        if col not in df_movimentacoes.columns:
            colunas_faltando.append(col)

    # Verificar coluna de estágio atual (stage_id ou estagio_id)
    col_stage_atual = None
    if 'stage_id' in df_movimentacoes.columns:
        col_stage_atual = 'stage_id'
    elif 'estagio_id' in df_movimentacoes.columns:
        col_stage_atual = 'estagio_id'
    elif 'STAGE_ID' in df_movimentacoes.columns:
        col_stage_atual = 'STAGE_ID'
    else:
        colunas_faltando.append('stage_id (ou estagio_id)')

    # Verificar coluna de estágio anterior (previous_stage_id)
    col_stage_anterior = None
    if 'previous_stage_id' in df_movimentacoes.columns:
        col_stage_anterior = 'previous_stage_id'
    elif 'estagio_anterior_id' in df_movimentacoes.columns:
        col_stage_anterior = 'estagio_anterior_id'
    elif 'PREVIOUS_STAGE_ID' in df_movimentacoes.columns:
        col_stage_anterior = 'PREVIOUS_STAGE_ID'
    else:
        colunas_faltando.append('previous_stage_id')

    # Se há colunas faltando, mostrar erro
    if colunas_faltando:
        st.error(f"Colunas esperadas não encontradas nos dados do Supabase: {', '.join(colunas_faltando)}. Verifique a consulta em `fetch_supabase_producao_data`.")
        # --- INÍCIO DEBUG --- 
        print("--- DEBUG: Colunas FALTANDO em df_movimentacoes ---")
        print(f"Esperadas: {cols_necessarias_base + ['stage_id/estagio_id', 'previous_stage_id']}")
        print(f"Encontradas: {df_movimentacoes.columns.tolist()}")
        # --- FIM DEBUG ---
        return

    # Converter data_criacao para datetime
    df_movimentacoes['data_criacao'] = pd.to_datetime(df_movimentacoes['data_criacao'], errors='coerce')
    df_movimentacoes.dropna(subset=['data_criacao'], inplace=True) # Remover linhas onde a data não pôde ser convertida

    # Simplificar nomes dos estágios usando as colunas detectadas
    # Usar o MAPA_ESTAGIOS_TIME_DOUTORA para a simplificação
    df_movimentacoes['PREVIOUS_STAGE_NAME_SIMPLIFIED'] = df_movimentacoes[col_stage_anterior].apply(
        lambda x: simplificar_nome_estagio_time_doutora(x, MAPA_ESTAGIOS_TIME_DOUTORA) if pd.notna(x) else "N/A"
    )
    df_movimentacoes['CURRENT_STAGE_NAME_SIMPLIFIED'] = df_movimentacoes[col_stage_atual].apply(
        lambda x: simplificar_nome_estagio_time_doutora(x, MAPA_ESTAGIOS_TIME_DOUTORA) if pd.notna(x) else "N/A"
    )
    
    # --- INÍCIO DEBUG: Verificar simplificação do stage_id e previous_stage_id ---
    print("--- DEBUG: Amostra de df_movimentacoes APÓS simplificação de estágios ---")
    if not df_movimentacoes.empty:
        print(df_movimentacoes[['id_card', col_stage_anterior, 'PREVIOUS_STAGE_NAME_SIMPLIFIED', col_stage_atual, 'CURRENT_STAGE_NAME_SIMPLIFIED', 'movido_por_id']].head())
        # Verificar o registro específico do seu exemplo
        exemplo_card_id = '7092' # ID do card do seu exemplo SQL
        df_exemplo_card = df_movimentacoes[df_movimentacoes['id_card'] == exemplo_card_id]
        if not df_exemplo_card.empty:
            print(f"--- DEBUG: Detalhes do card {exemplo_card_id} em df_movimentacoes ---")
            print(df_exemplo_card[['data_criacao', 'id_card', col_stage_anterior, 'PREVIOUS_STAGE_NAME_SIMPLIFIED', col_stage_atual, 'CURRENT_STAGE_NAME_SIMPLIFIED', 'movido_por_id']])
        else:
            print(f"--- DEBUG: Card {exemplo_card_id} NÃO encontrado em df_movimentacoes após fetch e simplificação inicial.")
    else:
        print("df_movimentacoes está vazio APÓS simplificação de estágios.")
    # --- FIM DEBUG ---
    
    # Mapear ID do responsável para Nome
    df_movimentacoes['movido_por_nome'] = df_movimentacoes['movido_por_id'].astype(str).map(mapa_nomes_usuarios_global).fillna(df_movimentacoes['movido_por_id'])

    # 1. Filtrar pelas movimentações feitas pelos usuários do Time Doutora
    df_movimentacoes_time_doutora = df_movimentacoes[
        df_movimentacoes['movido_por_id'].astype(str).isin(IDS_USUARIOS_TIME_DOUTORA_COM_PREFIXO)
    ].copy()

    if df_movimentacoes_time_doutora.empty:
        st.info("Nenhuma movimentação encontrada para os usuários do Time Doutora no período.")
        return
        
    # Aplicar filtro de usuário selecionado (se não for "Todos os Usuários")
    if usuario_selecionado_nome != 'Todos os Usuários':
        df_movimentacoes_time_doutora = df_movimentacoes_time_doutora[
            df_movimentacoes_time_doutora['movido_por_nome'] == usuario_selecionado_nome
        ]
        if df_movimentacoes_time_doutora.empty:
            st.info(f"Nenhuma movimentação encontrada para o usuário '{usuario_selecionado_nome}' no período.")
            return

    # --- INÍCIO DEBUG: Verificar df_movimentacoes_time_doutora ANTES de filtrar por estágio inicial ---
    print("--- DEBUG: Amostra de df_movimentacoes_time_doutora ANTES do filtro de estágio inicial ---")
    if not df_movimentacoes_time_doutora.empty:
        print(df_movimentacoes_time_doutora[['id_card', 'PREVIOUS_STAGE_NAME_SIMPLIFIED', 'movido_por_id', 'movido_por_nome']].head())
        df_exemplo_card_time_doutora = df_movimentacoes_time_doutora[df_movimentacoes_time_doutora['id_card'] == exemplo_card_id]
        if not df_exemplo_card_time_doutora.empty:
            print(f"--- DEBUG: Detalhes do card {exemplo_card_id} em df_movimentacoes_time_doutora ---")
            print(df_exemplo_card_time_doutora[['data_criacao', 'id_card', col_stage_anterior, 'PREVIOUS_STAGE_NAME_SIMPLIFIED', col_stage_atual, 'CURRENT_STAGE_NAME_SIMPLIFIED', 'movido_por_id', 'movido_por_nome']])
        else:
            print(f"--- DEBUG: Card {exemplo_card_id} NÃO encontrado em df_movimentacoes_time_doutora (após filtro de usuário/time).")
    else:
        print("df_movimentacoes_time_doutora está vazio ANTES do filtro de estágio inicial.")
    print(f"--- DEBUG: NOME_SIMPLIFICADO_STAGE_INICIAL esperado: '{NOME_SIMPLIFICADO_STAGE_INICIAL}'")
    # --- FIM DEBUG ---

    # 2. LÓGICA CORRIGIDA: Montagens concluídas 
    # CASO 1: Cards que SAÍRAM de "MONTAGEM REQUERIMENTO CARTÓRIO" e FORAM para "SOLICITAR CARTÓRIO"
    df_montagens_de_montagem = df_movimentacoes_time_doutora[
        (df_movimentacoes_time_doutora[col_stage_anterior].isin(STAGE_INICIAL_MONTAGEM_NOMES)) &
        (df_movimentacoes_time_doutora[col_stage_atual].isin([
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE"
        ]))
    ]
    
    # CASO 2: Cards que SAÍRAM de "DEVOLVIDO REQUERIMENTO" e FORAM para "SOLICITAR CARTÓRIO"
    df_montagens_de_devolvido = df_movimentacoes_time_doutora[
        (df_movimentacoes_time_doutora[col_stage_anterior].isin([
            "EMISSÕES CASA VERDE/DEVOLVIDO REQUERIMENTO",
            "EMISSÕES TATUAPÉ/DEVOLVIDO REQUERIMENTO"
        ])) &
        (df_movimentacoes_time_doutora[col_stage_atual].isin([
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE"
        ]))
    ]

    # UNIR OS DOIS CASOS (com tratamento para DataFrames vazios)
    dfs_montagens = [df for df in [df_montagens_de_montagem, df_montagens_de_devolvido] if not df.empty]
    if dfs_montagens:
        df_montagens_concluidas = pd.concat(dfs_montagens).drop_duplicates().copy()
    else:
        df_montagens_concluidas = pd.DataFrame().copy()

    # 2.1. NOVA MÉTRICA: Total de solicitações realizadas (independente da origem)
    df_solicitacoes_realizadas = df_movimentacoes_time_doutora[
        df_movimentacoes_time_doutora[col_stage_atual].isin([
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE"
        ])
    ].copy()
    
    # 3. Categorizar TODAS as movimentações do time em Ganhos e Perdas
    df_ganhos = df_movimentacoes_time_doutora[
        df_movimentacoes_time_doutora[col_stage_atual].isin(STAGES_GANHO_NOMES)
    ].copy()
    
    df_perdas = df_movimentacoes_time_doutora[
        df_movimentacoes_time_doutora[col_stage_atual].isin(STAGES_PERCA_NOMES)
    ].copy()

    # --- MÉTRICAS PRINCIPAIS ---
    st.subheader("📊 Produção - Time Doutora")

    total_montagens_realizadas = len(df_montagens_concluidas)
    total_solicitacoes_realizadas = len(df_solicitacoes_realizadas)

    # MÉTRICAS SIMPLES E CLARAS
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.metric("🎯 Montagens Realizadas", f"{total_montagens_realizadas}", 
                 help="Montagens concluídas (saiu de MONTAGEM→SOLICITAR ou saiu de DEVOLVIDO→SOLICITAR)")
    with col_metric2:
        st.metric("📨 Solicitações Realizadas", f"{total_solicitacoes_realizadas}",
                 help="Total de solicitações ao cartório (todas as origens)")

    st.markdown("---")

    # TABELAS PRINCIPAIS - SIMPLES E CLARAS
    col_tab1, col_tab2 = st.columns(2)
    
    with col_tab1:
        st.markdown("### 🎯 Quem Realizou Montagens")
        if not df_montagens_concluidas.empty:
            df_montagens_simples = df_montagens_concluidas.groupby('movido_por_nome').size().reset_index(name='Montagens')
            df_montagens_simples = df_montagens_simples.sort_values('Montagens', ascending=False)
            st.dataframe(df_montagens_simples, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma montagem encontrada.")
    
    with col_tab2:
        st.markdown("### 📨 Quem Realizou Solicitações")
        if not df_solicitacoes_realizadas.empty:
            df_solicitacoes_simples = df_solicitacoes_realizadas.groupby('movido_por_nome').size().reset_index(name='Solicitações')
            df_solicitacoes_simples = df_solicitacoes_simples.sort_values('Solicitações', ascending=False)
            st.dataframe(df_solicitacoes_simples, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma solicitação encontrada.")

    # TABELA DE DETALHES - REGISTRO DO BANCO
    st.markdown("---")
    with st.expander("📋 Detalhes dos Registros no Banco", expanded=False):
        st.markdown("### 🎯 Montagens Realizadas - Registros do Banco")
        if not df_montagens_concluidas.empty:
            # Preparar dados simples e claros
            df_detalhes_montagens = df_montagens_concluidas.copy()
            df_detalhes_montagens['Data/Hora'] = pd.to_datetime(df_detalhes_montagens['data_criacao']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Tabela limpa
            df_detalhes_display = df_detalhes_montagens[[
                'id_card', 'Data/Hora', 'movido_por_nome', col_stage_anterior, col_stage_atual
            ]].copy()
            
            df_detalhes_display.rename(columns={
                'id_card': 'ID Card',
                'movido_por_nome': 'Quem Movimentou',
                col_stage_anterior: 'Etapa Anterior', 
                col_stage_atual: 'Etapa Atual'
            }, inplace=True)
            
            # Filtro simples
            usuarios_montagem = ['Todos'] + sorted(df_detalhes_display['Quem Movimentou'].unique().tolist())
            usuario_filtro_montagem = st.selectbox("Filtrar montagens por usuário:", usuarios_montagem, key="filtro_montagem_user")
            
            if usuario_filtro_montagem != 'Todos':
                df_detalhes_display = df_detalhes_display[df_detalhes_display['Quem Movimentou'] == usuario_filtro_montagem]
            
            st.dataframe(df_detalhes_display.sort_values('Data/Hora', ascending=False), use_container_width=True, hide_index=True)
            st.caption(f"💡 {len(df_detalhes_display)} registros de montagens concluídas")
        else:
            st.info("Nenhuma montagem encontrada.")
            
        st.markdown("### 📨 Solicitações Realizadas - Registros do Banco") 
        if not df_solicitacoes_realizadas.empty:
            # Preparar dados simples e claros
            df_detalhes_solicitacoes = df_solicitacoes_realizadas.copy()
            df_detalhes_solicitacoes['Data/Hora'] = pd.to_datetime(df_detalhes_solicitacoes['data_criacao']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Tabela limpa
            df_detalhes_sol_display = df_detalhes_solicitacoes[[
                'id_card', 'Data/Hora', 'movido_por_nome', col_stage_anterior, col_stage_atual
            ]].copy()
            
            df_detalhes_sol_display.rename(columns={
                'id_card': 'ID Card',
                'movido_por_nome': 'Quem Movimentou',
                col_stage_anterior: 'Etapa Anterior',
                col_stage_atual: 'Etapa Atual'
            }, inplace=True)
            
            # Filtro simples
            usuarios_solicitacao = ['Todos'] + sorted(df_detalhes_sol_display['Quem Movimentou'].unique().tolist())
            usuario_filtro_solicitacao = st.selectbox("Filtrar solicitações por usuário:", usuarios_solicitacao, key="filtro_solicitacao_user")
            
            if usuario_filtro_solicitacao != 'Todos':
                df_detalhes_sol_display = df_detalhes_sol_display[df_detalhes_sol_display['Quem Movimentou'] == usuario_filtro_solicitacao]
            
            st.dataframe(df_detalhes_sol_display.sort_values('Data/Hora', ascending=False), use_container_width=True, hide_index=True)
            st.caption(f"💡 {len(df_detalhes_sol_display)} registros de solicitações realizadas")
        else:
            st.info("Nenhuma solicitação encontrada.")

    # RESUMO FINAL
    st.markdown("---")
    st.info(f"""
    💡 **Resumo:**
    - **Montagens Realizadas:** {total_montagens_realizadas} (saíram de MONTAGEM→SOLICITAR ou saíram de DEVOLVIDO→SOLICITAR)
    - **Solicitações Realizadas:** {total_solicitacoes_realizadas} (todas as solicitações ao cartório)
    - **Período:** {data_inicio_analise.strftime('%d/%m/%Y')} a {data_fim_analise.strftime('%d/%m/%Y')}
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha cartorio-container

if __name__ == '__main__':
    # Para testar o módulo isoladamente (requer um contexto Streamlit simulado ou dados de exemplo)
    # st.set_page_config(layout="wide")
    
    # Simular df_cartorio_original_bitrix se necessário para carregar usuários
    mock_df_usuarios = pd.DataFrame({
        'ID': ["178", "260", "262", "270", "286", "612", "630", "632", "652", "999"],
        'FULL_NAME': [
            "Fernanda Santicioli", "Nadya Pedroso", "Stefany Valentin", "Layla Lopes", 
            "Juliane Gonçalves", "Bianca Lima", "Felipe Paulino", "Danyelle Santos", 
            "Angelica Santos", "Usuário Teste Extra"
        ]
    })

    # Sobrescrever a função de carregar usuários para o teste
    original_carregar_dados_usuarios_bitrix = carregar_dados_usuarios_bitrix
    carregar_dados_usuarios_bitrix = lambda: mock_df_usuarios
    
    # Sobrescrever a função de fetch do Supabase para o teste
    def mock_fetch_supabase_producao_data(data_inicio, data_fim):
        print(f"Mock fetch supabase: {data_inicio} a {data_fim}")
        # Dados de exemplo para teste
        data = {
            'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'data_criacao': pd.to_datetime([
                '2023-10-01 10:00:00', '2023-10-01 11:00:00', '2023-10-02 09:00:00',
                '2023-10-02 14:00:00', '2023-10-03 10:00:00', '2023-10-03 12:00:00',
                '2023-10-04 10:00:00', '2023-10-04 11:00:00', '2023-10-05 09:00:00',
                '2023-10-05 14:00:00', '2023-10-06 10:00:00', '2023-10-06 12:00:00'
            ]),
            'id_card': ['C1', 'C2', 'C3', 'C1', 'C4', 'C2', 'C5', 'C6', 'C7', 'C5', 'C8', 'C9'],
            'previous_stage_id': [ # Estágio de onde saiu
                "DT1098_92:UC_ZWO7BI", # Montagem Req -> Ganho (Fernanda)
                "DT1098_94:UC_UZHXWF", # Montagem Req -> Perca (Nadya)
                "DT1098_92:OTHER_STAGE", # Outro estágio
                "DT1098_92:UC_ZWO7BI", # Montagem Req -> Ganho Prioridade (Fernanda)
                "DT1098_94:UC_UZHXWF", # Montagem Req -> Certidão Emitida (Stefany)
                "DT1098_92:UC_ZWO7BI", # Montagem Req -> Devolução ADM (Layla)
                "DT1098_92:UC_ZWO7BI", # Montagem Req -> Ganho (Bianca)
                "DT1098_94:UC_UZHXWF", # Montagem Req -> Perca (Felipe)
                "DT1098_92:OTHER_STAGE", # Outro estágio
                "DT1098_92:UC_ZWO7BI", # Montagem Req -> Ganho Prioridade (Danyelle)
                "DT1098_94:UC_UZHXWF", # Montagem Req -> Certidão Emitida (Angelica)
                "DT1098_92:UC_ZWO7BI", # Montagem Req -> Devolução ADM (Juliane)
            ],
            'stage_id': [ # Estágio para onde foi
                "DT1098_92:UC_83ZGKS",  # SOLICITAR CARTÓRIO DE ORIGEM
                "DT1098_94:UC_M6A09E",  # DEVOLVIDO REQUERIMENTO
                "DT1098_92:UC_83ZGKS",
                "DT1098_92:UC_6TECYL",  # SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE
                "DT1098_94:UC_K4JS04",  # CERTIDÃO EMITIDA
                "DT1098_92:UC_EYBGVD",  # DEVOLUÇÃO ADM
                "DT1098_92:UC_83ZGKS",  # SOLICITAR CARTÓRIO DE ORIGEM
                "DT1098_94:UC_M6A09E",  # DEVOLVIDO REQUERIMENTO
                "DT1098_92:UC_83ZGKS",
                "DT1098_92:UC_6TECYL",  # SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE
                "DT1098_94:UC_K4JS04",  # CERTIDÃO EMITIDA
                "DT1098_92:UC_EYBGVD",  # DEVOLUÇÃO ADM
            ],
            'movido_por_id': [ # Quem moveu
                "178", "260", "178", "user_178", "262", 
                "270", "612", "630", "630", "user_632", 
                "652", "286"
            ],
            'id_familia': ['F1','F2','F3','F1','F4','F2','F5','F6','F7','F5','F8','F9'],
            'id_requerente': ['R1','R2','R3','R1','R4','R2','R5','R6','R7','R5','R8','R9']
        }
        return pd.DataFrame(data)

    original_fetch_supabase = fetch_supabase_producao_data
    fetch_supabase_producao_data = mock_fetch_supabase_producao_data
    
    # Chamada da função principal para teste
    exibir_producao_time_doutora(None) # Passando None para df_cartorio_original_bitrix
    
    # Restaurar funções originais se necessário após o teste
    carregar_dados_usuarios_bitrix = original_carregar_dados_usuarios_bitrix
    fetch_supabase_producao_data = original_fetch_supabase 