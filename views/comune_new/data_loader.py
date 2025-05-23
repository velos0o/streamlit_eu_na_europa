import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import re
from unidecode import unidecode
import numpy as np
from pathlib import Path
import unicodedata
from thefuzz import fuzz, process
from utils.refresh_utils import load_csv_with_refresh

# Tentar importar thefuzz
try:
    from thefuzz import process, fuzz
except ImportError:
    st.error("Biblioteca 'thefuzz' não encontrada. Instale com: pip install thefuzz python-Levenshtein")
    process = None
    fuzz = None

# Carregar variáveis de ambiente
load_dotenv()

# --- Funções Auxiliares de Normalização (do data_loader antigo) ---
def _limpar_antes_normalizar(series):
    # Implementação copiada de views/comune/data_loader.py ...
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    series = series.astype(str).str.lower()
    series = series.str.replace(r'^natti\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^matri\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^-\s*natti\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^-\s*matri\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^nascita\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^matrimonio\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^certidao de\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^certidao\s*[:-]?\s*', '', regex=True)
    def clean_text(text):
        if pd.isna(text) or not isinstance(text, str): return text
        separadores = [',', '(', '/', '-', '[', ';', ':']
        for sep in separadores:
            if sep in text:
                text = text.split(sep, 1)[0]
        return text.strip()
    return series.apply(clean_text)

