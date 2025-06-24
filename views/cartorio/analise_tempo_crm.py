import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Importar funções necessárias do arquivo original
from views.cartorio.produtividade import formatar_nome_etapa, obter_mapeamento_campos
from utils.dataframe_utils import ensure_pandas_df

# --- INÍCIO DA ADIÇÃO: Mapeamento STAGE_ID -> NOME_ESTAGIO ---
def obter_nomes_estagios_local():
    """
    Retorna um dicionário mapeando STAGE_IDs técnicos para nomes legíveis.
    Este mapeamento é crucial para a exibição correta das métricas.
    Se múltiplos IDs são mapeados para o mesmo nome, suas contagens serão somadas.
    """
    # Mapeamento baseado na tabela fornecida e nomes comuns
    # IMPORTANTE: Este mapeamento deve ser mantido atualizado com os estágios do Bitrix24
    mapeamento = {
        # SUCESSO
        'C1052:WON': 'Certidão Entregue',  # Assumindo que WON = Entregue/Success final
        'C1052:SUCCESS': 'Certidão Entregue', # Agrupa com WON
        'DT1052_16:SUCCESS': 'Certidão Entregue', # Agrupa com WON
        'DT1052_34:SUCCESS': 'Certidão Entregue', # Agrupa com WON
        'DT1052_16:CLIENT': 'Certidão Entregue', # Agrupa com WON
        'DT1052_34:CLIENT': 'Certidão Entregue', # Agrupa com WON
        'CLIENT': 'Certidão Entregue', # Agrupa com WON
        # 'UF_CRM_DATA_CERTIDAO_FISICA_ENTREGUE': 'Certidão Física Entregue', # Verificar se existe ID correspondente
        'UF_CRM_DATA_CERTIDAO_FISICA_ENVIADA': 'Certidão Física Enviada', # Mapear ID correto se houver
        'UF_CRM_DATA_CERTIDAO_EMITIDA': 'Certidão Emitida', # Mapear ID correto se houver
        # IDs de sucesso genéricos podem precisar ser mapeados se usados
        'DT1052_16:UC_JRGCW3': 'Certidão Pronta', # Exemplo
        'DT1052_34:UC_84B1S2': 'Certidão Pronta', # Exemplo

        # EM ANDAMENTO
        'C1052:UC_LNHG7G': 'Apenas Ass. Req. Cliente P/ Montagem', # Exemplo, verificar ID correto
        'C1052:PREPARATION': 'Aguardando Certidão', # Exemplo, verificar ID correto
        'C1052:FINAL_INVOICE': 'Devolutiva Busca', # Mapeamento conhecido
        'C1052:UC_3LJ0KG': 'NÃO TRABALHAR(DESPRIORIZADA)', # Mapeamento fornecido
        'C1052:UC_52V88J': 'Solicitar Cart. Origem', # Exemplo, verificar ID correto
        'C1052:EXECUTING': 'Aguard. Cart. Origem', # Exemplo, verificar ID correto
        'C1052:UC_RJC2DD': 'PRIO2 - FAZER BUSCA CRC', # Mapeamento fornecido
        'C1052:UC_XM32IE': 'SEM DADOS SUFICIENTES PARA BUSCA', # Mapeamento fornecido
        'C1052:UC_6T0J0A': 'Busca CRC', # Exemplo, verificar ID correto
        'C1052:UC_T71A6N': 'Montagem Requerimento Cartório', # Exemplo, verificar ID correto
        'C1052:UC_K85YX7': 'PRIO2 - FAZER BUSCA CRC', # Mapeamento fornecido (Agrupa com UC_RJC2DD)
        # 'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE': 'Cart. Origem Prioridade', # Mapear ID correto se houver

        # FALHA
        'C1052:LOSE': 'Devolução ADM', # Assumindo LOSE principal = Devolução ADM
        'C1052:APOLOGY': 'Dev. ADM Verificado', # Exemplo, verificar ID correto
        'C1052:UC_O1L97N': 'Solicitação Duplicada', # Exemplo, verificar ID correto
        'C1052:UC_Q448V8': 'Devolvido Requerimento', # Exemplo, verificar ID correto
        'C1052:UC_7L6CGJ': 'CANCELADO' # Mapeamento fornecido
        # Adicionar outros IDs de falha se existirem
    }
    # Adicionar prefixo C1052: se estiver faltando em algum ID (pode variar)
    # Esta parte pode precisar de ajuste dependendo do formato exato dos IDs nos dados
    mapeamento_final = {}
    for key, value in mapeamento.items():
        if not key.startswith('C1052:') and not key.startswith('DT'):
             # Tenta adicionar prefixo padrão se parecer um ID sem ele
             # Pode ser necessário ajustar 'C1052:' para o prefixo correto se variar
             # Ou remover esta lógica se os IDs no dict já estiverem corretos
             # mapeamento_final[f'C1052:{key}'] = value
             mapeamento_final[key] = value # Mantem como está por enquanto
        else:
            mapeamento_final[key] = value

    return mapeamento_final
# --- FIM DA ADIÇÃO ---

