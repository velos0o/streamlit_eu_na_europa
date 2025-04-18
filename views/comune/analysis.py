import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from .data_loader import mapear_estagios_comune, mapear_estagios_macro

def criar_visao_geral_comune(df_comune):
    """
    Cria uma visão geral dos dados de COMUNE, incluindo estágios sem registros
    """
    if df_comune.empty:
        return pd.DataFrame()
    
    # Mapeamento de estágios
    mapa_estagios = mapear_estagios_comune()
    
    # Adicionar uma coluna com o nome legível do estágio
    df_comune['STAGE_NAME'] = df_comune['STAGE_ID'].map(mapa_estagios)
    
    # Agrupar por estágio e contar
    visao_geral = df_comune.groupby('STAGE_NAME').size().reset_index(name='QUANTIDADE')
    
    # Criar um DataFrame com todos os estágios definidos no mapeamento
    todos_estagios = pd.DataFrame({'STAGE_NAME': list(set(mapa_estagios.values()))})
    
    # Mesclar para garantir que todos os estágios estejam presentes
    visao_completa = pd.merge(todos_estagios, visao_geral, on='STAGE_NAME', how='left')
    
    # Preencher valores ausentes com zero
    visao_completa['QUANTIDADE'] = visao_completa['QUANTIDADE'].fillna(0).astype(int)
    
    # Ordenar por quantidade (decrescente)
    visao_completa = visao_completa.sort_values('QUANTIDADE', ascending=False)
    
    return visao_completa

def criar_visao_macro(df_comune):
    """
    Cria uma visão detalhada com todos os estágios do processo, incluindo os zerados
    """
    if df_comune.empty:
        return pd.DataFrame()
    
    # Mapeamento de estágios para os nomes legíveis
    mapa_estagios = mapear_estagios_comune()
    
    # Adicionar uma coluna com o estágio detalhado (usando o mesmo nome de coluna para compatibilidade)
    df_comune['MACRO_STAGE'] = df_comune['STAGE_ID'].map(mapa_estagios)
    
    # Agrupar por estágio e contar
    visao_macro = df_comune.groupby('MACRO_STAGE').size().reset_index(name='QUANTIDADE')
    
    # Criar um DataFrame com todos os estágios definidos no mapeamento
    todos_estagios = pd.DataFrame({'MACRO_STAGE': list(set(mapa_estagios.values()))})
    
    # Mesclar para garantir que todos os estágios estejam presentes
    visao_completa = pd.merge(todos_estagios, visao_macro, on='MACRO_STAGE', how='left')
    
    # Preencher valores ausentes com zero
    visao_completa['QUANTIDADE'] = visao_completa['QUANTIDADE'].fillna(0).astype(int)
    
    # Ordenar por quantidade (decrescente)
    visao_completa = visao_completa.sort_values('QUANTIDADE', ascending=False)
    
    return visao_completa