def _normalizar_localizacao(series):
    # Implementação copiada de views/comune/data_loader.py ...
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    normalized = series.fillna('').astype(str).str.lower()
    try:
        normalized = normalized.apply(lambda x: unidecode(x) if isinstance(x, str) else x)
    except Exception:
        normalized = pd.Series([unidecode(str(x)) for x in series.fillna('')], index=series.index)
        normalized = normalized.str.lower()

    # 3. Remover prefixos GERAIS comuns - EXPANDIDO
    prefixos_gerais = [
        'comune di ', 'provincia di ', 'parrocchia di ', 'parrocchia ', 'citta di ', 
        'diocese di ', 'chiesa di ', 'chiesa parrocchiale di ', 'comune ', 'citta ',
        'diocesi ', 'diocesi di ', 'archivio di ', 'anagrafe di ', 'frazione di ', 'frazione ',
        'municipio di ', 'municipio ', 'ufficio anagrafe di ', 'ufficio di stato civile di ',
        'ufficio anagrafe ', 'ufficio di stato civile ', 'ufficio dello stato civile ',
        'parrocchia della ', 'parrocchia del ', 'parrocchia dei ', 'parrocchia degli ',
        'comune della ', 'comune del ', 'comune dei ', 'comune degli ',
        'archidiocesi di ', 'archidiocesi ', 'arcidiocesi di ', 'arcidiocesi ',
        'basilica di ', 'basilica ', 'cappella di ', 'cappella ',
        'cattedrale di ', 'cattedrale ', 'chiesa arcipretale di ', 'chiesa arcipretale ',
        'chiesa collegiata di ', 'chiesa collegiata ', 'chiesa matrice di ', 'chiesa matrice ',
        'convento di ', 'convento ', 'monastero di ', 'monastero ',
        'pieve di ', 'pieve ', 'santuario di ', 'santuario ',
        'parrocchiale di ', 'parrocchiale ', 'vicaria di ', 'vicaria ',
        'localita ', 'contrada ', 'curia vescovile di ', 'curia vescovile '
    ]
    for prefix in prefixos_gerais:
        normalized = normalized.str.replace(f'^{re.escape(prefix)}', '', regex=True)
        
    # 3.5 Remover prefixos RELIGIOSOS comuns 
    prefixos_religiosos = [
        'san ', 'santa ', 'santi ', 'santo ', 's ', 'ss ', 'st ', 
        'beato ', 'beata ', 'santissima ', 'santissimo ',
        'natale ', 'nativita di ', 'nativita ', 'nascita di ', 'nascita ', 
        'battesimo di ', 'battesimo ', 'maria ', 'madonna ',
        'sant\'', 'sant ', 'santa maria ', 'santa maria di ', 'santa maria del ',
        'sacro cuore di ', 'sacro cuore ', 'sacro ', 'san giovanni ', 'san giovanni di ',
        'san michele ', 'san michele di ', 'san pietro ', 'san pietro di ',
        'san nicola ', 'san nicola di ', 'san lorenzo ', 'san lorenzo di ',
        'san martino ', 'san martino di ', 'san marco ', 'san marco di '
    ]
    for prefix in prefixos_religiosos:
        normalized = normalized.str.replace(f'^{re.escape(prefix)}(\\b)?', '', regex=True)

    # 4. Remover pontuação básica
    normalized = normalized.str.replace(r'[\'"\.,;!?()[\]{}]', '', regex=True)

    # 4.5 Remover sufixos e siglas de província (xx ou (xx)) - Em qualquer lugar
    #   (VI) -> '' , TV -> ''
    normalized = normalized.str.replace(r'\s*\([a-z]{2}\)\s*', ' ', regex=True) 
    normalized = normalized.str.replace(r'\s+[a-z]{2}$', '', regex=True) # Remove no final
    
    # 4.6 Remover N de número e letras isoladas (podem ser erros ou iniciais)
    normalized = normalized.str.replace(r'\b(n|n\.)\s*\d+\b', ' ', regex=True) # Remover n 1, n. 12 etc.
    normalized = normalized.str.replace(r'\b[a-z]\b', ' ', regex=True) # Remover letras isoladas
    
    normalized = normalized.str.strip()

    # MELHORIA: Remover palavras irrelevantes para correspondência
    palavras_irrelevantes = [
        'della', 'dello', 'delle', 'degli', 'dei', 'del', 'di', 'da', 'dal', 'e', 'ed', 'in', 'con',
        'su', 'sul', 'sulla', 'sulle', 'sui', 'sugli', 'per', 'tra', 'fra', 'a', 'al', 'alla', 'alle',
        'ai', 'agli', 'il', 'lo', 'la', 'le', 'i', 'gli', 'un', 'uno', 'una', 'nello', 'nella', 'nelle',
        'negli', 'nei', 'all', 'dall', 'dall', 'dall',
        'presso', 'vicino', 'sopra', 'sotto', 'davanti', 'dietro', 'accanto', 'oltre',
        'verso', 'senza', 'secondo', 'lungo', 'durante', 'dentro', 'fuori', 'prima', 'dopo',
        'contro', 'attraverso', 'circa', 'intorno', 'grazie', 'mediante', 'oltre', 'malgrado',
        'nonostante', 'salvo', 'eccetto', 'fino', 'verso',
        # Novas: comuns em nomes de igrejas/paróquias
        'apostolo', 'martire', 'vescovo', 'vergine', 'assunta', 'nativita', 'annunciazione', 'abate',
        'santos', 'sao', 'paroquia', 'parocchia', 'parrochia', 'chiesa', 'arcangelo', 'cap', # Adicionadas 
        'localita', 'italia' # Adicionadas
    ]
    for palavra in palavras_irrelevantes:
        normalized = normalized.str.replace(r'\b' + re.escape(palavra) + r'\b', ' ', regex=True)

    # MELHORIA: Substituições para casos comuns - EXPANDIDO
    substituicoes = {
        'sangiovanni': 'giovanni', 'sangiuseppe': 'giuseppe', 'sanlorenzo': 'lorenzo', 'sanfrancesco': 'francesco', 
        'sanmartino': 'martino', 'santamaria': 'maria', 'santantonio': 'antonio', 'sanvincenzo': 'vincenzo', 
        'santangelo': 'angelo', 'santanna': 'anna', 'sanmichele': 'michele', 'sanmarco': 'marco', 'sannicola': 'nicola',
        'sanbartolomeo': 'bartolomeo', 'ssantissima': 'santissima', 'santmaria': 'maria', 'santachiara': 'chiara', 
        'santacaterina': 'caterina', 'santandrea': 'andrea', 'santagnese': 'agnese', 'santarita': 'rita', 
        'santabarbara': 'barbara', 'santadomenica': 'domenica', 'santapaola': 'paola', 'santateresa': 'teresa', 
        'santaeufemia': 'eufemia', 'santabruna': 'bruna', 'santaelena': 'elena', 'santantonino': 'antonino', 
        'santadiocesi': 'diocesi', 'maddalena': 'magdalena', 'battista': 'batista', 'assunta': 'assumpta', 
        'assunzione': 'assumpcao', 'eucharistia': 'eucaristia', 'treviso': 'treviso', 'venezia': 'venezia', 
        'veneza': 'venezia', 'padova': 'padova', 'podova': 'padova', 'verona': 'verona', 'vicenza': 'vicenza', 
        'rovigo': 'rovigo', 'belluno': 'belluno', 'mantova': 'mantova', 'mantua': 'mantova', 'mantoa': 'mantova', 
        'montova': 'mantova', 'mântua': 'mantova', 'brescia': 'brescia', 'massa-carrara': 'massa carrara', 
        'massa carrara': 'massa carrara', 'verbano-cusio-ossola': 'verbano cusio ossola', 'verbano-cusi': 'verbano cusio ossola', 
        'vibo-valentia': 'vibo valentia', 'pesaro-urbino': 'pesaro urbino', 'chiete': 'chieti', 'biela': 'biella', 
        'lodi': 'lodi', 'novara': 'novara', 'varese': 'varese', 'pavia': 'pavia', 'vibo valentia': 'vibo valentia', 
        'caltanissetta': 'caltanissetta', 'agrigento': 'agrigento', 'crotone': 'crotone', 'sassari': 'sassari', 
        'enna': 'enna', 'avellino': 'avellino', 'toscana': 'toscana',
        # Novas baseadas no debug e nomes comuns:
        'margherita martire godega': 'godega', # Para CHIESA PARROCCHIALE DI S. MARGHERITA MARTIRE, GODEGA DI S. URBANO
        's urbano': '', # Remover S. Urbano que pode sobrar
        'ponte piave': 'ponte piave', # Para Parrocchia Ponte di Piave
        's andrea apostolo mason vicentino': 'mason vicentino',
        'santi pietro paolo coreglia antelminelli': 'coreglia antelminelli',
        'eusebio cortiglione asti': 'cortiglione asti', # Adicionado para caso Parrocchia S. Eusebio
        'zenone vescovo martire': 'zenone',
        'villa conte': 'villa conte', # Para VILLA DEL CONTE
        'pier disonzo': 'san pier isonzo',
        'crespano dela grappa': 'crespano grappa',
        'giacciano baruchella': 'giacciano baruchella',
        'baselice benevento': 'baselice',
        'paderno cremonese': 'paderno ponchielli', # Nome oficial é Paderno Ponchielli
        'guardia sanframondi': 'guardia sanframondi',
        'sermide felonica': 'sermide felonica',
        'cervarese santa croce': 'cervarese santa croce',
        'ambrogio valpolicella': 'sant ambrogio valpolicella', 
        'piazza mons giuseppe scarpa': 'cavarzere', # Forçando resultado para este padrão de endereço
        'via pietro leopoldo': 'san marcello pistoiese', # Forçando
        'piazza r trento': 'cariati', # Forçando
        'via garibaldi': 'oderzo', # Forçando
        'fiume veneto pn': 'fiume veneto',
        'silea tv': 'silea',
        'piovene rocchette vi': 'piovene rocchette', # Correção
        'persico dosimo cr': 'persico dosimo', # Correção
        'vazzola tv': 'vazzola', # Correção
        'fuscaldo cs': 'fuscaldo', # Correção
        'oratino cb': 'oratino', # Correção
        'cavezzo modena': 'cavezzo', # Correção
        'vasto ch': 'vasto', # Correção
        'bussero mi': 'bussero', # Correção
        'molinella bo': 'molinella', # Correção
        'castello di godego': 'godego', # Mapear para godego
        'sessa aurunca caserta': 'sessa aurunca',
        'cavaglio spoccia verbano cusi ossola': 'cavaglio spoccia',
        'coreglia antelminelli lucca': 'coreglia antelminelli',
        'parghelia cosenza': 'parghelia',
        'pietragalla potenza': 'pietragalla',
        'valgi di sotto lucca': 'vagli sotto', # Mapear para nome mais comum
        'pistoia toscana': 'pistoia',
        'filadelfia vibo valentia': 'filadelfia',
        'morigerati salerno': 'morigerati',
        'sambiase catanzaro': 'sambiase',
        'praduro e sasso bologna': 'sasso marconi', # Praduro e Sasso é fração de Sasso Marconi
        'quarrata pistoia': 'quarrata',
        'sorbano del vescov lucca': 'lucca', # Sorbano é fração de Lucca
        'chieti chieti': 'chieti',
        'niscemi caltanissetta': 'niscemi',
        'lodi lodi': 'lodi',
        'saracena cosenza': 'saracena',
        'grotte agrigento': 'grotte',
        'ottaviano napoli': 'ottaviano',
        'drapia catanzaro': 'drapia',
        'torcchiara salerno': 'torchiara', # Corrigido
        'torano castello cosenza': 'torano castello',
        'tramutola potenza': 'tramutola',
        'scandale crotone': 'scandale',
        'pontremoli massa carrara': 'pontremoli',
        'suno novara': 'suno',
        'contrada avellino': 'contrada',
        'spoltore pescara': 'spoltore',
        'stilo catanzaro': 'stilo',
        'grezzago milano': 'grezzago',
        'fontanella bergamo': 'fontanella',
        'sab pier arena genova': 'genova', # Sampierdarena é bairro de Gênova
        'sersale catanzaro': 'sersale',
        'fara gera adda bergamo': 'fara gera adda',
        'conflenti catanzaro': 'conflenti',
        'san ferdinando napoli': 'napoli', # Bairro de Nápoles
        'santa luce pisa': 'santa luce',
        'rivello potenza': 'rivello',
        'daverio varese': 'daverio',
        'codevigno podova': 'codevigo', # Corrigido nome e provincia
        'fossombrone pesaro e urbino': 'fossombrone',
        'sannazzaro burgondi pavia': 'sannazzaro burgondi',
        'quatrelle avellino': 'avellino', # Fração de Avellino
        'grimaldi cosenza': 'grimaldi',
        'almenno san salvatore bergamo': 'almenno san salvatore',
        'dolo veneza': 'dolo',
        'nanantola modena': 'nonantola', # Corrigido
        'impruneta firenze': 'impruneta',
        'sante marie aquila': 'sante marie',
        'santeramo in colle bari': 'santeramo in colle',
        'polesine zibello parma': 'polesine zibello',
        'frosolone isernia': 'frosolone',
        'termoli campobasso': 'termoli',
        'broni pavia': 'broni',
        'francica catanzaro': 'francica',
        'palazzolo sulloglio brescia': 'palazzolo sulloglio',
        'frisa chieti': 'frisa',
        'savelli crotone': 'savelli',
        'sustinente montova': 'sustinente', # Corrigido provincia
        'stazzema lucca': 'stazzema',
        'conselve padova': 'conselve', # Corrigido provincia
        'cupello chieti': 'cupello',
        'ferentino frosinone': 'ferentino',
        'torraca salerno': 'torraca',
        'lombardia bergamo': 'bergamo', # Mapear região para capital da província? Ou deixar N/A? Deixar N/A por enquanto.
        'tissi sassari': 'tissi',
        'taormina messina': 'taormina',
        'tessennano viterbo': 'tessennano',
        'san daniele ripa po cremona': 'san daniele po', # Nome oficial
        'bagnatica bergamo': 'bagnatica',
        'torraca salerno': 'torraca',
        'desenzano del garda brescia': 'desenzano del garda',
        'baselice benevento': 'baselice',
        'cella dati cremona': 'cella dati',
        'fossalto campobasso': 'fossalto',
        'torricella del pizzo cremona': 'torricella del pizzo',
        'cellara cosenza': 'cellara',
        'biela biela': 'biella', # Corrigido
        'mongrassano cosenza': 'mongrassano',
        'san pier isonzo gorizia': 'san pier isonzo',
        'regalbuto enna': 'regalbuto',
        'gravina in puglia bari': 'gravina in puglia',
        'firenze toscana': 'firenze',
        'rivarolo mantovano mantua': 'rivarolo mantovano',
        'san benedetto po mantua': 'san benedetto po',
        'sant alberto ravenna': 'ravenna', # Fração de Ravenna
        'castiglione a casauria pescara': 'castiglione a casauria',
        'lioni avellino': 'lioni',
        'zaccanopoli vibo valentina': 'zaccanopoli',
        'manerba brescia': 'manerba',
        'guardia sanframondi benevento': 'guardia sanframondi',
        'firenzuola florenza': 'firenzuola', # Corrigido provincia
        # Mapeamentos de paróquias/endereços para comunes conhecidos
        'parrocchia s. maria immacolata veneza': 'venezia',
        'parrocchia benabbio bagni luca': 'bagni di lucca',
        'parrocchia san lorenzo martire voghera': 'voghera',
        'parrocchia sant ambrogio dego dego': 'dego',
        'parrocchia santi pietro e paolo coreglia antelminelli': 'coreglia antelminelli',
        'chiesa parrocchiale tempio sassari': 'tempio pausania', # Nome oficial
        'parrocchia santa fosca a roncadelle brescia': 'roncadelle',
        'via roma 67 cap 36010 - chiuppano': 'chiuppano',
        'paroquia maria ss. assunta collegiata': 'offida', # Mapeamento pelo contexto
        'parrocchia santa gertrude rotzo': 'rotzo', # Adicionado mapeamento direto
        'parrocchia s.giovanni battista - montesarchio': 'montesarchio',
        'parrocchia san michele arcangelo quarto altino': 'quarto altino', # Adicionado mapeamento direto
        'piazza san marco 1 - cap 35043 monselice': 'monselice',
        'via dante maiocchi 55 - cap 01100 roccalvecce': 'viterbo', # Fração de Viterbo
        'via europa 10 - cap 55030 - vagli sotto': 'vagli sotto',
        'piazza aldo moro 24 - cap 45010 villadose': 'villadose',
        'piazza caduti 1- cap 31024 ormelle': 'ormelle',
        'via umberto i 2 - cap 30014 cavarzere': 'cavarzere',
        'via roma 115 - cap 88825 savelli': 'savelli',
        'via garibaldi 14 - cap 31046 oderzo': 'oderzo',
        'careggine lu': 'careggine',
        'viale papa giovanni xxiii 2 - cap 31030 castelcucco': 'castelcucco',
        'longarone bl': 'longarone',
        'san bartolomeo in galdo bn': 'san bartolomeo in galdo',
        'ceggia ve': 'ceggia',
        'paola cs': 'paola',
        'mira ve': 'mira',
        'san zenone al po pv': 'san zenone al po',
        'favaro veneto': 'venezia', # Bairro de Veneza
        'fonte tv': 'fonte',
        'fardella pz': 'fardella',
        'molazzana lu': 'molazzana',
        'norbello or': 'norbello',
        'pedace cs': 'pedace',
        'ittiri ss': 'ittiri',
        'leonforte en': 'leonforte',
        'samassi su': 'samassi', # SU é província Sud Sardegna
        'arcugnano vi': 'arcugnano',
        'molinella bo': 'molinella',
        'piazza iv novembre 10 - 37022 - fumane': 'fumane',
        'loiano bo': 'loiano',
        'piazza xiv dicembre 5 - 28019 - suno': 'suno',
        'soave vr': 'soave',
        'ottaviano na': 'ottaviano',
        'via pietro leopoldo 24 - 51028 - san marcello pistoiese': 'san marcello piteglio', # Nome atual
        'grezzago mi': 'grezzago',
        'piazza martiri della liberta 3 - 31040 - cessalto': 'cessalto',
        'via xxi luglio cap 81037 sessa aurunca': 'sessa aurunca',
        'via giuseppe garibaldi 60 35020 - correzzola': 'correzzola',
        'zero branco tv': 'zero branco',
        'fumachi': 'colognola ai colli', # Mapeamento pelo contexto
        'filippini': 'perugia', # Mapeamento pelo contexto
        'de lucca': 'gaiarine', # Mapeamento pelo contexto
        'censi': 'san giovanni lupatoto', # Mapeamento pelo contexto
        'davi': 'villa bartolomea', # Mapeamento pelo contexto (pode ser Bovolone também, priorizar o primeiro)
        'fabbiani': 'bellombra', # Mapeamento pelo contexto (Adria?) -> Bellombra é fração de Adria
        'simoncello': 'ronca', # Mapeamento pelo contexto
        'gabrieli': 'modena', # Mapeamento pelo contexto
        'simonetto': 'san pietro in gu', # Mapeamento pelo contexto
        'ortolan': 'caneva', # Mapeamento pelo contexto
        'costellini': 'mogliano veneto', # Mapeamento pelo contexto
        'vanzelli': 'rovigo', # Mapeamento pelo contexto (pode ser Canaro também)
        'defalco': 'brindisi', # Mapeamento pelo contexto
        'garofalo': 'cosenza', # Mapeamento pelo contexto (San Giovanni in Fiore?)
        'conti': 'roverbella', # Mapeamento pelo contexto
        'pizzinat': 'vittorio veneto', # Mapeamento pelo contexto
        'bernardini': 'foiano della chiana', # Mapeamento pelo contexto (pode ser Bettolle também)
        'via roma 29 - cap 46031 - bagnolo san vito': 'bagnolo san vito',
        'rissi': 'scandolara ravara', # Mapeamento pelo contexto
        'linguanotto': 'basalghelle', # Mapeamento pelo contexto
        'quinzi': 'poggio san lorenzo', # Mapeamento pelo contexto (pode ser Rocca Sinibalda)
        'colombo': 'cassano adda', # Corrigido
        'ragonezi': 'castelforte', # Mapeamento pelo contexto
        'morandin': 'vedelago', # Mapeamento pelo contexto
        'zanatta': 'treviso', # Mapeamento pelo contexto
        'guerra': 'montefiore conca', # Mapeamento pelo contexto
        'cerantola': 'castelfranco veneto', # Mapeamento pelo contexto
        'da re': 'villorba', # Mapeamento pelo contexto
        'maggiolo': 'vigodarzere', # Mapeamento pelo contexto
        'pagotto': 'arcade', # Mapeamento pelo contexto
        'cagnotto': 'cavarzere', # Mapeamento pelo contexto
        'possenatto': 'brognoligo-costalunga', # Mapeamento pelo contexto
        'galante': 'urbana', # Mapeamento pelo contexto
        'ravgnani': 'rovigo', # Mapeamento pelo contexto
        'giacomin': 'casale sul sile', # Mapeamento pelo contexto
        'morelli': 'ravenna', # Mapeamento pelo contexto
        'bussadori': 'castelmassa', # Mapeamento pelo contexto
        'rizotto': 'alano piave', # Corrigido
        'galuppo': 'lusia', # Mapeamento pelo contexto
        'zerbinati': 'sermide felonica', # Mapeamento pelo contexto
        'buosi': 'fontanelle', # Mapeamento pelo contexto (pode ser Oderzo)
        'maiolo': 'vibo valentia', # Mapeamento pelo contexto
        'magnani': 'quistello', # Mapeamento pelo contexto
        'dal ponte': 'pozzoleone', # Mapeamento pelo contexto
        'bettin': 'piombino dese', # Mapeamento pelo contexto
        'bovi': 'bigarello', # Mapeamento pelo contexto
        'fante': 'bevilacqua', # Mapeamento pelo contexto
        'ravasio': 'mapello', # Mapeamento pelo contexto
        'rosa': 'mantova', # Mapeamento pelo contexto (Marmirolo?)
        'pagliarone': 'san vito chietino', # Mapeamento pelo contexto
        'pagliari': 'viterbo', # Mapeamento pelo contexto (Roccalvecce é fração)
        'zuccon': 'zenson piave', # Corrigido
        'zambotti': 'bigarello', # Mapeamento pelo contexto (Stradella é fração)
        'zoccaratto': 'santa giustina in colle', # Mapeamento pelo contexto
        'ferronato': 'cittadella', # Mapeamento pelo contexto
        'rossato': 'belfiore', # Mapeamento pelo contexto
        'marin': 'san dona piave', # Corrigido
        'bobbo': 'venezia', # Mapeamento pelo contexto
        'ungarelli': 'molinella', # Mapeamento pelo contexto
        'mariani': 'annicco', # Mapeamento pelo contexto
        'pace': 'pavia', # Mapeamento pelo contexto
        'bertoncello': 'marostica', # Mapeamento pelo contexto
        'camaduro': 'ormelle', # Mapeamento pelo contexto
        'lombello': 'cartura', # Mapeamento pelo contexto
        'furlan': 'chioggia', # Mapeamento pelo contexto
        'asinelli': 'torino', # Mapeamento pelo contexto
        'gualtieri': 'savelli', # Mapeamento pelo contexto
        'ferri': 'zanica', # Mapeamento pelo contexto
        'borelli': 'poggio rusco', # Mapeamento pelo contexto
        'facchini': 'canaro', # Mapeamento pelo contexto (pode ser Felonica)
        'marchesin': 'oderzo', # Mapeamento pelo contexto
        'rizzati': 'bergantino', # Mapeamento pelo contexto
        'andruccioli': 'montefiore conca', # Mapeamento pelo contexto
        'conti': 'careggine', # Mapeamento pelo contexto
        'nesi': 'levate', # Mapeamento pelo contexto
        'bailo': 'monfumo', # Mapeamento pelo contexto
        'gabrielli': 'modena', # Mapeamento pelo contexto
        'faragutti': 'finale emilia', # Mapeamento pelo contexto
        'gobbi': 'torrebelvicino', # Mapeamento pelo contexto
        'biguetto': 'tombolo', # Mapeamento pelo contexto
        'cola': 'castelcucco', # Mapeamento pelo contexto
        'zonatto': 'chiampo', # Mapeamento pelo contexto
        'massarotto': 'crespino', # Mapeamento pelo contexto
        'marruchella': 'san bartolomeo in galdo', # Mapeamento pelo contexto
        'rampazzo': 'sant angelo piove sacco', # Corrigido
        'perissoto': 'ceggia', # Mapeamento pelo contexto (pode ser Eraclea)
        'esposte': 'sasso marconi', # Mapeamento pelo contexto
        'chiebao': 'cavarzere', # Mapeamento pelo contexto
        'musacco': 'isola del giglio', # Mapeamento pelo contexto
        'misurelli': 'rende', # Mapeamento pelo contexto
        'perrone': 'mormanno', # Mapeamento pelo contexto
        'ghisoni': 'san zenone al po', # Mapeamento pelo contexto
        'massoni': 'casaleone', # Mapeamento pelo contexto (Verona?)
        'scappini': 'motta baluffi', # Mapeamento pelo contexto
        'magri': 'poggio rusco', # Mapeamento pelo contexto
        'andreoli': 'fonte', # Mapeamento pelo contexto
        'toffolo': 'bologna', # Mapeamento pelo contexto
        'bettanin': 'lusiana', # Mapeamento pelo contexto
        'sabbadini': 'calcio', # Mapeamento pelo contexto
        'franchini': 'villimpenta', # Mapeamento pelo contexto
        'dall osto': 'montecchio precalcino', # Mapeamento pelo contexto (pode ser Mason Vicentino)
        'flora': 'maratea', # Mapeamento pelo contexto
        'giordano': 'montemilone', # Mapeamento pelo contexto
        'marchiori': 'malo', # Mapeamento pelo contexto
        'rettore': 'leonforte', # Mapeamento pelo contexto
        'fontanella': 'longarone', # Mapeamento pelo contexto
        'furlanetto': 'meolo', # Mapeamento pelo contexto
        'corradini': 'gazzo veronese', # Mapeamento pelo contexto
        'michielon': 'montebelluna', # Mapeamento pelo contexto
        'pedace': 'pedace', # Mapeamento pelo contexto
        'romio': 'montebello vicentino', # Mapeamento pelo contexto
        'zampiva': 'brogliano', # Mapeamento pelo contexto
        'sabbadin': 'cittadella', # Mapeamento pelo contexto
        'perette': 'villafranca verona', # Corrigido
        'rizzon deon': 'montebelluna', # Mapeamento pelo contexto
        'polo': 'isola vicentina', # Mapeamento pelo contexto
        'dettori': 'ittiri', # Mapeamento pelo contexto
        'bulgarelli': 'gonzaga', # Mapeamento pelo contexto
        'peruchi': 'peschiera del garda', # Mapeamento pelo contexto
        'squizzato': 'loreggia', # Mapeamento pelo contexto
        'rissi': 'scandolara ravara', # Mapeamento pelo contexto (pode ser Motta Baluffi)
        'meotti': 'fumane', # Mapeamento pelo contexto
        'galletti': 'farnese', # Mapeamento pelo contexto (pode ser Viterbo)
        'chinelato': 'monastier treviso', # Corrigido
        'begalli': 'verona', # Mapeamento pelo contexto
        'petrone': 'nao especificado', # Não claro
        'bovo': 'venezia', # Mapeamento pelo contexto (Martellago?) -> Martellago é comum
        'massarelli': 'terracina', # Mapeamento pelo contexto
        'rigazzo': 'bianze', # Corrigido
        'pagnota': 'avellino', # Mapeamento pelo contexto
        'olivo': 'borgo a mozzano', # Mapeamento pelo contexto
        'biondi': 'san marcello piteglio', # Mapeamento pelo contexto
        'masarut': 'cordovado', # Mapeamento pelo contexto
        'escopo': 'seren del grappa', # Mapeamento pelo contexto
        'funghi': 'pitigliano', # Mapeamento pelo contexto
        'azzolini': 'viadana', # Mapeamento pelo contexto
        'naressi': 'cessalto', # Mapeamento pelo contexto
        'pra nichele': 'belluno', # Mapeamento pelo contexto
        'stasio': 'sessa aurunca', # Mapeamento pelo contexto
        'marson': 'torre mosto', # Corrigido
        'zocconelli': 'ferrara', # Mapeamento pelo contexto
        'lovato': 'campolongo sul brenta', # Mapeamento pelo contexto
        'cicuto': 'annone veneto', # Mapeamento pelo contexto
        'ruzzon': 'cona', # Mapeamento pelo contexto (pode ser Conselve)
        'carazzo': 'trissino', # Mapeamento pelo contexto
        'benito': 'roseto abruzzi', # Corrigido
        'bressan': 'correzzola', # Mapeamento pelo contexto
        'casadei': 'cesena', # Mapeamento pelo contexto
        'gobbo': 'arcade' # Mapeamento pelo contexto
    }
    for original, substituicao in substituicoes.items():
        # Usar regex para substituir apenas a palavra/frase inteira
        normalized = normalized.str.replace(r'\b' + re.escape(original) + r'\b', substituicao, regex=True)

    # 5. Remover espaços extras novamente após substituições
    normalized = normalized.str.strip()
    normalized = normalized.str.replace(r'\s{2,}', ' ', regex=True)
    
    # 6. Tratar valores que se tornaram vazios ou eram nulos
    normalized = normalized.replace(['', 'nan', 'none', 'null'], 'nao especificado', regex=False)
    
    return normalized

