import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import re # Para remoção de pontuação e prefixos
from unidecode import unidecode # Para remover acentos

# Try importing thefuzz, provide guidance if not found
try:
    from thefuzz import process, fuzz
except ImportError:
    st.error("Biblioteca 'thefuzz' não encontrada. Por favor, instale com: pip install thefuzz python-Levenshtein")
    # You might want to stop execution or return an empty DataFrame here
    # For now, let functions proceed but fuzzy matching will fail if called.
    process = None
    fuzz = None

# Carregar variáveis de ambiente
load_dotenv()

def _limpar_antes_normalizar(series):
    """Tenta remover texto extra após vírgula, parêntese, barra ou hífen e prefixos natti/matri."""
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    
    # Remover prefixos natti/matri primeiro
    series = series.astype(str).str.lower()
    series = series.str.replace(r'^natti\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^matri\s*[:-]?\s*', '', regex=True)
    # Remover prefixos como "-natti..." ou "- matri..."
    series = series.str.replace(r'^-\s*natti\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^-\s*matri\s*[:-]?\s*', '', regex=True)
    # MELHORIA: Remover prefixos de certidões específicos italianos
    series = series.str.replace(r'^nascita\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^matrimonio\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^certidao de\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^certidao\s*[:-]?\s*', '', regex=True)

    def clean_text(text):
        if pd.isna(text) or not isinstance(text, str): return text
        # Tenta dividir por separadores e pegar a primeira parte
        separadores = [',', '(', '/', '-', '[', ';', ':']  # Adicionados mais separadores
        for sep in separadores:
            if sep in text:
                text = text.split(sep, 1)[0]
        return text.strip()

    return series.apply(clean_text)

def _normalizar_localizacao(series):
    """Normalização agressiva para campos de localização."""
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
        
    # 1. Converter para string e minúsculas (já feito parcialmente em _limpar_antes_normalizar)
    normalized = series.fillna('').astype(str).str.lower()
    
    # 2. Remover acentos
    try:
        normalized = normalized.apply(lambda x: unidecode(x) if isinstance(x, str) else x)
    except Exception:
         normalized = pd.Series([unidecode(str(x)) for x in series.fillna('')], index=series.index)
         normalized = normalized.str.lower()

    # 3. Remover prefixos GERAIS comuns - AMPLIADO
    prefixos_gerais = [
        'comune di ', 'provincia di ', 'parrocchia di ', 'parrocchia ', 'citta di ', 
        'diocese di ', 'chiesa di ', 'chiesa parrocchiale di ', 'comune ', 'citta ',
        'diocesi ', 'diocesi di ', 'archivio di ', 'anagrafe di ', 'frazione di ', 'frazione ',
        'municipio di ', 'municipio ', 'ufficio anagrafe di ', 'ufficio di stato civile di ',
        'ufficio anagrafe ', 'ufficio di stato civile ', 'ufficio dello stato civile ',
        'parrocchia della ', 'parrocchia del ', 'parrocchia dei ', 'parrocchia degli ',
        'comune della ', 'comune del ', 'comune dei ', 'comune degli ',
        # Novas adições:
        'archidiocesi di ', 'archidiocesi ', 'arcidiocesi di ', 'arcidiocesi ',
        'basilica di ', 'basilica ', 'cappella di ', 'cappella ',
        'cattedrale di ', 'cattedrale ', 'chiesa arcipretale di ', 'chiesa arcipretale ',
        'chiesa collegiata di ', 'chiesa collegiata ', 'chiesa matrice di ', 'chiesa matrice ',
        'convento di ', 'convento ', 'monastero di ', 'monastero ',
        'pieve di ', 'pieve ', 'santuario di ', 'santuario ',
        'parrocchiale di ', 'parrocchiale ', 'vicaria di ', 'vicaria '
    ]
    for prefix in prefixos_gerais:
        normalized = normalized.str.replace(f'^{re.escape(prefix)}', '', regex=True)
        
    # 3.5 Remover prefixos RELIGIOSOS comuns (após os gerais) - AMPLIADO
    prefixos_religiosos = [
        'san ', 'santa ', 'santi ', 'santo ', 's ', 'ss ', 'st ', 
        'beato ', 'beata ', 'santissima ', 'santissimo ',
        'natale ', 'nativita di ', 'nativita ', 'nascita di ', 'nascita ', 
        'battesimo di ', 'battesimo ', 'maria ', 'madonna ',
        # Novas adições:
        'sant\'', 'sant ', 'santa maria ', 'santa maria di ', 'santa maria del ',
        'sacro cuore di ', 'sacro cuore ', 'sacro ', 'san giovanni ', 'san giovanni di ',
        'san michele ', 'san michele di ', 'san pietro ', 'san pietro di ',
        'san nicola ', 'san nicola di ', 'san lorenzo ', 'san lorenzo di ',
        'san martino ', 'san martino di ', 'san marco ', 'san marco di '
    ]
    for prefix in prefixos_religiosos:
        # Usar word boundary (\b) para evitar remover 'san' de 'sanremo'
        normalized = normalized.str.replace(f'^{re.escape(prefix)}(\\b)?', '', regex=True)

    # 4. Remover pontuação básica
    normalized = normalized.str.replace(r'[\'"\.,;!?()[\]{}]', '', regex=True)

    # 4.5 Remover sufixos de província (espaço + 2 letras maiúsculas no fim)
    # Primeiro remove o padrão com espaço, depois o padrão entre parênteses (se houver)
    normalized = normalized.str.replace(r'\s+[a-z]{2}$', '', regex=True) # Remove ' xx' no final
    normalized = normalized.str.replace(r'\s*\([a-z]{2}\)$', '', regex=True) # Remove ' (xx)' no final
    normalized = normalized.str.strip() # Garante remoção de espaços caso o sufixo fosse a única coisa após a limpeza

    # MELHORIA: Remover palavras irrelevantes para correspondência
    palavras_irrelevantes = [
        'della', 'dello', 'delle', 'degli', 'dei', 'del', 'di', 'da', 'dal', 'e', 'ed', 'in', 'con',
        'su', 'sul', 'sulla', 'sulle', 'sui', 'sugli', 'per', 'tra', 'fra', 'a', 'al', 'alla', 'alle',
        'ai', 'agli', 'il', 'lo', 'la', 'le', 'i', 'gli', 'un', 'uno', 'una', 'nello', 'nella', 'nelle',
        'negli', 'nei', 'all', 'dall', 'dall', 'dall',
        # Novas adições:
        'presso', 'vicino', 'sopra', 'sotto', 'davanti', 'dietro', 'accanto', 'oltre',
        'verso', 'senza', 'secondo', 'lungo', 'durante', 'dentro', 'fuori', 'prima', 'dopo',
        'contro', 'attraverso', 'circa', 'intorno', 'grazie', 'mediante', 'oltre', 'malgrado',
        'nonostante', 'salvo', 'eccetto', 'fino', 'verso'
    ]
    for palavra in palavras_irrelevantes:
        normalized = normalized.str.replace(r'\b' + palavra + r'\b', ' ', regex=True)

    # MELHORIA: Substituições para casos comuns
    substituicoes = {
        'sangiovanni': 'giovanni',
        'sangiuseppe': 'giuseppe',
        'sanlorenzo': 'lorenzo',
        'sanfrancesco': 'francesco',
        'sanmartino': 'martino',
        'santamaria': 'maria',
        'santantonio': 'antonio',
        'sanvincenzo': 'vincenzo',
        'santangelo': 'angelo',
        'santanna': 'anna',
        'sanmichele': 'michele',
        'sanmarco': 'marco',
        'sannicola': 'nicola',
        # Novas adições:
        'sanbartolomeo': 'bartolomeo',
        'ssantissima': 'santissima',
        'santmaria': 'maria',
        'santachiara': 'chiara',
        'santacaterina': 'caterina',
        'santandrea': 'andrea',
        'santagnese': 'agnese',
        'santarita': 'rita',
        'santabarbara': 'barbara',
        'santadomenica': 'domenica',
        'santapaola': 'paola',
        'santateresa': 'teresa',
        'santaeufemia': 'eufemia',
        'santabruna': 'bruna',
        'santaelena': 'elena',
        'santantonino': 'antonino',
        'santadiocesi': 'diocesi',
        'maddalena': 'magdalena',
        'battista': 'batista',
        'assunta': 'assumpta',
        'assunzione': 'assumpcao',
        'eucharistia': 'eucaristia',
        # Correções regionais e províncias:
        'treviso': 'treviso',
        'venezia': 'venezia',
        'veneza': 'venezia',
        'padova': 'padova',
        'podova': 'padova',
        'verona': 'verona',
        'vicenza': 'vicenza',
        'rovigo': 'rovigo',
        'belluno': 'belluno',
        'mantova': 'mantova',
        'mantua': 'mantova',
        'mantoa': 'mantova',
        'montova': 'mantova',
        'mântua': 'mantova',
        'brescia': 'brescia',
        'massa-carrara': 'massa carrara',
        'massa carrara': 'massa carrara',
        'verbano-cusio-ossola': 'verbano cusio ossola',
        'verbano-cusi': 'verbano cusio ossola',
        'vibo-valentia': 'vibo valentia',
        'pesaro-urbino': 'pesaro e urbino',
        'chiete': 'chieti',
        'biela': 'biella',
        'lodi': 'lodi',
        'novara': 'novara',
        'varese': 'varese',
        'pavia': 'pavia',
        'vibo valentia': 'vibo valentia',
        'caltanissetta': 'caltanissetta',
        'agrigento': 'agrigento',
        'crotone': 'crotone',
        'sassari': 'sassari',
        'enna': 'enna',
        'avellino': 'avellino',
        'toscana': 'toscana'
    }
    for original, substituicao in substituicoes.items():
        normalized = normalized.str.replace(r'\b' + original + r'\b', substituicao, regex=True)

    # 5. Remover espaços extras
    normalized = normalized.str.strip()
    normalized = normalized.str.replace(r'\s+', ' ', regex=True)
    
    # 6. Tratar valores que se tornaram vazios após limpeza ou eram nulos originalmente
    normalized = normalized.replace(['', 'nan', 'none', 'null'], 'nao especificado', regex=False)
    
    return normalized