def cruzar_comune_deal(df_comune, df_deal, df_deal_uf):
    """
    Cruza os dados de COMUNE com os negócios (CRM_DEAL)
    """
    # Resumo inicial dos dataframes
    print(f"\n=== RESUMO ANTES DO CRUZAMENTO ===")
    print(f"df_comune: {len(df_comune)} registros")
    print(f"df_deal: {len(df_deal)} registros")
    print(f"df_deal_uf: {len(df_deal_uf)} registros")
    
    if df_comune.empty or df_deal.empty or df_deal_uf.empty:
        st.warning("Um dos DataFrames está vazio, não é possível fazer o cruzamento.")
        return pd.DataFrame()
    
    # Verificar se as colunas necessárias existem
    colunas_comune = df_comune.columns.tolist()
    colunas_deal = df_deal.columns.tolist()
    colunas_deal_uf = df_deal_uf.columns.tolist()
    
    # Imprimir informações para debug
    print(f"\n=== COLUNAS DISPONÍVEIS ===")
    print(f"Colunas em df_comune: {colunas_comune}")
    print(f"Colunas em df_deal: {colunas_deal}")
    print(f"Colunas em df_deal_uf: {colunas_deal_uf}")
    
    # Verificar coluna de cruzamento UF_CRM_12_1723552666 (COMUNE)
    if 'UF_CRM_12_1723552666' not in colunas_comune:
        # Tentar identificar colunas alternativas para cruzamento
        possiveis_colunas_comune = [col for col in colunas_comune if 'UF_CRM_' in col]
        
        if possiveis_colunas_comune:
            print(f"\n=== POSSÍVEIS COLUNAS DE CRUZAMENTO EM COMUNE ===")
            print(f"Possíveis alternativas: {possiveis_colunas_comune}")
            
            # Mostrar alguns valores de exemplo para cada coluna possível
            for col in possiveis_colunas_comune[:5]:  # limitar a 5 para não sobrecarregar
                valores = df_comune[col].dropna().unique()[:5]  # mostrar até 5 valores únicos
                print(f"Coluna {col} - Exemplos: {valores}")
                
            st.warning(f"Coluna 'UF_CRM_12_1723552666' não encontrada em df_comune. Verifique se existe uma coluna alternativa nos logs.")
        else:
            st.warning(f"Coluna 'UF_CRM_12_1723552666' não encontrada em df_comune e não foram identificadas alternativas.")
        
        return pd.DataFrame()
    
    # Verificar coluna de cruzamento UF_CRM_1722605592778 (DEAL_UF)
    if 'UF_CRM_1722605592778' not in colunas_deal_uf:
        # Tentar identificar colunas alternativas para cruzamento
        possiveis_colunas_deal = [col for col in colunas_deal_uf if 'UF_CRM_' in col]
        
        if possiveis_colunas_deal:
            print(f"\n=== POSSÍVEIS COLUNAS DE CRUZAMENTO EM DEAL_UF ===")
            print(f"Possíveis alternativas: {possiveis_colunas_deal}")
            
            # Mostrar alguns valores de exemplo para cada coluna possível
            for col in possiveis_colunas_deal[:5]:  # limitar a 5 para não sobrecarregar
                valores = df_deal_uf[col].dropna().unique()[:5]  # mostrar até 5 valores únicos
                print(f"Coluna {col} - Exemplos: {valores}")
                
            st.warning(f"Coluna 'UF_CRM_1722605592778' não encontrada em df_deal_uf. Verifique se existe uma coluna alternativa nos logs.")
        else:
            st.warning(f"Coluna 'UF_CRM_1722605592778' não encontrada em df_deal_uf e não foram identificadas alternativas.")
        
        return pd.DataFrame()
    
    # CORREÇÃO: Verificar se os campos contêm múltiplas URLs separadas por vírgulas
    # Verificar um valor exemplo em cada coluna
    exemplo_comune = df_comune['UF_CRM_12_1723552666'].dropna().iloc[0] if not df_comune['UF_CRM_12_1723552666'].dropna().empty else ''
    exemplo_deal = df_deal_uf['UF_CRM_1722605592778'].dropna().iloc[0] if not df_deal_uf['UF_CRM_1722605592778'].dropna().empty else ''
    
    print(f"\n=== ANÁLISE DE VALORES PARA CRUZAMENTO ===")
    print(f"Exemplo em UF_CRM_12_1723552666 (COMUNE): {exemplo_comune[:100]}...")
    print(f"Exemplo em UF_CRM_1722605592778 (DEAL_UF): {exemplo_deal[:100]}...")
    
    # Verificar se contém vírgulas (indicando múltiplas URLs)
    contem_virgulas_comune = ',' in str(exemplo_comune)
    contem_virgulas_deal = ',' in str(exemplo_deal)
    
    print(f"Campo COMUNE contém múltiplos valores separados por vírgula: {contem_virgulas_comune}")
    print(f"Campo DEAL_UF contém múltiplos valores separados por vírgula: {contem_virgulas_deal}")
    
    # Preparar DataFrame de COMUNE com mapeamento de estágios
    mapa_estagios = mapear_estagios_comune()
    df_comune_prep = df_comune.copy()
    
    if 'STAGE_ID' in df_comune_prep.columns:
        df_comune_prep['STAGE_NAME'] = df_comune_prep['STAGE_ID'].map(mapa_estagios)
    else:
        st.warning("Coluna 'STAGE_ID' não encontrada no DataFrame de comune.")
        # Criar uma coluna STAGE_NAME padrão para evitar erros
        df_comune_prep['STAGE_NAME'] = "DESCONHECIDO"
    
    # Preparar DataFrame de DEAL_UF
    try:
        print(f"\n=== JUNTANDO DEAL E DEAL_UF ===")
        print(f"Colunas utilizadas para join: 'ID' em df_deal e 'DEAL_ID' em df_deal_uf")
        
        df_deal_prep = pd.merge(df_deal, df_deal_uf, left_on='ID', right_on='DEAL_ID', how='inner')
        
        print(f"Resultado do join: {len(df_deal_prep)} registros (de {len(df_deal)} em df_deal e {len(df_deal_uf)} em df_deal_uf)")
    except Exception as e:
        st.warning(f"Erro ao mesclar df_deal e df_deal_uf: {str(e)}")
        # Criar um DataFrame vazio com as colunas necessárias
        df_cruzado = pd.DataFrame(columns=['STAGE_NAME', 'TEM_DEAL'])
        return df_cruzado
    
    # CORREÇÃO: Usar uma abordagem diferente para o cruzamento quando há múltiplos valores
    # Em vez de fazer um merge que explode os registros, vamos fazer um loop e verificar a correspondência
    
    # Inicializar o DataFrame de resultado como uma cópia do DataFrame do Comune
    df_cruzado = df_comune_prep.copy()
    
    # Inicializar uma coluna TEM_DEAL com False
    df_cruzado['TEM_DEAL'] = False
    
    # Inicializar colunas para armazenar informações do Deal
    df_cruzado['DEAL_ID'] = None
    df_cruzado['DEAL_TITLE'] = None
    
    # Iniciar contagem
    registros_processados = 0
    total_registros = len(df_cruzado)
    registros_com_match = 0
    
    # Criar um conjunto com todos os valores do campo UF_CRM_1722605592778 do deal para busca rápida
    # Se o campo contiver múltiplos valores separados por vírgula, tratar cada um como um valor separado
    valores_deal = set()
    
    for valor in df_deal_prep['UF_CRM_1722605592778'].dropna():
        if contem_virgulas_deal and isinstance(valor, str):
            # Dividir por vírgula e adicionar cada valor ao conjunto
            for v in valor.split(','):
                v_limpo = v.strip()
                if v_limpo:
                    valores_deal.add(v_limpo)
        else:
            # Adicionar o valor diretamente
            valores_deal.add(valor)
    
    print(f"Total de valores únicos em DEAL_UF após processamento: {len(valores_deal)}")
    
    # Para cada registro no Comune, verificar se há correspondência em Deal
    for idx, row in df_cruzado.iterrows():
        registros_processados += 1
        
        if registros_processados % 100 == 0:
            print(f"Processados {registros_processados}/{total_registros} registros ({registros_processados/total_registros*100:.1f}%)")
        
        valor_comune = row['UF_CRM_12_1723552666']
        tem_match = False
        deal_id = None
        deal_title = None
        
        # Verificar se o valor do Comune está no conjunto de valores Deal
        if pd.notna(valor_comune):
            if contem_virgulas_comune and isinstance(valor_comune, str):
                # Dividir por vírgula e verificar cada valor
                for v in valor_comune.split(','):
                    v_limpo = v.strip()
                    if v_limpo and v_limpo in valores_deal:
                        tem_match = True
                        break
            else:
                # Verificar o valor diretamente
                tem_match = valor_comune in valores_deal
        
        # Se encontrou correspondência, buscar informações do Deal correspondente
        if tem_match:
            registros_com_match += 1
            
            # Para simplicidade, não nos preocupamos em identificar qual Deal específico corresponde
            # Apenas marcamos como tendo correspondência
            df_cruzado.at[idx, 'TEM_DEAL'] = True
    
    print(f"\n=== RESULTADO DO CRUZAMENTO ===")
    print(f"Total de registros no Comune: {total_registros}")
    print(f"Registros com correspondência: {registros_com_match} ({registros_com_match/total_registros*100:.2f}%)")
    print(f"Registros sem correspondência: {total_registros - registros_com_match} ({(total_registros - registros_com_match)/total_registros*100:.2f}%)")
    
    # Verificar o tamanho do DataFrame resultante para garantir que não houve explosão
    print(f"Tamanho do DataFrame resultante: {len(df_cruzado)} registros")
    if len(df_cruzado) > len(df_comune) * 1.1:
        print("ALERTA: O DataFrame resultante é significativamente maior que o original!")
    
    # Garantir que a coluna STAGE_NAME exista
    if 'STAGE_NAME' not in df_cruzado.columns:
        df_cruzado['STAGE_NAME'] = "DESCONHECIDO"
    
    # Resumo por estágio
    if 'STAGE_NAME' in df_cruzado.columns and 'TEM_DEAL' in df_cruzado.columns:
        print(f"\n=== RESUMO DE CORRESPONDÊNCIAS POR ESTÁGIO ===")
        resumo = df_cruzado.groupby('STAGE_NAME').agg(
            TOTAL=('STAGE_NAME', 'count'),
            COM_DEAL=('TEM_DEAL', lambda x: sum(x)),
            PERCENTUAL=('TEM_DEAL', lambda x: f"{sum(x)/len(x)*100:.2f}%")
        )
        print(resumo)
    
    return df_cruzado