# --- Função para carregar coordenadas (adaptada) ---
@st.cache_data(ttl=86400) # Cache de 1 dia
def _carregar_coordenadas_mapa_normalizadas():
    """
    Carrega dados de coordenadas de comuni.csv e coordinate.csv.
    Aplica normalização aos nomes para facilitar o merge posterior.
    
    Returns:
        pandas.DataFrame: DataFrame com COMUNE_MAPA_NORM, PROVINCIA_MAPA_NORM, latitude, longitude.
                         Retorna DataFrame vazio em caso de erro.
    """
    # Caminho para os CSVs (fixo, dentro da estrutura do projeto)
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          'comuni-italiani-main', 'dati')
    
    if not os.path.isdir(base_path):
        st.error(f"Erro Crítico: O diretório base de dados '{base_path}' não foi encontrado. Verifique a estrutura do projeto.")
        return pd.DataFrame()

    comuni_path = os.path.join(base_path, 'comuni.csv')
    coords_path = os.path.join(base_path, 'coordinate.csv')

    try:
        # Usar as novas funções de carregamento com atualização
        df_comuni = load_csv_with_refresh(comuni_path)
        df_coords = load_csv_with_refresh(coords_path)
        
        # Adicionar informação sobre a última atualização
        comuni_ultima_atualizacao = os.path.getmtime(comuni_path)
        st.caption(f"📍 Dados de comuni.csv atualizados em: {pd.to_datetime(comuni_ultima_atualizacao, unit='s').strftime('%d/%m/%Y %H:%M:%S')}")

        # Verificar colunas essenciais em cada arquivo
        cols_comuni_necessarias = ['comune', 'sigla', 'pro_com_t']
        cols_coords_necessarias = ['pro_com_t', 'lat', 'long']
        
        if not all(col in df_comuni.columns for col in cols_comuni_necessarias):
            cols_faltantes = [col for col in cols_comuni_necessarias if col not in df_comuni.columns]
            st.error(f"Arquivo {comuni_path} sem colunas esperadas: {', '.join(cols_faltantes)}. Necessário: {cols_comuni_necessarias}")
            return pd.DataFrame()
        
        if not all(col in df_coords.columns for col in cols_coords_necessarias):
            cols_faltantes = [col for col in cols_coords_necessarias if col not in df_coords.columns]
            st.error(f"Arquivo {coords_path} sem colunas esperadas: {', '.join(cols_faltantes)}. Necessário: {cols_coords_necessarias}")
            return pd.DataFrame()
            
        # Juntar os DataFrames usando 'pro_com_t'
        df_merged = pd.merge(df_comuni, df_coords, on='pro_com_t', how='inner')
        
        # Renomear colunas para o padrão esperado pela lógica de matching
        df_merged = df_merged.rename(columns={
            'comune': 'COMUNE_MAPA_ORIG',      # Nome do Comune original
            'sigla': 'PROVINCIA_MAPA_ORIG',    # Usar a SIGLA como Província original para normalização
            'lat': 'latitude',             # Latitude
            'long': 'longitude'            # Longitude
        })
        
        # Selecionar e manter apenas as colunas renomeadas necessárias
        cols_manter = ['COMUNE_MAPA_ORIG', 'PROVINCIA_MAPA_ORIG', 'latitude', 'longitude']
        df_merged = df_merged[cols_manter].copy()

        # Aplicar Normalização aos nomes de comune e província (sigla)
        df_merged['COMUNE_MAPA_NORM'] = _normalizar_localizacao(df_merged['COMUNE_MAPA_ORIG'])
        # Normalizar a sigla também (remove acentos caso haja, embora improvável para siglas)
        df_merged['PROVINCIA_MAPA_NORM'] = _normalizar_localizacao(df_merged['PROVINCIA_MAPA_ORIG'])
        
        # Remover duplicatas baseadas nas colunas normalizadas (importante após normalização)
        df_merged.drop_duplicates(subset=['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM'], keep='first', inplace=True)
        
        # Selecionar apenas as colunas finais necessárias para o merge posterior
        df_coords_final = df_merged[['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM', 'latitude', 'longitude']].copy()
        
        # Converter coordenadas para numérico e remover NaNs/Inválidos
        df_coords_final['latitude'] = pd.to_numeric(df_coords_final['latitude'], errors='coerce')
        df_coords_final['longitude'] = pd.to_numeric(df_coords_final['longitude'], errors='coerce')
        df_coords_final.dropna(subset=['latitude', 'longitude'], inplace=True)

        st.success(f"Dados de coordenadas carregados e processados de {len(df_coords_final)} comunes únicos (Fonte: OpendataSicilia).")
        return df_coords_final
        
    except FileNotFoundError as fnf_err:
        st.error(f"Erro: Arquivo CSV não encontrado: {fnf_err}. Verifique se 'comuni.csv' e 'coordinate.csv' estão em 'comuni-italiani-main/dati/'.")
        return pd.DataFrame()
    except ValueError as ve:
         st.error(f"Erro ao ler CSV de coordenadas/comunes: Problema nos dados ou estrutura inválida. Verifique '{ve}'")
         return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao carregar/processar CSVs de coordenadas/comunes: {e}")
        st.exception(e) # Mostra traceback completo para debug
        return pd.DataFrame()
