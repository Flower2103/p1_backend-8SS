"""
🏪 Simulador de Apertura de Negocios - Baja California
Página Principal (Home)
"""

import streamlit as st
import sys
import os

# Agregar la carpeta utils al path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from api_client import api

# ========== CONFIGURACIÓN DE LA PÁGINA ==========
st.set_page_config(
    page_title="Simulador de Negocios BC",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTILOS CUSTOM ==========
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1e5fb8;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .feature-box {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown('<h1 class="main-header">🏪 Simulador de Apertura de Negocios</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Estado de Baja California</p>', unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🏪 Simulador BC")
    st.markdown("---")
    st.markdown("### 📍 Navegación")
    st.info("""
    **Usa el menú superior** para acceder a:
    - 🔍 Buscar Zona
    """)
    
    st.markdown("---")
    st.markdown("### 🔧 Estado del Sistema")
    
    # Health check del backend
    with st.spinner("Verificando conexión..."):
        health = api.health_check()
        if health:
            st.success("✅ Backend conectado")
        else:
            st.error("❌ Backend no disponible")
            st.warning("Asegúrate de que Flask esté corriendo en el puerto 5500")

# ========== DESCRIPCIÓN DEL PROYECTO ==========
st.markdown("---")
st.markdown("## 🎯 ¿Qué es este sistema?")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    Este simulador te ayuda a **tomar decisiones informadas** sobre dónde abrir tu negocio
    en Baja California. 
    
    **Utilizamos datos históricos de INEGI** para analizar:
    - 📊 Densidad de negocios por zona
    - 🏪 Competencia directa en tu sector
    - 📍 Ubicaciones estratégicas
    - 🎯 Recomendaciones basadas en datos reales
    """)

with col2:
    st.markdown("""
    ### ✨ Características principales:
    
    - ✅ Análisis de ~138,000 negocios registrados
    - ✅ Búsqueda por ubicación y radio
    - ✅ Filtros por tipo de actividad empresarial
    - ✅ Mapas interactivos con visualización
    - ✅ Recomendaciones en tiempo real
    - ✅ Sin necesidad de modelos complejos de IA
    """)

# ========== ESTADÍSTICAS RÁPIDAS ==========
st.markdown("---")
st.markdown("## 📊 Datos del Sistema")

# Intentar obtener estadísticas básicas
try:
    with st.spinner("Cargando estadísticas..."):
        # Obtener datos del mapa (más ligero que todos los negocios)
        datos_mapa = api.obtener_datos_mapa()
        
        if datos_mapa:
            total_negocios = len(datos_mapa)
            
            # Crear métricas visuales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🏪 Total de Negocios</div>
                    <div class="metric-number">{total_negocios:,}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Calcular tipos únicos de actividades
                actividades_unicas = len(set(n.get('id_actividad_empresarial', 0) for n in datos_mapa))
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <div class="metric-label">📋 Tipos de Actividad</div>
                    <div class="metric-number">{actividades_unicas}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <div class="metric-label">🗺️ Estado</div>
                    <div class="metric-number">BC</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No se pudieron cargar las estadísticas. Verifica la conexión con el backend.")
            
except Exception as e:
    st.error(f"❌ Error al cargar estadísticas: {e}")

# ========== CÓMO USAR EL SISTEMA ==========
st.markdown("---")
st.markdown("## 🚀 ¿Cómo usar el simulador?")

# Solo una pestaña
tab1 = st.tabs(["🔍 Buscar Zona"])

with tab1[0]:
    st.markdown("""
    ### Paso a paso:
    
    1. **Selecciona una ubicación:**
       - Ingresa coordenadas manualmente (latitud/longitud)
       - O busca un negocio existente como referencia
    
    2. **Define el radio de búsqueda:**
       - Usa el slider para seleccionar de 0.5 km hasta 10 km
       - El sistema buscará todos los negocios dentro de ese radio
    
    3. **Elige el tipo de negocio:**
       - Selecciona la actividad empresarial que planeas abrir
       - Por ejemplo: Restaurante, Tienda de abarrotes, Farmacia, etc.
    
    4. **Obtén tu recomendación:**
       - El sistema analizará la densidad de competidores
       - Verás cuántos negocios similares existen en la zona
       - Recibirás una recomendación: **"Buena oportunidad"** o **"Zona saturada"**
    
    5. **Visualiza en el mapa:**
       - Mapa interactivo con todos los negocios
       - Competidores directos marcados en naranja
       - Otros negocios en verde
    """)
    
    st.info("💡 **Tip:** Comienza con un radio de 2-3 km para una zona urbana típica.")

# ========== CONSIDERACIONES ==========
st.markdown("---")
st.markdown("## ⚠️ Consideraciones Importantes")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### ✅ Lo que SÍ hace el sistema:
    
    - Analiza densidad de negocios existentes
    - Identifica zonas con alta/baja competencia
    - Visualiza ubicaciones en mapas
    - Ofrece recomendaciones basadas en datos históricos
    - Filtra por tipo de actividad
    """)

with col2:
    st.markdown("""
    ### ❌ Lo que NO hace el sistema:
    
    - No predice ventas futuras con IA
    - No considera factores económicos externos
    - No analiza flujo de personas o tráfico
    - No incluye datos de renta o costos
    - No garantiza el éxito del negocio
    """)

st.info("""
**📌 Nota importante:** Este simulador es una **herramienta de apoyo** para la toma de decisiones. 
Los resultados deben complementarse con análisis adicionales como: estudio de mercado, análisis financiero, 
evaluación de la ubicación física, y consulta con expertos en el sector.
""")

# ========== TECNOLOGÍA ==========
st.markdown("---")
st.markdown("## 🛠️ Tecnología Utilizada")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### Backend
    - 🐍 Python 3.10+
    - 🌶️ Flask
    - 🐼 Pandas
    """)

with col2:
    st.markdown("""
    ### Frontend
    - ⚡ Streamlit
    - 🗺️ Folium
    - 📊 Plotly
    """)

with col3:
    st.markdown("""
    ### Datos
    - 📂 Excel (INEGI)
    - 📍 ~138k registros
    - 🗓️ Datos históricos
    """)

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>Desarrollado con 🐍 Python y ☕ para el análisis de negocios en Baja California</p>
    <p style="font-size: 0.9rem;">Datos proporcionados por INEGI • Sistema educativo sin fines de lucro</p>
</div>
""", unsafe_allow_html=True)