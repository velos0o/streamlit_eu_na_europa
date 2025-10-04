"""
Módulo de processamento de emissões para a ficha da família
"""
import pandas as pd
from .business_logic import (
    normalizar_id_requerente,
    extrair_nome_limpo,
    gerar_chave_sem_id,
    ordenar_requerentes_por_posicao,
    obter_nome_pipeline_legivel,
    determinar_categoria_por_pipeline_status,
    aplicar_precedencia_pipelines
)

try:
    from views.cartorio_new.visao_geral import simplificar_nome_estagio
except ImportError:
    def simplificar_nome_estagio(nome):
        return str(nome) if nome else "Erro Import"


def processar_emissoes(emissoes_df, familia_serie):
    """
    Processa as emissões de uma família e retorna lista de requerentes com status.
    
    Returns:
        tuple: (requerentes_data_list, processamento_ok, resumo_categorias, total_certidoes)
    """
    if emissoes_df is None or emissoes_df.empty:
        return ([], False, {}, 0)
    
    # Aplicar simplificação de stage
    col_stage_para_simplificar = None
    if 'STAGE_ID' in emissoes_df.columns:
        col_stage_para_simplificar = 'STAGE_ID'
    elif 'STAGE_NAME' in emissoes_df.columns:
        col_stage_para_simplificar = 'STAGE_NAME'
    
    if not col_stage_para_simplificar:
        return ([], False, {}, 0)
    
    try:
        emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar].apply(simplificar_nome_estagio)
        
        # Normalização para estágio específico
        try:
            mask_uc_pbay8u = pd.Series(False, index=emissoes_df.index)
            if 'STAGE_ID' in emissoes_df.columns:
                mask_uc_pbay8u = mask_uc_pbay8u | emissoes_df['STAGE_ID'].astype(str).str.upper().str.contains('UC_PBAY8U', na=False)
            if 'STAGE_NAME' in emissoes_df.columns:
                mask_uc_pbay8u = mask_uc_pbay8u | emissoes_df['STAGE_NAME'].astype(str).str.upper().str.contains('UC_PBAY8U', na=False)
            emissoes_df.loc[mask_uc_pbay8u, 'STAGE_NAME_LEGIVEL'] = '[EM EXECUÇÃO]DEVOLUÇÃO ADM'
        except Exception:
            pass
        
        print("\n[DEBUG] Primeiras 20 linhas de emissoes_df com STAGE_NAME_LEGIVEL:")
        if not emissoes_df.empty:
            print(emissoes_df[['TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', col_stage_para_simplificar, 'STAGE_NAME_LEGIVEL']].head(20))
            
    except Exception:
        emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar]
    
    # Processar requerentes
    map_tipo_certidao = {'NASCIMENTO': 'Nascimento', 'CASAMENTO': 'Casamento', 'ÓBITO': 'Óbito'}
    cols_req = ['UF_CRM_34_ID_REQUERENTE', 'TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', 'STAGE_NAME_LEGIVEL', 'UF_CRM_34_POSICAO_ARVORE']
    
    # Verificar colunas necessárias
    colunas_faltantes = [col for col in cols_req if col not in emissoes_df.columns]
    if colunas_faltantes:
        print(f"[AVISO] Colunas ausentes: {colunas_faltantes}")
        if 'UF_CRM_34_POSICAO_ARVORE' in colunas_faltantes:
            emissoes_df['UF_CRM_34_POSICAO_ARVORE'] = "N/D"
            colunas_faltantes.remove('UF_CRM_34_POSICAO_ARVORE')
    
    if colunas_faltantes:
        return ([], False, {}, 0)
    
    # Preparar dados
    col_id_requerente = cols_req[0]
    emissoes_df[col_id_requerente] = emissoes_df[col_id_requerente].fillna('').astype(str)
    emissoes_df[col_id_requerente] = emissoes_df[col_id_requerente].apply(normalizar_id_requerente)
    emissoes_df['_NOME_LIMPO'] = emissoes_df['TITLE'].apply(extrair_nome_limpo)
    emissoes_df['_ID_REQUERENTE_ORIGINAL'] = emissoes_df[col_id_requerente].apply(
        lambda valor: valor if valor else 'ID Requerente N/D'
    )
    
    # Gerar chaves de grupo
    emissoes_df['_ID_REQUERENTE_GRUPO'] = emissoes_df['_ID_REQUERENTE_ORIGINAL']
    mask_sem_id = emissoes_df['_ID_REQUERENTE_ORIGINAL'] == 'ID Requerente N/D'
    emissoes_df.loc[mask_sem_id, '_ID_REQUERENTE_GRUPO'] = emissoes_df.loc[mask_sem_id].apply(gerar_chave_sem_id, axis=1)
    
    # Preencher valores
    emissoes_df[cols_req[1]] = emissoes_df[cols_req[1]].fillna('Nome N/D').astype(str)
    emissoes_df[cols_req[2]] = emissoes_df[cols_req[2]].fillna('Tipo N/D').astype(str)
    emissoes_df[cols_req[3]] = emissoes_df[cols_req[3]].fillna('Status N/D').astype(str)
    emissoes_df[cols_req[4]] = emissoes_df[cols_req[4]].fillna('Não informado').astype(str)
    
    # Agrupar por requerente e processar
    requerentes_data_list = []
    grouped_by_requerente = emissoes_df.groupby('_ID_REQUERENTE_GRUPO', sort=False)
    
    if grouped_by_requerente.ngroups > 0:
        for id_req_grupo, grupo in grouped_by_requerente:
            id_req_original = grupo['_ID_REQUERENTE_ORIGINAL'].iloc[0] if '_ID_REQUERENTE_ORIGINAL' in grupo.columns else id_req_grupo
            nome_req_bruto = ''
            if '_NOME_LIMPO' in grupo.columns and grupo['_NOME_LIMPO'].iloc[0]:
                nome_req_bruto = grupo['_NOME_LIMPO'].iloc[0]
            elif not grupo[cols_req[1]].empty:
                nome_req_bruto = grupo[cols_req[1]].iloc[0]
            else:
                nome_req_bruto = "Req. Desconhecido"

            posicao_arvore = grupo[cols_req[4]].iloc[0] if not grupo[cols_req[4]].empty else "N/D"

            # Limpar nome
            nome_limpo = str(nome_req_bruto)
            prefixes_to_remove = ["NASCIMENTO - ", "CASAMENTO - ", "ÓBITO - "]
            for prefix in prefixes_to_remove:
                if nome_limpo.startswith(prefix):
                    nome_limpo = nome_limpo[len(prefix):]
                    break
            nome_req_disp = nome_limpo.strip()

            if not nome_req_disp:
                nome_req_disp = "Requerente sem identificação"

            cert_status = {v: 'Dispensado' for k, v in map_tipo_certidao.items() if v}
            
            # Aplicar lógica de precedência
            pipeline_104_pronto = False
            registros_pipelines_superiores = []
            
            for _, row in grupo.iterrows():
                if 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) == '104':
                    if row[cols_req[3]] == 'PESQUISA PRONTA PARA EMISSÃO':
                        pipeline_104_pronto = True
                elif 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) in ['92', '94', '102']:
                    registros_pipelines_superiores.append(row)
            
            if pipeline_104_pronto and registros_pipelines_superiores:
                print(f"[DEBUG PRECEDÊNCIA] ID_REQUERENTE {id_req_original}: Pipeline 104 pronto, usando status dos pipelines superiores")
                for row in registros_pipelines_superiores:
                    tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                    if tipo_l:
                        cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]
            else:
                for _, row in grupo.iterrows():
                    tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                    if tipo_l:
                        cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]

            requerentes_data_list.append({
                'ID_Requerente': id_req_original,
                'ID_Requerente_Grupo': id_req_grupo,
                'Requerente': nome_req_disp,
                'Posição': posicao_arvore,
                **cert_status
            })
    
    # Ordenar por posição
    requerentes_data_list = ordenar_requerentes_por_posicao(requerentes_data_list)
    
    # Calcular resumo
    resumo_categorias, total_certidoes = calcular_resumo_emissoes(emissoes_df)
    
    return (requerentes_data_list, True, resumo_categorias, total_certidoes)