def analisar_distribuicao_deals(df_cruzado):
    """
    Analisa a distribuição de deals por estágio de COMUNE
    """
    if df_cruzado.empty:
        return pd.DataFrame()
    
    # Verificar colunas disponíveis no DataFrame
    print(f"Colunas disponíveis: {df_cruzado.columns.tolist()}")
    
    # Usar uma coluna que sabemos que existe para contar registros
    # Trocar 'ID' por outra coluna que certamente existe ou usar qualquer coluna
    distribuicao = df_cruzado.groupby('STAGE_NAME').agg(
        TOTAL=('STAGE_NAME', 'count'),  # Usar STAGE_NAME no lugar de ID para contar
        COM_DEAL=('TEM_DEAL', lambda x: sum(x)),
        SEM_DEAL=('TEM_DEAL', lambda x: sum(~x))
    ).reset_index()
    
    # Adicionar percentuais
    distribuicao['PERCENTUAL_COM_DEAL'] = (distribuicao['COM_DEAL'] / distribuicao['TOTAL'] * 100).round(2)
    
    # Ordenar por total
    distribuicao = distribuicao.sort_values('TOTAL', ascending=False)
    
    return distribuicao

def analisar_registros_sem_correspondencia(df_cruzado):
    """
    Realiza uma análise mais detalhada dos registros sem correspondência
    """
    if df_cruzado.empty or 'TEM_DEAL' not in df_cruzado.columns:
        return pd.DataFrame()
    
    # Filtrar apenas registros sem correspondência
    df_sem_match = df_cruzado[~df_cruzado['TEM_DEAL']].copy()
    
    if df_sem_match.empty:
        print("Todos os registros possuem correspondência!")
        return pd.DataFrame()
    
    print(f"Total de registros sem correspondência: {len(df_sem_match)}")
    
    # Análise por estágio
    if 'STAGE_NAME' in df_sem_match.columns:
        por_estagio = df_sem_match.groupby('STAGE_NAME').size().reset_index(name='QUANTIDADE')
        por_estagio = por_estagio.sort_values('QUANTIDADE', ascending=False)
        
        # Calcular percentual
        total = por_estagio['QUANTIDADE'].sum()
        por_estagio['PERCENTUAL'] = (por_estagio['QUANTIDADE'] / total * 100).round(2)
        
        print("\n=== Registros sem correspondência por estágio ===")
        print(por_estagio)
    
    # Análise por data de criação (se existir)
    if 'DATE_CREATE' in df_sem_match.columns:
        try:
            # Converter para datetime se ainda não for
            if not pd.api.types.is_datetime64_any_dtype(df_sem_match['DATE_CREATE']):
                df_sem_match['DATE_CREATE'] = pd.to_datetime(df_sem_match['DATE_CREATE'], errors='coerce')
            
            # Agrupar por mês/ano
            df_sem_match['MES_ANO'] = df_sem_match['DATE_CREATE'].dt.strftime('%Y-%m')
            por_periodo = df_sem_match.groupby('MES_ANO').size().reset_index(name='QUANTIDADE')
            por_periodo = por_periodo.sort_values('MES_ANO')
            
            print("\n=== Registros sem correspondência por período ===")
            print(por_periodo)
        except Exception as e:
            print(f"Erro ao analisar por data: {str(e)}")
    
    # Verificar valores no campo de cruzamento
    if 'UF_CRM_12_1723552666' in df_sem_match.columns:
        # Contar valores nulos ou vazios
        valores_nulos = df_sem_match['UF_CRM_12_1723552666'].isna().sum()
        valores_vazios = (df_sem_match['UF_CRM_12_1723552666'] == '').sum() if df_sem_match['UF_CRM_12_1723552666'].dtype == 'object' else 0
        
        print(f"\n=== Análise do campo de cruzamento UF_CRM_12_1723552666 ===")
        print(f"Valores nulos: {valores_nulos} ({valores_nulos/len(df_sem_match)*100:.2f}%)")
        print(f"Valores vazios: {valores_vazios} ({valores_vazios/len(df_sem_match)*100:.2f}%)")
        
        # Verificar valores mais comuns (excluindo nulos/vazios)
        valores_validos = df_sem_match[df_sem_match['UF_CRM_12_1723552666'].notna()]
        if not valores_validos.empty and valores_validos['UF_CRM_12_1723552666'].dtype == 'object':
            valores_validos = valores_validos[valores_validos['UF_CRM_12_1723552666'] != '']
            if not valores_validos.empty:
                mais_comuns = valores_validos['UF_CRM_12_1723552666'].value_counts().head(10)
                print(f"\nValores mais comuns que não têm correspondência:")
                print(mais_comuns)
    
    # Criar resumo estruturado para return
    resumo = {
        'total_sem_match': len(df_sem_match)
    }
    
    if 'STAGE_NAME' in df_sem_match.columns:
        resumo['por_estagio'] = por_estagio
    
    if 'DATE_CREATE' in df_sem_match.columns and 'MES_ANO' in df_sem_match.columns:
        resumo['por_periodo'] = por_periodo
    
    return resumo

