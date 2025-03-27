import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# Importações de módulos internos
from views.apresentacao.utils import hide_streamlit_elements
from views.apresentacao.styles import aplicar_estilos_apresentacao
from views.apresentacao.data_loader import (
    carregar_dados_apresentacao,
    carregar_dados_producao,
    carregar_dados_cartorio
)

# Importar slides
from views.apresentacao.producao.metricas_macro import slide_producao_metricas_macro
from views.apresentacao.producao.status_responsavel import slide_producao_status_responsavel

def show_apresentacao_conclusoes(slide_inicial=0):
    """
    Exibe o modo de apresentação da página de conclusões,
    otimizado para telas verticais (9:16) como TVs.
    
    Args:
        slide_inicial (int): Índice do slide para iniciar a apresentação (0-11)
    """
    print(f"Iniciando apresentação com slide_inicial={slide_inicial}")
    
    # Verificar se há redirecionamento solicitado na sessão
    if 'slide_redirect' in st.session_state:
        slide_inicial = st.session_state['slide_redirect']
        print(f"Usando slide_redirect da sessão: {slide_inicial}")
        # Limpar para não influenciar futuras chamadas
        del st.session_state['slide_redirect']
    
    # Verificar se há parâmetro na URL para definir o slide inicial
    try:
        if 'slide' in st.query_params:
            try:
                slide_inicial = int(st.query_params['slide'])
                print(f"Iniciando apresentação do slide {slide_inicial}")
            except (ValueError, TypeError):
                print("Parâmetro de slide inválido na URL")
        
        # Verificar parâmetro config para alternar o modo
        if 'config' in st.query_params:
            try:
                config_value = int(st.query_params['config'])
                st.session_state.modo_config = (config_value == 1)
                print(f"Modo configuração: {st.session_state.modo_config}")
            except (ValueError, TypeError):
                print("Parâmetro config inválido na URL")
    except Exception as e:
        print(f"Erro ao processar parâmetros da URL: {str(e)}")
    
    # Verificar o modo de configuração
    modo_config = st.session_state.get('modo_config', False)
    
    # Esconder elementos desnecessários
    hide_streamlit_elements()
    
    # Aplicar estilos para o modo apresentação
    aplicar_estilos_apresentacao()
    
    # Container para o cabeçalho personalizado e parâmetros de controle
    header_container = st.container()
    
    # Inicializar parâmetros de controle na sessão
    if 'tempo_slide' not in st.session_state:
        st.session_state.tempo_slide = 10  # Tempo padrão reduzido para 10 segundos por slide
    
    if 'ultima_atualizacao' not in st.session_state:
        st.session_state.ultima_atualizacao = datetime.now()
    
    # Verificar se é hora de atualizar os dados (a cada 1 minuto)
    agora = datetime.now()
    tempo_desde_atualizacao = (agora - st.session_state.ultima_atualizacao).total_seconds()
    recarregar = tempo_desde_atualizacao > 60 # 1 minuto em segundos
    
    if recarregar:
        st.session_state.ultima_atualizacao = agora
        print(f"Recarregando dados... Última atualização: {tempo_desde_atualizacao:.1f}s atrás")
    
    # Painel de configuração se modo_config estiver ativo
    if modo_config:
        with header_container:
            st.markdown("""
            <div style="background-color: #F5F5F5; padding: 10px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #1976D2;">
                <h3 style="color: #1976D2; margin: 0 0 10px 0;">Modo de Configuração</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_from = st.date_input(
                    "Data inicial", 
                    value=datetime.now() - timedelta(days=30),
                    format="DD/MM/YYYY",
                    key="main_date_from"
                )
            
            with col2:
                date_to = st.date_input(
                    "Data final", 
                    value=datetime.now(),
                    format="DD/MM/YYYY",
                    key="main_date_to"
                )
            
            with col3:
                tempo_slide = st.number_input(
                    "Tempo por slide (segundos)",
                    min_value=5,
                    max_value=60,
                    value=st.session_state.tempo_slide,
                    step=5
                )
                st.session_state.tempo_slide = tempo_slide
            
            # Seleção de módulos
            st.markdown("### Módulos a exibir:")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                mostrar_conclusoes = st.checkbox("Conclusões", value=True)
            
            with col2:
                mostrar_producao = st.checkbox("Produção", value=True)
            
            with col3:
                mostrar_cartorio = st.checkbox("Cartório", value=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Conclusões", use_container_width=True):
                    # Usar redirecionamento direto para garantir que o slide seja mostrado
                    st.switch_page("main.py")
                    st.query_params["slide"] = 0
            
            with col2:
                if st.button("📈 Produção", use_container_width=True):
                    # Usar redirecionamento direto para garantir que o slide seja mostrado
                    st.switch_page("main.py")
                    st.query_params["slide"] = 6
            
            with col3:
                if st.button("📁 Cartório", use_container_width=True):
                    # Usar redirecionamento direto para garantir que o slide seja mostrado
                    st.switch_page("main.py")
                    st.query_params["slide"] = 9
            
            # Botões de ação
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Iniciar Apresentação", use_container_width=True):
                    st.switch_page("main.py")
                    st.query_params["config"] = 0
                    st.query_params["slide"] = slide_inicial
            
            with col2:
                if st.button("Recarregar Dados", use_container_width=True):
                    recarregar = True
                    st.success("Recarregando dados...")
                    # Recarregar a página para garantir que os dados serão atualizados
                    st.rerun()
    else:
        # Interface simplificada no modo apresentação
        with header_container:
            col1, col2, col3 = st.columns([7, 1, 2])
            
            with col1:
                # Título ajustado para o modo apresentação
                st.markdown("""
                <h1 style="font-size: 1.8rem; color: #1A237E; margin: 0; padding: 5px 0;">
                    Painel de Higienização
                </h1>
                """, unsafe_allow_html=True)
            
            with col3:
                # Mostrar a data e hora atual
                agora_str = agora.strftime("%d/%m/%Y %H:%M")
                st.markdown(f"""
                <div style="text-align: right; font-size: 1rem; color: #616161; padding: 5px 0; font-family: Arial, sans-serif;">
                    <i class="fas fa-calendar"></i> {agora_str}
                </div>
                """, unsafe_allow_html=True)
            
            # Botão oculto para modo config (apenas na apresentação)
            with col2:
                # Botão pequeno para entrar no modo de configuração
                if st.button("⚙️"):
                    st.switch_page("main.py")
                    st.query_params["config"] = 1
                    st.query_params["slide"] = slide_inicial
    
    # Guardar os valores de configuração em parâmetros
    mostrar_conclusoes = st.session_state.get('mostrar_conclusoes', True) if not modo_config else mostrar_conclusoes
    mostrar_producao = st.session_state.get('mostrar_producao', True) if not modo_config else mostrar_producao
    mostrar_cartorio = st.session_state.get('mostrar_cartorio', True) if not modo_config else mostrar_cartorio
    
    # Armazenar na sessão para uso futuro
    st.session_state['mostrar_conclusoes'] = mostrar_conclusoes
    st.session_state['mostrar_producao'] = mostrar_producao
    st.session_state['mostrar_cartorio'] = mostrar_cartorio
    
    # Aplicar estilo de fundo para o cabeçalho
    st.markdown("""
    <style>
    [data-testid="stHeader"] {
        background-color: white;
        border-bottom: 1px solid #E0E0E0;
        padding: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        # Container para exibir progresso
        progress_container = st.empty()
        message_container = st.empty()
        
        # Formatar datas para API
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")
        
        # Definir chave para sessão para evitar recarregar desnecessariamente
        data_cache_key = f"dados_apresentacao_{date_from_str}_{date_to_str}"
        
        # 1. Carregar dados de conclusões
        if mostrar_conclusoes and (data_cache_key not in st.session_state or recarregar):
            # Atualizar mensagem
            message_container.text("Carregando dados de conclusões...")
            
            # Carregar dados
            df, df_todos = carregar_dados_apresentacao(
                date_from=date_from_str,
                date_to=date_to_str,
                progress_bar=progress_container.progress(0),
                message_container=message_container
            )
            
            # Armazenar no cache da sessão
            st.session_state[data_cache_key] = (df, df_todos)
        elif mostrar_conclusoes:
            # Usar dados do cache
            df, df_todos = st.session_state[data_cache_key]
        else:
            # Dados vazios se não mostrar conclusões
            df, df_todos = pd.DataFrame(), pd.DataFrame()
        
        # 2. Carregar dados de produção
        if mostrar_producao and ('df_producao' not in st.session_state or recarregar):
            # Atualizar mensagem
            message_container.text("Carregando dados de produção...")
            
            try:
                # Carregar dados
                df_producao = carregar_dados_producao(
                    date_from=date_from_str,
                    date_to=date_to_str,
                    progress_bar=progress_container.progress(0.33),
                    message_container=message_container
                )
                
                # Verificar se os dados foram carregados corretamente
                if df_producao.empty:
                    message_container.warning("Dados de produção estão vazios!")
                else:
                    message_container.success(f"Dados de produção carregados com sucesso: {len(df_producao)} registros")
                
                # Armazenar no cache da sessão
                st.session_state['df_producao'] = df_producao
            except Exception as e:
                message_container.error(f"Erro ao carregar dados de produção: {str(e)}")
                import traceback
                print(f"Erro ao carregar dados de produção: {traceback.format_exc()}")
        
        # 3. Carregar dados de cartório
        if mostrar_cartorio and ('df_cartorio' not in st.session_state or recarregar):
            # Atualizar mensagem
            message_container.text("Carregando dados de cartório...")
            
            try:
                # Carregar dados
                df_cartorio = carregar_dados_cartorio(
                    progress_bar=progress_container.progress(0.66),
                    message_container=message_container
                )
                
                # Verificar se os dados foram carregados corretamente
                if df_cartorio.empty:
                    message_container.warning("Dados de cartório estão vazios!")
                else:
                    message_container.success(f"Dados de cartório carregados com sucesso: {len(df_cartorio)} registros")
                
                # Armazenar no cache da sessão
                st.session_state['df_cartorio'] = df_cartorio
                
                # Carregar dados de famílias (opcional, será carregado sob demanda se não disponível)
                try:
                    message_container.text("Carregando dados de famílias do cartório...")
                    from views.cartorio.analysis import analisar_familia_certidoes
                    df_familias = analisar_familia_certidoes()
                    if not df_familias.empty:
                        st.session_state['df_familias'] = df_familias
                        message_container.success(f"Dados de famílias carregados: {len(df_familias)} registros")
                except Exception as e:
                    message_container.error(f"Erro ao carregar famílias: {str(e)}")
                    import traceback
                    print(f"Erro de famílias: {traceback.format_exc()}")
            except Exception as e:
                message_container.error(f"Erro ao carregar dados de cartório: {str(e)}")
                import traceback
                print(f"Erro completo: {traceback.format_exc()}")
        
        # Adicionar pequena pausa para mensagens serem visíveis
        time.sleep(1)
        
        # Limpar containers
        progress_container.empty()
        message_container.empty()
    
    # Verificar se há dados de pelo menos um dos módulos
    tem_dados = (not df.empty and mostrar_conclusoes) or \
                ('df_producao' in st.session_state and not st.session_state['df_producao'].empty and mostrar_producao) or \
                ('df_cartorio' in st.session_state and not st.session_state['df_cartorio'].empty and mostrar_cartorio)
    
    if not tem_dados:
        st.error("Não foram encontrados dados para o período ou módulos selecionados.")
        return
    
    # Interface de apresentação - abordagem com tabs em vez de carrossel
    if not modo_config:
        # Criar tabs para cada slide
        total_tabs = 0
        if mostrar_conclusoes:
            total_tabs += 6  # 6 slides de conclusões
        if mostrar_producao: 
            total_tabs += 3  # 3 slides de produção
        if mostrar_cartorio:
            total_tabs += 3  # 3 slides de cartório
        
        # Criar tabs e mantê-las escondidas no modo apresentação
        slide_tabs = st.tabs([f"Slide {i+1}" for i in range(total_tabs)])
        
        # Índice da tab atual
        tab_index = 0
        
        # Adicionar CSS para ocultar as tabs no modo apresentação
        if not modo_config:
            st.markdown("""
            <style>
            [data-testid="stTabBar"] {
                display: none;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Slides de Conclusões
        if mostrar_conclusoes:
            # Aqui seriam adicionados os slides de conclusões
            # Por enquanto, deixamos como placeholder para não modificar conclusões.py
            tab_index += 6
        
        # Slides de Produção
        if mostrar_producao:
            with slide_tabs[tab_index]:
                slide_producao_metricas_macro()
            tab_index += 1
            
            with slide_tabs[tab_index]:
                slide_producao_status_responsavel()
            tab_index += 1
            
            # Slide de pendências por responsável seria adicionado aqui
            tab_index += 1
        
        # Slides de Cartório
        if mostrar_cartorio:
            # Aqui seriam adicionados os slides de cartório
            tab_index += 3
        
        # Selecionar a tab atual com base no slide_inicial
        if 0 <= slide_inicial < total_tabs:
            # Usar JavaScript para clicar na tab correta
            tab_script = f"""
            <script>
                function select_tab() {{
                    const tabs = window.parent.document.querySelectorAll('[data-testid="stTabBar"] button');
                    if (tabs.length > {slide_inicial}) {{
                        tabs[{slide_inicial}].click();
                    }}
                }}
                setTimeout(select_tab, 100);
            </script>
            """
            st.markdown(tab_script, unsafe_allow_html=True)
            
            # Lógica de temporização para avançar automaticamente
            if not modo_config:
                # Contador de tempo restante
                time_container = st.empty()
                
                # Começar contagem regressiva
                tempo_restante = st.session_state.tempo_slide
                proximo_slide = (slide_inicial + 1) % total_tabs
                
                # Mostrar contador em formato pequeno no canto
                time_container.markdown(f"""
                <div style="position: fixed; bottom: 10px; right: 10px; background-color: rgba(25, 118, 210, 0.7); 
                     color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px; z-index: 1000;">
                    Próximo slide em {tempo_restante}s
                </div>
                """, unsafe_allow_html=True)
                
                # Aguardar o tempo definido
                time.sleep(tempo_restante)
                
                # Redirecionar para o próximo slide
                st.switch_page("main.py")
                st.query_params["slide"] = proximo_slide
                st.query_params["config"] = 0
