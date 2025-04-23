import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import unicodedata
import re
import os
import json
from unidecode import unidecode

# Try importing thefuzz, provide guidance if not found
try:
    from thefuzz import process, fuzz
except ImportError:
    st.warning("Biblioteca 'thefuzz' não encontrada para geocodificação avançada. Instale com: pip install thefuzz python-Levenshtein")
    process = None
    fuzz = None

def visualizar_mapa_cat58(df_comune_cat58):
    """
    Exibe um mapa interativo com os processos da Categoria 58, 
    mostrando a localização baseada em Comune/Província.
    Utiliza geocodificação similar à função original 'visualizar_providencias'.
    
    Args:
        df_comune_cat58 (pd.DataFrame): DataFrame contendo os dados da categoria 58,
                                       já com coordenadas (latitude, longitude) e fonte (COORD_SOURCE)
                                       adicionadas pelo data_loader.
    """
    st.markdown("""
    <h3 style="font-size: 26px; font-weight: 800; color: #1A237E; margin: 30px 0 15px 0; 
    padding-bottom: 8px; border-bottom: 2px solid #E0E0E0; font-family: Arial, Helvetica, sans-serif;">
    MAPA DE PROCESSOS (Categoria 58)</h3>
    """, unsafe_allow_html=True)

    if df_comune_cat58.empty:
        st.warning("Nenhum dado da Categoria 58 disponível para visualização no mapa.")
        return

    # --- Colunas Esperadas (verificar se existem) ---
    col_id = 'ID'
    col_title = 'TITLE'
    col_provincia_orig = 'PROVINCIA_ORIG'
    col_comune_orig = 'COMUNE_ORIG'
    col_stage_name = 'STAGE_NAME' # Pode ou não ser relevante para o popup
    col_lat = 'latitude' 
    col_lon = 'longitude' 
    col_coord_source = 'COORD_SOURCE' 

    # Verificar a existência das colunas essenciais para o mapa
    cols_essenciais_mapa = [col_id, col_title, col_comune_orig, col_provincia_orig, col_lat, col_lon, col_coord_source]
    cols_faltantes = [col for col in cols_essenciais_mapa if col not in df_comune_cat58.columns]
    
    if cols_faltantes:
        st.error(f"Erro: Colunas essenciais para o mapa não encontradas nos dados: {', '.join(cols_faltantes)}")
        st.info("Verifique se a função 'carregar_dados_comune' está retornando estas colunas.")
        # Mostrar colunas disponíveis para debug
        st.write("Colunas disponíveis:", df_comune_cat58.columns.tolist())
        return

    # --- Processamento e Exibição do Mapa ---
    
    # Filtrar dados que possuem coordenadas válidas
    # Assegura que as colunas são numéricas antes de filtrar NaNs
    try:
        df_comune_cat58[col_lat] = pd.to_numeric(df_comune_cat58[col_lat], errors='coerce')
        df_comune_cat58[col_lon] = pd.to_numeric(df_comune_cat58[col_lon], errors='coerce')
    except Exception as e:
        st.warning(f"Erro ao converter colunas de coordenadas para numérico: {e}")
        # Tenta continuar mesmo assim, mas pode falhar no dropna

    df_mapa = df_comune_cat58.dropna(subset=[col_lat, col_lon]).copy()
    
    pontos_no_mapa = len(df_mapa)
    total_processos = len(df_comune_cat58)
    percentual_mapeado = (pontos_no_mapa / total_processos * 100) if total_processos > 0 else 0

    st.markdown("#### Métricas de Mapeamento (Categoria 58)")
    
    # Calcular contagens por tipo de match (baseado na coluna COORD_SOURCE)
    count_exact_cp = df_mapa[df_mapa[col_coord_source].str.contains('ExactMatch_ComuneProv', na=False)].shape[0]
    count_exact_c = df_mapa[df_mapa[col_coord_source].str.contains('ExactMatch_Comune', na=False)].shape[0]
    count_fuzzy = df_mapa[df_mapa[col_coord_source].str.contains('FuzzyMatch', na=False)].shape[0]
    count_partial = df_mapa[df_mapa[col_coord_source].str.contains('PartialMatch', na=False)].shape[0]
    count_text = df_mapa[df_mapa[col_coord_source].str.contains('TextMatch', na=False)].shape[0]
    count_manual = df_mapa[df_mapa[col_coord_source].str.contains('Correção Manual', na=False)].shape[0]
    count_provincia = df_mapa[df_mapa[col_coord_source].str.contains('ProvinciaMatch|Correção Província', regex=True, na=False)].shape[0]
    count_prefix = df_mapa[df_mapa[col_coord_source].str.contains('PrefixMatch', na=False)].shape[0]
    
    # Contagem de registros sem coordenadas válidas
    count_no_match = total_processos - pontos_no_mapa

    # Exibir Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Processos (Cat 58)", total_processos)
    with col2:
        st.metric("Processos Mapeados", pontos_no_mapa, f"{percentual_mapeado:.1f}%", delta_color="off")
    with col3:
        st.metric("Sem Coordenadas", count_no_match)

    # Mostrar estatísticas detalhadas por tipo de correspondência
    st.markdown("##### Detalhes da Correspondência")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"*   **Match Exato (Comune+Prov):** {count_exact_cp}")
        st.markdown(f"*   **Match Exato (Comune):** {count_exact_c}")
        st.markdown(f"*   **Match Fuzzy:** {count_fuzzy}")
        st.markdown(f"*   **Match Parcial/Fragmento:** {count_partial}")
    with col2:
        st.markdown(f"*   **Match por Prefixo:** {count_prefix}")
        st.markdown(f"*   **Match por Província:** {count_provincia}")
        st.markdown(f"*   **Correções Manuais:** {count_manual}")
        st.markdown(f"*   **Match por Texto:** {count_text}")
        

    # Exibir Mapa aprimorado com Folium
    if not df_mapa.empty:
        try:
            # Criar um mapa interativo centrado na Itália
            m = folium.Map(location=[42.5, 12.5], zoom_start=6)
            
            # Adicionar um cluster de marcadores
            marker_cluster = MarkerCluster().add_to(m)
            
            # Definir cores para cada tipo de correspondência (simplificado se necessário)
            cores = {
                'ExactMatch': 'green',      # Verde para qualquer match exato
                'FuzzyMatch': 'orange',      # Laranja para qualquer match fuzzy
                'PartialMatch': 'darkblue',  # Azul escuro para parciais/fragmentos
                'PrefixMatch': 'lightblue',   # Azul claro para prefixos
                'ProvinciaMatch': 'red',    # Vermelho para match por província
                'Correção Província': 'red',
                'Correção Manual': 'purple',  # Roxo para correções manuais
                'TextMatch': 'cadetblue', # Azul cadete para match de texto
                'default': 'gray'          # Cinza para outros ou não especificado
            }
            
            # Adicionar marcadores para cada ponto com cores diferentes por tipo de match
            for idx, row in df_mapa.iterrows():
                # Determinar a cor do marcador com base no tipo de match
                source = str(row[col_coord_source]) if pd.notna(row[col_coord_source]) else ''
                color = 'default' # padrão
                for key, cor_val in cores.items():
                    if key in source:
                        color = cor_val
                        break # Usa a primeira chave encontrada
                
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
                
                # Criar popup com informações detalhadas
                popup_html = f"""
                <div style="font-family: Arial; width: 250px">
                    <h4 style="color: #1A237E; margin-bottom: 5px">{row.get(col_title, 'Processo')} (ID: {row.get(col_id, 'N/A')})</h4>
                    <p><strong>Comune:</strong> {row.get(col_comune_orig, 'N/A')}</p>
                    <p><strong>Província:</strong> {row.get(col_provincia_orig, 'N/A')}</p>
                    <p><strong>Estágio:</strong> {row.get(col_stage_name, 'N/A')}</p>
                    <p><strong>Tipo de Match:</strong> {source}</p>
                    <p><strong>Coordenadas:</strong> [{lat_formatted}, {lon_formatted}]</p>
                </div>
                """
                
                # Adicionar marcador ao cluster
                try:
                    # Garantir que as coordenadas são numéricas
                    lat_num = float(row[col_lat])
                    lon_num = float(row[col_lon])
                    
                    folium.Marker(
                        location=[lat_num, lon_num],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{row.get(col_comune_orig, 'Localidade')} ({row.get(col_id, 'ID')})",
                        icon=folium.Icon(color=color, icon='info-sign') # Usar ícone padrão
                    ).add_to(marker_cluster)
                except (ValueError, TypeError) as e:
                    print(f"Erro ao converter coordenadas para o registro {row.get(col_id, 'ID?')}: {e}")
            
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
            st.subheader("Mapa Interativo (Categoria 58)")
            
            # Adicionar CSS para maximizar a largura do mapa (copiado do original)
            st.markdown("""
            <style>
            .reportview-container .main .block-container {
                max-width: 100% !important; /* Maximizar largura */
                padding-top: 1rem;
                padding-right: 1rem;
                padding-left: 1rem;
                padding-bottom: 1rem;
            }
            
            /* Ajustar container para o mapa Folium */
            .stApp {
                max-width: 100%;
            }
            
            [data-testid="stHorizontalBlock"] {
                width: 100%;
            }
            
            /* Aumentar largura do iframe do folium */
            iframe {
                width: 100%;
                min-height: 700px; /* Altura mínima */
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Usar um container HTML com a classe especial para o mapa
            folium_static(m, width=None, height=700) # Ajustar altura se necessário
            
            # Adicionar explicação abaixo do mapa
            st.info("""
            **Informações do Mapa:**
            - Os marcadores indicam a localização estimada dos processos da Categoria 58.
            - A cor do marcador representa o método utilizado para encontrar as coordenadas (veja legenda).
            - Clique nos marcadores para ver informações detalhadas de cada processo.
            """)
        except ImportError:
            st.error("As bibliotecas 'folium' e 'streamlit-folium' são necessárias para exibir o mapa interativo.")
            st.info("Instale com: pip install folium streamlit-folium")
            # Fallback para o mapa padrão do Streamlit (menos informativo)
            st.warning("Exibindo mapa simplificado.")
            st.map(df_mapa, latitude=col_lat, longitude=col_lon, size=10, use_container_width=True)
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o mapa Folium: {e}")
            # Tentar exibir o mapa padrão como fallback
            try:
                st.warning("Tentando exibir mapa simplificado como fallback.")
                st.map(df_mapa, latitude=col_lat, longitude=col_lon, size=10, use_container_width=True)
            except Exception as fallback_e:
                st.error(f"Falha ao exibir mapa simplificado: {fallback_e}")

    else:
        st.warning("Nenhum processo com coordenadas válidas encontrado na Categoria 58 para exibir no mapa.")

    # --- Tabela de Registros Sem Coordenadas (Opcional, mas útil) ---
    registros_nao_mapeados = df_comune_cat58[df_comune_cat58[col_lat].isna() | df_comune_cat58[col_lon].isna()].copy()

    if not registros_nao_mapeados.empty:
        with st.expander(f"Ver {len(registros_nao_mapeados)} Registros da Categoria 58 Sem Coordenadas", expanded=False):
            st.markdown(f"""
            <div style="background-color: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #ffa000;">
            <h4 style="color: #e65100; margin-top: 0;">Atenção: {len(registros_nao_mapeados)} registros sem coordenadas geográficas</h4>
            <p>Estes registros não puderam ser mapeados e podem requerer revisão manual dos campos de Comune/Província.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Selecionar colunas para exibição
            colunas_exibir_nao_map = [
                col_id, col_title, col_stage_name, col_provincia_orig, col_comune_orig
            ]
            
            # Filtrar apenas colunas que realmente existem no dataframe
            colunas_presentes_nao_map = [col for col in colunas_exibir_nao_map if col in registros_nao_mapeados.columns]
            df_exibir_nao_map = registros_nao_mapeados[colunas_presentes_nao_map].copy()
            
            # Renomear colunas para melhor visualização
            colunas_renomear_nao_map = {
                col_id: 'ID',
                col_title: 'Título',
                col_stage_name: 'Estágio', 
                col_provincia_orig: 'Província (Original)',
                col_comune_orig: 'Comune/Paróquia (Original)'
            }
            
            # Renomear apenas as colunas presentes
            df_exibir_nao_map = df_exibir_nao_map.rename(columns={
                k: v for k, v in colunas_renomear_nao_map.items() if k in df_exibir_nao_map.columns
            })
            
            st.dataframe(df_exibir_nao_map, use_container_width=True, hide_index=True) 