def calcular_tempo_solicitacao(df_comune):
    """
    Calcula o tempo entre a data de criação e a última modificação dos registros
    """
    if df_comune.empty:
        return pd.DataFrame()
    
    # Verificar se as colunas necessárias existem
    colunas_necessarias = ['MOVED_TIME', 'UF_CRM_12_1723552666']
    if not all(col in df_comune.columns for col in colunas_necessarias):
        missing_cols = [col for col in colunas_necessarias if col not in df_comune.columns]
        print(f"Colunas ausentes: {missing_cols}")
        # Criar colunas faltantes com NaN para evitar erros
        for col in missing_cols:
            df_comune[col] = np.nan
    
    # Copiar o dataframe para não modificar o original
    df_calculo = df_comune.copy()
    
    # Converter as colunas de data/hora para datetime (se não forem)
    if 'MOVED_TIME' in df_calculo.columns:
        df_calculo['MOVED_TIME'] = pd.to_datetime(df_calculo['MOVED_TIME'], errors='coerce')
    
    # Filtrar apenas registros que possuem valores válidos para as colunas necessárias
    df_valido = df_calculo.dropna(subset=['MOVED_TIME', 'UF_CRM_12_1723552666'])
    
    # Verificar se há dados válidos após filtro
    if df_valido.empty:
        return pd.DataFrame(columns=['UF_CRM_12_1723552666', 'TEMPO_SOLICITACAO_HORAS', 'QUANTIDADE'])
    
    # Calcular o tempo de solicitação (assumindo que MOVED_TIME é quando o item entrou no estágio "NEW")
    df_valido['TEMPO_ATUAL'] = pd.Timestamp.now()
    df_valido['TEMPO_SOLICITACAO'] = df_valido['TEMPO_ATUAL'] - df_valido['MOVED_TIME']
    
    # Converter para horas
    df_valido['TEMPO_SOLICITACAO_HORAS'] = df_valido['TEMPO_SOLICITACAO'].dt.total_seconds() / 3600
    
    # Agrupar por UF_CRM_12_1723552666 e calcular média do tempo
    resultado = df_valido.groupby('UF_CRM_12_1723552666').agg(
        TEMPO_SOLICITACAO_HORAS=('TEMPO_SOLICITACAO_HORAS', 'mean'),
        QUANTIDADE=('TEMPO_SOLICITACAO_HORAS', 'count')
    ).reset_index()
    
    # Arredondar para 2 casas decimais
    resultado['TEMPO_SOLICITACAO_HORAS'] = resultado['TEMPO_SOLICITACAO_HORAS'].round(2)
    
    # Ordenar do maior tempo para o menor
    resultado = resultado.sort_values('TEMPO_SOLICITACAO_HORAS', ascending=False)
    
    return resultado

