import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go

# --- 1. CEREBRO DEL MODELO (LÓGICA INTERNA PRO) ---

PESOS = {
    'RIESGO_PATRIMONIAL_CALCULADO': 0.25,
    'COMPRAS_PRIVADAS_SCORE': 0.15,
    'DENUNCIAS_SCORE': 0.15,
    'N_PROCESOS_JUDICIAL': 0.10,
    'RIESGO_ETICO_SCORE': 0.10,
    'TRANSFUGUISMO': 0.10,
    'PRENSA_NEGATIVA_SCORE': 0.08,
    'PERIODOS_EN_PODER': 0.05,
    'PROCESOS_ELECTORAL_SCORE': 0.02
}

# Variables que activan el riesgo máximo silenciosamente
VARIABLES_CRITICAS = ['RIESGO_PATRIMONIAL_CALCULADO', 'COMPRAS_PRIVADAS_SCORE', 'DENUNCIAS_SCORE', 'RIESGO_ETICO_SCORE']
UMBRAL_VETO = 85

REQUIRED_FINANCIAL_COLS = ['INGRESOS_TOTAL', 'PATRIMONIO_TOTAL']

def calcular_riesgo_corrupcion(df):
    if df.empty: return 0, df

    # 1. Análisis Financiero Estricto (Backend)
    if all(col in df.columns for col in REQUIRED_FINANCIAL_COLS):
        df['RATIO'] = np.where(df['INGRESOS_TOTAL'] > 0, df['PATRIMONIO_TOTAL'] / df['INGRESOS_TOTAL'], 0)
        # Penalización exponencial interna
        df['RIESGO_PATRIMONIAL_CALCULADO'] = df['RATIO'].apply(
            lambda x: 100 if x >= 10 else (90 if x >= 5 else (75 if x >= 3 else (50 if x >= 1.5 else 10)))
        )
    else:
        df['RIESGO_PATRIMONIAL_CALCULADO'] = 0 
    
    # 2. Detección de Veto (Backend)
    veto_activado = False
    for var in VARIABLES_CRITICAS:
        if var in df.columns and df[var].iloc[0] >= UMBRAL_VETO:
            veto_activado = True
            break 

    # 3. Cálculo del Score
    if veto_activado:
        # Si hay veto, forzamos 100% pero calculamos los parciales para el gráfico
        riesgo_final = 100.00
        df['SCORE_FINAL_INTERNAL'] = 0
        for variable, peso in PESOS.items():
            if variable in df.columns or variable == 'RIESGO_PATRIMONIAL_CALCULADO':
                df['SCORE_FINAL_INTERNAL'] += df[variable] * peso
    else:
        df['SCORE_FINAL'] = 0
        for variable, peso in PESOS.items():
            if variable in df.columns or variable == 'RIESGO_PATRIMONIAL_CALCULADO':
                df['SCORE_FINAL'] += df[variable] * peso
        riesgo_final = round(df['SCORE_FINAL'].mean(), 2)

    return riesgo_final, df

def crear_grafico_radial(df_scores):
    categories = list(PESOS.keys())
    categories_clean = [c.replace('_SCORE', '').replace('_', ' ').title().replace('Calculado', '(Calc)') for c in categories]
    values = df_scores[categories].iloc[0].tolist()
    values += values[:1]
    categories_clean += categories_clean[:1]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories_clean, fill='toself', name='Puntaje', line_color='red', opacity=0.7
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title={'text': "Perfil de Riesgo (0-100)", 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
        height=450, margin=dict(l=60, r=60, t=80, b=60)
    )
    return fig

# --- 2. INTERFAZ VISUAL (DISEÑO ANTERIOR) ---

st.set_page_config(page_title="SERC - Análisis de Riesgo", page_icon="🕵️", layout="wide")

st.sidebar.title("🗂️ Panel de Control")
uploaded_file = st.sidebar.file_uploader("Cargar Excel (.xlsx)", type=['xlsx', 'csv'])

# Rúbrica oculta en sidebar por si se necesita consultar, pero discreta
with st.sidebar.expander("📘 Guía de Calificación"):
    st.write("Guía interna de puntajes para llenado de datos.")