def calcular_resumo_emissoes(emissoes_df):
    """
    Calcula o resumo de emissões por categoria.
    
    Returns:
        tuple: (resumo_dict, total_certidoes)
    """
    # Definir emissões ativas
    df_emissoes_ativas = pd.DataFrame()
    total_certidoes = 0
    
    if emissoes_df is not None and not emissoes_df.empty and 'STAGE_NAME_LEGIVEL' in emissoes_df.columns:
        status_de_dispensa_reais = ["SOLICITAÇÃO DUPLICADA", "CANCELADO"]
        emissoes_df_valid_stages = emissoes_df[pd.notna(emissoes_df['STAGE_NAME_LEGIVEL'])].copy()
        emissoes_df_valid_stages['STAGE_NAME_LEGIVEL_UPPER'] = emissoes_df_valid_stages['STAGE_NAME_LEGIVEL'].astype(str).str.upper()
        
        df_emissoes_ativas = emissoes_df_valid_stages[
            ~emissoes_df_valid_stages['STAGE_NAME_LEGIVEL_UPPER'].isin(status_de_dispensa_reais)
        ].copy()
    elif emissoes_df is not None and not emissoes_df.empty:
        df_emissoes_ativas = emissoes_df.copy()
    
    # Aplicar precedência de pipelines no resumo
    df_emissoes_ativas = aplicar_precedencia_pipelines(df_emissoes_ativas)
    
    total_certidoes = len(df_emissoes_ativas)
    
    # Inicializar resumo
    resumo_categorias = {
        'Brasileiras Pendências': 0,
        'Brasileiras Pesquisas': 0,
        'Brasileiras Solicitadas': 0,
        'Brasileiras Emitida': 0,
        'AGUARDANDO DECISÃO CLIENTE': 0,
        'Paróquia Pendências': 0,
        'Paróquia Solicitadas': 0,
        'Paróquia Emitida': 0,
        'Pesquisa BR Pendências': 0,
        'Pesquisa BR Em Andamento': 0,
        'Pesquisa BR Concluída': 0,
        'Pesquisa BR Não Encontrada': 0,
        'Outros': 0
    }
    
    if not df_emissoes_ativas.empty:
        for _idx, certidao_ativa_row in df_emissoes_ativas.iterrows():
            status_legivel = certidao_ativa_row['STAGE_NAME_LEGIVEL']
            category_id = certidao_ativa_row.get('CATEGORY_ID', '')
            
            if pd.isna(status_legivel) or (isinstance(status_legivel, str) and not status_legivel.strip()):
                continue
            
            categoria_para_resumo = determinar_categoria_por_pipeline_status(category_id, status_legivel)
            
            if categoria_para_resumo.endswith("Dispensada"):
                continue
            
            if categoria_para_resumo in resumo_categorias:
                resumo_categorias[categoria_para_resumo] += 1
            else:
                resumo_categorias['Outros'] += 1
        
        # Calcular "Pasta C/Emissão Concluída" (métrica derivada)
        total_ativas = (resumo_categorias['Brasileiras Pendências'] + 
                       resumo_categorias['Brasileiras Pesquisas'] + 
                       resumo_categorias['Brasileiras Solicitadas'] + 
                       resumo_categorias['Brasileiras Emitida'] +
                       resumo_categorias.get('AGUARDANDO DECISÃO CLIENTE', 0))
        
        if total_ativas > 0 and total_ativas == resumo_categorias['Brasileiras Emitida']:
            resumo_categorias['Pasta C/Emissão Concluída'] = 1
        else:
            resumo_categorias['Pasta C/Emissão Concluída'] = 0
    
    return (resumo_categorias, total_certidoes)


