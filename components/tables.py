import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from api.bitrix_connector import get_higilizacao_fields, get_status_color

# Obter o caminho absoluto para a pasta utils
utils_path = os.path.join(Path(__file__).parents[1], 'utils')
sys.path.insert(0, str(utils_path))

# Agora importa diretamente do arquivo data_processor
from data_processor import format_status_text

def render_styled_table(df, height=None):
    """
    Renderiza tabela estilizada com CSS personalizado
    
    Args:
        df (pandas.DataFrame): DataFrame a ser exibido
        height (str, optional): Altura máxima da tabela (ex: '400px')
    """
    # Converter DataFrame para HTML com classes CSS
    html = df.to_html(classes='styled-table', escape=False)
    
    # Adicionar estilo para controlar altura, se especificado
    style_tag = f'<style>div.table-container {{ max-height: {height}; overflow-y: auto; }}</style>' if height else ''
    
    # Renderizar HTML
    st.markdown(
        f'{style_tag}<div class="table-container">{html}</div>',
        unsafe_allow_html=True
    )

def create_responsible_status_table(df):
    """
    Cria tabela de status por responsável
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        
    Returns:
        pandas.DataFrame: Tabela cruzada de responsáveis por status
    """
    if df.empty:
        return pd.DataFrame()
    
    # Garantir que temos as colunas necessárias
    if 'ASSIGNED_BY_NAME' not in df.columns or 'UF_CRM_HIGILIZACAO_STATUS' not in df.columns:
        return pd.DataFrame()
    
    # Preencher valores nulos no status como PENDENCIA
    df['UF_CRM_HIGILIZACAO_STATUS'] = df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
    
    # Criar tabela cruzada sem margens (sem linha e coluna de total)
    cross_tab = pd.crosstab(
        index=df['ASSIGNED_BY_NAME'],
        columns=df['UF_CRM_HIGILIZACAO_STATUS'],
        margins=False
    )
    
    # Garantir que todas as colunas existem
    for status in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA']:
        if status not in cross_tab.columns:
            cross_tab[status] = 0
    
    # Reordenar as colunas
    ordered_columns = ['PENDENCIA', 'INCOMPLETO', 'COMPLETO']
    cross_tab = cross_tab[ordered_columns]
    
    return cross_tab

def create_pendencias_table(df):
    """
    Cria uma tabela de pendências por responsável, contando todas as ocorrências de 'NÃO', 
    'NÃO SELECIONADO' ou campos vazios em cada coluna
    """
    if df.empty:
        return pd.DataFrame()

    # Campos específicos de higienização com seus nomes e IDs
    campos_higilizacao = {
        'UF_CRM_1741183785848': 'Documentação',        # DOCUMENTAÇÃO PEND/INFOS
        'UF_CRM_1741183721969': 'Cadastro',           # CADASTRO NA ARVORE HIGIELIZADO
        'UF_CRM_1741183685327': 'Estrutura',          # ESTRUTURA ARVORE HIGIENIZA
        'UF_CRM_1741183828129': 'Requerimento',       # REQUERIMENTO
        'UF_CRM_1741198696': 'Emissões'               # EMISSÕES BRASILEIRAS BITRIX24
    }

    # Lista de valores que contam como pendência
    valores_pendencia = [
        'NÃO', 'Não', 'NAO', 'nao', 'não', 'N', 'n',
        'NÃO SELECIONADO', 'Não Selecionado', 'NAO SELECIONADO', 
        'Nao Selecionado', 'não selecionado', 'não selecionada',
        'n/s', 'N/S', False, 'false', 'FALSE'
    ]

    # Inicializar dicionário para armazenar contagens
    contagens = {}

    # Para cada responsável
    for responsavel in df['ASSIGNED_BY_NAME'].unique():
        # Filtrar dados do responsável
        df_resp = df[df['ASSIGNED_BY_NAME'] == responsavel]
        
        contagens_resp = {}
        total_pendencias = 0
        
        # Para cada campo específico
        for campo_id, nome_campo in campos_higilizacao.items():
            # Verificar se o campo existe no DataFrame
            if campo_id in df_resp.columns:
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
                contagens_resp[nome_campo] = pendencias
                total_pendencias += pendencias
            else:
                contagens_resp[nome_campo] = 0
        
        # Adicionar ao dicionário principal
        contagens[responsavel] = {**contagens_resp, 'Total': total_pendencias}

    # Converter para DataFrame
    result_df = pd.DataFrame.from_dict(contagens, orient='index')
    
    # Reordenar as colunas para ter Total por último
    cols = [col for col in result_df.columns if col != 'Total'] + ['Total']
    result_df = result_df[cols]
    
    # Ordenar por Total em ordem decrescente
    result_df = result_df.sort_values('Total', ascending=False)
    
    # Resetar o índice e renomear a coluna do índice
    result_df = result_df.reset_index()
    result_df = result_df.rename(columns={'index': 'Responsável'})

    return result_df

def create_production_table(df):
    """
    Cria tabela de produção geral, contando todas as ocorrências de 'SIM' em cada campo
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        
    Returns:
        pandas.DataFrame: Tabela com produção por responsável
    """
    if df.empty:
        return pd.DataFrame()

    # Campos específicos de higienização com seus nomes e IDs
    campos_higilizacao = {
        'UF_CRM_1741183785848': 'Documentação',        # DOCUMENTAÇÃO PEND/INFOS
        'UF_CRM_1741183721969': 'Cadastro',           # CADASTRO NA ARVORE HIGIELIZADO
        'UF_CRM_1741183685327': 'Estrutura',          # ESTRUTURA ARVORE HIGIENIZA
        'UF_CRM_1741183828129': 'Requerimento',       # REQUERIMENTO
        'UF_CRM_1741198696': 'Emissões'               # EMISSÕES BRASILEIRAS BITRIX24
    }

    # Lista de valores que contam como concluído
    valores_sim = ['SIM', 'Sim', 'sim', 'S', 's', True, 'true', 'TRUE']

    # Inicializar dicionário para armazenar contagens
    contagens = {}

    # Para cada responsável
    for responsavel in df['ASSIGNED_BY_NAME'].unique():
        # Filtrar dados do responsável
        df_resp = df[df['ASSIGNED_BY_NAME'] == responsavel]
        
        contagens_resp = {}
        total_concluidos = 0
        
        # Para cada campo específico
        for campo_id, nome_campo in campos_higilizacao.items():
            # Verificar se o campo existe no DataFrame
            if campo_id in df_resp.columns:
                # Criar máscara para identificar registros que são 'SIM' ou equivalentes
                mascara_sim = df_resp[campo_id].astype(str).str.upper().isin([str(v).upper() for v in valores_sim])
                
                # Contar todas as ocorrências de SIM
                concluidos = mascara_sim.sum()
                contagens_resp[nome_campo] = concluidos
                total_concluidos += concluidos
            else:
                contagens_resp[nome_campo] = 0
        
        # Adicionar ao dicionário principal
        contagens[responsavel] = {**contagens_resp, 'Total': total_concluidos}

    # Converter para DataFrame
    result_df = pd.DataFrame.from_dict(contagens, orient='index')
    
    # Reordenar as colunas para ter Total por último
    cols = [col for col in result_df.columns if col != 'Total'] + ['Total']
    result_df = result_df[cols]
    
    # Ordenar por Total em ordem decrescente
    result_df = result_df.sort_values('Total', ascending=False)
    
    # Resetar o índice e renomear a coluna do índice
    result_df = result_df.reset_index()
    result_df = result_df.rename(columns={'index': 'Responsável'})

    return result_df 