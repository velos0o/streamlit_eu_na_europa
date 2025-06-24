import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.dataframe_utils import ensure_pandas_df

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
    "652",  # Angelica Santos
    "282"   # Jhenifer
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


    # --- FILTROS ---
    with st.expander("🔍 Filtros", expanded=True):
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns([0.25, 0.25, 0.25, 0.25])
        
        with col_filtro1:
            st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
            st.markdown('<label class="filtro-label">Data Inicial</label>', unsafe_allow_html=True)
            data_inicio_analise = st.date_input("", value=datetime.now().date() - pd.Timedelta(days=30), key="doutora_data_inicio", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_filtro2:
            st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
            st.markdown('<label class="filtro-label">Data Final</label>', unsafe_allow_html=True)
            data_fim_analise = st.date_input("", value=datetime.now().date(), key="doutora_data_fim", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_filtro3:
            st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
            st.markdown('<label class="filtro-label">Usuário do Time Doutora</label>', unsafe_allow_html=True)
            # Filtro por usuário do Time Doutora
            nomes_time_doutora_para_filtro = sorted([mapa_nomes_usuarios_global.get(id_user, f"ID {id_user}") for id_user in IDS_USUARIOS_TIME_DOUTORA])
            usuario_selecionado_nome = st.selectbox(
                "",  # Label vazio pois usamos HTML
                options=['Todos os Usuários'] + nomes_time_doutora_para_filtro,
                index=0,
                key="doutora_usuario_select",
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_filtro4:
            st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
            st.markdown('<label class="filtro-label">Protocolizado</label>', unsafe_allow_html=True)
            # Filtro de Protocolizado
            coluna_protocolizado = 'UF_CRM_34_PROTOCOLIZADO'
            filtro_protocolizado_habilitado = coluna_protocolizado in df_cartorio_original.columns if df_cartorio_original is not None else False
            if filtro_protocolizado_habilitado:
                filtro_protocolizado = st.selectbox(
                    "",  # Label vazio pois usamos HTML
                    options=["Todos", "Protocolizado", "Não Protocolizado"],
                    index=0,
                    key="filtro_protocolizado_time_doutora",
                    label_visibility="collapsed"
                )
            else:
                st.caption(f":warning: Campo protocolizado não encontrado.")
                filtro_protocolizado = "Todos"
            st.markdown('</div>', unsafe_allow_html=True)

    if data_inicio_analise > data_fim_analise:
        st.warning("A data inicial não pode ser posterior à data final.")
        return

    st.info(f"""
    **Filtros Aplicados:**
    - Período: {data_inicio_analise.strftime('%d/%m/%Y')} a {data_fim_analise.strftime('%d/%m/%Y')}
    - Usuário: {usuario_selecionado_nome}
    - Protocolizado: {filtro_protocolizado}
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

    # Aplicar filtro de Protocolizado se o DataFrame original estiver disponível
    if df_cartorio_original is not None and filtro_protocolizado != "Todos" and filtro_protocolizado_habilitado:
        if coluna_protocolizado in df_cartorio_original.columns:
            # Converter para string e normalizar valores
            df_cartorio_original[coluna_protocolizado] = df_cartorio_original[coluna_protocolizado].fillna('').astype(str).str.strip().str.upper()
            
            # Criar um conjunto de IDs que atendem ao critério de protocolização
            if filtro_protocolizado == "Protocolizado":
                # Consideramos como protocolizado: "Y", "YES", "1", "TRUE", "SIM"
                ids_protocolizados = set(df_cartorio_original[df_cartorio_original[coluna_protocolizado].isin(['Y', 'YES', '1', 'TRUE', 'SIM'])]['ID'].astype(str))
            else:  # "Não Protocolizado"
                # Consideramos como não protocolizado: "N", "NO", "0", "FALSE", "NÃO", valores vazios
                ids_protocolizados = set(df_cartorio_original[~df_cartorio_original[coluna_protocolizado].isin(['Y', 'YES', '1', 'TRUE', 'SIM']) | (df_cartorio_original[coluna_protocolizado] == '')]['ID'].astype(str))
            
            # Filtrar df_movimentacoes para incluir apenas os IDs que atendem ao critério
            df_movimentacoes = df_movimentacoes[df_movimentacoes['id_card'].astype(str).isin(ids_protocolizados)]
            
            if df_movimentacoes.empty:
                st.warning(f"Nenhum registro encontrado para o filtro de protocolizado: {filtro_protocolizado}")
                return
        else:
            st.warning(f"Coluna {coluna_protocolizado} não encontrada ao aplicar filtro de protocolizado.")

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

    # 2.1. RENOMEADA: Total de solicitações realizadas (independente da origem) -> PRODUÇÃO
    df_producao_realizadas = df_movimentacoes_time_doutora[
        df_movimentacoes_time_doutora[col_stage_atual].isin([
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE"
        ])
    ].copy()
    
    # 2.2. NOVA MÉTRICA: Solicitação Cartório (SOLICITAR CARTÓRIO → AGUARDANDO CARTÓRIO)
    # ATENÇÃO: Esta métrica NÃO usa filtro do time doutora, pois quem faz essa movimentação é outro setor
    df_solicitacao_cartorio = df_movimentacoes[  # <- Usar df_movimentacoes (TODOS os dados) em vez de df_movimentacoes_time_doutora
        (df_movimentacoes[col_stage_anterior].isin([
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM",
            "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
            "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE"
        ])) &
        (df_movimentacoes[col_stage_atual].isin([
            "EMISSÕES CASA VERDE/AGUARDANDO CARTÓRIO ORIGEM",
            "EMISSÕES TATUAPÉ/AGUARDANDO CARTÓRIO ORIGEM"
        ]))
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
    total_producao_realizadas = len(df_producao_realizadas)
    total_solicitacao_cartorio = len(df_solicitacao_cartorio)

    # Criar métricas customizadas com HTML puro
    st.markdown(f"""
    <style>
    .metrica-custom-doutora {{
        background: #F8F9FA;
        border: 2px solid #DEE2E6;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    
    .metrica-custom-doutora:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #ADB5BD;
    }}
    
    .metrica-custom-doutora .label {{
        color: #6C757D;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        line-height: 1.2;
    }}
    
    .metrica-custom-doutora .valor {{
        color: #495057;
        font-weight: 700;
        font-size: 30px;
        line-height: 1.2;
        margin-bottom: 4px;
    }}
    
    .metrica-custom-doutora .help {{
        font-size: 10px;
        color: #6C757D;
        margin-top: 4px;
        font-style: italic;
    }}
    
    .metricas-container-doutora {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }}
    </style>
    
    <div class="metricas-container-doutora">
        <div class="metrica-custom-doutora">
            <div class="label">🎯 Montagens Realizadas</div>
            <div class="valor">{total_montagens_realizadas:,}</div>
            <div class="help">Montagens concluídas (saiu de MONTAGEM→SOLICITAR ou saiu de DEVOLVIDO→SOLICITAR)</div>
        </div>
        <div class="metrica-custom-doutora">
            <div class="label">📊 Produção</div>
            <div class="valor">{total_producao_realizadas:,}</div>
            <div class="help">Total de produção ao cartório (todas as origens)</div>
        </div>
        <div class="metrica-custom-doutora">
            <div class="label">📨 Solicitação Cartório</div>
            <div class="valor">{total_solicitacao_cartorio:,}</div>
            <div class="help">Conversão de solicitações (saiu de SOLICITAR→AGUARDANDO) - TODOS os setores</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # TABELAS PRINCIPAIS - SIMPLES E CLARAS
    col_tab1, col_tab2, col_tab3 = st.columns(3)
    
    with col_tab1:
        st.markdown("### 🎯 Quem Realizou Montagens")
        if not df_montagens_concluidas.empty:
            df_montagens_simples = df_montagens_concluidas.groupby('movido_por_nome').size().reset_index(name='Montagens')
            df_montagens_simples = df_montagens_simples.sort_values('Montagens', ascending=False)
            st.dataframe(df_montagens_simples, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma montagem encontrada.")
    
    with col_tab2:
        st.markdown("### 📊 Quem Realizou Produção")
        if not df_producao_realizadas.empty:
            df_producao_simples = df_producao_realizadas.groupby('movido_por_nome').size().reset_index(name='Produção')
            df_producao_simples = df_producao_simples.sort_values('Produção', ascending=False)
            st.dataframe(df_producao_simples, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma produção encontrada.")
    
    with col_tab3:
        st.markdown("### 📨 Quem Realizou Solicitação Cartório")
        if not df_solicitacao_cartorio.empty:
            # Mapear nomes dos usuários (incluindo outros setores, não só time doutora)
            df_solicitacao_cartorio['movido_por_nome'] = df_solicitacao_cartorio['movido_por_id'].astype(str).map(mapa_nomes_usuarios_global).fillna(df_solicitacao_cartorio['movido_por_id'])
            
            df_solicitacao_simples = df_solicitacao_cartorio.groupby('movido_por_nome').size().reset_index(name='Solicitações')
            df_solicitacao_simples = df_solicitacao_simples.sort_values('Solicitações', ascending=False)
            st.dataframe(df_solicitacao_simples, use_container_width=True, hide_index=True)
            st.caption("💡 Inclui usuários de todos os setores (não apenas Time Doutora)")
        else:
            st.info("Nenhuma solicitação cartório encontrada.")

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
            
        st.markdown("### 📨 Produção Realizadas - Registros do Banco") 
        if not df_producao_realizadas.empty:
            # Preparar dados simples e claros
            df_detalhes_producao = df_producao_realizadas.copy()
            df_detalhes_producao['Data/Hora'] = pd.to_datetime(df_detalhes_producao['data_criacao']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Tabela limpa
            df_detalhes_prod_display = df_detalhes_producao[[
                'id_card', 'Data/Hora', 'movido_por_nome', col_stage_anterior, col_stage_atual
            ]].copy()
            
            df_detalhes_prod_display.rename(columns={
                'id_card': 'ID Card',
                'movido_por_nome': 'Quem Movimentou',
                col_stage_anterior: 'Etapa Anterior',
                col_stage_atual: 'Etapa Atual'
            }, inplace=True)
            
            # Filtro simples
            usuarios_producao = ['Todos'] + sorted(df_detalhes_prod_display['Quem Movimentou'].unique().tolist())
            usuario_filtro_producao = st.selectbox("Filtrar produção por usuário:", usuarios_producao, key="filtro_producao_user")
            
            if usuario_filtro_producao != 'Todos':
                df_detalhes_prod_display = df_detalhes_prod_display[df_detalhes_prod_display['Quem Movimentou'] == usuario_filtro_producao]
            
            st.dataframe(df_detalhes_prod_display.sort_values('Data/Hora', ascending=False), use_container_width=True, hide_index=True)
            st.caption(f"💡 {len(df_detalhes_prod_display)} registros de produção realizadas")
        else:
            st.info("Nenhuma produção encontrada.")

        st.markdown("### 📨 Solicitação Cartório - Registros do Banco") 
        if not df_solicitacao_cartorio.empty:
            # Preparar dados simples e claros
            df_detalhes_solicitacao_cartorio = df_solicitacao_cartorio.copy()
            # Garantir que o mapeamento de nomes esteja aplicado
            df_detalhes_solicitacao_cartorio['movido_por_nome'] = df_detalhes_solicitacao_cartorio['movido_por_id'].astype(str).map(mapa_nomes_usuarios_global).fillna(df_detalhes_solicitacao_cartorio['movido_por_id'])
            df_detalhes_solicitacao_cartorio['Data/Hora'] = pd.to_datetime(df_detalhes_solicitacao_cartorio['data_criacao']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Tabela limpa
            df_detalhes_solic_display = df_detalhes_solicitacao_cartorio[[
                'id_card', 'Data/Hora', 'movido_por_nome', col_stage_anterior, col_stage_atual
            ]].copy()
            
            df_detalhes_solic_display.rename(columns={
                'id_card': 'ID Card',
                'movido_por_nome': 'Quem Movimentou',
                col_stage_anterior: 'Etapa Anterior',
                col_stage_atual: 'Etapa Atual'
            }, inplace=True)
            
            # Filtro simples
            usuarios_solicitacao_cartorio = ['Todos'] + sorted(df_detalhes_solic_display['Quem Movimentou'].unique().tolist())
            usuario_filtro_solicitacao_cartorio = st.selectbox("Filtrar solicitações cartório por usuário:", usuarios_solicitacao_cartorio, key="filtro_solicitacao_cartorio_user")
            
            if usuario_filtro_solicitacao_cartorio != 'Todos':
                df_detalhes_solic_display = df_detalhes_solic_display[df_detalhes_solic_display['Quem Movimentou'] == usuario_filtro_solicitacao_cartorio]
            
            st.dataframe(df_detalhes_solic_display.sort_values('Data/Hora', ascending=False), use_container_width=True, hide_index=True)
            st.caption(f"💡 {len(df_detalhes_solic_display)} registros de solicitações cartório realizadas (todos os setores)")
        else:
            st.info("Nenhuma solicitação cartório encontrada.")

    # RESUMO FINAL
    st.markdown("---")
    st.info(f"""
    💡 **Resumo:**
    - **Montagens Realizadas:** {total_montagens_realizadas} (Time Doutora: saíram de MONTAGEM→SOLICITAR ou saíram de DEVOLVIDO→SOLICITAR)
    - **Produção:** {total_producao_realizadas} (Time Doutora: todas as solicitações ao cartório)
    - **Solicitação Cartório:** {total_solicitacao_cartorio} (Todos os setores: conversão saíram de SOLICITAR→AGUARDANDO)
    - **Período:** {data_inicio_analise.strftime('%d/%m/%Y')} a {data_fim_analise.strftime('%d/%m/%Y')}
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha cartorio-container

if __name__ == '__main__':
    # Para testar o módulo isoladamente (requer um contexto Streamlit simulado ou dados de exemplo)
    # st.set_page_config(layout="wide")
    
    # Simular df_cartorio_original_bitrix se necessário para carregar usuários
    mock_df_usuarios = pd.DataFrame({
        'ID': ["178", "260", "262", "270", "286", "612", "630", "632", "652", "999", "888", "777"],
        'FULL_NAME': [
            "Fernanda Santicioli", "Nadya Pedroso", "Stefany Valentin", "Layla Lopes", 
            "Juliane Gonçalves", "Bianca Lima", "Felipe Paulino", "Danyelle Santos", 
            "Angelica Santos", "Usuário Outro Setor A", "Usuário Outro Setor B", "Usuário Outro Setor C"
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
            'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            'data_criacao': pd.to_datetime([
                '2023-10-01 10:00:00', '2023-10-01 11:00:00', '2023-10-02 09:00:00',
                '2023-10-02 14:00:00', '2023-10-03 10:00:00', '2023-10-03 12:00:00',
                '2023-10-04 10:00:00', '2023-10-04 11:00:00', '2023-10-05 09:00:00',
                '2023-10-05 14:00:00', '2023-10-06 10:00:00', '2023-10-06 12:00:00',
                '2023-10-07 10:00:00', '2023-10-07 14:00:00', '2023-10-08 11:00:00'
            ]),
            'id_card': ['C1', 'C2', 'C3', 'C1', 'C4', 'C2', 'C5', 'C6', 'C7', 'C5', 'C8', 'C9', 'C10', 'C11', 'C12'],
            'previous_stage_id': [ # Estágio de onde saiu
                "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Ganho (Fernanda)
                "EMISSÕES TATUAPÉ/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Perca (Nadya)
                "EMISSÕES CASA VERDE/OUTRO ESTÁGIO", # Outro estágio
                "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Ganho Prioridade (Fernanda)
                "EMISSÕES TATUAPÉ/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Certidão Emitida (Stefany)
                "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Devolução ADM (Layla)
                "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Ganho (Bianca)
                "EMISSÕES TATUAPÉ/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Perca (Felipe)
                "EMISSÕES CASA VERDE/OUTRO ESTÁGIO", # Outro estágio
                "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Ganho Prioridade (Danyelle)
                "EMISSÕES TATUAPÉ/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Certidão Emitida (Angelica)
                "EMISSÕES CASA VERDE/MONTAGEM REQUERIMENTO CARTÓRIO", # Montagem Req -> Devolução ADM (Juliane)
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM", # SOLICITAR CARTÓRIO -> AGUARDANDO (nova métrica)
                "EMISSÕES TATUAPÉ/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", # SOLICITAR PRIORIDADE -> AGUARDANDO (nova métrica)
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM", # SOLICITAR CARTÓRIO -> AGUARDANDO (nova métrica)
            ],
            'stage_id': [ # Estágio para onde foi
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",  # SOLICITAR CARTÓRIO DE ORIGEM
                "EMISSÕES TATUAPÉ/DEVOLVIDO REQUERIMENTO",  # DEVOLVIDO REQUERIMENTO
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE",  # SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE
                "EMISSÕES TATUAPÉ/CERTIDÃO EMITIDA",  # CERTIDÃO EMITIDA
                "EMISSÕES CASA VERDE/DEVOLUÇÃO ADM",  # DEVOLUÇÃO ADM
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",  # SOLICITAR CARTÓRIO DE ORIGEM
                "EMISSÕES TATUAPÉ/DEVOLVIDO REQUERIMENTO",  # DEVOLVIDO REQUERIMENTO
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM",
                "EMISSÕES CASA VERDE/SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE",  # SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE
                "EMISSÕES TATUAPÉ/CERTIDÃO EMITIDA",  # CERTIDÃO EMITIDA
                "EMISSÕES CASA VERDE/DEVOLUÇÃO ADM",  # DEVOLUÇÃO ADM
                "EMISSÕES CASA VERDE/AGUARDANDO CARTÓRIO ORIGEM",  # AGUARDANDO CARTÓRIO ORIGEM (nova métrica)
                "EMISSÕES TATUAPÉ/AGUARDANDO CARTÓRIO ORIGEM",  # AGUARDANDO CARTÓRIO ORIGEM (nova métrica)
                "EMISSÕES CASA VERDE/AGUARDANDO CARTÓRIO ORIGEM",  # AGUARDANDO CARTÓRIO ORIGEM (nova métrica)
            ],
            'movido_por_id': [ # Quem moveu
                "178", "260", "178", "user_178", "262", 
                "270", "612", "630", "630", "user_632", 
                "652", "286", "user_999", "user_888", "777"  # <- Incluir usuários de outros setores para SOLICITAR→AGUARDANDO
            ],
            'id_familia': ['F1','F2','F3','F1','F4','F2','F5','F6','F7','F5','F8','F9','F10','F11','F12'],
            'id_requerente': ['R1','R2','R3','R1','R4','R2','R5','R6','R7','R5','R8','R9','R10','R11','R12']
        }
        return pd.DataFrame(data)

    original_fetch_supabase = fetch_supabase_producao_data
    fetch_supabase_producao_data = mock_fetch_supabase_producao_data
    
    # Chamada da função principal para teste
    exibir_producao_time_doutora(None) # Passando None para df_cartorio_original_bitrix
    
    # Restaurar funções originais se necessário após o teste
    carregar_dados_usuarios_bitrix = original_carregar_dados_usuarios_bitrix
    fetch_supabase_producao_data = original_fetch_supabase 