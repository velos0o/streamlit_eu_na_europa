import streamlit as st
import pandas as pd
# import plotly.express as px # Não usaremos plotly aqui
# import pydeck as pdk # Usaremos Folium
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from datetime import datetime

# Importar função de simplificação de estágio
from .visao_geral import simplificar_nome_estagio_comune

def exibir_mapa_comune(df_mapa, category_id):
    """
    Exibe um mapa com os processos para um CATEGORY_ID específico usando Folium.
    Adaptação da lógica de mapa anterior (mapa_cat58.py).
    
    Args:
        df_mapa (pd.DataFrame): DataFrame já filtrado para o category_id.
        category_id (str): O ID da categoria sendo exibida (22, 58 ou 60).
    """
    st.subheader(f"Mapa de Processos - Comune (Categoria {category_id})")
    
    # --- Colunas Essenciais --- 
    col_id = 'ID'
    col_title = 'TITLE'
    col_lat = 'latitude'
    col_lon = 'longitude'
    col_stage_id = 'STAGE_ID'
    col_coord_source = 'COORD_SOURCE'  # Adicionada coluna de fonte das coordenadas
    # Colunas de localização original (para popup)
    col_comune_orig = 'UF_CRM_12_1722881735827' 
    col_provincia_orig = 'UF_CRM_12_1743015702671'

    # Verificar se as colunas de coordenadas existem
    cols_essenciais = [col_id, col_title, col_lat, col_lon, col_stage_id]
    # Verificar opcionais para popup
    if col_comune_orig not in df_mapa.columns: col_comune_orig = None
    if col_provincia_orig not in df_mapa.columns: col_provincia_orig = None
    if col_coord_source not in df_mapa.columns: col_coord_source = None
        
    cols_faltantes = [col for col in cols_essenciais if col not in df_mapa.columns]
    if cols_faltantes:
        st.error(f"Colunas essenciais para o mapa não encontradas: {', '.join(cols_faltantes)}. Verifique o data_loader.")
        st.dataframe(df_mapa)
        return

    # --- Métricas de Mapeamento ---
    # Calcular estatísticas de correspondência antes de filtrar
    total_processos = len(df_mapa)
    
    # Remover linhas sem coordenadas válidas
    df_mapa_coords = df_mapa.dropna(subset=[col_lat, col_lon]).copy() # Usar .copy()
    
    pontos_no_mapa = len(df_mapa_coords)
    percentual_mapeado = (pontos_no_mapa / total_processos * 100) if total_processos > 0 else 0
    
    st.markdown("#### Métricas de Mapeamento")
    
    # Exibir Métricas Gerais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Processos", total_processos)
    with col2:
        st.metric("Processos Mapeados", pontos_no_mapa, f"{percentual_mapeado:.1f}%", delta_color="off")
    with col3:
        st.metric("Sem Coordenadas", total_processos - pontos_no_mapa)

    if df_mapa_coords.empty:
        st.warning(f"Nenhum processo com coordenadas válidas encontrado para a Categoria {category_id}.")
        
        # Exibir tabela de registros não mapeados
        registros_nao_mapeados = df_mapa[df_mapa[col_lat].isna() | df_mapa[col_lon].isna()].copy()
        if not registros_nao_mapeados.empty:
            with st.expander(f"Ver {len(registros_nao_mapeados)} Registros Sem Coordenadas", expanded=True):
                st.markdown(f"""
                <div style="background-color: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #ffa000;">
                <h4 style="color: #e65100; margin-top: 0;">Atenção: {len(registros_nao_mapeados)} registros sem coordenadas geográficas</h4>
                <p>Estes registros não puderam ser mapeados e podem requerer revisão manual dos campos de Comune/Província.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Selecionar colunas para exibição
                colunas_exibir = [
                    col_id, col_title, col_stage_id, col_provincia_orig, col_comune_orig
                ]
                
                # Filtrar apenas colunas que realmente existem no dataframe
                colunas_presentes = [col for col in colunas_exibir if col in registros_nao_mapeados.columns]
                df_exibir = registros_nao_mapeados[colunas_presentes].copy()
                
                st.dataframe(df_exibir, use_container_width=True, hide_index=True)
        
        return

    # ----- Filtro de Tempo (Data de Criação) -----
    col_data_filtro = 'CREATED_TIME' 
    df_filtrado_data = df_mapa_coords.copy() # Começa com todos os pontos com coordenadas
    
    if col_data_filtro in df_filtrado_data.columns:
        df_filtrado_data[col_data_filtro] = pd.to_datetime(df_filtrado_data[col_data_filtro], errors='coerce')
        df_datas_validas_mapa = df_filtrado_data.dropna(subset=[col_data_filtro])
        
        if not df_datas_validas_mapa.empty:
            min_date_mapa = df_datas_validas_mapa[col_data_filtro].min().date()
            max_date_mapa = df_datas_validas_mapa[col_data_filtro].max().date()
            
            filtro_ativo, data_inicio, data_fim = False, None, None
            with st.expander("Filtrar Mapa por Data de Criação", expanded=False):
                 filtro_ativo = st.checkbox("Ativar filtro de data", key=f"chk_data_mapa_{category_id}")
                 col_d1, col_d2 = st.columns(2)
                 with col_d1:
                      data_inicio = st.date_input("De:", min_value=min_date_mapa, max_value=max_date_mapa, value=min_date_mapa, key=f"data_ini_mapa_{category_id}", disabled=not filtro_ativo)
                 with col_d2:
                      data_fim = st.date_input("Até:", min_value=min_date_mapa, max_value=max_date_mapa, value=max_date_mapa, key=f"data_fim_mapa_{category_id}", disabled=not filtro_ativo)
            
            if filtro_ativo and data_inicio and data_fim:
                 start_dt = pd.to_datetime(data_inicio)
                 end_dt = pd.to_datetime(data_fim) + pd.Timedelta(days=1)
                 df_filtrado_data = df_filtrado_data[
                      (df_filtrado_data[col_data_filtro].notna()) & # Garantir que não há NaT após conversão
                      (df_filtrado_data[col_data_filtro] >= start_dt) &
                      (df_filtrado_data[col_data_filtro] < end_dt)
                 ]
                 if df_filtrado_data.empty:
                      st.info("Nenhum processo encontrado para o período de data selecionado.")
                      # Mostrar mapa vazio ou tabela vazia
                      # return 
        else:
             st.caption("Coluna de data para filtro não possui valores válidos.")
    else:
        st.caption(f"Coluna '{col_data_filtro}' não encontrada para filtro de data.")
    # ----- Fim Filtro de Tempo -----

    # DataFrame final para o mapa (após filtro de data, se aplicado)
    df_final_mapa = df_filtrado_data

    if df_final_mapa.empty:
        st.info("Nenhum dado para exibir no mapa com os filtros atuais.")
        # Opcional: Mostrar tabela vazia abaixo
    else:
        st.markdown("#### Mapa Interativo")
        try:
            # Criar um mapa interativo centrado na Itália
            map_center = [df_final_mapa[col_lat].mean(), df_final_mapa[col_lon].mean()]
            m = folium.Map(location=map_center, zoom_start=6)
            
            # Adicionar um cluster de marcadores
            marker_cluster = MarkerCluster().add_to(m)
            
            # Definir cores para cada tipo de correspondência
            cores = {
                'ExactMatch': 'green',      # Verde para qualquer match exato
                'FuzzyMatch': 'orange',     # Laranja para qualquer match fuzzy
                'PartialMatch': 'darkblue', # Azul escuro para parciais/fragmentos
                'PrefixMatch': 'lightblue', # Azul claro para prefixos
                'ProvinciaMatch': 'red',    # Vermelho para match por província
                'ProvinciaFuzzy': 'red',    # Vermelho para match fuzzy por província
                'Correção Província': 'red',
                'Correção Manual': 'purple', # Roxo para correções manuais
                'TextMatch': 'cadetblue',   # Azul cadete para match de texto
                'default': 'gray'           # Cinza para outros ou não especificado
            }
            
            # Adicionar marcadores para cada ponto com cores diferentes por tipo de match
            for idx, row in df_final_mapa.iterrows():
                # Adicionar nome legível do estágio para o popup
                stage_legivel = simplificar_nome_estagio_comune(row[col_stage_id])
                
                # Determinar a cor do marcador com base no tipo de match
                color = 'default'  # padrão
                if col_coord_source in df_final_mapa.columns:
                    source = str(row[col_coord_source]) if pd.notna(row[col_coord_source]) else ''
                    for key, cor_val in cores.items():
                        if key in source:
                            color = cor_val
                            break  # Usa a primeira chave encontrada
                
                # Função interna para formatar coordenadas com segurança
                def format_coord(val):
                    try:
                        if pd.notna(val):
                            return f"{float(val):.4f}"
                        return "N/A"
                    except (ValueError, TypeError):
                        return str(val)

                lat_formatted = format_coord(row[col_lat])
                lon_formatted = format_coord(row[col_lon])
                comune_orig_val = row.get(col_comune_orig, 'N/A') if col_comune_orig else 'N/A'
                provincia_orig_val = row.get(col_provincia_orig, 'N/A') if col_provincia_orig else 'N/A'
                coord_source_val = row.get(col_coord_source, 'N/A') if col_coord_source else 'N/A'
                
                # Criar popup com informações detalhadas
                popup_html = f"""
                <div style="font-family: Arial; width: 250px">
                    <h4 style="color: #1A237E; margin-bottom: 5px">{row.get(col_title, 'Processo')} (ID: {row.get(col_id, 'N/A')})</h4>
                    <p><strong>Comune (Orig):</strong> {comune_orig_val}</p>
                    <p><strong>Província (Orig):</strong> {provincia_orig_val}</p>
                    <p><strong>Estágio:</strong> {stage_legivel} ({row[col_stage_id]})</p>
                    <p><strong>Tipo de Match:</strong> {coord_source_val}</p>
                    <p><strong>Coordenadas:</strong> [{lat_formatted}, {lon_formatted}]</p>
                </div>
                """
                
                # Adicionar marcador ao cluster
                try:
                    lat_num = float(row[col_lat])
                    lon_num = float(row[col_lon])
                    
                    folium.Marker(
                        location=[lat_num, lon_num],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{comune_orig_val} ({row.get(col_id, 'ID')})",
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(marker_cluster)
                except (ValueError, TypeError) as e:
                    # Remover ou comentar o print de erro
                    # print(f"Erro ao converter coordenadas para o registro {row.get(col_id, 'ID?')}: {e}")
                    pass # Simplesmente ignora o ponto se houver erro de coordenada
            
            # Adicionar legenda ao mapa
            legend_html = '''
            <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; 
                        background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px">
                <p><strong>Legenda (Tipo de Match)</strong></p>
                <p><i class="fa fa-circle" style="color:green"></i> Match Exato</p>
                <p><i class="fa fa-circle" style="color:orange"></i> Match Fuzzy</p>
                <p><i class="fa fa-circle" style="color:darkblue"></i> Match Parcial/Fragmento</p>
                <p><i class="fa fa-circle" style="color:lightblue"></i> Match por Prefixo</p>
                <p><i class="fa fa-circle" style="color:red"></i> Match Província / Corr. Província</p>
                <p><i class="fa fa-circle" style="color:purple"></i> Correção Manual</p>
                <p><i class="fa fa-circle" style="color:cadetblue"></i> Match por Texto</p>
                <p><i class="fa fa-circle" style="color:gray"></i> Outro / Indefinido</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Exibir o mapa
            folium_static(m, width=None, height=600) # Ajustar altura se necessário
            st.caption(f"Mostrando {len(df_final_mapa)} processos no mapa.")
            
        except ImportError:
            st.error("As bibliotecas 'folium' e 'streamlit-folium' são necessárias para exibir o mapa interativo.")
            st.info("Instale com: pip install folium streamlit-folium")
            # Fallback para st.map
            st.warning("Exibindo mapa simplificado (instale folium para interatividade).")
            if not df_final_mapa.empty:
                st.map(df_final_mapa, latitude=col_lat, longitude=col_lon, size=10)
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o mapa Folium: {e}")
            st.exception(e)
            # Tentar exibir o mapa padrão como fallback
            try:
                if not df_final_mapa.empty:
                     st.warning("Tentando exibir mapa simplificado como fallback.")
                     st.map(df_final_mapa, latitude=col_lat, longitude=col_lon, size=10)
            except Exception as fallback_e:
                st.error(f"Falha ao exibir mapa simplificado: {fallback_e}")


    # ----- Tabela de Dados do Mapa (Filtrada) -----
    st.markdown("---")
    st.markdown("##### Dados exibidos no mapa")
    # Selecionar colunas para a tabela
    cols_tabela = [col_id, col_title, col_stage_id, col_lat, col_lon, col_data_filtro]
    if col_coord_source: 
        cols_tabela.append(col_coord_source)  # Adicionar coluna de fonte de coordenadas
    if col_comune_orig:
        cols_tabela.append(col_comune_orig)   # Adicionar coluna de comune original
    if col_provincia_orig:
        cols_tabela.append(col_provincia_orig) # Adicionar coluna de província original
        
    cols_tabela_presentes = [c for c in cols_tabela if c in df_final_mapa.columns]
    
    if not df_final_mapa.empty and cols_tabela_presentes:
        st.dataframe(df_final_mapa[cols_tabela_presentes], use_container_width=True)
    elif df_final_mapa.empty:
         st.caption("Nenhum dado para exibir na tabela com os filtros atuais.")
    else:
         st.warning("Não foi possível encontrar colunas para exibir na tabela.")
         
    # ----- Exibir Registros Não Mapeados -----
    registros_nao_mapeados = df_mapa[df_mapa[col_lat].isna() | df_mapa[col_lon].isna()].copy()
    if not registros_nao_mapeados.empty:
        with st.expander(f"Ver {len(registros_nao_mapeados)} Registros Não Mapeados (Sem Coordenadas Válidas)", expanded=False):
            st.markdown(f"""
            <div style="background-color: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #ffa000;">
            <h4 style="color: #e65100; margin-top: 0;">Atenção: {len(registros_nao_mapeados)} registros sem coordenadas geográficas válidas</h4>
            <p>Estes registros não puderam ser exibidos no mapa e podem requerer revisão manual dos campos de Comune/Província ou da geocodificação no `data_loader`.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Selecionar colunas para exibição
            colunas_exibir_nao_map = [
                col_id, col_title, col_stage_id, col_provincia_orig, col_comune_orig
            ]
            # Adicionar coluna de fonte de coordenadas se existir, para ajudar no debug
            if col_coord_source in registros_nao_mapeados.columns:
                 colunas_exibir_nao_map.append(col_coord_source)
            
            # Filtrar apenas colunas que realmente existem no dataframe
            colunas_presentes_nao_map = [col for col in colunas_exibir_nao_map if col in registros_nao_mapeados.columns]
            df_exibir_nao_map = registros_nao_mapeados[colunas_presentes_nao_map].copy()
            
            st.dataframe(df_exibir_nao_map, use_container_width=True, hide_index=True)

            # Adicionar botão de download para os não mapeados
            csv_nao_mapeados = df_exibir_nao_map.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Registros Não Mapeados (CSV)",
                data=csv_nao_mapeados,
                file_name=f"registros_nao_mapeados_cat{category_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime='text/csv',
                key=f'download-nao-mapeados-cat{category_id}'
            ) 