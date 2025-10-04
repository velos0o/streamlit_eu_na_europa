"""
Lógica de negócio para categorização e processamento de emissões
"""
import pandas as pd
import re
from unidecode import unidecode

# Mapeamento de pipelines
PIPELINE_NOME_MAP = {
    '92': 'Cartório 92',
    '94': 'Cartório 94',
    '102': 'Paróquia',
    '104': 'Pesquisa BR'
}


def determinar_categoria_por_pipeline_status(category_id, stage_name_legivel):
    """Determina a categoria do resumo baseada no pipeline (CATEGORY_ID) e status (STAGE_NAME_LEGIVEL)"""
    category_id_str = str(category_id)
    status_upper = str(stage_name_legivel).upper() if pd.notna(stage_name_legivel) else ""
    
    # Pipeline 92 e 94 (Cartórios Casa Verde e Tatuapé)
    if category_id_str in ['92', '94']:
        if status_upper == "AGUARDANDO DECISÃO CLIENTE":
            return "AGUARDANDO DECISÃO CLIENTE"
        if status_upper in ["AGUARDANDO CERTIDÃO", "BUSCA - CRC", "DEVOLUTIVA BUSCA - CRC", 
                          "APENAS ASS. REQ CLIENTE P/MONTAGEM", "MONTAGEM REQUERIMENTO CARTÓRIO", 
                          "SOLICITAR CARTÓRIO DE ORIGEM", "SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
                          "DEVOLUÇÃO ADM", "DEVOLVIDO REQUERIMENTO"] or "DEVOLUÇÃO ADM" in status_upper:
            return "Brasileiras Pendências"
        elif status_upper == "PESQUISA - BR":
            return "Brasileiras Pesquisas"
        elif status_upper == "AGUARDANDO CARTÓRIO ORIGEM":
            return "Brasileiras Solicitadas"
        elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
            return "Brasileiras Emitida"
        elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
            return "Brasileiras Dispensada"
            
    # Pipeline 102 (Paróquia)
    elif category_id_str == '102':
        if status_upper in ["SOLICITAR PARÓQUIA DE ORIGEM", "DEVOLUÇÃO ADM"] or "DEVOLUÇÃO ADM" in status_upper:
            return "Paróquia Pendências"
        elif status_upper == "AGUARDANDO PARÓQUIA DE ORIGEM":
            return "Paróquia Solicitadas"
        elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
            return "Paróquia Emitida"
        elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
            return "Paróquia Dispensada"
            
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
    
    return "Outros"


def obter_nome_pipeline_legivel(row: pd.Series) -> str:
    """Obtém nome legível do pipeline"""
    nome_pipeline = str(row.get('NOME_PIPELINE', '') or '').strip()
    if nome_pipeline:
        return nome_pipeline
    categoria_id_local = str(row.get('CATEGORY_ID', '') or '').strip()
    return PIPELINE_NOME_MAP.get(categoria_id_local, f"Pipeline {categoria_id_local}" if categoria_id_local else '')


def aplicar_precedencia_pipelines(df_emissoes):
    """
    Aplica lógica de precedência de pipelines.
    Se uma pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104 
    E tem registros nos pipelines superiores (92, 94, 102),
    remove o registro do pipeline 104 do DataFrame.
    """
    if df_emissoes is None or df_emissoes.empty:
        return df_emissoes
    
    if 'UF_CRM_34_ID_REQUERENTE' not in df_emissoes.columns or 'CATEGORY_ID' not in df_emissoes.columns:
        return df_emissoes
    
    df_processado = df_emissoes.copy()
    requerentes_para_remover_104 = []
    
    for id_requerente, grupo_req in df_processado.groupby('UF_CRM_34_ID_REQUERENTE'):
        tem_104_pronto = False
        tem_pipelines_superiores = False
        
        for _, row in grupo_req.iterrows():
            if str(row['CATEGORY_ID']) == '104' and row.get('STAGE_NAME_LEGIVEL') == 'PESQUISA PRONTA PARA EMISSÃO':
                tem_104_pronto = True
            elif str(row['CATEGORY_ID']) in ['92', '94', '102']:
                tem_pipelines_superiores = True
        
        if tem_104_pronto and tem_pipelines_superiores:
            requerentes_para_remover_104.append(id_requerente)
            print(f"[DEBUG PRECEDÊNCIA] ID_REQUERENTE {id_requerente}: Removendo pipeline 104 (precedência)")
    
    if requerentes_para_remover_104:
        mask_remover = (df_processado['UF_CRM_34_ID_REQUERENTE'].isin(requerentes_para_remover_104)) & (df_processado['CATEGORY_ID'].astype(str) == '104')
        df_processado = df_processado[~mask_remover].copy()
        print(f"[DEBUG PRECEDÊNCIA] Removidos {mask_remover.sum()} registros do pipeline 104 devido à precedência")
    
    return df_processado


def normalizar_id_requerente(valor: str) -> str:
    """Normaliza ID de requerente"""
    valores_invalidos_id_norm = {
        '', 'nan', 'none', 'null', 'n/d',
        'id requerente n/d', 'id req. nao localizado', 'id req. nao localizados',
        'id req. nao localizado.', 'id req. nao localizados.', 'id req. nao localizado)'
    }
    texto = str(valor or '').strip()
    texto_norm = unidecode(texto).lower()
    return '' if texto_norm in valores_invalidos_id_norm else texto


def extrair_nome_limpo(titulo: str) -> str:
    """Extrai nome limpo do título"""
    texto = str(titulo or '').strip()
    if ' - ' in texto:
        texto = texto.split(' - ', 1)[1]
    texto = re.sub(r'\(.*?\)', '', texto)
    return re.sub(r'\s+', ' ', texto).strip()


def gerar_chave_sem_id(row) -> str:
    """Gera chave única para requerentes sem ID"""
    nome_limpo = row.get('_NOME_LIMPO', '') or ''
    posicao_val = str(row.get('UF_CRM_34_POSICAO_ARVORE', '') or '').strip()
    partes = [unidecode(nome_limpo).upper()]
    if posicao_val:
        partes.append(unidecode(posicao_val).upper())
    base = '_'.join(partes).strip('_')
    base = re.sub(r'[^A-Z0-9]+', '_', base)
    if not base:
        base = f"REQUERENTE_{row.name}"
    return f"SEM_ID::{base}"


def ordenar_requerentes_por_posicao(requerentes_list):
    """Ordena requerentes por posição: ITALIANO, FAMILIAR, REQUERENTE"""
    def ordem_posicao(item):
        posicao = item.get('Posição', '').upper()
        if posicao == 'ITALIANO':
            return 1
        elif posicao in ['FAMILIAR', 'FAMILIA']:
            item['Posição'] = 'FAMILIAR'
            return 2
        elif posicao == 'REQUERENTE':
            return 3
        else:
            return 4
    
    requerentes_list.sort(key=ordem_posicao)
    return requerentes_list


