import pandas as pd

def ensure_pandas_df(df):
    """
    Converte qualquer DataFrame para pandas nativo.
    
    Solução para o erro: "You passed a narwhals DataFrame to is_pandas_dataframe"
    que ocorre quando DataFrames narwhals são passados para componentes Streamlit
    como st.dataframe(), st.bar_chart(), etc.
    
    Args:
        df: DataFrame de qualquer tipo (pandas, narwhals, etc.)
        
    Returns:
        pandas.DataFrame: DataFrame convertido para pandas nativo
    """
    if df is None:
        return pd.DataFrame()
    
    # Verifica se é um DataFrame narwhals e tenta converter
    if hasattr(df, 'to_pandas'):
        return df.to_pandas()
    elif hasattr(df, 'to_native'):
        return df.to_native()
    elif str(type(df)).find('narwhals') != -1:
        # Para casos onde o DataFrame é narwhals mas não tem os métodos acima
        try:
            return pd.DataFrame(df)
        except Exception:
            # Se falhar, tenta converter os dados manualmente
            return pd.DataFrame(data=df.values if hasattr(df, 'values') else df)
    else:
        # Já é pandas ou outro tipo compatível
        return df

def ensure_pandas_series(series):
    """
    Converte qualquer Series para pandas nativo.
    
    Args:
        series: Series de qualquer tipo (pandas, narwhals, etc.)
        
    Returns:
        pandas.Series: Series convertido para pandas nativo
    """
    if series is None:
        return pd.Series()
    
    # Verifica se é uma Series narwhals e tenta converter
    if hasattr(series, 'to_pandas'):
        return series.to_pandas()
    elif hasattr(series, 'to_native'):
        return series.to_native()
    elif str(type(series)).find('narwhals') != -1:
        # Para casos onde a Series é narwhals mas não tem os métodos acima
        try:
            return pd.Series(series)
        except Exception:
            # Se falhar, tenta converter os dados manualmente
            return pd.Series(data=series.values if hasattr(series, 'values') else series)
    else:
        # Já é pandas ou outro tipo compatível
        return series

# Wrapper para st.dataframe que garante compatibilidade
def safe_dataframe(df, **kwargs):
    """
    Wrapper seguro para st.dataframe que garante compatibilidade com narwhals.
    
    Args:
        df: DataFrame de qualquer tipo
        **kwargs: Argumentos passados para st.dataframe
        
    Returns:
        Resultado do st.dataframe com DataFrame convertido
    """
    import streamlit as st
    return st.dataframe(ensure_pandas_df(df), **kwargs)

# Wrapper para st.bar_chart que garante compatibilidade
def safe_bar_chart(df, **kwargs):
    """
    Wrapper seguro para st.bar_chart que garante compatibilidade com narwhals.
    
    Args:
        df: DataFrame de qualquer tipo
        **kwargs: Argumentos passados para st.bar_chart
        
    Returns:
        Resultado do st.bar_chart com DataFrame convertido
    """
    import streamlit as st
    return st.bar_chart(ensure_pandas_df(df), **kwargs)

# Wrapper para st.line_chart que garante compatibilidade
def safe_line_chart(df, **kwargs):
    """
    Wrapper seguro para st.line_chart que garante compatibilidade com narwhals.
    
    Args:
        df: DataFrame de qualquer tipo
        **kwargs: Argumentos passados para st.line_chart
        
    Returns:
        Resultado do st.line_chart com DataFrame convertido
    """
    import streamlit as st
    return st.line_chart(ensure_pandas_df(df), **kwargs)

# Wrapper para st.scatter_chart que garante compatibilidade
def safe_scatter_chart(df, **kwargs):
    """
    Wrapper seguro para st.scatter_chart que garante compatibilidade com narwhals.
    
    Args:
        df: DataFrame de qualquer tipo
        **kwargs: Argumentos passados para st.scatter_chart
        
    Returns:
        Resultado do st.scatter_chart com DataFrame convertido
    """
    import streamlit as st
    return st.scatter_chart(ensure_pandas_df(df), **kwargs)

# Wrapper para st.area_chart que garante compatibilidade
def safe_area_chart(df, **kwargs):
    """
    Wrapper seguro para st.area_chart que garante compatibilidade com narwhals.
    
    Args:
        df: DataFrame de qualquer tipo
        **kwargs: Argumentos passados para st.area_chart
        
    Returns:
        Resultado do st.area_chart com DataFrame convertido
    """
    import streamlit as st
    return st.area_chart(ensure_pandas_df(df), **kwargs) 