def carregar_datas_solicitacao():
    """
    Carrega as datas de solicitação originais do arquivo CSV.
    """
    # Construir o caminho relativo para o arquivo CSV
    script_dir = os.path.dirname(__file__) # Diretório atual do script
    csv_path = os.path.join(script_dir, 'Planilhas', 'Emissões Italiana, Antes de movimentação geral - comune.csv')

    try:
        df_datas = pd.read_csv(csv_path, usecols=['ID', 'Movido em'], dtype={'ID': str})
        # Renomear colunas
        df_datas = df_datas.rename(columns={'Movido em': 'DATA_SOLICITACAO_ORIGINAL'})
        # Converter para datetime, tratando erros
        df_datas['DATA_SOLICITACAO_ORIGINAL'] = pd.to_datetime(df_datas['DATA_SOLICITACAO_ORIGINAL'], errors='coerce')
        # Remover linhas onde a data não pôde ser convertida ou o ID é nulo
        df_datas.dropna(subset=['ID', 'DATA_SOLICITACAO_ORIGINAL'], inplace=True)
        # Remover IDs duplicados, mantendo o primeiro (ou último, dependendo da lógica desejada)
        df_datas.drop_duplicates(subset=['ID'], keep='first', inplace=True)
        return df_datas
    except FileNotFoundError:
        st.error(f"Arquivo CSV não encontrado em: {csv_path}")
        return pd.DataFrame({'ID': [], 'DATA_SOLICITACAO_ORIGINAL': []})
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return pd.DataFrame({'ID': [], 'DATA_SOLICITACAO_ORIGINAL': []})