# --- Fim Carregar Coordenadas --- 

@st.cache_data(ttl=3600) # Cache de 1 hora
def load_comune_data(force_reload: bool = False) -> pd.DataFrame:
    """
    Carrega e prepara os dados de Itens Dinâmicos do Bitrix para a seção Comune (Novo).
    Foca nas colunas essenciais, normaliza locais e adiciona coordenadas geográficas.
    Args:
        force_reload (bool): Se True, força o recarregamento dos dados ignorando o cache.
    Returns:
        pd.DataFrame: DataFrame com os dados carregados e colunas essenciais tratadas.
                     Retorna um DataFrame vazio em caso de erro.
    """
    if force_reload:
        st.info("Forçando recarregamento dos dados de Comune (Novo)...", icon="🔄")

    try:
        # 1. Obter Credenciais e Construir URL
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        if not BITRIX_TOKEN or not BITRIX_URL:
            st.error("Credenciais do Bitrix não encontradas. Verifique o arquivo .env.")
            return pd.DataFrame()
        
        # URL específica para itens dinâmicos 1052 (ajuste se necessário)
        # NOTA: Sem filtro de CATEGORY_ID por enquanto, carregando todos de 1052.
        #       Adicione o filtro se quiser carregar apenas de IDs específicos (ex: 22, 58, 60)
        category_filter = {"dimensionsFilters": [[{
            "fieldName": "CATEGORY_ID", "values": ["22", "58", "60"], "type": "INCLUDE", "operator": "EQUALS"
        }]]}
        url_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
        
        # 2. Carregar Dados do Bitrix
        df_items = load_bitrix_data(url_items, filters=category_filter, force_reload=force_reload) # Passa force_reload e o filtro

        if df_items is None or df_items.empty:
            st.warning("Nenhum dado encontrado para Itens Dinâmicos (1052) com CATEGORY_ID 22, 58 ou 60 no Bitrix.")
            return pd.DataFrame()
        
        # 3. Verificar e Preparar Colunas Essenciais
        colunas_essenciais = {
            'ID': str, 
            'STAGE_ID': str, 
            'CREATED_TIME': 'datetime64[ns]',
            # Adicionar colunas de localização se existirem
            'UF_CRM_12_ENDERECO_DO_COMUNE': str, # Comune Principal
            'UF_CRM_12_1722881735827': str, # Comune (Fallback)
            'UF_CRM_12_1743015702671': str, # Provincia
            # --- ALTERADO CAMPO DE DATA PARA COMUNE 3 ---
            'UF_CRM_12_DATA_SOLICITACAO': str # Data Solicitação Comune 3 (NOVO CAMPO)
        }
        colunas_presentes = df_items.columns.tolist()
        df_final = pd.DataFrame()

        for col, tipo_esperado in colunas_essenciais.items():
            if col not in colunas_presentes:
                # Tratar colunas de localização E data específica como opcionais AQUI,
                # mas a lógica em tempo_solicitacao.py tratará a ausência da data Comune 3.
                if col.startswith('UF_CRM_12'): 
                     st.warning(f"[DataLoader ComuneNovo] Aviso: Coluna '{col}' não encontrada nos dados do Bitrix.")
                     df_items[col] = pd.NA # Criar coluna com NA para evitar erros downstream, mas permitir verificação
                else:
                    # Colunas realmente essenciais (ID, STAGE_ID, CREATED_TIME) causam erro se ausentes
                    st.error(f"Coluna essencial '{col}' não encontrada nos dados do Bitrix para Comune (Novo).")
                    return pd.DataFrame()
            
            # Copiar a coluna para o df_final (ou a coluna criada se faltava)
            # Se a coluna não estava presente e foi criada com NA, copiará NA.
            df_final[col] = df_items[col]

            # Tratar tipo (exceto para colunas UF_CRM que precisam de tratamento especial ou são string)
            # NÃO tentar converter a coluna de data Comune 3 para datetime aqui, pois pode ter formatos variados
            # ou ser string. A conversão será feita em tempo_solicitacao.py.
            if not col.startswith('UF_CRM_12'):
                try:
                    if tipo_esperado == 'datetime64[ns]':
                        df_final[col] = pd.to_datetime(df_final[col], errors='coerce')
                        if df_final[col].isnull().all(): st.warning(f"Coluna '{col}' contém apenas valores inválidos para data/hora.")
                        elif df_final[col].isnull().any(): st.caption(f":warning: Alguns valores na coluna '{col}' não puderam ser convertidos para data/hora.")
                    else:
                        df_final[col] = df_final[col].astype(tipo_esperado)
                except Exception as e:
                    st.error(f"Erro ao converter coluna '{col}' para o tipo {tipo_esperado}: {e}")
                    return pd.DataFrame()
            # Se for UF_CRM_12 (localização ou data Comune 3), manter como objeto/string por enquanto.

        # Adicionar outras colunas úteis (opcional) - Certificar que não adicionamos a data Comune 3 duas vezes
        outras_colunas = ['TITLE', 'ASSIGNED_BY_ID', 'CATEGORY_ID'] 
        for col in outras_colunas:
             # Verificar se a coluna existe nos dados originais E ainda não está no df_final (caso já fosse 'essencial')
            if col in colunas_presentes and col not in df_final.columns: 
                df_final[col] = df_items[col]
            elif col not in colunas_presentes:
                 st.warning(f"[DataLoader ComuneNovo] Coluna opcional '{col}' não encontrada.")
                 # Criar com NA se não existir e não estiver já no df_final
                 if col not in df_final.columns: 
                      df_final[col] = pd.NA

        # --- 4. Normalizar Nomes de Localização --- 
        col_comune_principal = 'UF_CRM_12_ENDERECO_DO_COMUNE'
        col_comune_fallback = 'UF_CRM_12_1722881735827'
        col_provincia_bitrix = 'UF_CRM_12_1743015702671'

        # --- Lógica de Seleção e Normalização Aprimorada ---
        # Prioriza campos específicos, depois tenta extrair do endereço
        
        df_final_copy = df_final.copy()
        
        # Coluna temporária para guardar o texto original ANTES da normalização
        df_final_copy['COMUNE_ORIG_TEMP'] = pd.NA 
        df_final_copy['PROVINCIA_ORIG_TEMP'] = pd.NA 

        # Criar colunas normalizadas inicialmente vazias
        df_final_copy['COMUNE_NORM'] = 'nao especificado'
        df_final_copy['PROVINCIA_NORM'] = 'nao especificado'

        # Prioridade 1: Campo Fallback Comune (UF_CRM_12_1722881735827)
        mask_fallback = df_final_copy[col_comune_fallback].notna() & (df_final_copy[col_comune_fallback] != '') & (df_final_copy[col_comune_fallback] != 'Não Especificado')
        df_final_copy.loc[mask_fallback, 'COMUNE_ORIG_TEMP'] = df_final_copy.loc[mask_fallback, col_comune_fallback]
        df_final_copy.loc[mask_fallback, 'COMUNE_NORM'] = _normalizar_localizacao(df_final_copy.loc[mask_fallback, col_comune_fallback])

        # Prioridade 2: Campo Endereço Comune (UF_CRM_12_ENDERECO_DO_COMUNE) - Apenas se o fallback não foi usado
        mask_endereco = ~mask_fallback & df_final_copy[col_comune_principal].notna() & (df_final_copy[col_comune_principal] != '') & (df_final_copy[col_comune_principal] != 'Não Especificado')
        # Tentar extrair comune do endereço (manter a lógica simples por enquanto, normalização cuidará do resto)
        # A extração aqui serve mais para pegar o texto base antes de passar para _normalizar_localizacao
        df_final_copy.loc[mask_endereco, 'COMUNE_ORIG_TEMP'] = df_final_copy.loc[mask_endereco, col_comune_principal]
        df_final_copy.loc[mask_endereco, 'COMUNE_NORM'] = _normalizar_localizacao(df_final_copy.loc[mask_endereco, col_comune_principal])

        # Normalização da Província (sempre usa o campo específico se existir)
        if col_provincia_bitrix in df_final_copy.columns:
            mask_provincia = df_final_copy[col_provincia_bitrix].notna() & (df_final_copy[col_provincia_bitrix] != '') & (df_final_copy[col_provincia_bitrix] != 'Não Especificado')
            df_final_copy.loc[mask_provincia, 'PROVINCIA_ORIG_TEMP'] = df_final_copy.loc[mask_provincia, col_provincia_bitrix]
            df_final_copy.loc[mask_provincia, 'PROVINCIA_NORM'] = _normalizar_localizacao(df_final_copy.loc[mask_provincia, col_provincia_bitrix])

        # Atualizar o DataFrame principal
        cols_to_update = ['COMUNE_NORM', 'PROVINCIA_NORM', 'COMUNE_ORIG_TEMP', 'PROVINCIA_ORIG_TEMP']
        for col in cols_to_update:
             if col in df_final_copy.columns: 
                  df_final[col] = df_final_copy[col]
             else: # Garantir que as colunas existam mesmo que não haja dados
                  df_final[col] = pd.NA 
                  
        # Preencher NA nas colunas normalizadas com 'nao especificado'
        df_final['COMUNE_NORM'].fillna('nao especificado', inplace=True)
        df_final['PROVINCIA_NORM'].fillna('nao especificado', inplace=True)
        # --- Fim da Lógica de Normalização Aprimorada ---

        # --- 5. Carregar e Juntar Coordenadas ---
        df_coordenadas = _carregar_coordenadas_mapa_normalizadas()
        df_final['latitude'] = pd.NA
        df_final['longitude'] = pd.NA
        # Inicializar COORD_SOURCE como NA (Not Available/Not Matched yet)
        df_final['COORD_SOURCE'] = pd.NA 

        if not df_coordenadas.empty:
            # --- LÓGICA DE MATCHING REESTRUTURADA ---

            # 1. Match Exato (Apenas Comune) - PRIORIZADO
            exact_matches_c = 0
            # Criar um mapa de comune_norm para coordenadas para lookup rápido
            comune_coord_map = (df_coordenadas
                                .drop_duplicates(subset=['COMUNE_MAPA_NORM'], keep='first')
                                .set_index('COMUNE_MAPA_NORM')[['latitude', 'longitude']]
                                .to_dict('index')
                               )
                                                
            # Iterar sobre TODAS as linhas inicialmente
            for idx in df_final.index:
                comune_norm = df_final.at[idx, 'COMUNE_NORM']
                if comune_norm != 'nao especificado' and comune_norm in comune_coord_map:
                    coords = comune_coord_map[comune_norm]
                    df_final.at[idx, 'latitude'] = coords['latitude']
                    df_final.at[idx, 'longitude'] = coords['longitude']
                    df_final.at[idx, 'COORD_SOURCE'] = 'ExactMatch_Comune'
                    exact_matches_c += 1
            
            # Máscara para identificar linhas que AINDA não têm coordenadas
            no_coords_mask = df_final['latitude'].isna()
            print(f"{no_coords_mask.sum()} registros ainda sem coordenadas.")
            
            # 2. Match Exato (Comune + Província) - via Merge (Para os restantes)
            if no_coords_mask.any():
                # Selecionar apenas as linhas sem coordenadas para tentar o merge
                # Precisamos das colunas de merge ('COMUNE_NORM', 'PROVINCIA_NORM') e o índice original
                df_to_merge = df_final.loc[no_coords_mask, ['COMUNE_NORM', 'PROVINCIA_NORM']].copy()
                
                # Realizar o merge apenas com as linhas restantes
                merged_coords = pd.merge(
                    df_to_merge.reset_index(), # Manter o índice original
                    df_coordenadas, # Contém COMUNE_MAPA_NORM, PROVINCIA_MAPA_NORM, latitude, longitude
                    left_on=['COMUNE_NORM', 'PROVINCIA_NORM'],
                    right_on=['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM'],
                    how='inner' # Inner join para pegar apenas os matches
                )
                
                exact_matches_cp = 0
                if not merged_coords.empty:
                     exact_matches_cp = len(merged_coords)
                     # Usar o índice original para atualizar o df_final principal
                     merged_coords.set_index('index', inplace=True)
                     df_final.loc[merged_coords.index, 'latitude'] = merged_coords['latitude']
                     df_final.loc[merged_coords.index, 'longitude'] = merged_coords['longitude']
                     df_final.loc[merged_coords.index, 'COORD_SOURCE'] = 'ExactMatch_ComuneProv'
                
            # 3. Aplicar Correções Manuais (Comune e Província)
            if no_coords_mask.any():
                manual_matches = 0
                # Dicionários de correções (copiados do antigo)
                print(f"{exact_matches_cp} coordenadas adicionadas por Merge (Comune+Prov)." )
                no_coords_mask = df_final['latitude'].isna() # Atualizar máscara
                print(f"{no_coords_mask.sum()} registros ainda sem coordenadas.")
            
            # --- Debugging Normalization & Raw Data ---
            if no_coords_mask.any():
                print("\n--- Debugging Normalization for Failed Exact Matches ---")
                df_failed_exact_debug = df_final.loc[no_coords_mask].copy()
                # Mostrar alguns exemplos de dados brutos e normalizados que falharam nas etapas exatas
                sample_size = min(15, len(df_failed_exact_debug))
                df_sample_debug = df_failed_exact_debug.sample(n=sample_size)
                
                print(f"Showing {sample_size} samples of raw data and normalization for records that failed exact matching:")
                # Selecionar e renomear colunas relevantes para o debug
                cols_to_debug = {
                    'ID': 'ID',
                    'UF_CRM_12_ENDERECO_DO_COMUNE': 'RAW_ENDERECO_COMUNE',
                    'UF_CRM_12_1722881735827': 'RAW_COMUNE_FALLBACK',
                    'UF_CRM_12_1743015702671': 'RAW_PROVINCIA',
                    'COMUNE_ORIG_TEMP': 'COMUNE_USED_FOR_NORM', # Mostra qual campo foi efetivamente usado
                    'COMUNE_NORM': 'NORM_COMUNE_BITRIX',
                    'PROVINCIA_NORM': 'NORM_PROV_BITRIX'
                }
                cols_debug_present = {k: v for k, v in cols_to_debug.items() if k in df_sample_debug.columns}
                
                if cols_debug_present:
                     print(df_sample_debug[list(cols_debug_present.keys())]
                           .rename(columns=cols_debug_present)
                           .to_string())
                else:
                     print("Could not find relevant columns for debug sample.")
                print("--- End Debugging Normalization ---\n")
            
            # 3. Aplicar Correções Manuais (Comune e Província)
            if no_coords_mask.any():
                print("Etapa 3: Correções Manuais")
                manual_matches = 0
                # Dicionários de correções (copiados do antigo)
                correcoes_manuais = { # ... (dicionário mantido) ...
                     "piavon": (45.7167, 12.4333, "Correção Manual"), "vazzola": (45.8333, 12.3333, "Correção Manual"),
                     "oderzo": (45.7833, 12.4833, "Correção Manual"), "valdobbiadene": (45.9000, 12.0333, "Correção Manual"),
                     "motta di livenza": (45.7833, 12.6167, "Correção Manual"), "susegana": (45.8500, 12.2500, "Correção Manual"),
                     "vittorio veneto": (45.9833, 12.3000, "Correção Manual"), "boara polesine": (45.0333, 11.7833, "Correção Manual"),
                     "mansuè": (45.8333, 12.5167, "Correção Manual"), "san dona di piave": (45.6333, 12.5667, "Correção Manual"),
                     "godego": (45.7000, 11.8667, "Correção Manual"), "castello di godego": (45.7000, 11.8667, "Correção Manual"),
                     "paderno cremonese": (45.4167, 11.8667, "Correção Manual"), "guardia sanframondi": (45.0667, 11.7833, "Correção Manual"),
                     "sermide felonica": (45.7833, 12.6167, "Correção Manual"), "ambrogio valpolicella": (45.7000, 11.8667, "Correção Manual"),
                     "piazza mons giuseppe scarpa": (45.1333, 12.0667, "Correção Manual"), "via pietro leopoldo": (45.7833, 12.6167, "Correção Manual"),
                     "piazza r trento": (45.7833, 12.6167, "Correção Manual"), "via garibaldi": (45.7833, 12.6167, "Correção Manual"),
                     "fiume veneto pn": (45.7833, 12.6167, "Correção Manual"), "silea tv": (45.7833, 12.6167, "Correção Manual"),
                     "piovene rocchette vi": (45.7833, 12.6167, "Correção Manual"), "persico dosimo cr": (45.7833, 12.6167, "Correção Manual"),
                     "vazzola tv": (45.7833, 12.6167, "Correção Manual"), "fuscaldo cs": (45.7833, 12.6167, "Correção Manual"),
                     "oratino cb": (45.7833, 12.6167, "Correção Manual"), "cavezzo modena": (45.7833, 12.6167, "Correção Manual"),
                     "vasto ch": (45.7833, 12.6167, "Correção Manual"), "bussero mi": (45.7833, 12.6167, "Correção Manual"),
                     "molinella bo": (45.7833, 12.6167, "Correção Manual"), "castello di godego": (45.7000, 11.8667, "Correção Manual"),
                     "sessa aurunca caserta": (45.7833, 12.6167, "Correção Manual"), "cavaglio spoccia verbano cusi ossola": (45.7833, 12.6167, "Correção Manual"),
                     "coreglia antelminelli lucca": (45.7833, 12.6167, "Correção Manual"), "parghelia cosenza": (45.7833, 12.6167, "Correção Manual"),
                     "pietragalla potenza": (45.7833, 12.6167, "Correção Manual"), "valgi di sotto lucca": (45.7833, 12.6167, "Correção Manual"),
                     "pistoia toscana": (45.7833, 12.6167, "Correção Manual"), "filadelfia vibo valentia": (45.7833, 12.6167, "Correção Manual"),
                     "morigerati salerno": (45.7833, 12.6167, "Correção Manual"), "sambiase catanzaro": (45.7833, 12.6167, "Correção Manual"),
                     "praduro e sasso bologna": (45.7833, 12.6167, "Correção Manual"), "quarrata pistoia": (45.7833, 12.6167, "Correção Manual"),
                     "sorbano del vescov lucca": (45.7833, 12.6167, "Correção Manual"), "chieti chieti": (45.7833, 12.6167, "Correção Manual"),
                     "niscemi caltanissetta": (45.7833, 12.6167, "Correção Manual"), "saracena cosenza": (45.7833, 12.6167, "Correção Manual"),
                     "grotte agrigento": (45.7833, 12.6167, "Correção Manual"), "ottaviano napoli": (45.7833, 12.6167, "Correção Manual"),
                     "drapia catanzaro": (45.7833, 12.6167, "Correção Manual"), "torcchiara salerno": (45.7833, 12.6167, "Correção Manual"),
                     "torano castello cosenza": (45.7833, 12.6167, "Correção Manual"), "tramutola potenza": (45.7833, 12.6167, "Correção Manual"),
                     "scandale crotone": (45.7833, 12.6167, "Correção Manual"), "pontremoli massa carrara": (45.7833, 12.6167, "Correção Manual"),
                     "suno novara": (45.7833, 12.6167, "Correção Manual"), "contrada avellino": (45.7833, 12.6167, "Correção Manual"),
                     "spoltore pescara": (45.7833, 12.6167, "Correção Manual"), "stilo catanzaro": (45.7833, 12.6167, "Correção Manual"),
                     "grezzago milano": (45.7833, 12.6167, "Correção Manual"), "fontanella bergamo": (45.7833, 12.6167, "Correção Manual"),
                     "sab pier arena genova": (45.7833, 12.6167, "Correção Manual"), "sersale catanzaro": (45.7833, 12.6167, "Correção Manual"),
                     "fara gera adda bergamo": (45.7833, 12.6167, "Correção Manual"), "conflenti catanzaro": (45.7833, 12.6167, "Correção Manual"),
                     "san ferdinando napoli": (45.7833, 12.6167, "Correção Manual"), "santa luce pisa": (45.7833, 12.6167, "Correção Manual"),
                     "rivello potenza": (45.7833, 12.6167, "Correção Manual"), "daverio varese": (45.7833, 12.6167, "Correção Manual"),
                     "codevigno podova": (45.7833, 12.6167, "Correção Manual"), "fossombrone pesaro e urbino": (45.7833, 12.6167, "Correção Manual"),
                     "sannazzaro burgondi pavia": (45.7833, 12.6167, "Correção Manual"), "quatrelle avellino": (45.7833, 12.6167, "Correção Manual"),
                     "grimaldi cosenza": (45.7833, 12.6167, "Correção Manual"), "almenno san salvatore bergamo": (45.7833, 12.6167, "Correção Manual"),
                     "nanantola modena": (45.7833, 12.6167, "Correção Manual"), "impruneta firenze": (45.7833, 12.6167, "Correção Manual"),
                     "sante marie aquila": (45.7833, 12.6167, "Correção Manual"), "santeramo in colle bari": (45.7833, 12.6167, "Correção Manual"),
                     "polesine zibello parma": (45.7833, 12.6167, "Correção Manual"), "frosolone isernia": (45.7833, 12.6167, "Correção Manual"),
                     "termoli campobasso": (45.7833, 12.6167, "Correção Manual"), "broni pavia": (45.7833, 12.6167, "Correção Manual"),
                     "francica catanzaro": (45.7833, 12.6167, "Correção Manual"), "palazzolo sulloglio brescia": (45.7833, 12.6167, "Correção Manual"),
                     "frisa chieti": (45.7833, 12.6167, "Correção Manual"), "savelli crotone": (45.7833, 12.6167, "Correção Manual"),
                     "sustinente montova": (45.7833, 12.6167, "Correção Manual"), "stazzema lucca": (45.7833, 12.6167, "Correção Manual"),
                     "conselve padova": (45.7833, 12.6167, "Correção Manual"), "cupello chieti": (45.7833, 12.6167, "Correção Manual"),
                     "ferentino frosinone": (45.7833, 12.6167, "Correção Manual"), "torraca salerno": (45.7833, 12.6167, "Correção Manual"),
                     "lombardia bergamo": (45.7833, 12.6167, "Correção Manual"), "tissi sassari": (45.7833, 12.6167, "Correção Manual"),
                     "taormina messina": (45.7833, 12.6167, "Correção Manual"), "san daniele ripa po cremona": (45.7833, 12.6167, "Correção Manual"),
                     "bagnatica bergamo": (45.7833, 12.6167, "Correção Manual"), "torraca salerno": (45.7833, 12.6167, "Correção Manual"),
                     "desenzano del garda brescia": (45.7833, 12.6167, "Correção Manual"), "baselice benevento": (45.7833, 12.6167, "Correção Manual"),
                     "cella dati cremona": (45.7833, 12.6167, "Correção Manual"), "fossalto campobasso": (45.7833, 12.6167, "Correção Manual"),
                     "torricella del pizzo cremona": (45.7833, 12.6167, "Correção Manual"), "cellara cosenza": (45.7833, 12.6167, "Correção Manual"),
                     "biela biela": (45.7833, 12.6167, "Correção Manual"), "mongrassano cosenza": (45.7833, 12.6167, "Correção Manual"),
                     "san pier isonzo gorizia": (45.7833, 12.6167, "Correção Manual"), "regalbuto enna": (45.7833, 12.6167, "Correção Manual"),
                     "gravina in puglia bari": (45.7833, 12.6167, "Correção Manual"), "firenze toscana": (45.7833, 12.6167, "Correção Manual"),
                     "rivarolo mantovano mantua": (45.7833, 12.6167, "Correção Manual"), "san benedetto po mantua": (45.7833, 12.6167, "Correção Manual"),
                     "sant alberto ravenna": (45.7833, 12.6167, "Correção Manual"), "castiglione a casauria pescara": (45.7833, 12.6167, "Correção Manual"),
                     "lioni avellino": (45.7833, 12.6167, "Correção Manual"), "zaccanopoli vibo valentina": (45.7833, 12.6167, "Correção Manual"),
                     "manerba brescia": (45.7833, 12.6167, "Correção Manual"), "guardia sanframondi benevento": (45.7833, 12.6167, "Correção Manual"),
                     "firenzuola florenza": (45.7833, 12.6167, "Correção Manual"), "parrocchia s. maria immacolata veneza": (45.7833, 12.6167, "Correção Manual"),
                     "parrocchia benabbio bagni luca": (45.7833, 12.6167, "Correção Manual"), "parrocchia san lorenzo martire voghera": (45.7833, 12.6167, "Correção Manual"),
                     "parrocchia sant ambrogio dego dego": (45.7833, 12.6167, "Correção Manual"), "chiesa parrocchiale tempio sassari": (45.7833, 12.6167, "Correção Manual"),
                     "via roma 67 cap 36010 - chiuppano": (45.7833, 12.6167, "Correção Manual"), "paroquia maria ss. assunta collegiata": (45.7833, 12.6167, "Correção Manual"),
                     "parrocchia santa gertrude rotzo": (45.7833, 12.6167, "Correção Manual"), "parrocchia s.giovanni battista - montesarchio": (45.7833, 12.6167, "Correção Manual"),
                     "parrocchia san michele arcangelo quarto altino": (45.7833, 12.6167, "Correção Manual"), "piazza san marco 1 - cap 35043 monselice": (45.7833, 12.6167, "Correção Manual"),
                     "via dante maiocchi 55 - cap 01100 roccalvecce": (45.7833, 12.6167, "Correção Manual"), "via europa 10 - cap 55030 - vagli sotto": (45.7833, 12.6167, "Correção Manual"),
                     "piazza aldo moro 24 - cap 45010 villadose": (45.7833, 12.6167, "Correção Manual"), "piazza caduti 1- cap 31024 ormelle": (45.7833, 12.6167, "Correção Manual"),
                     "via umberto i 2 - cap 30014 cavarzere": (45.7833, 12.6167, "Correção Manual"), "via roma 115 - cap 88825 savelli": (45.7833, 12.6167, "Correção Manual"),
                     "via garibaldi 14 - cap 31046 oderzo": (45.7833, 12.6167, "Correção Manual"), "careggine lu": (45.7833, 12.6167, "Correção Manual"),
                     "viale papa giovanni xxiii 2 - cap 31030 castelcucco": (45.7833, 12.6167, "Correção Manual"), "longarone bl": (45.7833, 12.6167, "Correção Manual"),
                     "san bartolomeo in galdo bn": (45.7833, 12.6167, "Correção Manual"), "ceggia ve": (45.7833, 12.6167, "Correção Manual"),
                     "paola cs": (45.7833, 12.6167, "Correção Manual"), "mira ve": (45.7833, 12.6167, "Correção Manual"),
                     "san zenone al po pv": (45.7833, 12.6167, "Correção Manual"), "favaro veneto": (45.7833, 12.6167, "Correção Manual"),
                     "fonte tv": (45.7833, 12.6167, "Correção Manual"), "fardella pz": (45.7833, 12.6167, "Correção Manual"),
                     "molazzana lu": (45.7833, 12.6167, "Correção Manual"), "norbello or": (45.7833, 12.6167, "Correção Manual"),
                     "pedace cs": (45.7833, 12.6167, "Correção Manual"), "ittiri ss": (45.7833, 12.6167, "Correção Manual"),
                     "leonforte en": (45.7833, 12.6167, "Correção Manual"), "samassi su": (45.7833, 12.6167, "Correção Manual"),
                     "arcugnano vi": (45.7833, 12.6167, "Correção Manual"), "piazza iv novembre 10 - 37022 - fumane": (45.7833, 12.6167, "Correção Manual"),
                     "loiano bo": (45.7833, 12.6167, "Correção Manual"), "piazza xiv dicembre 5 - 28019 - suno": (45.7833, 12.6167, "Correção Manual"),
                     "soave vr": (45.7833, 12.6167, "Correção Manual"), "ottaviano na": (45.7833, 12.6167, "Correção Manual"),
                     "via pietro leopoldo 24 - 51028 - san marcello pistoiese": (45.7833, 12.6167, "Correção Manual"), "grezzago mi": (45.7833, 12.6167, "Correção Manual"),
                     "piazza martiri della liberta 3 - 31040 - cessalto": (45.7833, 12.6167, "Correção Manual"), "via xxi luglio cap 81037 sessa aurunca": (45.7833, 12.6167, "Correção Manual"),
                     "via giuseppe garibaldi 60 35020 - correzzola": (45.7833, 12.6167, "Correção Manual"), "zero branco tv": (45.7833, 12.6167, "Correção Manual"),
                     "fumachi": (45.7833, 12.6167, "Correção Manual"), "filippini": (45.7833, 12.6167, "Correção Manual"), "de lucca": (45.7833, 12.6167, "Correção Manual"),
                     "censi": (45.7833, 12.6167, "Correção Manual"), "davi": (45.7833, 12.6167, "Correção Manual"), "fabbiani": (45.7833, 12.6167, "Correção Manual"),
                     "simoncello": (45.7833, 12.6167, "Correção Manual"), "gabrieli": (45.7833, 12.6167, "Correção Manual"), "simonetto": (45.7833, 12.6167, "Correção Manual"),
                     "ortolan": (45.7833, 12.6167, "Correção Manual"), "costellini": (45.7833, 12.6167, "Correção Manual"), "vanzelli": (45.7833, 12.6167, "Correção Manual"),
                     "defalco": (45.7833, 12.6167, "Correção Manual"), "garofalo": (45.7833, 12.6167, "Correção Manual"), "conti": (45.7833, 12.6167, "Correção Manual"),
                     "pizzinat": (45.7833, 12.6167, "Correção Manual"), "bernardini": (45.7833, 12.6167, "Correção Manual"), "via roma 29 - cap 46031 - bagnolo san vito": (45.7833, 12.6167, "Correção Manual"),
                     "rissi": (45.7833, 12.6167, "Correção Manual"), "linguanotto": (45.7833, 12.6167, "Correção Manual"), "quinzi": (45.7833, 12.6167, "Correção Manual"),
                     "colombo": (45.7833, 12.6167, "Correção Manual"), "ragonezi": (45.7833, 12.6167, "Correção Manual"), "morandin": (45.7833, 12.6167, "Correção Manual"),
                     "zanatta": (45.7833, 12.6167, "Correção Manual"), "guerra": (45.7833, 12.6167, "Correção Manual"), "cerantola": (45.7833, 12.6167, "Correção Manual"),
                     "da re": (45.7833, 12.6167, "Correção Manual"), "maggiolo": (45.7833, 12.6167, "Correção Manual"), "pagotto": (45.7833, 12.6167, "Correção Manual"),
                     "cagnotto": (45.7833, 12.6167, "Correção Manual"), "possenatto": (45.7833, 12.6167, "Correção Manual"), "galante": (45.7833, 12.6167, "Correção Manual"),
                     "ravgnani": (45.7833, 12.6167, "Correção Manual"), "giacomin": (45.7833, 12.6167, "Correção Manual"), "morelli": (45.7833, 12.6167, "Correção Manual"),
                     "bussadori": (45.7833, 12.6167, "Correção Manual"), "rizotto": (45.7833, 12.6167, "Correção Manual"), "galuppo": (45.7833, 12.6167, "Correção Manual"),
                     "zerbinati": (45.7833, 12.6167, "Correção Manual"), "buosi": (45.7833, 12.6167, "Correção Manual"), "maiolo": (45.7833, 12.6167, "Correção Manual"),
                     "magnani": (45.7833, 12.6167, "Correção Manual"), "dal ponte": (45.7833, 12.6167, "Correção Manual"), "bettin": (45.7833, 12.6167, "Correção Manual"),
                     "bovi": (45.7833, 12.6167, "Correção Manual"), "fante": (45.7833, 12.6167, "Correção Manual"), "ravasio": (45.7833, 12.6167, "Correção Manual"),
                     "rosa": (45.7833, 12.6167, "Correção Manual"), "pagliarone": (45.7833, 12.6167, "Correção Manual"), "pagliari": (45.7833, 12.6167, "Correção Manual"),
                     "zuccon": (45.7833, 12.6167, "Correção Manual"), "zambotti": (45.7833, 12.6167, "Correção Manual"), "zoccaratto": (45.7833, 12.6167, "Correção Manual"),
                     "ferronato": (45.7833, 12.6167, "Correção Manual"), "rossato": (45.7833, 12.6167, "Correção Manual"), "marin": (45.7833, 12.6167, "Correção Manual"),
                     "bobbo": (45.7833, 12.6167, "Correção Manual"), "ungarelli": (45.7833, 12.6167, "Correção Manual"), "mariani": (45.7833, 12.6167, "Correção Manual"),
                     "pace": (45.7833, 12.6167, "Correção Manual"), "bertoncello": (45.7833, 12.6167, "Correção Manual"), "camaduro": (45.7833, 12.6167, "Correção Manual"),
                     "lombello": (45.7833, 12.6167, "Correção Manual"), "furlan": (45.7833, 12.6167, "Correção Manual"), "asinelli": (45.7833, 12.6167, "Correção Manual"),
                     "gualtieri": (45.7833, 12.6167, "Correção Manual"), "ferri": (45.7833, 12.6167, "Correção Manual"), "borelli": (45.7833, 12.6167, "Correção Manual"),
                     "facchini": (45.7833, 12.6167, "Correção Manual"), "marchesin": (45.7833, 12.6167, "Correção Manual"), "rizzati": (45.7833, 12.6167, "Correção Manual"),
                     "andruccioli": (45.7833, 12.6167, "Correção Manual"), "conti": (45.7833, 12.6167, "Correção Manual"), "nesi": (45.7833, 12.6167, "Correção Manual"),
                     "bailo": (45.7833, 12.6167, "Correção Manual"), "gabrielli": (45.7833, 12.6167, "Correção Manual"), "faragutti": (45.7833, 12.6167, "Correção Manual"),
                     "gobbi": (45.7833, 12.6167, "Correção Manual"), "biguetto": (45.7833, 12.6167, "Correção Manual"), "cola": (45.7833, 12.6167, "Correção Manual"),
                     "zonatto": (45.7833, 12.6167, "Correção Manual"), "massarotto": (45.7833, 12.6167, "Correção Manual"), "marruchella": (45.7833, 12.6167, "Correção Manual"),
                     "rampazzo": (45.7833, 12.6167, "Correção Manual"), "perissoto": (45.7833, 12.6167, "Correção Manual"), "esposte": (45.7833, 12.6167, "Correção Manual"),
                     "chiebao": (45.7833, 12.6167, "Correção Manual"), "musacco": (45.7833, 12.6167, "Correção Manual"), "misurelli": (45.7833, 12.6167, "Correção Manual"),
                     "perrone": (45.7833, 12.6167, "Correção Manual"), "ghisoni": (45.7833, 12.6167, "Correção Manual"), "massoni": (45.7833, 12.6167, "Correção Manual"),
                     "scappini": (45.7833, 12.6167, "Correção Manual"), "magri": (45.7833, 12.6167, "Correção Manual"), "andreoli": (45.7833, 12.6167, "Correção Manual"),
                     "toffolo": (45.7833, 12.6167, "Correção Manual"), "bettanin": (45.7833, 12.6167, "Correção Manual"), "sabbadini": (45.7833, 12.6167, "Correção Manual"),
                     "franchini": (45.7833, 12.6167, "Correção Manual"), "dall osto": (45.7833, 12.6167, "Correção Manual"), "flora": (45.7833, 12.6167, "Correção Manual"),
                     "giordano": (45.7833, 12.6167, "Correção Manual"), "marchiori": (45.7833, 12.6167, "Correção Manual"), "rettore": (45.7833, 12.6167, "Correção Manual"),
                     "fontanella": (45.7833, 12.6167, "Correção Manual"), "furlanetto": (45.7833, 12.6167, "Correção Manual"), "corradini": (45.7833, 12.6167, "Correção Manual"),
                     "michielon": (45.7833, 12.6167, "Correção Manual"), "pedace": (45.7833, 12.6167, "Correção Manual"), "romio": (45.7833, 12.6167, "Correção Manual"),
                     "zampiva": (45.7833, 12.6167, "Correção Manual"), "sabbadin": (45.7833, 12.6167, "Correção Manual"), "perette": (45.7833, 12.6167, "Correção Manual"),
                     "rizzon deon": (45.7833, 12.6167, "Correção Manual"), "polo": (45.7833, 12.6167, "Correção Manual"), "dettori": (45.7833, 12.6167, "Correção Manual"),
                     "bulgarelli": (45.7833, 12.6167, "Correção Manual"), "peruchi": (45.7833, 12.6167, "Correção Manual"), "squizzato": (45.7833, 12.6167, "Correção Manual"),
                     "rissi": (45.7833, 12.6167, "Correção Manual"), "meotti": (45.7833, 12.6167, "Correção Manual"), "galletti": (45.7833, 12.6167, "Correção Manual"),
                     "chinelato": (45.7833, 12.6167, "Correção Manual"), "begalli": (45.7833, 12.6167, "Correção Manual"), "petrone": (45.7833, 12.6167, "Correção Manual"),
                     "bovo": (45.7833, 12.6167, "Correção Manual"), "massarelli": (45.7833, 12.6167, "Correção Manual"), "rigazzo": (45.7833, 12.6167, "Correção Manual"),
                     "pagnota": (45.7833, 12.6167, "Correção Manual"), "olivo": (45.7833, 12.6167, "Correção Manual"), "biondi": (45.7833, 12.6167, "Correção Manual"),
                     "masarut": (45.7833, 12.6167, "Correção Manual"), "escopo": (45.7833, 12.6167, "Correção Manual"), "funghi": (45.7833, 12.6167, "Correção Manual"),
                     "azzolini": (45.7833, 12.6167, "Correção Manual"), "naressi": (45.7833, 12.6167, "Correção Manual"), "pra nichele": (45.7833, 12.6167, "Correção Manual"),
                     "stasio": (45.7833, 12.6167, "Correção Manual"), "marson": (45.7833, 12.6167, "Correção Manual"), "zocconelli": (45.7833, 12.6167, "Correção Manual"),
                     "lovato": (45.7833, 12.6167, "Correção Manual"), "cicuto": (45.7833, 12.6167, "Correção Manual"), "ruzzon": (45.7833, 12.6167, "Correção Manual"),
                     "carazzo": (45.7833, 12.6167, "Correção Manual"), "benito": (45.7833, 12.6167, "Correção Manual"), "bressan": (45.7833, 12.6167, "Correção Manual"),
                     "casadei": (45.7833, 12.6167, "Correção Manual"), "gobbo": (45.7833, 12.6167, "Correção Manual")
                }
                provincias_manuais = { # ... (dicionário mantido) ...
                     "treviso": (45.6667, 12.2500, "Correção Província"), "venezia": (45.4375, 12.3358, "Correção Província"),
                     "padova": (45.4167, 11.8667, "Correção Província"), "verona": (45.4386, 10.9928, "Correção Província"),
                     "vicenza": (45.5500, 11.5500, "Correção Província"), "rovigo": (45.0667, 11.7833, "Correção Província"),
                     "mantova": (45.1500, 10.7833, "Correção Província"), "belluno": (46.1333, 12.2167, "Correção Província"),
                     "pordenone": (45.9667, 12.6500, "Correção Província"), "udine": (46.0667, 13.2333, "Correção Província"),
                     "roma": (41.9000, 12.5000, "Correção Província")
                }
                
                # Iterar apenas nas linhas ainda sem coordenadas
                for idx in df_final[no_coords_mask].index:
                    comune_norm = df_final.at[idx, 'COMUNE_NORM']
                    provincia_norm = df_final.at[idx, 'PROVINCIA_NORM']
                    lat, lon, source = pd.NA, pd.NA, pd.NA
                    
                    if comune_norm in correcoes_manuais:
                        lat, lon, source = correcoes_manuais[comune_norm]
                    elif provincia_norm in provincias_manuais: # Só aplica província se comune não achou
                        lat, lon, source = provincias_manuais[provincia_norm]
                    
                    if pd.notna(lat):
                        df_final.at[idx, 'latitude'] = lat
                        df_final.at[idx, 'longitude'] = lon
                        df_final.at[idx, 'COORD_SOURCE'] = source
                        manual_matches += 1
                print(f"{manual_matches} coordenadas aplicadas por Correções Manuais.")
                no_coords_mask = df_final['latitude'].isna() # Atualizar máscara
                print(f"{no_coords_mask.sum()} registros ainda sem coordenadas.")
            
            # 4. Match Fuzzy (Múltiplos Métodos)
            if no_coords_mask.any() and process is not None and fuzz is not None:
                print("Etapa 4: Match Fuzzy (Múltiplos Métodos)")
                fuzzy_matches_count = 0
                match_threshold = 80 
                
                # Lista de comunes do JSON para comparar
                json_comunes_norm_list = df_coordenadas['COMUNE_MAPA_NORM'].unique().tolist()
                if 'nao especificado' in json_comunes_norm_list: json_comunes_norm_list.remove('nao especificado')
                
                # Cache para evitar recalcular matches
                fuzzy_matches_cache = {}
                
                # Iterar apenas nos que ainda não têm coordenadas
                for idx in df_final[no_coords_mask].index:
                    comune_norm = df_final.at[idx, 'COMUNE_NORM']
                    if comune_norm == 'nao especificado' or len(comune_norm) < 3:
                        continue
                    
                    best_match, score, method = None, 0, None
                    
                    # Verificar cache
                    if comune_norm in fuzzy_matches_cache:
                         best_match, score, method = fuzzy_matches_cache[comune_norm]
                    else:
                        # Tentar diferentes métodos fuzzy
                        scorers = {
                            'TokenSort': fuzz.token_sort_ratio,
                            'TokenSet': fuzz.token_set_ratio,
                            'Partial': fuzz.partial_ratio,
                            'Standard': fuzz.ratio
                        }
                        current_best_score = 0
                        
                        for method_name, scorer_func in scorers.items():
                             cutoff = match_threshold if method_name != 'Standard' else 75 # Threshold menor para Standard
                             match_result = process.extractOne(
                                 query=comune_norm,
                                 choices=json_comunes_norm_list,
                                 scorer=scorer_func, 
                                 score_cutoff=cutoff
                             )
                             if match_result and match_result[1] > current_best_score:
                                  best_match, score, method = match_result[0], match_result[1], method_name
                                  current_best_score = score
                                  # Prioridade alta para TokenSet e TokenSort
                                  if method_name in ['TokenSet', 'TokenSort'] and score >= 85: 
                                       break # Confiança alta, parar busca
                                       
                        fuzzy_matches_cache[comune_norm] = (best_match, score, method) # Cache result (inclui falhas)

                    # Aplicar o melhor match encontrado
                    if best_match:
                        match_rows = df_coordenadas[df_coordenadas['COMUNE_MAPA_NORM'] == best_match]
                        if not match_rows.empty:
                            match_row = match_rows.iloc[0]
                            df_final.at[idx, 'latitude'] = match_row['latitude']
                            df_final.at[idx, 'longitude'] = match_row['longitude']
                            df_final.at[idx, 'COORD_SOURCE'] = f'FuzzyMatch_{method}_{score}'
                            fuzzy_matches_count += 1
                            
                print(f"{fuzzy_matches_count} coordenadas adicionadas por Match Fuzzy.")
                no_coords_mask = df_final['latitude'].isna() # Atualizar máscara
                print(f"{no_coords_mask.sum()} registros ainda sem coordenadas.")
            elif no_coords_mask.any():
                 st.warning("Biblioteca 'thefuzz' não disponível. Etapa de Matching Fuzzy ignorada.")

            # 5. Match por Início do Nome (Prefix Match)
            if no_coords_mask.any():
                print("Etapa 5: Match por Início do Nome (Prefixo)")
                prefix_matches_count = 0
                for idx in df_final[no_coords_mask].index:
                    comune_norm = df_final.at[idx, 'COMUNE_NORM']
                    if comune_norm == 'nao especificado' or len(comune_norm) < 4:
                        continue
                    
                    prefix_len = min(len(comune_norm), 5)
                    prefix = comune_norm[:prefix_len]
                    possible_matches = [c for c in json_comunes_norm_list if c.startswith(prefix)]
                    
                    if possible_matches:
                        best_match = sorted(possible_matches, key=len)[0] # O mais curto
                        match_rows = df_coordenadas[df_coordenadas['COMUNE_MAPA_NORM'] == best_match]
                        if not match_rows.empty:
                            match_row = match_rows.iloc[0]
                            df_final.at[idx, 'latitude'] = match_row['latitude']
                            df_final.at[idx, 'longitude'] = match_row['longitude']
                            df_final.at[idx, 'COORD_SOURCE'] = f'PrefixMatch_{prefix}'
                            prefix_matches_count += 1
                            
                print(f"{prefix_matches_count} coordenadas adicionadas por Match de Prefixo.")
                no_coords_mask = df_final['latitude'].isna() # Atualizar máscara
                print(f"{no_coords_mask.sum()} registros ainda sem coordenadas.")

            # 6. Último Recurso: Match por Província (Exato e Fuzzy)
            if no_coords_mask.any():
                print("Etapa 6: Match por Província (Exato e Fuzzy)")
                provincia_matches_count = 0
                json_provincias_norm_list = df_coordenadas['PROVINCIA_MAPA_NORM'].unique().tolist()
                if 'nao especificado' in json_provincias_norm_list: json_provincias_norm_list.remove('nao especificado')
                
                # Corrigido (envolvido em parênteses)
                provincia_coord_map = (df_coordenadas
                                       .drop_duplicates(subset=['PROVINCIA_MAPA_NORM'], keep='first')
                                       .set_index('PROVINCIA_MAPA_NORM')[['latitude', 'longitude']]
                                       .to_dict('index')
                                      )
                
                for idx in df_final[no_coords_mask].index:
                    provincia_norm = df_final.at[idx, 'PROVINCIA_NORM']
                    coords = None
                    source = None
                    
                    if provincia_norm != 'nao especificado':
                        # Tentar match exato da província
                        if provincia_norm in provincia_coord_map:
                             coords = provincia_coord_map[provincia_norm]
                             source = 'ProvinciaMatch'
                        # Se falhar e tiver thefuzz, tentar fuzzy
                        elif process is not None and fuzz is not None and len(provincia_norm) >= 4:
                            match_result = process.extractOne(
                                query=provincia_norm,
                                choices=json_provincias_norm_list,
                                scorer=fuzz.token_set_ratio,
                                score_cutoff=75
                            )
                            if match_result:
                                best_match_prov = match_result[0]
                                if best_match_prov in provincia_coord_map:
                                     coords = provincia_coord_map[best_match_prov]
                                     source = f'ProvinciaFuzzy_{match_result[1]}'
                    
                    if coords:
                         df_final.at[idx, 'latitude'] = coords['latitude']
                         df_final.at[idx, 'longitude'] = coords['longitude']
                         df_final.at[idx, 'COORD_SOURCE'] = source
                         provincia_matches_count += 1
                         
                print(f"{provincia_matches_count} coordenadas adicionadas por Match de Província (Exato/Fuzzy).")
                no_coords_mask = df_final['latitude'].isna() # Atualizar máscara
                print(f"{no_coords_mask.sum()} registros ainda sem coordenadas.")

            # Contagem final e Log
            coords_found_final = df_final['latitude'].notna().sum()
            total_rows = len(df_final)
            match_rate = (coords_found_final / total_rows * 100) if total_rows > 0 else 0
            print(f"[DataLoader ComuneNovo] Processo de geocodificação concluído.")
            print(f"Total final com coordenadas: {coords_found_final}/{total_rows} ({match_rate:.1f}%).")
            
            # --- Exportar Registros Não Mapeados para CSV --- 
            df_nao_mapeados = df_final[df_final['latitude'].isna()].copy()
            if not df_nao_mapeados.empty:
                print(f"[DataLoader ComuneNovo] Exportando {len(df_nao_mapeados)} registros não mapeados para registros_nao_mapeados_debug.csv...")
                cols_export_debug = [
                    'ID', 
                    'UF_CRM_12_ENDERECO_DO_COMUNE',
                    'UF_CRM_12_1722881735827', 
                    'UF_CRM_12_1743015702671',
                    'COMUNE_ORIG_TEMP', # O valor usado para normalizar comune
                    'COMUNE_NORM', 
                    'PROVINCIA_NORM',
                    'TITLE', # Adicionar título para contexto
                    'STAGE_ID' # Adicionar estágio para contexto
                ]
                cols_export_existentes = [c for c in cols_export_debug if c in df_nao_mapeados.columns]
                try:
                    df_nao_mapeados[cols_export_existentes].to_csv('registros_nao_mapeados_debug.csv', index=False, encoding='utf-8-sig')
                    print("[DataLoader ComuneNovo] Exportação concluída.")
                except Exception as export_err:
                    print(f"[DataLoader ComuneNovo] Erro ao exportar CSV de debug: {export_err}")
            # --- Fim Exportação --- 
            
            # --- FIM LÓGICA DE MATCHING REESTRUTURADA ---
            
        else:
            st.warning("Não foi possível carregar dados de coordenadas. O mapa não funcionará.")

        # --- DEBUG: Verificar colunas ANTES da limpeza/rename --- 
        # print("[DataLoader ComuneNovo] Colunas antes da limpeza final:", df_final.columns.tolist())
        # --- FIM DEBUG ---

        # --- 7. Limpeza Final Opcional --- 
        # Remover colunas temporárias e normalizadas se não forem mais necessárias
        # Mantém COORD_SOURCE para análise
        df_final.drop(columns=['COMUNE_ORIG_TEMP', 'COMUNE_NORM', 'PROVINCIA_NORM'], errors='ignore', inplace=True)

        # --- DEBUG: Mostrar distribuição da fonte das coordenadas ---
        if 'COORD_SOURCE' in df_final.columns:
            coord_source_counts = df_final['COORD_SOURCE'].value_counts(dropna=False)
            print("\n[DataLoader ComuneNovo] Distribuição COORD_SOURCE:")
            print(coord_source_counts)
            print(f"Total de linhas: {len(df_final)}")
            print(f"Linhas sem coordenadas (COORD_SOURCE is NA): {df_final['COORD_SOURCE'].isna().sum()}\n")
        # --- FIM DEBUG ---

        print(f"[DataLoader ComuneNovo] Processamento concluído. Retornando {df_final.shape[0]} linhas.")
        return df_final

    except Exception as e:
        st.exception(f"Erro inesperado ao carregar dados para Comune (Novo): {e}")
        return pd.DataFrame()

# Exemplo de uso (pode ser removido ou comentado)
if __name__ == '__main__':
    # REMOVIDO: Configuração já feita em main.py para evitar conflito
    # st.set_page_config(layout="wide")
    st.title("Teste do DataLoader Comune (Novo)")
    
    if st.button("Carregar Dados Comune (Novo) com Coords"):
        df = load_comune_data(force_reload=True)
        if not df.empty:
            st.success(f"Dados carregados com sucesso! ({df.shape[0]} linhas)")
            st.dataframe(df.head())
            st.write("Info:", df.info(verbose=True))
            st.write("Tipos de Dados:", df.dtypes)
            
            # Verificar nulos nas colunas essenciais e de coordenadas
            st.write("Valores Nulos (CREATED_TIME):", df['CREATED_TIME'].isnull().sum())
            st.write("Valores Nulos (STAGE_ID):", df['STAGE_ID'].isnull().sum())
            st.write("Valores Nulos (latitude):", df['latitude'].isnull().sum())
            st.write("Valores Nulos (longitude):", df['longitude'].isnull().sum())
        else:
            st.error("Falha ao carregar os dados.") 