def criar_metricas_certidoes(df_comune):
    """
    Cria métricas agregadas para monitoramento das certidões, agrupadas por categoria
    """
    if df_comune.empty:
        return {}
    
    # Adicionar nomes legíveis dos estágios
    mapa_estagios = mapear_estagios_comune()
    df_comune['STAGE_NAME'] = df_comune['STAGE_ID'].map(mapa_estagios)
    
    # Definir as categorias e os estágios que pertencem a cada uma
    categorias = {
        "Solicitado - Aguardando Retorno": [
            "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO",
            "AGUARDANDO COMUNE/PARÓQUIA",
            "AGUARDANDO PDF"
        ],
        "Pendência de Solicitação Comune - Parceiro": [
            "PENDENTE",
            "PESQUISA NÃO FINALIZADA",
            "SOLICITAR",
            "SOLICITAR - TEM INFO"
        ],
        "Pendência de Solicitação Comune - Empresa": [
            "NEGATIVA COMUNE",
            "DEVOLUTIVA EMISSOR"
        ],
        "Entregas": [
            "DOCUMENTO FISICO ENTREGUE",
            "ENTREGUE PDF"
        ],
        "Processos Cancelados/Inativos": [
            "CANCELADO",
            "INSOLAR"  # Incluir outros estágios inativos aqui, se necessário
        ]
    }
    
    # Inicializar dicionário para armazenar as métricas
    metricas = {}
    
    # Computar as métricas para cada categoria
    for categoria, estagios in categorias.items():
        # Filtrar o dataframe pelos estágios da categoria
        df_categoria = df_comune[df_comune['STAGE_NAME'].isin(estagios)]
        
        # Agrupar por estágio e contar
        contagem = df_categoria.groupby('STAGE_NAME').size().reset_index(name='Certidões')
        
        # Adicionar total
        total = contagem['Certidões'].sum()
        
        # Ordernar por contagem (decrescente)
        contagem = contagem.sort_values('Certidões', ascending=False)
        
        # Armazenar métricas
        metricas[categoria] = {
            'dados': contagem, 
            'total': total
        }
    
    return metricas

