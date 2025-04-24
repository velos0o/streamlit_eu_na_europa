import streamlit as st
import pandas as pd
# Remover import re, não é mais necessário

# Importar AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# --- Função Auxiliar Copiada de visao_geral.py ---
# TODO: Considerar mover esta função para um módulo utils compartilhado
def simplificar_nome_estagio(nome):
    """ Simplifica o nome do estágio para exibição. """
    if pd.isna(nome):
        return "Desconhecido"

    codigo_estagio = str(nome) # Garante que é string

    # Mapeamento Atualizado com base na descrição do usuário e categorias
    mapeamento = {
        # SUCESSO -> VERDE
        'DT1052_16:SUCCESS': 'Entregue',
        'DT1052_34:SUCCESS': 'Entregue',
        'SUCCESS': 'Entregue',
        'DT1052_16:UC_JRGCW3': 'Física Entregue',
        'DT1052_34:UC_84B1S2': 'Física Entregue',
        'UC_JRGCW3': 'Física Entregue',
        'UC_84B1S2': 'Física Entregue',
        'DT1052_16:CLIENT': 'Emitida (Cliente)',
        'DT1052_34:CLIENT': 'Emitida (Cliente)',
        'DT1052_34:UC_D0RG5P': 'Emitida (Cliente)',
        'CLIENT': 'Emitida (Cliente)',
        'UC_D0RG5P': 'Emitida (Cliente)',

        # EM ANDAMENTO -> Amarelo
        'DT1052_16:UC_7F0WK2': 'Ass. Req. Cliente',
        'DT1052_34:UC_HN9GMI': 'Ass. Req. Cliente',
        'UC_7F0WK2': 'Ass. Req. Cliente',
        'UC_HN9GMI': 'Ass. Req. Cliente',
        'DT1052_16:NEW': 'Aguard. Certidão',
        'DT1052_34:NEW': 'Aguard. Certidão',
        'NEW': 'Aguard. Certidão',
        'DT1052_16:UC_HYO7L2': 'Devolutiva Busca',
        'DT1052_34:UC_5LAJNY': 'Devolutiva Busca',
        'UC_HYO7L2': 'Devolutiva Busca',
        'UC_5LAJNY': 'Devolutiva Busca',
        'DT1052_16:UC_IWZBMO': 'Solic. Cart. Origem',
        'DT1052_34:UC_8L5JUS': 'Solic. Cart. Origem',
        'UC_IWZBMO': 'Solic. Cart. Origem',
        'UC_8L5JUS': 'Solic. Cart. Origem',
        'DT1052_16:UC_KXHDOQ': 'Aguard. Cart. Origem',
        'DT1052_34:UC_6KOYL5': 'Aguard. Cart. Origem',
        'UC_KXHDOQ': 'Aguard. Cart. Origem',
        'UC_6KOYL5': 'Aguard. Cart. Origem',
        'DT1052_16:UC_RJC2DD': 'PRIO2 - Busca CRC',
        'DT1052_34:UC_RJC2DD': 'PRIO2 - Busca CRC',
        'UC_RJC2DD': 'PRIO2 - Busca CRC',
        'K85YX7': 'PRIO2 - Busca CRC', 
        'DT1052_16:PREPARATION': 'Montagem Req.',
        'DT1052_34:PREPARATION': 'Montagem Req.',
        'PREPARATION': 'Montagem Req.',
        'DT1052_16:UC_8EGMU7': 'Cart. Origem Prior.',
        'UC_8EGMU7': 'Cart. Origem Prior.',
        'DT1052_16:UC_QRZ6JG': 'Busca CRC',
        'DT1052_34:UC_68BLQ7': 'Busca CRC',
        'UC_QRZ6JG': 'Busca CRC',
        'UC_68BLQ7': 'Busca CRC',
        'DT1052_16:UC_K85YX7': 'Solic. C. Origem Prior.',
        'DT1052_34:UC_K85YX7': 'Solic. C. Origem Prior.',
        'UC_K85YX7': 'Solic. C. Origem Prior.',

        # FALHA -> VERMELHO
        'DT1052_16:FAIL': 'Devolução ADM',
        'DT1052_34:FAIL': 'Devolução ADM',
        'FAIL': 'Devolução ADM',
        'DT1052_16:UC_R5UEXF': 'Dev. ADM Verif.',
        'DT1052_34:UC_Z3J98J': 'Dev. ADM Verif.',
        'UC_R5UEXF': 'Dev. ADM Verif.',
        'UC_Z3J98J': 'Dev. ADM Verif.',
        'DT1052_16:UC_UG0UDZ': 'Solic. Duplicada',
        'DT1052_34:UC_LF04SU': 'Solic. Duplicada',
        'UC_UG0UDZ': 'Solic. Duplicada',
        'UC_LF04SU': 'Solic. Duplicada',
        'DT1052_16:UC_XM32IE': 'Sem Dados Busca',
        'DT1052_34:UC_XM32IE': 'Sem Dados Busca',
        'UC_XM32IE': 'Sem Dados Busca',
        'DT1052_16:UC_P61ZVH': 'Devolvido Req.',
        'DT1052_34:UC_2BAINE': 'Devolvido Req.',
        'UC_P61ZVH': 'Devolvido Req.',
        'UC_2BAINE': 'Devolvido Req.',
        'DT1052_16:UC_7L6CGJ': 'Cancelado',
        'DT1052_34:UC_7L6CGJ': 'Cancelado',
        'UC_7L6CGJ': 'Cancelado',
        'DT1052_16:UC_3LJ0KG': 'Não Trabalhar',
        'DT1052_34:UC_3LJ0KG': 'Não Trabalhar',
        'UC_3LJ0KG': 'Não Trabalhar',
    }

    # Tentar encontrar no mapeamento completo
    nome_legivel = mapeamento.get(codigo_estagio)

    # Se não encontrou e tem ':', tentar buscar só o código após ':'
    if nome_legivel is None and ':' in codigo_estagio:
        apenas_codigo = codigo_estagio.split(':')[-1]
        nome_legivel = mapeamento.get(apenas_codigo)

    # Se ainda não encontrou, retornar o código original (ou 'Desconhecido')
    if nome_legivel is None:
        if ':' in codigo_estagio:
            # Retorna só o código se não mapeado, para consistência
            return codigo_estagio.split(':')[-1]
        # Retorna o próprio código se não tiver ':' e não for mapeado
        return codigo_estagio if codigo_estagio else "Desconhecido"

    return nome_legivel