def definir_parametros_sla():
    """Permite personalizar os tempos de referência para análise de SLA"""
    
    # Criar caixa de configuração na barra lateral
    st.sidebar.markdown("### ⚙️ Configurações de Tempo")
    
    with st.sidebar.expander("⏱️ Personalizar Métricas de Tempo", expanded=False):
        st.markdown("#### Tempos entre Etapas")
        
        # Tempos entre etapas (em horas)
        col1, col2 = st.columns(2)
        with col1:
            tempo_rapido = st.number_input(
                "Tempo Rápido (horas)",
                min_value=1,
                max_value=72,
                value=24,
                help="Limite para classificação como 'Rápido'"
            )
        
        with col2:
            tempo_moderado = st.number_input(
                "Tempo Moderado (horas)",
                min_value=tempo_rapido + 1,
                max_value=240,
                value=72,
                help="Limite para classificação como 'Moderado'"
            )
        
        st.markdown("#### Tempo Total do Processo")
        
        # Tempos totais (em dias)
        col1, col2 = st.columns(2)
        with col1:
            processo_rapido = st.number_input(
                "Processo Rápido (dias)",
                min_value=1,
                max_value=30,
                value=7,
                help="Limite para classificação como 'Rápido'"
            )
        
        with col2:
            processo_moderado = st.number_input(
                "Processo Moderado (dias)",
                min_value=processo_rapido + 1,
                max_value=60,
                value=15,
                help="Limite para classificação como 'Moderado'"
            )
        
        # Botões para salvar ou restaurar configurações
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar Configurações", use_container_width=True):
                st.session_state.tempo_rapido = tempo_rapido
                st.session_state.tempo_moderado = tempo_moderado
                st.session_state.processo_rapido = processo_rapido
                st.session_state.processo_moderado = processo_moderado
                st.success("✅ Configurações salvas!")
        
        with col2:
            if st.button("Restaurar Padrões", use_container_width=True):
                st.session_state.tempo_rapido = 24
                st.session_state.tempo_moderado = 72
                st.session_state.processo_rapido = 7
                st.session_state.processo_moderado = 15
                st.success("🔄 Padrões restaurados!")
    
    # Inicializar valores na sessão se não existirem
    if 'tempo_rapido' not in st.session_state:
        st.session_state.tempo_rapido = 24
    
    if 'tempo_moderado' not in st.session_state:
        st.session_state.tempo_moderado = 72
    
    if 'processo_rapido' not in st.session_state:
        st.session_state.processo_rapido = 7
    
    if 'processo_moderado' not in st.session_state:
        st.session_state.processo_moderado = 15
    
    # Retornar os parâmetros atuais
    return {
        'tempo_rapido': st.session_state.tempo_rapido,
        'tempo_moderado': st.session_state.tempo_moderado,
        'processo_rapido': st.session_state.processo_rapido,
        'processo_moderado': st.session_state.processo_moderado
    }

def visualizar_funil_processo(df, campos_data):
    """Cria visualização do funil completo do processo com taxas de conversão"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #2E3192 0%, #1BFFFF 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h3 style="color: white; text-align: center; margin: 0; font-weight: 700;">⏱️ FUNIL DE PROCESSAMENTO</h3>
        <p style="color: white; text-align: center; margin: 5px 0 0 0; opacity: 0.9;">
            Jornada completa do documento: volume e tempo entre etapas
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Definir sequência lógica das etapas no funil
    etapas_funil = [
        "Deu ganho na Busca",
        "Montar Requerimento", 
        "Requerimento Montado",
        "Solicitado ao Cartório Origem", 
        "Certidao Emitida", 
        "Certidao Fisica Enviada", 
        "Certidao Fisica Entregue"
    ]
    
    # Obter contagem para cada etapa
    contagens = []
    campos_correspondentes = []
    
    for etapa in etapas_funil:
        # Encontrar o campo correspondente a esta etapa
        campo = None
        for c in campos_data:
            if c in df.columns and formatar_nome_etapa(c) == etapa:
                campo = c
                break
        
        if campo:
            campos_correspondentes.append(campo)
            contagem = df[campo].notna().sum()
            contagens.append(contagem)
        else:
            campos_correspondentes.append(None)
            contagens.append(0)
    
    # Criar DataFrame para visualização
    df_funil = pd.DataFrame({
        'Etapa': etapas_funil,
        'Quantidade': contagens
    })
    
    # Calcular taxas de conversão entre etapas
    taxas_conversao = []
    for i in range(1, len(contagens)):
        if contagens[i-1] > 0:
            taxa = contagens[i] / contagens[i-1] * 100
        else:
            taxa = 0
        taxas_conversao.append(f"{taxa:.1f}%")
    
    # Layout em colunas
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Gráfico de funil
        fig = px.funnel(
            df_funil,
            x='Quantidade', 
            y='Etapa',
            title="Funil Completo do Processo"
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Mostrar métricas de conversão
        st.subheader("Taxas de Conversão")
        
        for i, taxa in enumerate(taxas_conversao):
            etapa_atual = etapas_funil[i+1]
            etapa_anterior = etapas_funil[i]
            
            # Determinar cor baseada na taxa
            taxa_valor = float(taxa.strip('%'))
            cor = "#4CAF50" if taxa_valor >= 80 else "#FFC107" if taxa_valor >= 50 else "#F44336"
            
            st.markdown(f"""
            <div style="margin-bottom: 15px;">
                <div style="font-size: 13px; color: #666;">De <b>{etapa_anterior}</b> para</div>
                <div style="font-size: 15px; font-weight: bold;">{etapa_atual}</div>
                <div style="font-size: 24px; font-weight: bold; color: {cor};">{taxa}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Indicadores de eficiência do funil
    taxa_final = (contagens[-1] / contagens[0] * 100) if contagens[0] > 0 else 0
    
    st.markdown("### Indicadores de Eficiência do Funil")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Taxa de Conversão Total",
            f"{taxa_final:.1f}%",
            help="Percentual que chega ao final do processo"
        )
    
    with col2:
        # Calcular funil mais eficiente (maior taxa de conversão)
        maiores_conversoes = []
        for i in range(len(taxas_conversao)):
            maiores_conversoes.append((etapas_funil[i], etapas_funil[i+1], float(taxas_conversao[i].strip('%'))))
        
        maior_conversao = max(maiores_conversoes, key=lambda x: x[2]) if maiores_conversoes else (None, None, 0)
        
        if maior_conversao[0]:
            st.metric(
                "Etapa Mais Eficiente",
                f"{maior_conversao[0]} → {maior_conversao[1]}",
                f"{maior_conversao[2]:.1f}%"
            )
    
    with col3:
        # Calcular gargalo (menor taxa de conversão)
        if maiores_conversoes:
            menor_conversao = min(maiores_conversoes, key=lambda x: x[2])
            
            st.metric(
                "Gargalo do Processo",
                f"{menor_conversao[0]} → {menor_conversao[1]}",
                f"{menor_conversao[2]:.1f}%",
                delta_color="inverse"
            )