def carregar_coordenadas_mapa():
    """
    Carrega as coordenadas do arquivo JSON mapa_italia.json e normaliza.
    """
    script_dir = os.path.dirname(__file__)
    json_path = os.path.join(script_dir, 'Mapa', 'mapa_italia.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        df_coords = pd.DataFrame(data_json)
        
        cols_necessarias = ['city', 'admin_name', 'lat', 'lng']
        if not all(col in df_coords.columns for col in cols_necessarias):
            cols_faltantes = [col for col in cols_necessarias if col not in df_coords.columns]
            st.error(f"JSON {json_path} sem colunas: {cols_faltantes}. Necessário: {cols_necessarias}")
            return pd.DataFrame()
        
        df_coords = df_coords[cols_necessarias].copy()
        df_coords = df_coords.rename(columns={
            'city': 'COMUNE_MAPA_ORIG', 
            'admin_name': 'PROVINCIA_MAPA_ORIG',
            'lat': 'latitude',
            'lng': 'longitude'
        })
        
        # Aplicar Normalização Agressiva
        df_coords['COMUNE_MAPA_NORM'] = _normalizar_localizacao(df_coords['COMUNE_MAPA_ORIG'])
        df_coords['PROVINCIA_MAPA_NORM'] = _normalizar_localizacao(df_coords['PROVINCIA_MAPA_ORIG'])
        
        # Remover duplicatas baseadas nas colunas normalizadas
        # Mantém a primeira ocorrência de uma combinação (Comune, Provincia)
        df_coords.drop_duplicates(subset=['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM'], keep='first', inplace=True)
        # Opcional: Remover duplicatas baseadas APENAS no comune (se quiser apenas uma coord por comune)
        # df_coords.drop_duplicates(subset=['COMUNE_MAPA_NORM'], keep='first', inplace=True)
        
        df_coords_final = df_coords[['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM', 'latitude', 'longitude']].copy()

        df_coords_final['latitude'] = pd.to_numeric(df_coords_final['latitude'], errors='coerce')
        df_coords_final['longitude'] = pd.to_numeric(df_coords_final['longitude'], errors='coerce')
        df_coords_final.dropna(subset=['latitude', 'longitude'], inplace=True)

        print(f"Carregadas {len(df_coords_final)} coordenadas únicas (Comune+Prov) e válidas do JSON.")
        return df_coords_final
        
    except FileNotFoundError:
        st.error(f"Arquivo JSON de coordenadas não encontrado em: {json_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler ou processar o arquivo JSON de coordenadas: {e}")
        return pd.DataFrame()

def carregar_dados_comune(category_id="22", force_reload=False):
    """
    Carrega dados do Bitrix para um category_id específico, normaliza locais, 
    junta datas e coordenadas.
    
    Args:
        category_id (str): O ID da categoria do item dinâmico a ser carregado. Padrão é "22".
        force_reload (bool): Se True, força o recarregamento dos dados ignorando o cache
        
    Returns:
        pandas.DataFrame: DataFrame com os dados processados
    """
    # Verificar se deve forçar o recarregamento
    if force_reload:
        st.info("Forçando recarregamento completo dos dados do Comune (ignorando cache)")
    
    # --- Carregar Bitrix --- 
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    url_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
    category_filter = {"dimensionsFilters": [[{
        "fieldName": "CATEGORY_ID", "values": [str(category_id)], "type": "INCLUDE", "operator": "EQUALS"
    }]]}
    df_items = load_bitrix_data(url_items, filters=category_filter, force_reload=force_reload)
    if df_items is None or df_items.empty:
        st.warning(f"Nenhum dado encontrado para a categoria {category_id}.")
        return pd.DataFrame()
    if 'ID' not in df_items.columns:
        st.error("Coluna 'ID' não encontrada nos dados carregados.")
        return pd.DataFrame()
    df_items['ID'] = df_items['ID'].astype(str)

    # --- Normalizar Locais Bitrix (com limpeza prévia do Comune) --- 
    col_provincia_bitrix = 'UF_CRM_12_1743015702671'
    col_comune_bitrix = 'UF_CRM_12_1722881735827'

    if col_provincia_bitrix in df_items.columns:
        df_items['PROVINCIA_ORIG'] = df_items[col_provincia_bitrix]
        # Normalizar província (pode não ser usada para merge, mas útil para exibição)
        df_items['PROVINCIA_NORM'] = _normalizar_localizacao(df_items[col_provincia_bitrix])
    else:
        df_items['PROVINCIA_ORIG'] = 'Não Especificado'; df_items['PROVINCIA_NORM'] = 'nao especificado'

    if col_comune_bitrix in df_items.columns:
        df_items['COMUNE_ORIG'] = df_items[col_comune_bitrix]
        # 1. Limpar antes de normalizar
        comunes_limpos = _limpar_antes_normalizar(df_items[col_comune_bitrix])
        # 2. Normalizar o resultado limpo
        df_items['COMUNE_NORM'] = _normalizar_localizacao(comunes_limpos)
    else:
        df_items['COMUNE_ORIG'] = 'Não Especificado'; df_items['COMUNE_NORM'] = 'nao especificado'
        
    # --- Juntar Datas CSV --- 
    df_datas_solicitacao = carregar_datas_solicitacao()
    if not df_datas_solicitacao.empty:
        df_items = pd.merge(df_items, df_datas_solicitacao, on='ID', how='left')
        print(f"{df_items['DATA_SOLICITACAO_ORIGINAL'].notna().sum()}/{len(df_items)} registros com data.")
    else: df_items['DATA_SOLICITACAO_ORIGINAL'] = pd.NaT
    
    # --- Juntar Coordenadas (JSON) --- 
    df_coordenadas = carregar_coordenadas_mapa()
    
    df_items['latitude'] = pd.NA
    df_items['longitude'] = pd.NA
    df_items['COORD_SOURCE'] = pd.NA

    if not df_coordenadas.empty and process is not None and fuzz is not None:
        print(f"\nIniciando busca de coordenadas para category_id={category_id} via correspondência múltipla...")
        # Lista de nomes de comunes únicos do JSON para comparar
        json_comunes_norm_list = df_coordenadas['COMUNE_MAPA_NORM'].unique().tolist()
        if 'nao especificado' in json_comunes_norm_list: 
            json_comunes_norm_list.remove('nao especificado')

        json_provincias_norm_list = df_coordenadas['PROVINCIA_MAPA_NORM'].unique().tolist()
        if 'nao especificado' in json_provincias_norm_list: 
            json_provincias_norm_list.remove('nao especificado')

        # Nova adição: Dicionário de correções manuais para casos específicos
        correcoes_manuais = {
            # Comune: (latitude, longitude, fonte)
            "piavon": (45.7167, 12.4333, "Correção Manual"),
            "vazzola": (45.8333, 12.3333, "Correção Manual"),
            "oderzo": (45.7833, 12.4833, "Correção Manual"),
            "valdobbiadene": (45.9000, 12.0333, "Correção Manual"),
            "motta di livenza": (45.7833, 12.6167, "Correção Manual"),
            "susegana": (45.8500, 12.2500, "Correção Manual"),
            "vittorio veneto": (45.9833, 12.3000, "Correção Manual"),
            "boara polesine": (45.0333, 11.7833, "Correção Manual"),
            "mansuè": (45.8333, 12.5167, "Correção Manual"),
            "san dona di piave": (45.6333, 12.5667, "Correção Manual"),
            "godego": (45.7000, 11.8667, "Correção Manual"),
            "castello di godego": (45.7000, 11.8667, "Correção Manual"),
            "legnago": (45.1833, 11.3167, "Correção Manual"),
            "stienta": (44.9500, 11.5500, "Correção Manual"),
            "montebelluna": (45.7833, 12.0500, "Correção Manual"),
            "vigasio": (45.3167, 10.9333, "Correção Manual"),
            "villorba": (45.7333, 12.2333, "Correção Manual"),
            "bondeno": (44.8833, 11.4167, "Correção Manual"),
            "trevignano": (45.7333, 12.1000, "Correção Manual"),
            "cavarzere": (45.1333, 12.0667, "Correção Manual"),
            "arcade": (45.7333, 12.2000, "Correção Manual"),
            "castelfranco veneto": (45.6667, 11.9333, "Correção Manual"),
            "gaiarine": (45.9000, 12.4833, "Correção Manual"),
            "borso del grappa": (45.8167, 11.8000, "Correção Manual"),
            "cittadella": (45.6500, 11.7833, "Correção Manual"),
            "albignasego": (45.3667, 11.8500, "Correção Manual"),
            "zero branco": (45.6167, 12.1667, "Correção Manual"),
            "sona": (45.4333, 10.8333, "Correção Manual"),
            "lendinara": (45.0833, 11.5833, "Correção Manual"),
            # Novas correções manuais
            "annone veneto": (45.8000, 12.7000, "Correção Manual"),
            "campagna lupia": (45.3667, 12.1000, "Correção Manual"),
            "campolongo maggiore": (45.3000, 12.0500, "Correção Manual"),
            "fossalta di portogruaro": (45.7833, 12.9000, "Correção Manual"),
            "meolo": (45.6167, 12.4667, "Correção Manual"),
            "marcon": (45.5500, 12.3000, "Correção Manual"),
            "pramaggiore": (45.7833, 12.7500, "Correção Manual"),
            "san stino di livenza": (45.7333, 12.6833, "Correção Manual"),
            "spinea": (45.4833, 12.1667, "Correção Manual"),
            "scorzè": (45.5833, 12.1000, "Correção Manual"),
            "salgareda": (45.7167, 12.5000, "Correção Manual"),
            "pravisdomini": (45.8167, 12.6333, "Correção Manual"),
            "cinto caomaggiore": (45.8167, 12.8333, "Correção Manual"),
            "ceggia": (45.6833, 12.6333, "Correção Manual"),
            "casale sul sile": (45.5833, 12.3333, "Correção Manual"),
            "mira": (45.4333, 12.1333, "Correção Manual"),
            "mogliano veneto": (45.5833, 12.2333, "Correção Manual"),
            "noale": (45.5500, 12.0667, "Correção Manual"),
            "preganziol": (45.6000, 12.2667, "Correção Manual"),
            "quarto d'altino": (45.5667, 12.3667, "Correção Manual"),
            "lancenigo": (45.7000, 12.2500, "Correção Manual"),
            "sanguinetto": (45.1833, 11.1500, "Correção Manual"),
            "bovolone": (45.2500, 11.1167, "Correção Manual"),
            "roncade": (45.6333, 12.3833, "Correção Manual"),
            "casier": (45.6500, 12.3000, "Correção Manual"),
            "paese": (45.7167, 12.1667, "Correção Manual"),
            "castelfranco": (45.6667, 11.9333, "Correção Manual"),
            "pederobba": (45.8500, 11.9833, "Correção Manual"),
            "vedelago": (45.7000, 12.0333, "Correção Manual"),
            "riese pio x": (45.7333, 11.9167, "Correção Manual"),
            "altivole": (45.7833, 11.9333, "Correção Manual"),
            "camposampiero": (45.5667, 11.9333, "Correção Manual"),
            "trebaseleghe": (45.5667, 12.0333, "Correção Manual"),
            "noventa padovana": (45.3833, 11.9500, "Correção Manual"),
            "chioggia": (45.2167, 12.2833, "Correção Manual"),
            "motta": (45.7833, 12.6167, "Correção Manual")
        }

        # Adicionar correções de províncias típicas italianas
        provincias_manuais = {
            "treviso": (45.6667, 12.2500, "Correção Província"),
            "venezia": (45.4375, 12.3358, "Correção Província"),
            "padova": (45.4167, 11.8667, "Correção Província"),
            "verona": (45.4386, 10.9928, "Correção Província"),
            "vicenza": (45.5500, 11.5500, "Correção Província"),
            "rovigo": (45.0667, 11.7833, "Correção Província"),
            "mantova": (45.1500, 10.7833, "Correção Província"),
            "belluno": (46.1333, 12.2167, "Correção Província"),
            "pordenone": (45.9667, 12.6500, "Correção Província"),
            "udine": (46.0667, 13.2333, "Correção Província"),
            "cremona": (45.1333, 10.0333, "Correção Província"),
            "brescia": (45.5417, 10.2167, "Correção Província"),
            "bergamo": (45.6950, 9.6700, "Correção Província"),
            "milano": (45.4669, 9.1900, "Correção Província"),
            "cosenza": (39.3000, 16.2500, "Correção Província"),
            "salerno": (40.6806, 14.7594, "Correção Província"),
            "caserta": (41.0667, 14.3333, "Correção Província"),
            "napoli": (40.8333, 14.2500, "Correção Província"),
            "potenza": (40.6333, 15.8000, "Correção Província"),
            "ferrara": (44.8333, 11.6167, "Correção Província"),
            "bologna": (44.4939, 11.3428, "Correção Província"),
            "lucca": (43.8428, 10.5039, "Correção Província"),
            "roma": (41.9000, 12.5000, "Correção Província"),
            "benevento": (41.1333, 14.7833, "Correção Província"),
            "campobasso": (41.5667, 14.6667, "Correção Província"),
            "cagliari": (39.2278, 9.1111, "Correção Província"),
            "messina": (38.1936, 15.5542, "Correção Província"),
            "catanzaro": (38.9000, 16.6000, "Correção Província"),
            "palermo": (38.1111, 13.3517, "Correção Província"),
            # Novas adições
            "trento": (46.0667, 11.1167, "Correção Província"),
            "bolzano": (46.5000, 11.3500, "Correção Província"),
            "gorizia": (45.9419, 13.6167, "Correção Província"),
            "trieste": (45.6486, 13.7772, "Correção Província"),
            "modena": (44.6458, 10.9256, "Correção Província"),
            "parma": (44.8015, 10.3280, "Correção Província"),
            "reggio emilia": (44.6979, 10.6312, "Correção Província"),
            "piacenza": (45.0472, 9.6997, "Correção Província"),
            "ravenna": (44.4167, 12.2000, "Correção Província"),
            "forlì": (44.2225, 12.0408, "Correção Província"),
            "rimini": (44.0592, 12.5683, "Correção Província"),
            "ancona": (43.6167, 13.5167, "Correção Província"),
            "pesaro": (43.9100, 12.9139, "Correção Província"),
            "macerata": (43.3000, 13.4500, "Correção Província"),
            "fermo": (43.1583, 13.7167, "Correção Província"),
            "ascoli piceno": (42.8500, 13.5833, "Correção Província"),
            "perugia": (43.1167, 12.3833, "Correção Província"),
            "terni": (42.5667, 12.6500, "Correção Província"),
            "firenze": (43.7714, 11.2542, "Correção Província"),
            "prato": (43.8833, 11.1000, "Correção Província"),
            "pistoia": (43.9333, 10.9167, "Correção Província"),
            "massa": (44.0333, 10.1500, "Correção Província"),
            "lucca": (43.8500, 10.5000, "Correção Província"),
            "pisa": (43.7167, 10.3833, "Correção Província"),
            "livorno": (43.5500, 10.3167, "Correção Província"),
            "arezzo": (43.4667, 11.8833, "Correção Província"),
            "siena": (43.3167, 11.3500, "Correção Província"),
            "grosseto": (42.7667, 11.1167, "Correção Província"),
            "viterbo": (42.4167, 12.1000, "Correção Província"),
            "rieti": (42.4000, 12.8500, "Correção Província"),
            "latina": (41.4667, 12.9000, "Correção Província"),
            "frosinone": (41.6333, 13.3500, "Correção Província"),
            "caserta": (41.0833, 14.3333, "Correção Província"),
            "isernia": (41.6000, 14.2333, "Correção Província"),
            "chieti": (42.3500, 14.1667, "Correção Província"),
            "pescara": (42.4667, 14.2000, "Correção Província"),
            "teramo": (42.6667, 13.7000, "Correção Província")
        }

        # Aplicar correções manuais primeiro
        registros_atualizados = 0
        
        for idx, row in df_items.iterrows():
            # Verificar nome do comune nas correções manuais
            comune_norm = row['COMUNE_NORM']
            if comune_norm in correcoes_manuais:
                lat, lon, source = correcoes_manuais[comune_norm]
                df_items.at[idx, 'latitude'] = lat
                df_items.at[idx, 'longitude'] = lon
                df_items.at[idx, 'COORD_SOURCE'] = source
                registros_atualizados += 1
                continue
                
            # Verificar província se o comune não foi encontrado
            provincia_norm = row['PROVINCIA_NORM']
            if pd.isna(row['latitude']) and provincia_norm in provincias_manuais:
                lat, lon, source = provincias_manuais[provincia_norm]
                df_items.at[idx, 'latitude'] = lat
                df_items.at[idx, 'longitude'] = lon
                df_items.at[idx, 'COORD_SOURCE'] = source
                registros_atualizados += 1

        # Continuar com o processamento normal para os itens restantes
        if json_comunes_norm_list:
            # Nomes únicos de comunes e províncias do Bitrix 
            bitrix_comunes_to_match = df_items['COMUNE_NORM'].unique().tolist()
            bitrix_provincias_to_match = df_items['PROVINCIA_NORM'].unique().tolist()
            
            # MELHORIA: Implementar múltiplos tipos de matching
            # 1. Match exato (Comune + Província)
            print(f"Aplicando correspondência exata (Comune + Província) para category_id={category_id}...")
            for idx, row in df_items.iterrows():
                # Pular se já tem coordenadas
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    continue
                    
                comune_norm = row['COMUNE_NORM']
                provincia_norm = row['PROVINCIA_NORM']
                
                if comune_norm == 'nao especificado' or provincia_norm == 'nao especificado':
                    continue
                
                # Tentar match exato com comune e província    
                exact_match = df_coordenadas[
                    (df_coordenadas['COMUNE_MAPA_NORM'] == comune_norm) & 
                    (df_coordenadas['PROVINCIA_MAPA_NORM'] == provincia_norm)
                ]
                
                if not exact_match.empty:
                    match_row = exact_match.iloc[0]
                    df_items.at[idx, 'latitude'] = match_row['latitude']
                    df_items.at[idx, 'longitude'] = match_row['longitude']
                    df_items.at[idx, 'COORD_SOURCE'] = 'ExactMatch_ComuneProv'
            
            # Contagem de matches exatos
            exact_matches = df_items[df_items['COORD_SOURCE'] == 'ExactMatch_ComuneProv'].shape[0]
            print(f"Encontrados {exact_matches} correspondências exatas (Comune + Província) para category_id={category_id}")
            
            # 2. Match exato (apenas Comune)
            print(f"Aplicando correspondência exata (apenas Comune) para category_id={category_id}...")
            for idx, row in df_items.iterrows():
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    continue  # Pular se já tem coordenadas
                
                comune_norm = row['COMUNE_NORM']
                if comune_norm == 'nao especificado':
                    continue
                
                # Tentar match exato com comune
                exact_comune_match = df_coordenadas[df_coordenadas['COMUNE_MAPA_NORM'] == comune_norm]
                
                if not exact_comune_match.empty:
                    match_row = exact_comune_match.iloc[0]
                    df_items.at[idx, 'latitude'] = match_row['latitude']
                    df_items.at[idx, 'longitude'] = match_row['longitude']
                    df_items.at[idx, 'COORD_SOURCE'] = 'ExactMatch_Comune'
            
            # Contagem de matches exatos por comune
            comune_matches = df_items[df_items['COORD_SOURCE'] == 'ExactMatch_Comune'].shape[0]
            print(f"Encontrados {comune_matches} correspondências exatas (apenas Comune) para category_id={category_id}")
            
            # 3. Match Fuzzy (Comune)
            print(f"Aplicando correspondência fuzzy para category_id={category_id}...")
            fuzzy_matches_map = {}
            # MELHORIA: Usar threshold mais baixo para aumentar correspondências
            match_threshold = 80  # Reduzindo para aumentar as correspondências (era 85)
            
            # MELHORIA: Usar todos os algoritmos de fuzzy matching disponiveis
            for bitrix_comune in bitrix_comunes_to_match:
                if bitrix_comune == 'nao especificado': 
                    continue
                
                # 3.1 Token Sort Ratio - Melhor para palavras na ordem errada
                token_sort_match = process.extractOne(
                    query=bitrix_comune,
                    choices=json_comunes_norm_list,
                    scorer=fuzz.token_sort_ratio, 
                    score_cutoff=match_threshold
                )
                
                if token_sort_match:
                    fuzzy_matches_map[bitrix_comune] = (token_sort_match[0], token_sort_match[1], "TokenSort")
                    continue
                
                # 3.2 Token Set Ratio - Melhor para substrings/partials
                token_set_match = process.extractOne(
                    query=bitrix_comune,
                    choices=json_comunes_norm_list,
                    scorer=fuzz.token_set_ratio, 
                    score_cutoff=match_threshold
                )
                
                if token_set_match:
                    fuzzy_matches_map[bitrix_comune] = (token_set_match[0], token_set_match[1], "TokenSet")
                    continue
                
                # 3.3 Partial Ratio - Melhor para casos específicos de substring
                partial_match = process.extractOne(
                    query=bitrix_comune,
                    choices=json_comunes_norm_list,
                    scorer=fuzz.partial_ratio, 
                    score_cutoff=match_threshold
                )
                
                if partial_match:
                    fuzzy_matches_map[bitrix_comune] = (partial_match[0], partial_match[1], "Partial")
                    continue
                
                # 3.4 Ratio padrão como última opção - com threshold mais baixo
                if len(bitrix_comune) > 3:  # Evitar nomes muito curtos
                    std_match = process.extractOne(
                        query=bitrix_comune,
                        choices=json_comunes_norm_list,
                        scorer=fuzz.ratio, 
                        score_cutoff=75  # Threshold mais baixo (era 80)
                    )
                    
                    if std_match:
                        fuzzy_matches_map[bitrix_comune] = (std_match[0], std_match[1], "Standard")
                    else:
                        # 3.5 NOVA ETAPA: Tentar correspondência de prefixo para nomes mais longos
                        # Para encontrar casos onde o name do comune no Bitrix é apenas o início do nome real
                        if len(bitrix_comune) >= 5:
                            # Encontrar todos os comunes que começam com o bitrix_comune
                            prefix_matches = [c for c in json_comunes_norm_list if c.startswith(bitrix_comune)]
                            if prefix_matches:
                                # Ordenar por comprimento para pegar o mais curto (mais próximo)
                                best_prefix = sorted(prefix_matches, key=len)[0]
                                fuzzy_matches_map[bitrix_comune] = (best_prefix, 90, "PrefixMatch")
                
            # 4. NOVO: Para casos muito difíceis, tente matching por token parcial
            # (encontrar partes do nome em comum quando os nomes são muito diferentes)
            if match_threshold > 60:  # Apenas se o threshold principal não for muito baixo
                for bitrix_comune in bitrix_comunes_to_match:
                    if bitrix_comune in fuzzy_matches_map or bitrix_comune == 'nao especificado' or len(bitrix_comune) < 4:
                        continue
                    
                    # Dividir o nome em tokens
                    tokens = bitrix_comune.split()
                    if len(tokens) > 1:  # Apenas se houver múltiplos tokens
                        for token in tokens:
                            if len(token) >= 4:  # Token grande o suficiente para ser significativo
                                token_matches = [c for c in json_comunes_norm_list if token in c.split()]
                                if token_matches:
                                    # Usar o primeiro match como base
                                    fuzzy_matches_map[bitrix_comune] = (token_matches[0], 70, "TokenPartialMatch")
                                    break

            # Aplicar correspondências fuzzy ao DataFrame
            for idx, row in df_items.iterrows():
                # Pular se já tem coordenadas
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    continue
                
                comune_norm = row['COMUNE_NORM']
                if comune_norm in fuzzy_matches_map:
                    best_match, score, method = fuzzy_matches_map[comune_norm]
                    
                    # Encontrar as coordenadas do match
                    match_rows = df_coordenadas[df_coordenadas['COMUNE_MAPA_NORM'] == best_match]
                    if not match_rows.empty:
                        match_row = match_rows.iloc[0]
                        
                        # Atualizar as coordenadas
                        df_items.at[idx, 'latitude'] = match_row['latitude']
                        df_items.at[idx, 'longitude'] = match_row['longitude']
                        df_items.at[idx, 'COORD_SOURCE'] = f'FuzzyMatch_{method}_{score}'

            # 5. NOVO: Para casos ainda sem correspondência, tentar pelo início do nome
            # Isso ajuda em casos onde o nome está parcialmente digitado
            print(f"Aplicando correspondência por início do nome para casos sem match (category_id={category_id})...")
            for idx, row in df_items.iterrows():
                # Pular se já tem coordenadas
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    continue
                
                comune_norm = row['COMUNE_NORM']
                if comune_norm == 'nao especificado' or len(comune_norm) < 4:
                    continue
                
                # Encontrar comuns que começam com os primeiros n caracteres
                prefix_len = min(len(comune_norm), 5)  # Usar até 5 caracteres iniciais
                prefix = comune_norm[:prefix_len]
                
                prefix_matches = [c for c in json_comunes_norm_list if c.startswith(prefix)]
                if prefix_matches:
                    # Usar o mais curto (mais próximo do prefixo)
                    best_match = sorted(prefix_matches, key=len)[0]
                    match_rows = df_coordenadas[df_coordenadas['COMUNE_MAPA_NORM'] == best_match]
                    
                    if not match_rows.empty:
                        match_row = match_rows.iloc[0]
                        df_items.at[idx, 'latitude'] = match_row['latitude']
                        df_items.at[idx, 'longitude'] = match_row['longitude']
                        df_items.at[idx, 'COORD_SOURCE'] = f'PrefixMatch_{prefix}'

            # 6. Último recurso: tentar match por província
            # Após todas as tentativas, use a província como último recurso
            print(f"Aplicando correspondência por província para casos sem match (category_id={category_id})...")
            for idx, row in df_items.iterrows():
                # Pular se já tem coordenadas
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    continue
                
                provincia_norm = row['PROVINCIA_NORM']
                if provincia_norm == 'nao especificado':
                    continue
                
                # Primeiro tenta match exato por província
                provincia_matches = df_coordenadas[df_coordenadas['PROVINCIA_MAPA_NORM'] == provincia_norm]
                
                if not provincia_matches.empty:
                    # Usar o primeiro match (primeira cidade da província)
                    match_row = provincia_matches.iloc[0]
                    df_items.at[idx, 'latitude'] = match_row['latitude']
                    df_items.at[idx, 'longitude'] = match_row['longitude']
                    df_items.at[idx, 'COORD_SOURCE'] = 'ProvinciaMatch'
                else:
                    # Tentar fuzzy match por província se ainda não tiver correspondência
                    if len(provincia_norm) >= 4 and provincia_norm not in ['roma', 'bari']:  # Evitar nomes muito curtos/genéricos
                        provincia_fuzzy = process.extractOne(
                            query=provincia_norm,
                            choices=json_provincias_norm_list,
                            scorer=fuzz.token_set_ratio,
                            score_cutoff=75
                        )
                        
                        if provincia_fuzzy:
                            best_match_prov = provincia_fuzzy[0]
                            prov_match_rows = df_coordenadas[df_coordenadas['PROVINCIA_MAPA_NORM'] == best_match_prov]
                            
                            if not prov_match_rows.empty:
                                match_row = prov_match_rows.iloc[0]
                                df_items.at[idx, 'latitude'] = match_row['latitude']
                                df_items.at[idx, 'longitude'] = match_row['longitude']
                                df_items.at[idx, 'COORD_SOURCE'] = f'ProvinciaFuzzy_{provincia_fuzzy[1]}'

            # 7. Contagem final de matches
            fuzzy_matches = df_items[df_items['COORD_SOURCE'].str.contains('Fuzzy', na=False)].shape[0] if 'COORD_SOURCE' in df_items.columns else 0
            prefix_matches = df_items[df_items['COORD_SOURCE'].str.contains('Prefix', na=False)].shape[0] if 'COORD_SOURCE' in df_items.columns else 0
            provincia_matches = df_items[df_items['COORD_SOURCE'].str.contains('Provincia', na=False)].shape[0] if 'COORD_SOURCE' in df_items.columns else 0
            
            print(f"Correspondências encontradas (category_id={category_id}) - Fuzzy: {fuzzy_matches}, Prefixo: {prefix_matches}, Província: {provincia_matches}")
            
            total_matches = df_items[pd.notna(df_items['latitude']) & pd.notna(df_items['longitude'])].shape[0]
            match_rate = (total_matches / len(df_items)) * 100 if len(df_items) > 0 else 0
            
            print(f"Taxa de correspondência total (category_id={category_id}): {match_rate:.1f}% ({total_matches}/{len(df_items)})")
    
    # Aplicar limpeza final e conversão de tipos
    if 'latitude' in df_items.columns and 'longitude' in df_items.columns:
        # Converter coordenadas para numérico
        df_items['latitude'] = pd.to_numeric(df_items['latitude'], errors='coerce')
        df_items['longitude'] = pd.to_numeric(df_items['longitude'], errors='coerce')
    
    return df_items

def carregar_dados_negocios(force_reload=False):
    """
    Carrega os dados dos negócios da categoria 32 e seus campos personalizados
    
    Args:
        force_reload (bool): Se True, força o recarregamento dos dados ignorando o cache
        
    Returns:
        tuple: (DataFrame com negócios, DataFrame com campos personalizados)
    """
    # Verificar se deve forçar o recarregamento
    if force_reload:
        st.info("Forçando recarregamento completo dos dados de negócios (ignorando cache)")
    
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URLs para acessar as tabelas
    url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
    url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
    
    # Preparar filtro para a categoria 32
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["32"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Log do filtro aplicado
    print(f"Aplicando filtro para CRM_DEAL: {category_filter}")
    
    # Carregar dados principais dos negócios com filtro de categoria
    df_deal = load_bitrix_data(url_deal, filters=category_filter, force_reload=force_reload)
    
    # Verificar se conseguiu carregar os dados
    if df_deal is None or df_deal.empty:
        print("Nenhum dado encontrado para CRM_DEAL com CATEGORY_ID=32")
        return pd.DataFrame(), pd.DataFrame()
    else:
        print(f"Carregados {len(df_deal)} registros de CRM_DEAL com CATEGORY_ID=32")
        
    # Verificar se a coluna CATEGORY_ID existe e tem valores esperados
    if 'CATEGORY_ID' in df_deal.columns:
        categorias_encontradas = df_deal['CATEGORY_ID'].unique()
        print(f"Categorias encontradas nos dados: {categorias_encontradas}")
    
    # Simplificar: selecionar apenas as colunas necessárias
    colunas_deal = ['ID', 'TITLE', 'ASSIGNED_BY_NAME']
    
    # Verificar se todas as colunas existem
    colunas_existentes = [col for col in colunas_deal if col in df_deal.columns]
    if len(colunas_existentes) < len(colunas_deal):
        print(f"Aviso: Nem todas as colunas desejadas existem. Colunas disponíveis: {df_deal.columns.tolist()}")
    
    # Selecionar apenas as colunas que existem
    df_deal = df_deal[colunas_existentes]
    
    # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
    deal_ids = df_deal['ID'].astype(str).tolist()
    
    # Mostrar alguns IDs para debug
    print(f"Exemplos de IDs de deals que serão usados: {deal_ids[:5] if len(deal_ids) > 5 else deal_ids}")
    
    # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
    if len(deal_ids) > 1000:
        print(f"Limitando a consulta para os primeiros 1000 IDs (de {len(deal_ids)} disponíveis)")
        deal_ids = deal_ids[:1000]
    
    # Se não houver IDs, retornar DataFrames vazios
    if not deal_ids:
        print("Nenhum ID de deal encontrado para filtrar campos personalizados")
        return df_deal, pd.DataFrame()
    
    # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 32
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    print(f"Aplicando filtro para CRM_DEAL_UF com {len(deal_ids)} IDs")
    
    # Carregar dados da tabela crm_deal_uf (onde estão os campos personalizados do funil de negócios)
    df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter, force_reload=force_reload)
    
    # Verificar se conseguiu carregar os dados
    if df_deal_uf is None or df_deal_uf.empty:
        print("Nenhum dado encontrado em DEAL_UF para os IDs filtrados")
        return df_deal, pd.DataFrame()
    else:
        print(f"Carregados {len(df_deal_uf)} registros de DEAL_UF")
    
    # Verificar as colunas disponíveis em df_deal_uf
    print(f"Colunas disponíveis em DEAL_UF: {df_deal_uf.columns.tolist()}")
    
    # Filtrar apenas as colunas relevantes
    colunas_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778']
    
    # Verificar quais colunas existem no DataFrame
    colunas_selecionadas = [coluna for coluna in colunas_obrigatorias if coluna in df_deal_uf.columns]
    
    if len(colunas_selecionadas) < len(colunas_obrigatorias):
        print(f"Aviso: Nem todas as colunas necessárias foram encontradas em DEAL_UF")
        print(f"Colunas necessárias: {colunas_obrigatorias}")
        print(f"Colunas encontradas: {colunas_selecionadas}")
    
    # Verificar se a coluna de cruzamento existe
    if 'UF_CRM_1722605592778' not in df_deal_uf.columns:
        print("ATENÇÃO: Coluna UF_CRM_1722605592778 não encontrada em DEAL_UF!")
        # Tentar sugerir colunas que possam conter o valor desejado
        possiveis_colunas = [col for col in df_deal_uf.columns if 'UF_CRM_' in col]
        if possiveis_colunas:
            print(f"Possíveis colunas alternativas: {possiveis_colunas}")
    
    # Simplificar: manter apenas as colunas necessárias
    if colunas_selecionadas:
        df_deal_uf = df_deal_uf[colunas_selecionadas]
    
    return df_deal, df_deal_uf

def carregar_estagios_bitrix(force_reload=False):
    """
    Carrega os estágios dos funis do Bitrix24
    
    Args:
        force_reload (bool): Se True, força o recarregamento dos dados ignorando o cache
        
    Returns:
        pandas.DataFrame: DataFrame com os estágios
    """
    # Verificar se deve forçar o recarregamento
    if force_reload:
        st.info("Forçando recarregamento completo dos dados de estágios (ignorando cache)")
    
    # Obter token e URL do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # Obter estágios únicos do pipeline
    url_stages = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_status"
    df_stages = load_bitrix_data(url_stages, force_reload=force_reload)
    
    return df_stages

def mapear_estagios_comune():
    """
    Retorna um dicionário com mapeamento dos estágios do COMUNE
    """
    return {
        "DT1052_22:UC_2QZ8S2": "PENDENTE",
        "DT1052_22:UC_E1VKYT": "PESQUISA NÃO FINALIZADA",
        "DT1052_22:UC_MVS02R": "DEVOLUTIVA EMISSOR",
        "DT1052_22:NEW": "SOLICITAR",
        "DT1052_22:UC_4RQBZV": "URGENTE",
        "DT1052_22:UC_F0IRDH": "SOLICITAR - TEM INFO",
        "DT1052_22:PREPARATION": "AGUARDANDO COMUNE/PARÓQUIA",
        "DT1052_22:UC_S4DFU2": "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO",
        "DT1052_22:UC_1RC076": "AGUARDANDO PDF",
        "DT1052_22:CLIENT": "ENTREGUE PDF",
        "DT1052_22:UC_A9UEMO": "NEGATIVA COMUNE",
        "DT1052_22:SUCCESS": "DOCUMENTO FISICO ENTREGUE",
        "DT1052_22:FAIL": "CANCELADO"
    }

def mapear_estagios_macro():
    """
    Retorna um dicionário com mapeamento dos estágios do COMUNE para a visão macro
    """
    return {
        "DT1052_22:UC_2QZ8S2": "PENDENTE",                    # PENDENTE
        "DT1052_22:UC_E1VKYT": "PESQUISA NÃO FINALIZADA",     # PESQUISA NÃO FINALIZADA
        "DT1052_22:UC_MVS02R": "DEVOLUTIVA EMISSOR",          # DEVOLUTIVA EMISSOR
        "DT1052_22:NEW": "SOLICITAR",                         # SOLICITAR
        "DT1052_22:UC_4RQBZV": "URGENTE",                     # URGENTE
        "DT1052_22:UC_F0IRDH": "SOLICITAR - TEM INFO",        # SOLICITAR - TEM INFO
        "DT1052_22:PREPARATION": "AGUARDANDO COMUNE/PARÓQUIA", # AGUARDANDO COMUNE/PARÓQUIA
        "DT1052_22:UC_S4DFU2": "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO", # AGUARDANDO COMUNE/PARÓQUIA - TEM INFO
        "DT1052_22:UC_1RC076": "AGUARDANDO PDF",              # AGUARDANDO PDF
        "DT1052_22:CLIENT": "ENTREGUE PDF",                   # ENTREGUE PDF
        "DT1052_22:UC_A9UEMO": "NEGATIVA COMUNE",             # NEGATIVA COMUNE
        "DT1052_22:SUCCESS": "DOCUMENTO FISICO ENTREGUE",     # DOCUMENTO FISICO ENTREGUE
        "DT1052_22:FAIL": "CANCELADO"                         # CANCELADO
    } 