# TODO: Mover para utils
def categorizar_estagio(estagio_legivel):
    """ Categoriza o estágio simplificado em SUCESSO, EM ANDAMENTO ou FALHA. """
    sucesso = [
        'Entregue', 'Física Entregue', 'Emitida (Cliente)'
    ]
    falha = [
        'Devolução ADM', 'Dev. ADM Verif.', 'Solic. Duplicada',
        'Sem Dados Busca', 'Devolvido Req.', 'Cancelado',
        'Não Trabalhar', 'Devolutiva Busca' # Adicionada aqui conforme visao_geral
    ]

    if estagio_legivel in sucesso:
        return 'SUCESSO'
    elif estagio_legivel in falha:
        return 'FALHA'
    else:
        return 'EM ANDAMENTO' if estagio_legivel != "Desconhecido" else "DESCONHECIDO"

def exibir_pendencias(df_original):
    """
    Exibe uma tabela dinâmica mostrando a contagem de processos por responsável e estágio,
    com filtro por nome e estilização SCSS.
    """
    st.markdown("#### Pendências por Responsável e Estágio")

    if df_original is None or df_original.empty:
        st.warning("Não há dados disponíveis para exibir as pendências.")
        return

    df = df_original.copy()

    # --- Verificação das Colunas Essenciais ---
    coluna_responsavel = 'UF_CRM_12_1724194024'
    coluna_estagio_id = 'STAGE_ID'
    coluna_estagio_name = 'STAGE_NAME'

    if coluna_responsavel not in df.columns:
        st.error(f"Erro: A coluna de responsável '{coluna_responsavel}' não foi encontrada.")
        st.caption(f"Colunas disponíveis: {list(df.columns)}")
        return

    # Determinar qual coluna de estágio usar
    coluna_estagio = coluna_estagio_id if coluna_estagio_id in df.columns else coluna_estagio_name
    if coluna_estagio not in df.columns:
        st.error(f"Erro: Nenhuma coluna de estágio ('{coluna_estagio_id}' ou '{coluna_estagio_name}') encontrada.")
        st.caption(f"Colunas disponíveis: {list(df.columns)}")
        return

    # --- Pré-processamento ---
    df = df.dropna(subset=[coluna_responsavel, coluna_estagio])
    df = df[df[coluna_responsavel] != '']
    df[coluna_responsavel] = df[coluna_responsavel].astype(str)
    df['ESTAGIO_SIMPLIFICADO'] = df[coluna_estagio].astype(str).apply(simplificar_nome_estagio)

    def extrair_nome_responsavel(resp):
        if isinstance(resp, (list, dict)):
            if isinstance(resp, dict):
                return resp.get('name', resp.get('NAME', str(resp)))
            elif isinstance(resp, list) and len(resp) > 0 and isinstance(resp[0], dict):
                 return resp[0].get('name', resp[0].get('NAME', str(resp)))
            else:
                return str(resp)
        return str(resp)

    df['RESPONSAVEL_NOME'] = df[coluna_responsavel].apply(extrair_nome_responsavel)

    if df.empty:
        st.info("Não há dados válidos após o pré-processamento para gerar a tabela de pendências.")
        return

    # --- Criação da Tabela Dinâmica ---
    try:
        tabela_pendencias = pd.pivot_table(
            df,
            values='ID',
            index='RESPONSAVEL_NOME',
            columns='ESTAGIO_SIMPLIFICADO',
            aggfunc='count',
            fill_value=0
        )
        
        # --- Mapear Categorias para Colunas --- 
        mapa_categoria_coluna = {col: categorizar_estagio(col) for col in tabela_pendencias.columns}
        
        # Ordenar colunas por categoria e depois alfabeticamente
        ordem_categorias = {'EM ANDAMENTO': 1, 'SUCESSO': 2, 'FALHA': 3, 'DESCONHECIDO': 4}
        colunas_ordenadas = sorted(
            tabela_pendencias.columns,
            key=lambda col: (ordem_categorias.get(mapa_categoria_coluna.get(col, 'DESCONHECIDO'), 99), col)
        )
        tabela_pendencias = tabela_pendencias[colunas_ordenadas]
        # Atualizar mapa após reordenar (se necessário, mas as categorias são as mesmas)
        mapa_categoria_coluna = {col: categorizar_estagio(col) for col in tabela_pendencias.columns}

        # Adicionar Total por Responsável
        tabela_pendencias['TOTAL GERAL'] = tabela_pendencias.sum(axis=1)
        
        # Adicionar Total por Estágio
        tabela_pendencias.loc['TOTAL GERAL'] = tabela_pendencias.sum(axis=0)
        tabela_pendencias.loc['TOTAL GERAL', 'TOTAL GERAL'] = tabela_pendencias.loc['TOTAL GERAL', :].iloc[:-1].sum()

    except Exception as e:
        st.error(f"Erro ao criar a tabela dinâmica: {e}")
        st.dataframe(df[['RESPONSAVEL_NOME', 'ESTAGIO_SIMPLIFICADO', 'ID']].head())
        return

    # Resetar índice para tornar 'RESPONSAVEL_NOME' uma coluna
    tabela_pendencias_reset = tabela_pendencias.reset_index()
    # Renomear índice para um nome mais amigável
    tabela_pendencias_reset = tabela_pendencias_reset.rename(columns={'RESPONSAVEL_NOME': 'Responsável'})

    # --- Barra de Busca --- 
    termo_busca = st.text_input("Buscar por Responsável:", key="busca_responsavel_pendencias", placeholder="Digite parte do nome...")

    # --- Filtragem da Tabela ---
    tabela_filtrada = tabela_pendencias_reset.copy()
    if termo_busca:
        # Separar linha de total antes de filtrar
        total_row = tabela_filtrada[tabela_filtrada['Responsável'] == 'TOTAL GERAL']
        tabela_sem_total = tabela_filtrada[tabela_filtrada['Responsável'] != 'TOTAL GERAL']
        
        # Filtrar linhas (responsáveis) que contêm o termo de busca (case-insensitive)
        mask = tabela_sem_total['Responsável'].str.contains(termo_busca, case=False, na=False)
        tabela_filtrada = tabela_sem_total[mask]
        
        # Readicionar a linha de total no final, se houver resultados ou se a busca estiver vazia
        if not tabela_filtrada.empty:
             tabela_filtrada = pd.concat([tabela_filtrada, total_row], ignore_index=True)
        elif not termo_busca:
             tabela_filtrada = tabela_pendencias_reset # Mostra tudo se busca vazia
        else:
             # CORREÇÃO: Usar colunas de tabela_pendencias_reset (que inclui 'Responsável')
             tabela_filtrada = pd.concat([
                 pd.DataFrame(columns=tabela_pendencias_reset.columns), 
                 total_row
             ], ignore_index=True)
             st.info("Nenhum responsável encontrado.")

    # --- Configuração das Colunas para st.dataframe ---
    column_config = {
        "Responsável": st.column_config.TextColumn(
            "Responsável",
            help="Nome do responsável pelo processo.",
            width="large", # <-- Aumentar largura sugerida
        ),
        "TOTAL GERAL": st.column_config.NumberColumn(
            "Total", 
            help="Total de processos para o responsável.",
            format="%d",
            width="small",
        )
    }
    
    # Configurar colunas de estágio dinamicamente
    for col_name in colunas_ordenadas:
        column_config[col_name] = st.column_config.NumberColumn(
            col_name, # Usar o nome simplificado como label
            help=f"Processos no estágio {col_name}",
            format="%d", # Formato inteiro
            width="medium", # Tentar largura média para evitar quebra
            # Não há opção direta para cor ou alinhamento central aqui
        )

    # --- Exibição com st.dataframe ---
    st.markdown("##### Contagem de Processos")
    if tabela_filtrada.empty and termo_busca:
        pass # Mensagem já exibida
    elif tabela_filtrada.empty:
         st.info("Tabela de pendências vazia.")
    else:
        # DEBUG 2: Verificar colunas antes de exibir (REMOVIDO)
        # st.write("Debug 2: Colunas da tabela_filtrada:", tabela_filtrada.columns.tolist())
        
        st.dataframe(
            tabela_filtrada,
            column_config=column_config,
            use_container_width=True, # Tentar usar largura total
            hide_index=True # Esconder o índice numérico padrão do dataframe resetado
            # Não há parâmetro direto para altura fixa como no AgGrid
        )

    # --- Opção de Download (mantida por enquanto) ---
    @st.cache_data
    def convert_df_to_csv(df_to_convert):
       # Usar a tabela original antes do reset para manter o nome como índice
       return tabela_pendencias.to_csv(index=True).encode('utf-8')
    csv = convert_df_to_csv(tabela_pendencias)
    st.download_button(
       label="Download Tabela Completa como CSV",
       data=csv,
       file_name='pendencias_responsaveis_estagios.csv',
       mime='text/csv',
       key='download-pendencias-csv'
    ) 