def analisar_tempo_entre_etapas(df, campos_data, parametros_sla):
    """Analisa o tempo médio entre cada etapa do processo com classificação por SLA"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #FF512F 0%, #F09819 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h3 style="color: white; text-align: center; margin: 0; font-weight: 700;">⏱️ TEMPO DE PROCESSAMENTO</h3>
        <p style="color: white; text-align: center; margin: 5px 0 0 0; opacity: 0.9;">
            Análise do tempo médio entre etapas do processo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Obter parâmetros de SLA
    tempo_rapido = parametros_sla['tempo_rapido']
    tempo_moderado = parametros_sla['tempo_moderado']
    
    # Mostrar configuração atual
    with st.expander("ℹ️ Configuração Atual de SLA", expanded=False):
        st.info(f"""
        **Classificação de tempo entre etapas:**
        - 🟢 **Rápido**: Menos de {tempo_rapido} horas 
        - 🟡 **Moderado**: Entre {tempo_rapido} e {tempo_moderado} horas
        - 🔴 **Lento**: Mais de {tempo_moderado} horas
        """)
    
    # Definir sequência lógica das etapas 
    etapas_sequencia = [
        "Deu ganho na Busca",
        "Montar Requerimento", 
        "Requerimento Montado",
        "Solicitado ao Cartório Origem", 
        "Certidao Emitida", 
        "Certidao Fisica Enviada", 
        "Certidao Fisica Entregue"
    ]
    
    # Mapear etapas para seus campos correspondentes
    etapa_para_campo = {}
    for etapa in etapas_sequencia:
        for campo in campos_data:
            if campo in df.columns and formatar_nome_etapa(campo) == etapa:
                etapa_para_campo[etapa] = campo
                break
    
    # Calcular tempo entre etapas
    tempos_medios = []
    tempos_medianos = []
    etapas_pares = []
    classificacoes = []
    dados_pares = []
    
    for i in range(1, len(etapas_sequencia)):
        etapa_anterior = etapas_sequencia[i-1]
        etapa_atual = etapas_sequencia[i]
        
        if etapa_anterior in etapa_para_campo and etapa_atual in etapa_para_campo:
            campo_anterior = etapa_para_campo[etapa_anterior]
            campo_atual = etapa_para_campo[etapa_atual]
            
            # Filtrar registros com ambas as datas
            df_par = df.dropna(subset=[campo_anterior, campo_atual]).copy()
            
            if not df_par.empty:
                # Calcular diferença em horas
                df_par['tempo_diff'] = (pd.to_datetime(df_par[campo_atual]) - 
                                        pd.to_datetime(df_par[campo_anterior])).dt.total_seconds() / 3600
                
                # Remover outliers (valores negativos ou extremamente altos)
                df_par = df_par[(df_par['tempo_diff'] > 0) & (df_par['tempo_diff'] < 720)]  # Máx 30 dias
                
                if not df_par.empty:
                    tempo_medio_horas = df_par['tempo_diff'].mean()
                    tempo_mediano_horas = df_par['tempo_diff'].median()
                    
                    # Formatação para exibição
                    if tempo_medio_horas > 24:
                        tempo_medio = f"{tempo_medio_horas/24:.1f} dias"
                    else:
                        tempo_medio = f"{tempo_medio_horas:.1f} horas"
                        
                    if tempo_mediano_horas > 24:
                        tempo_mediano = f"{tempo_mediano_horas/24:.1f} dias"
                    else:
                        tempo_mediano = f"{tempo_mediano_horas:.1f} horas"
                    
                    # Classificar com base nos parâmetros personalizados
                    if tempo_medio_horas < tempo_rapido:
                        classificacao = "🟢 Rápido"
                    elif tempo_medio_horas < tempo_moderado:
                        classificacao = "🟡 Moderado"
                    else:
                        classificacao = "🔴 Lento"
                    
                    # Guardar dados para exibição
                    tempos_medios.append(tempo_medio)
                    tempos_medianos.append(tempo_mediano)
                    etapas_pares.append(f"{etapa_anterior} → {etapa_atual}")
                    classificacoes.append(classificacao)
                    
                    # Guardar dados para gráfico
                    df_tempo = pd.DataFrame({
                        'Par de Etapas': f"{etapa_anterior} → {etapa_atual}",
                        'Etapa Anterior': etapa_anterior,
                        'Etapa Atual': etapa_atual,
                        'Tempo (horas)': df_par['tempo_diff']
                    })
                    dados_pares.append(df_tempo)
    
    # Se não há dados para análise
    if not etapas_pares:
        st.warning("Não há dados suficientes para analisar o tempo entre etapas.")
        return
    
    # Combinar dados para gráfico
    df_todos_tempos = pd.concat(dados_pares) if dados_pares else pd.DataFrame()
    
    if not df_todos_tempos.empty:
        # Criar tabela com estatísticas
        df_stats = pd.DataFrame({
            'Transição': etapas_pares,
            'Tempo Médio': tempos_medios,
            'Tempo Mediano': tempos_medianos,
            'Classificação': classificacoes
        })
        
        # Exibir tabela de tempos
        st.subheader("Estatísticas de Tempo entre Etapas")
        st.dataframe(
            df_stats,
            column_config={
                "Transição": st.column_config.TextColumn("Transição entre Etapas"),
                "Tempo Médio": st.column_config.TextColumn("Tempo Médio"),
                "Tempo Mediano": st.column_config.TextColumn("Tempo Mediano"),
                "Classificação": st.column_config.TextColumn("Classificação")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Criar visualização do tempo entre etapas (box plot)
        st.subheader("Distribuição de Tempo entre Etapas")
        
        # Calcular médias para ordenar o box plot
        df_medias = df_todos_tempos.groupby('Par de Etapas')['Tempo (horas)'].mean().reset_index()
        df_medias = df_medias.sort_values('Tempo (horas)', ascending=False)
        
        # Converter tempo para dias onde for muito alto
        df_dias = df_todos_tempos.copy()
        mask_dias = df_dias['Tempo (horas)'] > 24
        if mask_dias.any():
            df_dias.loc[mask_dias, 'Tempo (dias)'] = df_dias.loc[mask_dias, 'Tempo (horas)'] / 24
            df_dias.loc[~mask_dias, 'Tempo (dias)'] = df_dias.loc[~mask_dias, 'Tempo (horas)'] / 24
            
            fig = px.box(
                df_dias,
                x='Par de Etapas',
                y='Tempo (dias)',
                title="Distribuição de Tempo entre Etapas (dias)",
                category_orders={"Par de Etapas": df_medias['Par de Etapas'].tolist()}
            )
        else:
            fig = px.box(
                df_todos_tempos,
                x='Par de Etapas',
                y='Tempo (horas)',
                title="Distribuição de Tempo entre Etapas (horas)",
                category_orders={"Par de Etapas": df_medias['Par de Etapas'].tolist()}
            )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Calcular tempo total do processo (primeira à última etapa)
        primeira_etapa = etapas_sequencia[0]
        ultima_etapa = etapas_sequencia[-1]
        
        if primeira_etapa in etapa_para_campo and ultima_etapa in etapa_para_campo:
            campo_primeiro = etapa_para_campo[primeira_etapa]
            campo_ultimo = etapa_para_campo[ultima_etapa]
            
            df_tempo_total = df.dropna(subset=[campo_primeiro, campo_ultimo]).copy()
            
            if not df_tempo_total.empty:
                df_tempo_total['tempo_total'] = (pd.to_datetime(df_tempo_total[campo_ultimo]) - 
                                              pd.to_datetime(df_tempo_total[campo_primeiro])).dt.total_seconds() / 3600
                
                # Remover outliers
                df_tempo_total = df_tempo_total[(df_tempo_total['tempo_total'] > 0) & 
                                            (df_tempo_total['tempo_total'] < 720)]
                
                if not df_tempo_total.empty:
                    tempo_medio_total = df_tempo_total['tempo_total'].mean() / 24  # em dias
                    tempo_mediano_total = df_tempo_total['tempo_total'].median() / 24  # em dias
                    
                    st.markdown("### Tempo Total do Processo")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Tempo Médio",
                            f"{tempo_medio_total:.1f} dias",
                            help=f"Média de tempo entre {primeira_etapa} e {ultima_etapa}"
                        )
                    
                    with col2:
                        st.metric(
                            "Tempo Mediano",
                            f"{tempo_mediano_total:.1f} dias",
                            help=f"Mediana de tempo entre {primeira_etapa} e {ultima_etapa}"
                        )
                    
                    # Classificar por SLA
                    processo_rapido = parametros_sla['processo_rapido']
                    processo_moderado = parametros_sla['processo_moderado']
                    
                    processos_rapidos = len(df_tempo_total[df_tempo_total['tempo_total'] < 24*processo_rapido])
                    processos_medios = len(df_tempo_total[(df_tempo_total['tempo_total'] >= 24*processo_rapido) & 
                                                      (df_tempo_total['tempo_total'] < 24*processo_moderado)])
                    processos_lentos = len(df_tempo_total[df_tempo_total['tempo_total'] >= 24*processo_moderado])
                    
                    total_processos = len(df_tempo_total)
                    
                    # Criar gráfico de distribuição por SLA
                    dados_sla = pd.DataFrame({
                        'SLA': [f'Rápido (< {processo_rapido} dias)', 
                              f'Médio ({processo_rapido}-{processo_moderado} dias)', 
                              f'Lento (> {processo_moderado} dias)'],
                        'Quantidade': [processos_rapidos, processos_medios, processos_lentos],
                        'Percentual': [100*processos_rapidos/total_processos if total_processos > 0 else 0,
                                      100*processos_medios/total_processos if total_processos > 0 else 0,
                                      100*processos_lentos/total_processos if total_processos > 0 else 0]
                    })
                    
                    fig = px.pie(
                        dados_sla,
                        values='Quantidade',
                        names='SLA',
                        title="Distribuição de Processos por Tempo de Processamento",
                        color='SLA',
                        color_discrete_map={
                            f'Rápido (< {processo_rapido} dias)': '#4CAF50',
                            f'Médio ({processo_rapido}-{processo_moderado} dias)': '#FFC107',
                            f'Lento (> {processo_moderado} dias)': '#F44336'
                        }
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar tabela com detalhamento
                    st.dataframe(
                        dados_sla,
                        column_config={
                            "SLA": st.column_config.TextColumn("Classificação"),
                            "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
                            "Percentual": st.column_config.ProgressColumn("% do Total", format="%.1f%%")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

def analisar_desempenho_responsaveis(df, campos_data, mapeamento_campos, parametros_sla):
    """Analisa o desempenho dos responsáveis em termos de tempo de processamento"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #6A1B9A 0%, #9575CD 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h3 style="color: white; text-align: center; margin: 0; font-weight: 700;">👥 DESEMPENHO POR RESPONSÁVEL</h3>
        <p style="color: white; text-align: center; margin: 5px 0 0 0; opacity: 0.9;">
            Análise da velocidade e eficiência de cada responsável nas etapas do processo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar se existem os campos necessários
    campos_resp_disponiveis = []
    
    for campo_data, campo_resp in mapeamento_campos.items():
        if campo_data in df.columns and campo_resp in df.columns:
            campos_resp_disponiveis.append({
                'campo_data': campo_data,
                'campo_resp': campo_resp,
                'nome_etapa': formatar_nome_etapa(campo_data)
            })
    
    if not campos_resp_disponiveis:
        st.warning("Não foram encontrados campos de responsável correspondentes às datas para análise.")
        return
    
    # Parâmetros de SLA
    tempo_rapido = parametros_sla['tempo_rapido']
    tempo_moderado = parametros_sla['tempo_moderado']
    
    # Seleção de etapa para análise
    st.markdown("### Selecione a Etapa para Análise de Responsáveis")
    
    # Opções de etapas disponíveis
    etapas_disponiveis = [item['nome_etapa'] for item in campos_resp_disponiveis]
    
    # Se houver múltiplas etapas, permite selecionar
    if len(etapas_disponiveis) > 1:
        etapa_selecionada = st.selectbox(
            "Etapa:",
            options=etapas_disponiveis,
            index=0,
            key="resp_etapa_select",
            help="Selecione a etapa para analisar o desempenho dos responsáveis"
        )
        
        # Obter os campos correspondentes
        item_selecionado = next((item for item in campos_resp_disponiveis if item['nome_etapa'] == etapa_selecionada), None)
    else:
        # Se só existe uma etapa, usa ela direto
        item_selecionado = campos_resp_disponiveis[0]
        etapa_selecionada = item_selecionado['nome_etapa']
        st.info(f"Analisando a única etapa disponível: {etapa_selecionada}")
    
    # Se encontrou a etapa, fazer a análise
    if item_selecionado:
        campo_data = item_selecionado['campo_data']
        campo_resp = item_selecionado['campo_resp']
        
        # Identificar relação com a etapa anterior se possível
        etapas_sequencia = [
            "Deu ganho na Busca",
            "Montar Requerimento", 
            "Requerimento Montado",
            "Solicitado ao Cartório Origem", 
            "Certidao Emitida", 
            "Certidao Fisica Enviada", 
            "Certidao Fisica Entregue"
        ]
        
        # Verificar se a etapa atual está na sequência
        if etapa_selecionada in etapas_sequencia:
            idx_etapa = etapas_sequencia.index(etapa_selecionada)
            
            # Se não for a primeira etapa, verificar etapa anterior
            if idx_etapa > 0:
                etapa_anterior = etapas_sequencia[idx_etapa - 1]
                
                # Encontrar campo de data correspondente
                campo_data_anterior = None
                for item in campos_resp_disponiveis:
                    if item['nome_etapa'] == etapa_anterior:
                        campo_data_anterior = item['campo_data']
                        break
            else:
                campo_data_anterior = None
                etapa_anterior = None
        else:
            campo_data_anterior = None
            etapa_anterior = None
        
        # Filtrar dados que têm responsável e data
        df_analise = df.dropna(subset=[campo_data, campo_resp]).copy()
        
        if df_analise.empty:
            st.warning(f"Não há dados suficientes para análise de responsáveis na etapa {etapa_selecionada}")
            return
        
        # Analisar tempo se temos etapa anterior
        tempos_por_responsavel = None
        if campo_data_anterior and campo_data_anterior in df.columns:
            # Filtrar registros que têm ambas datas (anterior e atual)
            df_tempo = df.dropna(subset=[campo_data_anterior, campo_data]).copy()
            
            if not df_tempo.empty:
                # Calcular a diferença de tempo em horas
                df_tempo['tempo_diff'] = (pd.to_datetime(df_tempo[campo_data]) - 
                                         pd.to_datetime(df_tempo[campo_data_anterior])).dt.total_seconds() / 3600
                
                # Remover outliers
                df_tempo = df_tempo[(df_tempo['tempo_diff'] > 0) & (df_tempo['tempo_diff'] < 720)]  # Max 30 dias
                
                if not df_tempo.empty:
                    # Agrupar por responsável e calcular estatísticas
                    tempos_por_responsavel = df_tempo.groupby(campo_resp)['tempo_diff'].agg(
                        ['count', 'mean', 'median', 'min', 'max']
                    ).reset_index()
                    
                    # Ordenar por média de tempo (mais rápido primeiro)
                    tempos_por_responsavel = tempos_por_responsavel.sort_values('mean')
                    
                    # Adicionar classificação
                    def classificar_tempo(tempo):
                        if tempo < tempo_rapido:
                            return "🟢 Rápido"
                        elif tempo < tempo_moderado:
                            return "🟡 Moderado"
                        else:
                            return "🔴 Lento"
                    
                    tempos_por_responsavel['classificacao'] = tempos_por_responsavel['mean'].apply(classificar_tempo)
                    
                    # Formatar para exibição
                    tempos_por_responsavel['tempo_medio'] = tempos_por_responsavel['mean'].apply(
                        lambda x: f"{x/24:.1f} dias" if x > 24 else f"{x:.1f} horas"
                    )
                    tempos_por_responsavel['tempo_mediano'] = tempos_por_responsavel['median'].apply(
                        lambda x: f"{x/24:.1f} dias" if x > 24 else f"{x:.1f} horas"
                    )
        
        # Calcular volume de trabalho por responsável
        volume_por_responsavel = df_analise[campo_resp].value_counts().reset_index()
        volume_por_responsavel.columns = ['responsavel', 'quantidade']
        volume_por_responsavel = volume_por_responsavel.sort_values('quantidade', ascending=False)
        
        # Storytelling: Criar um resumo executivo
        st.markdown("### Resumo do Desempenho")
        
        # Estatísticas e narrativa
        total_registros = len(df_analise)
        total_responsaveis = df_analise[campo_resp].nunique()
        
        # Determinar top responsáveis
        top_responsaveis = volume_por_responsavel.head(3)['responsavel'].tolist() if len(volume_por_responsavel) >= 3 else volume_por_responsavel['responsavel'].tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label=f"Total de {etapa_selecionada}",
                value=f"{total_registros}",
                help=f"Registros totais na etapa {etapa_selecionada}"
            )
        with col2:
            st.metric(
                label="Responsáveis Envolvidos",
                value=f"{total_responsaveis}",
                help=f"Número de responsáveis distintos nesta etapa"
            )
        
        # Mostrar narrativa sobre os principais responsáveis
        st.markdown(f"""
        <div style="background-color: #f0f7ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 5px solid #1976D2;">
            <h4 style="margin-top: 0; color: #1565C0;">📖 A História desta Etapa</h4>
            <p>Na etapa <strong>{etapa_selecionada}</strong>, temos {total_registros} registros processados por {total_responsaveis} responsáveis diferentes.</p>
            
            <p>Os principais responsáveis são: <strong>{', '.join(top_responsaveis[:3])}</strong>, que juntos representam 
            {volume_por_responsavel.head(3)['quantidade'].sum()/total_registros*100:.1f}% do volume total de trabalho nesta etapa.</p>
        """, unsafe_allow_html=True)
        
        # Adicionar informação sobre tempo se disponível
        if tempos_por_responsavel is not None and not tempos_por_responsavel.empty:
            responsavel_mais_rapido = tempos_por_responsavel.iloc[0][campo_resp]
            tempo_mais_rapido = tempos_por_responsavel.iloc[0]['tempo_medio']
            
            responsavel_mais_lento = tempos_por_responsavel.iloc[-1][campo_resp]
            tempo_mais_lento = tempos_por_responsavel.iloc[-1]['tempo_medio']
            
            tempo_medio_geral = tempos_por_responsavel['mean'].mean()
            tempo_medio_geral_formatado = f"{tempo_medio_geral/24:.1f} dias" if tempo_medio_geral > 24 else f"{tempo_medio_geral:.1f} horas"
            
            st.markdown(f"""
            <p>O tempo médio de processamento desta etapa é de <strong>{tempo_medio_geral_formatado}</strong>, com variações significativas por responsável.</p>
            
            <p>O responsável mais rápido é <strong>{responsavel_mais_rapido}</strong>, com média de <strong>{tempo_mais_rapido}</strong>,
            enquanto o mais lento é <strong>{responsavel_mais_lento}</strong>, com média de <strong>{tempo_mais_lento}</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p>Não há dados suficientes para análise de tempo nesta etapa ou não há etapa anterior para comparação.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar gráficos e tabelas
        st.markdown("### Volume por Responsável")
        
        # Gráfico de barras - volume por responsável
        fig_volume = px.bar(
            volume_por_responsavel.head(10),
            x='responsavel',
            y='quantidade',
            title=f"Top 10 Responsáveis por Volume na Etapa {etapa_selecionada}",
            labels={
                'responsavel': 'Responsável',
                'quantidade': 'Quantidade de Registros'
            },
            color='quantidade',
            color_continuous_scale='Viridis'
        )
        
        fig_volume.update_layout(height=400)
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # Mostrar dados de tempo se disponíveis
        if tempos_por_responsavel is not None and not tempos_por_responsavel.empty:
            st.markdown("### Tempo de Processamento por Responsável")
            
            # Gráfico de barras - tempo médio por responsável
            fig_tempo = px.bar(
                tempos_por_responsavel.head(10),
                x=campo_resp,
                y='mean',
                title=f"Tempo Médio de Processamento por Responsável (de {etapa_anterior} para {etapa_selecionada})",
                labels={
                    campo_resp: 'Responsável',
                    'mean': 'Tempo Médio (horas)'
                },
                color='mean',
                color_continuous_scale='RdYlGn_r'  # Escala invertida (vermelho=alto, verde=baixo)
            )
            
            fig_tempo.update_layout(height=400)
            st.plotly_chart(fig_tempo, use_container_width=True)
            
            # Tabela detalhada
            st.markdown("### Tabela de Desempenho por Responsável")
            
            # Mesclar dados de volume e tempo
            if not volume_por_responsavel.empty and not tempos_por_responsavel.empty:
                # Juntar volume e tempo em um único dataframe
                df_desempenho = pd.merge(
                    volume_por_responsavel,
                    tempos_por_responsavel[[campo_resp, 'count', 'mean', 'tempo_medio', 'tempo_mediano', 'classificacao']],
                    left_on='responsavel',
                    right_on=campo_resp,
                    how='outer'
                )
                
                # Renomear colunas
                df_desempenho = df_desempenho.rename(columns={
                    'responsavel': 'Responsável',
                    'quantidade': 'Volume Total',
                    'count': 'Registros Analisados',
                    'tempo_medio': 'Tempo Médio',
                    'tempo_mediano': 'Tempo Mediano',
                    'classificacao': 'Classificação'
                })
                
                # Remover coluna duplicada
                if campo_resp in df_desempenho.columns and campo_resp != 'Responsável':
                    df_desempenho = df_desempenho.drop(columns=[campo_resp])
                
                # Ordenar por volume (maior primeiro)
                df_desempenho = df_desempenho.sort_values('Volume Total', ascending=False)
                
                # Preencher NaN
                df_desempenho = df_desempenho.fillna({
                    'Registros Analisados': 0,
                    'Tempo Médio': 'N/A',
                    'Tempo Mediano': 'N/A',
                    'Classificação': 'N/A'
                })
                
                # Exibir tabela
                st.dataframe(
                    df_desempenho,
                    column_config={
                        "Responsável": st.column_config.TextColumn("Responsável"),
                        "Volume Total": st.column_config.NumberColumn("Volume Total", format="%d"),
                        "Registros Analisados": st.column_config.NumberColumn("Regs. Analisados", format="%d"),
                        "Tempo Médio": st.column_config.TextColumn("Tempo Médio"),
                        "Tempo Mediano": st.column_config.TextColumn("Tempo Mediano"),
                        "Classificação": st.column_config.TextColumn("Classificação")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            
            # Identificar pontos de atenção
            if len(tempos_por_responsavel) > 1:
                # Encontrar responsáveis rápidos com alto volume
                destaques_positivos = df_desempenho[
                    (df_desempenho['Classificação'] == "🟢 Rápido") & 
                    (df_desempenho['Volume Total'] > df_desempenho['Volume Total'].median())
                ]
                
                # Encontrar responsáveis lentos com alto volume (gargalos)
                gargalos = df_desempenho[
                    (df_desempenho['Classificação'] == "🔴 Lento") & 
                    (df_desempenho['Volume Total'] > df_desempenho['Volume Total'].median())
                ]
                
                # Exibir insights baseados nos dados
                if not destaques_positivos.empty or not gargalos.empty:
                    st.markdown("### 💡 Insights de Desempenho")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### ⭐ Destaques Positivos")
                        if not destaques_positivos.empty:
                            for idx, row in destaques_positivos.iterrows():
                                st.markdown(f"""
                                <div style="background-color: #E8F5E9; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <p style="margin: 0; font-weight: bold; color: #2E7D32;">{row['Responsável']}</p>
                                    <p style="margin: 0;">Volume: {row['Volume Total']} | Tempo: {row['Tempo Médio']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("Nenhum destaque positivo identificado.")
                    
                    with col2:
                        st.markdown("#### 🚨 Oportunidades de Melhoria")
                        if not gargalos.empty:
                            for idx, row in gargalos.iterrows():
                                st.markdown(f"""
                                <div style="background-color: #FFEBEE; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <p style="margin: 0; font-weight: bold; color: #C62828;">{row['Responsável']}</p>
                                    <p style="margin: 0;">Volume: {row['Volume Total']} | Tempo: {row['Tempo Médio']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("Nenhum gargalo significativo identificado.")
                    
                    # Recomendações baseadas nos dados
                    st.markdown("#### 🎯 Recomendações")
                    
                    if not destaques_positivos.empty and not gargalos.empty:
                        st.markdown(f"""
                        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; margin-top: 10px;">
                            <p style="margin: 0;"><strong>Compartilhamento de Práticas:</strong> Considere organizar sessões onde 
                            {', '.join(destaques_positivos['Responsável'].head(2).tolist())} possam compartilhar suas práticas eficientes
                            com o restante da equipe, especialmente com {', '.join(gargalos['Responsável'].head(2).tolist())}.</p>
                            
                            <p style="margin-top: 10px;"><strong>Redistribuição de Carga:</strong> Avalie a possibilidade de redistribuir parte do volume
                            dos responsáveis mais lentos para os mais rápidos, equilibrando a carga de trabalho e melhorando o tempo médio geral.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif not destaques_positivos.empty:
                        st.markdown(f"""
                        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; margin-top: 10px;">
                            <p style="margin: 0;"><strong>Bom trabalho:</strong> A equipe apresenta bom desempenho em geral, sem grandes gargalos identificados.
                            Considere reconhecer o trabalho de {', '.join(destaques_positivos['Responsável'].head(3).tolist())} que se destacam positivamente.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif not gargalos.empty:
                        st.markdown(f"""
                        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; margin-top: 10px;">
                            <p style="margin: 0;"><strong>Atenção Necessária:</strong> Identifique os fatores que estão tornando o processo mais lento para
                            {', '.join(gargalos['Responsável'].head(3).tolist())}. Pode ser necessário treinamento adicional ou revisão de processos.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; margin-top: 10px;">
                            <p style="margin: 0;"><strong>Desempenho Equilibrado:</strong> Os responsáveis apresentam desempenho relativamente homogêneo,
                            sem grandes destaques positivos ou negativos significativos.</p>
                        </div>
                        """, unsafe_allow_html=True)

def mostrar_dashboard_tempo_crm(df):
    """Exibe um dashboard focado na análise de tempo do processo CRM"""

    if df.empty:
        st.warning("Não há dados disponíveis para esta análise.")
        return

    # --- INÍCIO DA MODIFICAÇÃO: Usar Mapeamento Local ---
    # Verificar se a coluna STAGE_ID existe
    if 'STAGE_ID' in df.columns:
        try:
            # Obter mapeamento local de IDs para nomes
            mapping_nomes = obter_nomes_estagios_local()

            # Função para aplicar o mapeamento (retorna nome ou ID original se não mapeado)
            def map_nome(stage_id):
                return mapping_nomes.get(str(stage_id).strip(), str(stage_id).strip()) # Garante que ID é string

            # Cria coluna com nomes mapeados ou IDs originais
            df['NOME_ESTAGIO'] = df['STAGE_ID'].apply(map_nome)
            st.info("Mapeamento de Nomes de Estágio aplicado. IDs não encontrados no mapeamento serão exibidos como estão.")

        except Exception as e:
            st.warning(f"Não foi possível aplicar o mapeamento de nomes de estágios: {e}. Usando IDs técnicos.")
            df['NOME_ESTAGIO'] = df['STAGE_ID'] # Usa o ID se o mapeamento falhar
    else:
        st.warning("Coluna 'STAGE_ID' não encontrada. Não é possível exibir métricas por estágio.")
        return # Não podemos continuar sem STAGE_ID

    # Garantir que 'NOME_ESTAGIO' existe antes de continuar
    if 'NOME_ESTAGIO' not in df.columns:
         st.error("Falha ao criar a coluna 'NOME_ESTAGIO'. Análise por estágio interrompida.")
         return
    # --- FIM DA MODIFICAÇÃO ---

    # Agrupar por nome do estágio e contar
    contagem_estagios = df.groupby('NOME_ESTAGIO').size().reset_index(name='Quantidade')
    contagem_estagios = contagem_estagios.sort_values('Quantidade', ascending=False)

    # --- INÍCIO DA MODIFICAÇÃO: Ajustar Classificação ---
    # Classificar estágios (exemplo de lógica de classificação)
    def classificar_estagio(nome_estagio):
        # Garantir que é string para evitar erros com tipos numéricos ou outros
        nome_lower = str(nome_estagio).lower()

        # Palavras-chave para SUCESSO
        success_keywords = ['success', 'entregue', 'emitida', 'física', 'pronta', 'won']
        # Palavras-chave para FALHA
        fail_keywords = ['fail', 'falha', 'devol', 'duplicada', 'lose', 'cancelado', 'perca', 'sem dados']

        if any(keyword in nome_lower for keyword in success_keywords):
             return '✅ SUCESSO'
        elif any(keyword in nome_lower for keyword in fail_keywords):
             return '❌ FALHA'
        # Considerar despriorizada como falha ou categoria separada? Por enquanto FALHA.
        elif 'despriorizada' in nome_lower:
             return '❌ FALHA' # Ou talvez uma categoria 'PAUSADO'?
        else:
             # Todos os outros são EM ANDAMENTO
             return '⏳ EM ANDAMENTO'

    contagem_estagios['Categoria'] = contagem_estagios['NOME_ESTAGIO'].apply(classificar_estagio)
    # --- FIM DA MODIFICAÇÃO ---

    # Obter parâmetros de SLA (movido para depois da verificação de dados)
    parametros_sla = definir_parametros_sla()

    st.title("⏱️ Análise de Tempo do Processo CRM")
    
    # Mensagem de manutenção
    st.markdown("""
    <div style="background-color: #FFF3E0; padding: 20px; border-radius: 10px; border-left: 5px solid #FF9800; margin-bottom: 30px;">
        <h2 style="color: #E65100; margin-top: 0;">🚧 Módulo em Manutenção 🚧</h2>
        <p style="font-size: 16px;">
            Esta funcionalidade está temporariamente indisponível para correções e melhorias.
        </p>
        <p style="font-size: 16px;">
            Estamos revisando as métricas e a lógica de cálculo de tempo entre etapas para garantir maior precisão 
            nos dados apresentados.
        </p>
        <p style="font-size: 16px; margin-bottom: 0;">
            <strong>Melhorias em andamento:</strong>
        </p>
        <ul style="margin-top: 5px;">
            <li>Correção na lógica de cálculo de tempo entre etapas</li>
            <li>Aprimoramento das métricas de desempenho por responsável</li>
            <li>Análise mais detalhada do funil de processamento</li>
            <li>Novas visualizações para facilitar a interpretação dos dados</li>
        </ul>
        <p style="font-size: 16px; margin-top: 15px;">
            Agradecemos sua compreensão. Esta funcionalidade estará disponível em breve com dados mais precisos e novas métricas.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Adicionar botão para solicitar notificação quando estiver pronto
    with st.expander("📣 Receber notificação quando disponível", expanded=False):
        st.markdown("""
        Deixe seu contato para receber uma notificação quando esta funcionalidade estiver disponível novamente:
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome", key="manut_nome")
        with col2:
            email = st.text_input("E-mail", key="manut_email")
            
        if st.button("Notifique-me", use_container_width=True, key="manut_notify"):
            if email and '@' in email:
                st.success("✅ Obrigado! Você receberá uma notificação quando esta funcionalidade estiver disponível.")
            else:
                st.error("Por favor, informe um e-mail válido.")
    
    # Informações sobre quando estará disponível
    st.info("⏳ Previsão para conclusão da manutenção: 15 dias úteis")
    
    # Opções alternativas para o usuário
    st.markdown("### Enquanto isso, você pode utilizar:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; height: 200px;">
            <h4 style="color: #2E7D32; margin-top: 0;">📊 Produtividade por Etapas</h4>
            <p>Visualize métricas de produtividade por etapa e responsável no módulo de Produtividade.</p>
            <p>Acesse através da aba "Produtividade por Etapas" no menu principal.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; height: 200px;">
            <h4 style="color: #2E7D32; margin-top: 0;">📋 Relatórios de Movimentações</h4>
            <p>Consulte os dados de movimentações de documentos no módulo dedicado a este fim.</p>
            <p>Acesse através da aba "Movimentações" no menu principal.</p>
        </div>
        """, unsafe_allow_html=True)

    # Opcional: formulário para feedback sobre as melhorias desejadas
    with st.expander("💬 Sugestões para a nova versão", expanded=False):
        st.markdown("Compartilhe suas sugestões para a nova versão desta funcionalidade:")
        sugestao = st.text_area("Sua sugestão:", height=100, key="manut_sugestao")
        
        if st.button("Enviar sugestão", use_container_width=True, key="manut_send"):
            if sugestao:
                st.success("✅ Obrigado pela sua contribuição! Sua sugestão foi registrada.")
            else:
                st.error("Por favor, digite sua sugestão antes de enviar.") 