def criar_metricas_tempo_dias(df_comune):
    """
    Cria métricas de tempo em dias, agrupadas por faixas de tempo,
    utilizando a DATA_SOLICITACAO_ORIGINAL.
    """
    if df_comune.empty:
        return {}

    # Verificar se a coluna DATA_SOLICITACAO_ORIGINAL existe
    coluna_data = 'DATA_SOLICITACAO_ORIGINAL'
    if coluna_data not in df_comune.columns:
        # Fallback para MOVED_TIME se a coluna original não existir
        coluna_data = 'MOVED_TIME'
        if coluna_data not in df_comune.columns:
            print(f"Colunas {coluna_data} e DATA_SOLICITACAO_ORIGINAL não encontradas.")
            return {}
        else:
            print(f"Aviso: Coluna DATA_SOLICITACAO_ORIGINAL não encontrada. Usando {coluna_data} como fallback.")

    # Copiar o dataframe para não modificar o original
    df_tempo = df_comune.copy()

    # Converter a coluna de data/hora para datetime
    df_tempo[coluna_data] = pd.to_datetime(df_tempo[coluna_data], errors='coerce')

    # Filtrar apenas registros que possuem valores válidos para a data
    df_tempo = df_tempo.dropna(subset=[coluna_data])

    if df_tempo.empty:
         print(f"Nenhum registro com data válida na coluna {coluna_data}.")
         return {}

    # Adicionar nomes legíveis dos estágios (se a coluna existir)
    if 'STAGE_ID' in df_tempo.columns:
        mapa_estagios = mapear_estagios_comune()
        df_tempo['STAGE_NAME'] = df_tempo['STAGE_ID'].map(mapa_estagios)
    else:
        # Se não houver STAGE_ID, criar uma coluna padrão para evitar erros no groupby
        df_tempo['STAGE_NAME'] = 'Desconhecido'


    # Calcular o tempo em dias desde a data de solicitação original
    df_tempo['TEMPO_ATUAL'] = pd.Timestamp.now(tz='UTC') # Usar timezone consistente
    # Garantir que a coluna de data também seja timezone-aware ou naive consistente
    if df_tempo[coluna_data].dt.tz is None:
        df_tempo[coluna_data] = df_tempo[coluna_data].dt.tz_localize('UTC')
    elif df_tempo[coluna_data].dt.tz != df_tempo['TEMPO_ATUAL'].dt.tz:
         df_tempo[coluna_data] = df_tempo[coluna_data].dt.tz_convert('UTC')


    df_tempo['TEMPO_DIAS'] = (df_tempo['TEMPO_ATUAL'] - df_tempo[coluna_data]).dt.total_seconds() / (24 * 3600)

    # Definir as categorias por faixas de tempo em dias - AJUSTADO
    categorias_tempo = {
        "Até 7 dias": (0, 7),
        "8 a 15 dias": (7, 15),
        "16 a 30 dias": (15, 30),
        "31 a 60 dias": (30, 60),
        "61 a 160 dias": (60, 160),         # Faixa intermediária
        "Mais de 160 dias": (160, float('inf')) # Nova faixa > 160 dias
    }

    # Inicializar dicionário para armazenar as métricas
    metricas_tempo = {}

    # Computar as métricas para cada categoria de tempo
    for categoria, (min_dias, max_dias) in categorias_tempo.items():
        # Filtrar o dataframe pela faixa de dias
        # Corrigido: inclui o limite inferior (>) e superior (<=)
        df_faixa = df_tempo[(df_tempo['TEMPO_DIAS'] > min_dias) & (df_tempo['TEMPO_DIAS'] <= max_dias)]

        # Agrupar por estágio e contar
        contagem = df_faixa.groupby('STAGE_NAME').size().reset_index(name='Certidões')

        # Adicionar total
        total = contagem['Certidões'].sum()

        # Ordenar por contagem (decrescente)
        contagem = contagem.sort_values('Certidões', ascending=False)

        # Calcular tempo médio da categoria
        tempo_medio = df_faixa['TEMPO_DIAS'].mean() if not df_faixa.empty else 0

        # Armazenar métricas
        metricas_tempo[categoria] = {
            'dados': contagem,
            'total': total,
            'tempo_medio': round(tempo_medio, 1)
        }

    return metricas_tempo

