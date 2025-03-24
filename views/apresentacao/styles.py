import streamlit as st

def aplicar_estilos_apresentacao():
    """Aplica estilos CSS otimizados para apresentação em TV vertical"""
    st.markdown("""
    <style>
    /* Estilos base para o modo apresentação */
    body, .stApp {
        font-family: 'Roboto', Arial, Helvetica, sans-serif !important;
        color: #333333;
        background-color: #f8f9fa !important;
        height: 100vh;
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    
    /* Adicionar regras para garantir que os containers sejam totalmente limpos */
    .element-container {
        overflow: hidden;
    }
    
    /* Garantir que elementos não vazem entre slides */
    [data-testid="column"] {
        overflow: hidden !important;
    }
    
    /* Garantir que o Streamlit limpe os elementos com display none */
    [data-empty="true"] {
        display: none !important;
    }
    
    /* Contêiner do cabeçalho */
    .header-container {
        background: linear-gradient(135deg, #1A237E 0%, #283593 100%);
        padding: 25px 15px;
        border-radius: 0 0 20px 20px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    /* Título da apresentação */
    .presentation-title {
        font-size: 3.2rem !important;
        font-weight: 900 !important;
        color: white !important;
        margin: 0 !important;
        line-height: 1.2 !important;
        letter-spacing: -0.5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Subtítulo da apresentação */
    .presentation-subtitle {
        font-size: 1.8rem;
        color: rgba(255,255,255,0.9);
        margin: 10px 0 0 0;
        font-weight: 400;
    }
    
    /* Contêiner de slides */
    .slide-container {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        padding: 25px;
        margin-bottom: 20px;
        height: calc(100vh - 200px);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    /* Título do slide */
    .slide-title {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #1A237E !important;
        margin-bottom: 25px !important;
        text-align: center;
        border-bottom: 3px solid #E0E0E0;
        padding-bottom: 15px;
        background: linear-gradient(to right, #1A237E, #3949AB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Contador de slides */
    .slide-counter {
        position: absolute;
        bottom: 25px;
        right: 20px;
        background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.8) 100%);
        color: white;
        padding: 8px 15px;
        border-radius: 30px;
        font-size: 1rem;
        font-weight: 600;
        z-index: 1000;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    
    /* Estilo para informações de slide */
    .slide-info {
        position: absolute;
        bottom: 25px;
        left: 20px;
        background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.8) 100%);
        color: white;
        padding: 8px 15px;
        border-radius: 30px;
        font-size: 0.9rem;
        z-index: 1000;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    
    .updated-at {
        display: flex;
        align-items: center;
    }
    
    .updated-at:before {
        content: "";
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #4CAF50;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
        }
        70% {
            box-shadow: 0 0 0 6px rgba(76, 175, 80, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
        }
    }
    
    /* Classes para cartões de métricas */
    .metric-card-tv {
        background: white;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        padding: 25px;
        margin-bottom: 20px;
        text-align: center;
        border-left: 10px solid;
        height: auto;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card-tv:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }
    
    .metric-card-tv.total {
        border-color: #2E7D32;
    }
    
    .metric-card-tv.media {
        border-color: #1565C0;
    }
    
    .metric-card-tv.taxa {
        border-color: #E65100;
    }
    
    .metric-value-tv {
        font-size: 5rem !important;
        font-weight: 900 !important;
        line-height: 1.1;
        margin: 10px 0;
        background: linear-gradient(to right, #1A237E, #3949AB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card-tv.total .metric-value-tv {
        background: linear-gradient(to right, #1B5E20, #2E7D32);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card-tv.media .metric-value-tv {
        background: linear-gradient(to right, #0D47A1, #1565C0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card-tv.taxa .metric-value-tv {
        background: linear-gradient(to right, #E65100, #F57C00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-title-tv {
        font-size: 2rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        margin-bottom: 15px;
    }
    
    .metric-subtitle-tv {
        font-size: 1.4rem;
        color: #666;
        font-weight: 400;
    }
    
    /* Para gráficos */
    .chart-container-tv {
        width: 100%;
        height: calc(100vh - 330px);
        min-height: 500px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        padding: 15px;
    }
    
    /* Rodapé com data de atualização */
    .update-footer {
        text-align: center;
        padding: 10px;
        background-color: #f8f9fa;
        color: #666;
        position: absolute;
        bottom: 10px;
        width: 100%;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    /* Estilo específico para o carrossel */
    .progress-bar-container {
        width: 100%;
        background-color: #e0e0e0;
        height: 6px;
        border-radius: 3px;
        margin-top: 10px;
        position: fixed;
        bottom: 15px;
        left: 0;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(to right, #1976D2, #1A237E);
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    
    /* Melhorias para tabelas */
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        border-radius: 10px;
        overflow: hidden;
    }
    
    thead tr {
        background: linear-gradient(135deg, #1A237E 0%, #283593 100%);
        color: white;
    }
    
    thead th {
        padding: 12px;
        font-weight: 600;
        text-align: center;
    }
    
    tbody tr:nth-child(even) {
        background-color: #f5f5f5;
    }
    
    tbody tr:nth-child(odd) {
        background-color: white;
    }
    
    tbody tr:hover {
        background-color: #e8eaf6;
    }
    
    tbody td {
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    
    /* Melhorias para os botões de navegação grandes */
    .big-nav-buttons {
        display: flex;
        justify-content: space-between;
        gap: 15px; 
        margin-bottom: 15px;
        background: linear-gradient(135deg, #f0f2f6 0%, #e6e9f0 100%);
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .nav-button {
        flex: 1;
        background: linear-gradient(135deg, #1A237E 0%, #303F9F 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 14px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        text-align: center;
        transition: all 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .nav-button:hover {
        background: linear-gradient(135deg, #303F9F 0%, #3949AB 100%);
        transform: translateY(-3px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.3);
    }
    
    .nav-button a {
        color: white;
        text-decoration: none;
        display: block;
        width: 100%;
        height: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
