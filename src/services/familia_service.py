"""Serviço para gerenciar dados das famílias"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
import streamlit as st
from ..data.database import db
from ..services.bitrix_service import bitrix_service
from datetime import datetime
from ..utils.constants import PAYMENT_OPTIONS, PAYMENT_OPTIONS_COLORS

class FamiliaService:
    """Classe para gerenciar dados das famílias"""

    @staticmethod
    def safe_convert_to_int(value) -> int:
        """Converte valor para inteiro de forma segura, tratando NaN e infinitos"""
        try:
            print(f"Tentando converter valor: {value}, tipo: {type(value)}")
            if pd.isna(value):
                print(f"Valor é NA/NaN")
                return 0
            if np.isinf(value):
                print(f"Valor é infinito")
                return 0
            result = int(value)
            print(f"Conversão bem sucedida: {result}")
            return result
        except Exception as e:
            print(f"Erro na conversão para inteiro: {str(e)}")
            return 0

    @staticmethod
    @st.cache_data(ttl=300)
    def get_dashboard_metrics() -> Optional[Dict[str, Any]]:
        """
        Obtém métricas do dashboard a partir da view
        
        Returns:
            Dicionário com as métricas ou None em caso de erro
        """
        try:
            print("Obtendo métricas do dashboard...")
            query = "SELECT * FROM vw_dashboard_metricas LIMIT 1"
            df = db.execute_query(query)
            
            if df is not None and not df.empty:
                print("Métricas obtidas com sucesso")
                metrics = df.iloc[0].to_dict()
                print(f"Colunas disponíveis: {list(metrics.keys())}")
                print(f"Valores: {metrics}")
                return metrics
            print("Nenhuma métrica encontrada")
            return None
        except Exception as e:
            print(f"Erro ao obter métricas do dashboard: {str(e)}")
            return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_total_requerentes() -> Optional[int]:
        """Obtém o total de requerentes que preencheram o formulário"""
        metrics = FamiliaService.get_dashboard_metrics()
        if metrics:
            return int(metrics['total_requerentes'])
        
        # Fallback para a query original caso a view não funcione
        query = """
        SELECT COUNT(*) as total
        FROM whatsapp_euna_data.euna_familias
        WHERE is_menor = 0
        AND isSpecial = 0 
        AND hasTechnicalProblems = 0
        AND idfamilia IS NOT NULL 
        AND TRIM(idfamilia) != ''
        """
        df = db.execute_query(query)
        if df is not None and not df.empty:
            return int(df['total'].iloc[0])
        return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_familias_status() -> Optional[pd.DataFrame]:
        """
        Obtém o status das famílias com cache
        
        Returns:
            DataFrame com o status das famílias ou None em caso de erro
        """
        try:
            print("Iniciando get_familias_status...")
            # Obter métricas da view
            metrics = FamiliaService.get_dashboard_metrics()
            
            if metrics:
                print("Criando DataFrame com totais...")
                # Criar DataFrame com os totais, convertendo valores de forma segura
                total_row = {
                    'ID_Familia': 'TOTAL',
                    'Nome_Familia': 'Total'
                }
                
                # Processar cada métrica individualmente com log
                for key in ['opcao_a', 'opcao_b', 'opcao_c', 'opcao_d', 'opcao_e', 'opcao_f', 'opcao_y']:
                    value = metrics.get(key, 0)
                    print(f"Processando {key}: valor original = {value}")
                    total_row[key.split('_')[1].upper()] = FamiliaService.safe_convert_to_int(value)
                
                # Processar outras métricas
                metric_mappings = {
                    'condicao_especial': 'Condicao_Especial',
                    'requerentes_continuar': 'Requerentes_Continuar',
                    'requerentes_cancelar': 'Requerentes_Cancelar',
                    'sem_opcao': 'Sem_Opcao',
                    'total_adendos': 'Total_Adendos_ID',
                    'familias_com_adendos': 'Total_Adendos_Familia',
                    'total_requerentes': 'Requerentes_Maiores'
                }
                
                for metric_key, row_key in metric_mappings.items():
                    value = metrics.get(metric_key, 0)
                    print(f"Processando {metric_key}: valor original = {value}")
                    total_row[row_key] = FamiliaService.safe_convert_to_int(value)
                
                # Campos fixos
                total_row['Requerentes_Menores'] = 0
                total_row['Total_Banco'] = total_row['Requerentes_Maiores']
                
                print("Total row criado:", total_row)
                
                # Consulta para obter detalhes por família
                print("Executando query para detalhes por família...")
                query_familias = """
                WITH FamiliaMetrics AS (
                    SELECT 
                        e.idfamilia AS ID_Familia,
                        COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
                        SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
                        SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
                        SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
                        SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
                        SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
                        SUM(CASE WHEN e.paymentOption = 'F' THEN 1 ELSE 0 END) AS F,
                        SUM(CASE WHEN e.paymentOption = 'Y' THEN 1 ELSE 0 END) AS Y,
                        SUM(CASE WHEN e.specialConditionFamily = 1 THEN 1 ELSE 0 END) AS Condicao_Especial,
                        SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F','Y') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
                        SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
                        SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
                        COUNT(DISTINCT CASE WHEN e.lastEventsUpdate IS NOT NULL AND e.lastEventsUpdate != '' THEN e.id END) AS Total_Adendos_ID,
                        1 AS Total_Adendos_Familia,
                        COUNT(DISTINCT e.id) AS Requerentes_Maiores,
                        0 AS Requerentes_Menores,
                        COUNT(DISTINCT e.id) AS Total_Banco
                    FROM whatsapp_euna_data.euna_familias e
                    LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
                    WHERE e.is_menor = 0 
                    AND e.isSpecial = 0 
                    AND e.hasTechnicalProblems = 0
                    GROUP BY e.idfamilia, f.nome_familia
                )
                SELECT * FROM FamiliaMetrics
                ORDER BY Nome_Familia
                """
                
                df_familias = db.execute_query(query_familias)
                
                if df_familias is not None and not df_familias.empty:
                    print(f"Dados das famílias obtidos: {len(df_familias)} registros")
                    print("Tipos de dados do DataFrame:", df_familias.dtypes)
                    
                    # Verificar valores não finitos
                    for col in df_familias.select_dtypes(include=[np.number]).columns:
                        non_finite = df_familias[col].isna().sum() + np.isinf(df_familias[col]).sum()
                        if non_finite > 0:
                            print(f"Coluna {col} tem {non_finite} valores não finitos")
                    
                    # Adicionar linha de totais
                    df_totals = pd.DataFrame([total_row])
                    print("Concatenando DataFrames...")
                    df_status = pd.concat([df_familias, df_totals], ignore_index=True)
                    print("DataFrame final criado com sucesso")
                    return df_status
                
                print("Nenhum dado de família encontrado, retornando apenas totais")
                return pd.DataFrame([total_row])
            
            print("Métricas não encontradas, usando fallback query")
            # Fallback para a query original caso a view não funcione
            query = """
            WITH AdendoMetrics AS (
                SELECT 
                    COUNT(DISTINCT CASE 
                        WHEN lastEventsUpdate IS NOT NULL 
                        AND lastEventsUpdate != ''
                        AND is_menor = 0
                        THEN id 
                    END) as total_adendos_id,
                    COUNT(DISTINCT CASE 
                        WHEN lastEventsUpdate IS NOT NULL 
                        AND lastEventsUpdate != ''
                        AND is_menor = 0
                        AND idfamilia IS NOT NULL 
                        AND TRIM(idfamilia) != ''
                        THEN idfamilia 
                    END) as total_adendos_familia
                FROM whatsapp_euna_data.euna_familias
                WHERE isSpecial = 0 
                AND hasTechnicalProblems = 0
            ),
            FamiliaDetalhes AS (
                SELECT 
                    e.idfamilia AS ID_Familia,
                    COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
                    SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
                    SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
                    SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
                    SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
                    SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
                    SUM(CASE WHEN e.paymentOption = 'F' THEN 1 ELSE 0 END) AS F,
                    SUM(CASE WHEN e.paymentOption = 'Y' THEN 1 ELSE 0 END) AS Y,
                    SUM(CASE WHEN e.specialConditionFamily = 1 THEN 1 ELSE 0 END) AS Condicao_Especial,
                    SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F','Y') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
                    SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
                    SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
                    COUNT(DISTINCT e.id) AS Requerentes_Preencheram,
                    (SELECT COUNT(DISTINCT unique_id) 
                     FROM whatsapp_euna_data.familiares f2 
                     WHERE f2.familia = e.idfamilia 
                     AND f2.is_conjuge = 0 
                     AND f2.is_italiano = 0
                     AND f2.is_menor = 0) AS Requerentes_Maiores,
                    (SELECT COUNT(DISTINCT unique_id) 
                     FROM whatsapp_euna_data.familiares f2 
                     WHERE f2.familia = e.idfamilia 
                     AND f2.is_menor = 1) AS Requerentes_Menores,
                    (SELECT COUNT(DISTINCT unique_id) 
                     FROM whatsapp_euna_data.familiares f2 
                     WHERE f2.familia = e.idfamilia) AS Total_Banco
                FROM whatsapp_euna_data.euna_familias e
                LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
                WHERE e.is_menor = 0 
                AND e.isSpecial = 0 
                AND e.hasTechnicalProblems = 0
                GROUP BY e.idfamilia, f.nome_familia
            ),
            TotalGeral AS (
                SELECT 
                    'TOTAL' AS ID_Familia,
                    'Total' AS Nome_Familia,
                    SUM(A) AS A,
                    SUM(B) AS B,
                    SUM(C) AS C,
                    SUM(D) AS D,
                    SUM(E) AS E,
                    SUM(F) AS F,
                    SUM(Y) AS Y,
                    SUM(Condicao_Especial) AS Condicao_Especial,
                    SUM(Requerentes_Continuar) AS Requerentes_Continuar,
                    SUM(Requerentes_Cancelar) AS Requerentes_Cancelar,
                    SUM(Sem_Opcao) AS Sem_Opcao,
                    SUM(Requerentes_Preencheram) AS Requerentes_Preencheram,
                    SUM(Requerentes_Maiores) AS Requerentes_Maiores,
                    SUM(Requerentes_Menores) AS Requerentes_Menores,
                    SUM(Total_Banco) AS Total_Banco,
                    (SELECT total_adendos_id FROM AdendoMetrics) AS Total_Adendos_ID,
                    (SELECT total_adendos_familia FROM AdendoMetrics) AS Total_Adendos_Familia
                FROM FamiliaDetalhes
            )
            SELECT * FROM FamiliaDetalhes
            UNION ALL
            SELECT * FROM TotalGeral
            ORDER BY CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END, Nome_Familia
            """
            
            df = db.execute_query(query)
            return df
        except Exception as e:
            print(f"Erro ao obter status das famílias: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_dados_grafico() -> Optional[pd.DataFrame]:
        """Obtém dados do gráfico com cache"""
        try:
            print("Iniciando get_dados_grafico...")
            query = """
            SELECT 
                DATE(createdAt) as data,
                HOUR(createdAt) as hora,
                COUNT(DISTINCT id) as total_ids
            FROM whatsapp_euna_data.euna_familias
            WHERE (idfamilia IS NOT NULL AND TRIM(idfamilia) <> '')
            AND (is_menor = 0 OR is_menor IS NULL)
            AND (isSpecial = 0 OR isSpecial IS NULL)
            AND (hasTechnicalProblems = 0 OR hasTechnicalProblems IS NULL)
            GROUP BY DATE(createdAt), HOUR(createdAt)
            ORDER BY data, hora
            """
            
            print("Executando query do gráfico...")
            df = db.execute_query(query)
            
            # Garantir que os dados estão no formato correto
            if df is not None and not df.empty:
                print(f"Dados obtidos: {len(df)} registros")
                print("Tipos de dados iniciais:", df.dtypes)
                
                # Converter a coluna 'data' para datetime se for string
                if df['data'].dtype == 'object':
                    print("Convertendo coluna 'data' para datetime")
                    df['data'] = pd.to_datetime(df['data'])
                    print("Tipo após conversão:", df['data'].dtype)
                
                # Verificar valores não finitos em 'hora'
                print("Verificando valores não finitos em 'hora'")
                non_finite_hora = df['hora'].isna().sum()
                if non_finite_hora > 0:
                    print(f"Encontrados {non_finite_hora} valores NA em 'hora'")
                
                # Garantir que 'hora' é um inteiro, tratando valores NA
                print("Convertendo coluna 'hora' para inteiro")
                df['hora'] = df['hora'].fillna(0).astype(int)
                
                # Verificar valores não finitos em 'total_ids'
                print("Verificando valores não finitos em 'total_ids'")
                non_finite_ids = df['total_ids'].isna().sum() + np.isinf(df['total_ids']).sum()
                if non_finite_ids > 0:
                    print(f"Encontrados {non_finite_ids} valores não finitos em 'total_ids'")
                
                # Garantir que 'total_ids' é um inteiro, tratando valores NA e infinitos
                print("Convertendo coluna 'total_ids'")
                df['total_ids'] = df['total_ids'].apply(lambda x: FamiliaService.safe_convert_to_int(x))
                
                print("Tipos de dados finais:", df.dtypes)
            else:
                print("Nenhum dado encontrado para o gráfico")
            
            return df
        except Exception as e:
            print(f"Erro ao obter dados do gráfico: {str(e)}")
            print("Stack trace:", e.__traceback__)
            return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_option_details(option: str) -> pd.DataFrame:
        """Busca detalhes de uma opção de pagamento"""
        try:
            if option == 'Condicao_Especial':
                query = """
                SELECT 
                    e.idfamilia,
                    e.nome_completo,
                    e.telefone,
                    f.nome_familia,
                    e.paymentOption,
                    e.createdAt
                FROM whatsapp_euna_data.euna_familias e
                LEFT JOIN whatsapp_euna_data.familias f 
                    ON TRIM(e.idfamilia) = TRIM(f.unique_id)
                WHERE e.specialConditionFamily = 1
                AND e.is_menor = 0 
                AND e.isSpecial = 0 
                AND e.hasTechnicalProblems = 0
                ORDER BY e.createdAt DESC
                """
                df = db.execute_query(query)
            else:
                query = """
                SELECT 
                    e.idfamilia,
                    e.nome_completo,
                    e.telefone,
                    f.nome_familia,
                    e.paymentOption,
                    e.createdAt
                FROM whatsapp_euna_data.euna_familias e
                LEFT JOIN whatsapp_euna_data.familias f 
                    ON TRIM(e.idfamilia) = TRIM(f.unique_id)
                WHERE e.paymentOption = %s
                AND e.is_menor = 0 
                AND e.isSpecial = 0 
                AND e.hasTechnicalProblems = 0
                ORDER BY e.createdAt DESC
                """
                df = db.execute_query(query, params=[option])
            
            if df is not None and not df.empty:
                # Tratar valores nulos
                df = df.fillna({
                    'idfamilia': 'N/A',
                    'nome_completo': 'N/A',
                    'telefone': 'N/A',
                    'nome_familia': 'N/A',
                    'paymentOption': 'N/A'
                })
                
                # Formatar datas com tratamento de valores nulos
                df['createdAt'] = pd.to_datetime(df['createdAt'], errors='coerce')
                df['createdAt'] = df['createdAt'].fillna(pd.Timestamp.min)
                df['createdAt'] = df['createdAt'].dt.strftime('%d/%m/%Y %H:%M')
                df['createdAt'] = df['createdAt'].replace('01/01/1677 00:00', 'N/A')
            else:
                # Criar DataFrame vazio com as colunas necessárias
                df = pd.DataFrame(columns=[
                    'idfamilia', 'nome_completo', 'telefone', 'nome_familia', 'paymentOption', 'createdAt'
                ])
                
            return df
        except Exception as e:
            print(f"Erro ao obter detalhes da opção {option}: {e}")
            # Retornar DataFrame vazio em caso de erro
            return pd.DataFrame(columns=[
                'idfamilia', 'nome_completo', 'telefone', 'nome_familia', 'paymentOption', 'createdAt'
            ])

    def clear_cache(self):
        """Limpa o cache do serviço"""
        st.cache_data.clear()

# Instância global do serviço
familia_service = FamiliaService()