def calcular_tempo_solicitacao_providencia(df_comune, retornar_dados_individuais=False):
    """
    Calcula o tempo de solicitação (baseado na DATA_SOLICITACAO_ORIGINAL)
    cruzado com dados de província/comune.
    Retorna um DataFrame com tempo médio de solicitação por local OU
    o DataFrame com os dados individuais e o tempo calculado.

    Args:
        df_comune: DataFrame com os dados de COMUNE
        retornar_dados_individuais (bool): Se True, retorna o DataFrame com
                                            cálculos individuais antes da agregação.

    Returns:
        DataFrame: Agregado por local (default) ou individual.
    """
    if df_comune.empty:
        return pd.DataFrame()

    # Verificar coluna de data - Priorizar DATA_SOLICITACAO_ORIGINAL
    coluna_data = 'DATA_SOLICITACAO_ORIGINAL'
    if coluna_data not in df_comune.columns:
        coluna_data = 'MOVED_TIME' # Fallback
        if coluna_data not in df_comune.columns:
             print(f"Colunas {coluna_data} e DATA_SOLICITACAO_ORIGINAL não encontradas.")
             return pd.DataFrame()
        else:
            print(f"Aviso: Coluna DATA_SOLICITACAO_ORIGINAL não encontrada. Usando {coluna_data} como fallback.")


    # Verificar se as colunas de localização necessárias existem
    provincia_cols = ['PROVINCIA_ORIG', 'UF_CRM_12_1743015702671', 'PROVINCIA_NORM'] # Adicionado ID da provincia do data_loader
    comune_cols = ['COMUNE_ORIG', 'UF_CRM_12_1722881735827', 'COMUNE_NORM'] # Adicionado ID do comune do data_loader

    provincia_col = next((col for col in provincia_cols if col in df_comune.columns), None)
    comune_col = next((col for col in comune_cols if col in df_comune.columns), None)

    # Copiar o dataframe para não modificar o original
    df_calculo = df_comune.copy()

    # Converter a coluna de data para datetime
    df_calculo[coluna_data] = pd.to_datetime(df_calculo[coluna_data], errors='coerce')

    # Filtrar apenas registros que possuem valores válidos para a data
    df_valido = df_calculo.dropna(subset=[coluna_data])

    # Calcular o tempo de solicitação usando a coluna_data selecionada
    df_valido['TEMPO_ATUAL'] = pd.Timestamp.now(tz='UTC') # Usar timezone consistente
    # Garantir consistência de timezone
    if df_valido[coluna_data].dt.tz is None:
        # Tentativa de localizar com 'UTC', mas tratar erros caso hajam offsets inválidos
        try:
            df_valido[coluna_data] = df_valido[coluna_data].dt.tz_localize('UTC', ambiguous='infer', nonexistent='NaT')
        except Exception as e:
             print(f"Erro ao localizar timezone para {coluna_data}: {e}. Tentando converter para UTC sem localizar.")
             # Como alternativa, apenas garantir que não há timezone para comparar com now() localizado
             try:
                 df_valido[coluna_data] = df_valido[coluna_data].dt.tz_convert(None)
                 df_valido['TEMPO_ATUAL'] = df_valido['TEMPO_ATUAL'].dt.tz_convert(None)
             except Exception as inner_e:
                  print(f"Erro ao remover timezone: {inner_e}. Calculo de tempo pode ser impreciso.")
                  # Deixar como está e permitir a subtração (pode gerar aviso ou erro)
                  pass
    elif df_valido[coluna_data].dt.tz != df_valido['TEMPO_ATUAL'].tz:
         try:
             df_valido[coluna_data] = df_valido[coluna_data].dt.tz_convert('UTC')
         except Exception as e:
             print(f"Erro ao converter timezone para {coluna_data}: {e}. Calculo de tempo pode ser impreciso.")
             pass # Continuar mesmo assim

    # Calcular diferença, tratando erros na subtração
    try:
        df_valido['TEMPO_SOLICITACAO'] = df_valido['TEMPO_ATUAL'] - df_valido[coluna_data]
    except TypeError as e:
        print(f"Erro de tipo ao calcular TEMPO_SOLICITACAO (provavelmente TZs mistos): {e}")
        # Tentar forçar a remoção de TZs como último recurso
        try:
            df_valido[coluna_data] = df_valido[coluna_data].dt.tz_convert(None)
            df_valido['TEMPO_ATUAL'] = df_valido['TEMPO_ATUAL'].dt.tz_convert(None)
            df_valido['TEMPO_SOLICITACAO'] = df_valido['TEMPO_ATUAL'] - df_valido[coluna_data]
            print("Timezones removidos para permitir cálculo.")
        except Exception as final_e:
             print(f"Falha final ao calcular tempo: {final_e}. Retornando NaT.")
             df_valido['TEMPO_SOLICITACAO'] = pd.NaT

    # Converter para horas e dias
    df_valido['TEMPO_SOLICITACAO_HORAS'] = df_valido['TEMPO_SOLICITACAO'].dt.total_seconds() / 3600
    df_valido['TEMPO_SOLICITACAO_DIAS'] = df_valido['TEMPO_SOLICITACAO_HORAS'] / 24

    # Remover linhas onde o cálculo falhou (resultou em NaT)
    df_valido.dropna(subset=['TEMPO_SOLICITACAO_DIAS'], inplace=True)

    # Arredondar dias para melhor visualização e filtragem
    df_valido['TEMPO_SOLICITACAO_DIAS'] = df_valido['TEMPO_SOLICITACAO_DIAS'].round(1)

    # ------------------------------------------------------------------
    # Decidir o que retornar baseado no parâmetro
    # ------------------------------------------------------------------
    if retornar_dados_individuais:
        print(f"Retornando {len(df_valido)} registros individuais com tempo calculado.")
        # Selecionar colunas relevantes para a visualização individual
        colunas_retorno = ['ID', 'TITLE', 'STAGE_ID', 'STAGE_NAME', 'ASSIGNED_BY_NAME',
                           coluna_data, 'TEMPO_SOLICITACAO_DIAS', 'TEMPO_SOLICITACAO_HORAS',
                           provincia_col, comune_col, 'latitude', 'longitude']
        # Filtrar colunas que realmente existem no df_valido
        colunas_existentes = [col for col in colunas_retorno if col in df_valido.columns]
        return df_valido[colunas_existentes]
    # ------------------------------------------------------------------

    # Continuar com a agregação se retornar_dados_individuais for False

    # Filtrar também por locais que não são nulos (pelo menos um deve existir)
    # Mover esta filtragem para DEPOIS do cálculo do tempo, mas ANTES da agregação
    if provincia_col and comune_col:
         df_agregacao = df_valido[df_valido[provincia_col].notna() | df_valido[comune_col].notna()].copy()
    elif provincia_col:
         df_agregacao = df_valido[df_valido[provincia_col].notna()].copy()
    elif comune_col:
         df_agregacao = df_valido[df_valido[comune_col].notna()].copy()
    else: # Se nenhuma coluna de local foi encontrada, retorna vazio
        print("Nenhuma coluna de localização válida encontrada para agregação.")
        return pd.DataFrame()

    # Verificar se há dados válidos após filtro de localização
    if df_agregacao.empty:
         print(f"Nenhum registro com localização válida ({provincia_col} ou {comune_col}) para agregação.")
         return pd.DataFrame()

    # --- Agregação por Localização ---
    resultados = []

    # Agrupar por província (se a coluna existir)
    if provincia_col:
        resultado_provincia = df_agregacao.groupby(provincia_col).agg(
            TEMPO_SOLICITACAO_DIAS=('TEMPO_SOLICITACAO_DIAS', 'mean'),
            TEMPO_SOLICITACAO_HORAS=('TEMPO_SOLICITACAO_HORAS', 'mean'),
            QUANTIDADE=('ID', 'count'), # Usar ID ou outra coluna não nula para contagem
            LATITUDE=('latitude', lambda x: x.dropna().mean() if 'latitude' in df_agregacao.columns and x.dropna().any() else None),
            LONGITUDE=('longitude', lambda x: x.dropna().mean() if 'longitude' in df_agregacao.columns and x.dropna().any() else None)
        ).reset_index()
        resultado_provincia = resultado_provincia.rename(columns={provincia_col: 'LOCAL', 'LATITUDE': 'lat', 'LONGITUDE': 'lng'})
        resultado_provincia['TIPO'] = 'Província'
        resultados.append(resultado_provincia)

    # Agrupar por comune (se a coluna existir)
    if comune_col:
        resultado_comune = df_agregacao.groupby(comune_col).agg(
            TEMPO_SOLICITACAO_DIAS=('TEMPO_SOLICITACAO_DIAS', 'mean'),
            TEMPO_SOLICITACAO_HORAS=('TEMPO_SOLICITACAO_HORAS', 'mean'),
            QUANTIDADE=('ID', 'count'), # Usar ID ou outra coluna não nula
            LATITUDE=('latitude', lambda x: x.dropna().mean() if 'latitude' in df_agregacao.columns and x.dropna().any() else None),
            LONGITUDE=('longitude', lambda x: x.dropna().mean() if 'longitude' in df_agregacao.columns and x.dropna().any() else None)
        ).reset_index()
        resultado_comune = resultado_comune.rename(columns={comune_col: 'LOCAL', 'LATITUDE': 'lat', 'LONGITUDE': 'lng'})
        resultado_comune['TIPO'] = 'Comune'
        resultados.append(resultado_comune)

    # Juntar os DataFrames (se houver algum)
    if not resultados:
        print("Não foi possível agregar por Província ou Comune.")
        return pd.DataFrame()

    resultado_final = pd.concat(resultados, ignore_index=True)

    # Arredondar para 1 casa decimal
    resultado_final['TEMPO_SOLICITACAO_DIAS'] = resultado_final['TEMPO_SOLICITACAO_DIAS'].round(1)
    resultado_final['TEMPO_SOLICITACAO_HORAS'] = resultado_final['TEMPO_SOLICITACAO_HORAS'].round(1)

    # Ordenar do maior tempo para o menor
    resultado_final = resultado_final.sort_values('TEMPO_SOLICITACAO_DIAS', ascending=False)

    # Garantir que QUANTIDADE seja inteiro
    resultado_final['QUANTIDADE'] = resultado_final['QUANTIDADE'].astype(int)

    return resultado_final 