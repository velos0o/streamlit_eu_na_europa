import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def slide_producao_pendencias_responsavel_v2(df):
    """
    Exibe um relatório de pendências por responsável com visualização aprimorada (versão 2)
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados de produção (ignorado, usamos df_producao da session_state)
    """
    # Usar os dados de produção armazenados na session_state
    if 'df_producao' in st.session_state and not st.session_state['df_producao'].empty:
        df = st.session_state['df_producao']
    
    if df.empty:
        st.warning("Não há dados disponíveis para exibir pendências por responsável.")
        return
    
    st.markdown('<h2 class="slide-title">Produção - Pendências por Responsável</h2>', unsafe_allow_html=True)
    
    # Verificar se temos os campos necessários
    campos_higienizacao = {
        'UF_CRM_1741183785848': 'Documentação',
        'UF_CRM_1741183721969': 'Cadastro',
        'UF_CRM_1741183685327': 'Estrutura', 
        'UF_CRM_1741183828129': 'Requerimento',
        'UF_CRM_1741198696': 'Emissões'
    }
    
    # Verificar quais campos existem no DataFrame
    campos_existentes = [campo for campo in campos_higienizacao.keys() if campo in df.columns]
    
    if not campos_existentes:
        st.error("Não foram encontrados campos de higienização nos dados.")
        return
    
    # Filtrar apenas os registros pendentes ou incompletos
    df_pendencias = df[df['UF_CRM_HIGILIZACAO_STATUS'].isin(['PENDENCIA', 'INCOMPLETO'])].copy()
    
    if df_pendencias.empty:
        st.success("Não há pendências! Todos os processos estão completos.")
        return
    
    # Criar DataFrame para armazenar as contagens de pendências
    pendencias_data = []
    
    # Processar cada responsável
    for responsavel in df_pendencias['ASSIGNED_BY_NAME'].unique():
        # Filtrar dados do responsável
        df_resp = df_pendencias[df_pendencias['ASSIGNED_BY_NAME'] == responsavel]
        
        # Inicializar contadores
        contagem = {'Responsável': responsavel}
        total_pendencias = 0
        
        # Contar pendências por categoria
        for campo_id, campo_nome in campos_higienizacao.items():
            if campo_id in df_resp.columns:
                # Lista de valores que contam como pendência (igual ao components/tables.py)
                valores_pendencia = [
                    'NÃO', 'Não', 'NAO', 'nao', 'não', 'N', 'n',
                    'NÃO SELECIONADO', 'Não Selecionado', 'NAO SELECIONADO', 
                    'Nao Selecionado', 'não selecionado', 'não selecionada',
                    'n/s', 'N/S', False, 'false', 'FALSE'
                ]
                
                # Criar máscara para identificar registros que são 'NÃO', 'NÃO SELECIONADO' ou equivalentes
                mascara_nao = df_resp[campo_id].astype(str).str.upper().isin([str(v).upper() for v in valores_pendencia])
                
                # Máscara para valores vazios ou nulos
                mascara_vazio = (
                    df_resp[campo_id].isna() | 
                    (df_resp[campo_id].astype(str).str.strip() == '') |
                    (df_resp[campo_id].astype(str).str.upper() == 'NAN') |
                    (df_resp[campo_id].astype(str).str.upper() == 'NONE') |
                    (df_resp[campo_id].astype(str).str.upper() == 'NULL')
                )
                
                # Contar todas as ocorrências de pendências
                pendencias = (mascara_nao | mascara_vazio).sum()
                contagem[campo_nome] = pendencias
                total_pendencias += pendencias
        
        # Adicionar total
        contagem['Total'] = total_pendencias
        
        # Adicionar à lista de dados
        pendencias_data.append(contagem)
    
    # Criar DataFrame com os dados de pendências
    df_pendencias_resumo = pd.DataFrame(pendencias_data)
    
    # Classificar por total de pendências (maior primeiro)
    df_pendencias_resumo = df_pendencias_resumo.sort_values('Total', ascending=False)
    
    # Preencher valores NaN com 0
    for campo in campos_higienizacao.values():
        if campo in df_pendencias_resumo.columns:
            df_pendencias_resumo[campo] = df_pendencias_resumo[campo].fillna(0).astype(int)
    
    # Exibir tabela de pendências usando HTML personalizado
    if not df_pendencias_resumo.empty:
        # Usar apenas a versão com componentes nativos do Streamlit (mais confiável)
        st.markdown("### Tabela de Pendências por Responsável")
        
        # Aplicar formatação condicional para destacar valores
        def destacar_celula(val):
            if pd.isna(val) or val == 0:
                return 'background-color: transparent'
            elif val == 1:
                return 'background-color: rgba(244, 67, 54, 0.5); color: black; font-weight: bold'
            else:
                return 'background-color: rgba(244, 67, 54, 1.0); color: white; font-weight: bold'
        
        # Destacar a coluna Total com cor diferente
        def destacar_total(val):
            return 'background-color: #1A237E; color: white; font-weight: bold'
        
        # Aplicar estilos ao dataframe
        df_styled = df_pendencias_resumo.style.applymap(
            destacar_celula, 
            subset=[col for col in df_pendencias_resumo.columns if col != 'Responsável' and col != 'Total']
        ).applymap(
            destacar_total,
            subset=['Total']
        ).format('{:.0f}', subset=[col for col in df_pendencias_resumo.columns if col != 'Responsável'])
        
        # Exibir dataframe estilizado
        st.dataframe(
            df_styled,
            use_container_width=True,
            height=min(400, 80 + 35 * len(df_pendencias_resumo)),
            column_config={
                "Responsável": st.column_config.TextColumn("Responsável", width="large"),
                **{campo: st.column_config.NumberColumn(campo, format="%d") 
                   for campo in campos_higienizacao.values() if campo in df_pendencias_resumo.columns},
                "Total": st.column_config.NumberColumn("Total", format="%d", width="medium")
            }
        )
        
        # Criar dois cards para mostrar informações de resumo usando elementos nativos do Streamlit
        col1, col2 = st.columns(2)
        
        # Calcular totais por categoria
        total_por_categoria = {
            campo: df_pendencias_resumo[campo].sum() if campo in df_pendencias_resumo.columns else 0
            for campo in campos_higienizacao.values()
        }
        
        # Encontrar a categoria mais crítica
        categoria_critica = max(total_por_categoria, key=total_por_categoria.get)
        total_geral = df_pendencias_resumo['Total'].sum()
        
        with col1:
            st.markdown("#### Resumo de Pendências")
            st.markdown(f"""
            - **Total de pendências:** {int(total_geral):,}
            - **Responsáveis com pendência:** {len(df_pendencias_resumo)}
            - **Categoria mais crítica:** {categoria_critica}
            """.replace(",", "."))
        
        with col2:
            st.markdown("#### Ações Recomendadas")
            st.markdown("""
            - Priorize a resolução das pendências em vermelho
            - Distribua tarefas entre a equipe
            - Monitore diariamente a evolução das pendências
            """)
        
        # Adicionar gráfico de barras empilhadas
        st.markdown("<h3 style='margin-top: 30px;'>Distribuição de Pendências</h3>", unsafe_allow_html=True)
        
        # Preparar dados para o gráfico
        df_grafico = df_pendencias_resumo.copy()
        
        # Filtrar apenas as colunas de categorias
        colunas_categorias = [col for col in campos_higienizacao.values() if col in df_grafico.columns]
        
        if len(colunas_categorias) > 0:
            # Limitar a 8 responsáveis para melhor visualização
            if len(df_grafico) > 8:
                df_grafico = df_grafico.head(8)
            
            # Criar gráfico
            fig = go.Figure()
            
            # Definir cores para as categorias - usar cores mais vibrantes
            cores = {
                'Documentação': '#E57373',  # Vermelho claro
                'Cadastro': '#FFB74D',      # Laranja
                'Estrutura': '#FFF176',     # Amarelo
                'Requerimento': '#81C784',  # Verde
                'Emissões': '#64B5F6'       # Azul
            }
            
            # Adicionar barras para cada categoria
            for categoria in colunas_categorias:
                cor = cores.get(categoria, px.colors.qualitative.Safe[colunas_categorias.index(categoria) % len(px.colors.qualitative.Safe)])
                fig.add_trace(go.Bar(
                    name=categoria,
                    x=df_grafico['Responsável'],
                    y=df_grafico[categoria],
                    marker_color=cor,
                    text=df_grafico[categoria],
                    textposition='auto'
                ))
            
            # Atualizar layout
            fig.update_layout(
                barmode='stack',
                title={
                    'text': 'Pendências por Categoria e Responsável',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 20, 'color': '#1A237E'}
                },
                xaxis_title='Responsável',
                yaxis_title='Número de Pendências',
                legend_title='Categoria',
                height=400,
                margin=dict(l=50, r=50, t=80, b=50),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14
                )
            )
            
            # Melhorar grid e eixos
            fig.update_xaxes(
                tickangle=30,
                title_font={"size": 14},
                tickfont={"size": 12},
            )
            fig.update_yaxes(
                gridcolor='lightgray',
                title_font={"size": 14},
                tickfont={"size": 12},
            )
            
            # Exibir o gráfico
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não foram encontradas pendências nos dados filtrados.") 