if uploaded_file is None:
    # --- PANTALLA DE BIENVENIDA LIMPIA ---
    st.title("🕵️ Sistema de Evaluación de Riesgo de Corrupción (SERC)")
    st.markdown("Herramienta de análisis forense basada en modelo heurístico ponderado.")
    st.warning("⚠️ **AVISO:** Resultados probabilísticos para identificación de anomalías. No constituyen prueba legal.")
    st.write("---")
    col1, col2, col3 = st.columns(3)
    col1.subheader("💰 Financiero"); col1.write("Desbalance patrimonial.")
    col2.subheader("⚖️ Legal"); col2.write("Antecedentes y procesos.")
    col3.subheader("🏛️ Político"); col3.write("Estabilidad y entorno.")
    st.write("---")
    st.info("👈 Cargue su base de datos para comenzar.")

else:
    # --- VISUALIZACIÓN DE RESULTADOS (ESTILO LIMPIO) ---
    try:
        if uploaded_file.name.endswith('.csv'):
            full_data = pd.read_csv(uploaded_file)
        else:
            full_data = pd.read_excel(uploaded_file)
            
        if 'POLÍTICO_ID' in full_data.columns:
            full_data['POLÍTICO_ID'] = full_data['POLÍTICO_ID'].astype(str)
            st.sidebar.success("✅ Datos cargados.")
            
            col_search_1, col_search_2 = st.columns([1, 3])
            with col_search_1:
                lista_ids = full_data['POLÍTICO_ID'].unique()
                selected_id = st.selectbox("ID Funcionario:", options=lista_ids)
            
            politico_data_raw = full_data[full_data['POLÍTICO_ID'] == selected_id].copy()
            
            if not politico_data_raw.empty:
                nombre = politico_data_raw['NOMBRE_COMPLETO'].iloc[0]
                cargo = politico_data_raw['CARGO'].iloc[0]
                
                with col_search_2:
                    st.info(f"👤 **{nombre}** | 🏛️ {cargo}")

                if st.button("🚀 Ejecutar Análisis", type="primary"):
                    
                    with st.spinner(f'Procesando datos de {nombre}...'):
                        time.sleep(0.8)
                        riesgo, df_scores = calcular_riesgo_corrupcion(politico_data_raw)
                    
                    st.write("---")
                    
                    # --- AQUÍ ESTÁ EL DISEÑO LIMPIO QUE PEDISTE ---
                    col_metrics, col_chart = st.columns([2, 3])
                    
                    with col_metrics:
                        # Semáforo simple sin explicar "por qué"
                        if riesgo < 35:
                            nivel, emoji, msg_tipo = "BAJO", "🟢", "success"
                            msg_txt = "Perfil Estable."
                        elif riesgo < 65:
                            nivel, emoji, msg_tipo = "MODERADO", "🟡", "warning"
                            msg_txt = "Precaución: Anomalías detectadas."
                        else:
                            nivel, emoji, msg_tipo = "ALTO", "🔴", "error"
                            msg_txt = "ALERTA CRÍTICA: Perfil de Alto Riesgo."

                        st.metric(label="Índice Global SERC", value=f"{riesgo}%", delta=f"{emoji} {nivel}")
                        
                        if msg_tipo == "success": st.success(msg_txt)
                        elif msg_tipo == "warning": st.warning(msg_txt)
                        else: st.error(msg_txt)

                        st.subheader("Indicadores Clave")
                        cols_clave = ['RIESGO_PATRIMONIAL_CALCULADO', 'COMPRAS_PRIVADAS_SCORE', 'DENUNCIAS_SCORE']
                        cols_existentes = [c for c in cols_clave if c in df_scores.columns]
                        if cols_existentes:
                            st.dataframe(df_scores[cols_existentes].T.rename(columns={df_scores.index[0]: 'Puntaje'}))

                    with col_chart:
                        try:
                            grafico = crear_grafico_radial(df_scores)
                            st.plotly_chart(grafico, use_container_width=True)
                        except Exception as e:
                             st.error(f"Error gráfico: {e}")

                    with st.expander("Ver Data Completa"):
                        cols_to_show = [c for c in PESOS.keys() if c in df_scores.columns]
                        st.dataframe(df_scores[cols_to_show].T.rename(columns={df_scores.index[0]: 'Score'}))
            else:
                st.error("ID no encontrado.")
        else:
            st.error("Error: Falta columna 'POLÍTICO_ID'.")

    except Exception as e:
        st.error(f"Error: {e}")