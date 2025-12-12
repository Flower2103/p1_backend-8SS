"""
🔍 Búsqueda por Zona - Un solo mapa que muestra los resultados
"""

import streamlit as st
import sys
import os
from streamlit_folium import st_folium
import folium

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from api_client import api
from map_generator import MapGenerator

st.set_page_config(
    page_title="Buscar Zona - Simulador BC",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    .recomendacion-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.1rem;
        font-weight: bold;
        text-align: center;
    }
    .buena-oportunidad {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .zona-saturada {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Buscar Zona y Recomendación")
st.markdown("Selecciona una ubicación en el mapa y analiza la densidad de negocios")
st.markdown("---")

# Variables de sesión
if 'latitud_seleccionada' not in st.session_state:
    st.session_state.latitud_seleccionada = 32.5149
if 'longitud_seleccionada' not in st.session_state:
    st.session_state.longitud_seleccionada = -117.0382
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False
if 'datos_analisis' not in st.session_state:
    st.session_state.datos_analisis = None

# ========== PARÁMETROS (ARRIBA DEL MAPA) ==========
st.markdown("## 🎯 Configuración del Análisis")

col1, col2, col3 = st.columns(3)

with col1:
    # Selector de rango
    rango = st.radio("Rango:", ["🔍 Corto (100m - 1km)", "📏 Largo (1-10km)"], horizontal=True)
    
    if rango == "🔍 Corto (100m - 1km)":
        # De 100 en 100 metros
        radio_metros = st.slider("Radio (metros):", 100, 1000, 200, 100)
        radio_km = radio_metros / 1000
        st.info(f"**Radio:** {radio_metros}m ({radio_km:.1f} km)")
    else:
        # De 0.5 en 0.5 km
        radio_km = st.slider("Radio (km):", 1.0, 10.0, 2.0, 0.5)
        st.info(f"**Radio:** {radio_km} km")

with col2:
    st.markdown("### 🏪 Tipo de Negocio")

    # ================== ACTIVIDADES DINÁMICAS ==================
    import requests

    try:
        resp = requests.get("http://localhost:5500/excel/actividades")  # Cambiar host/puerto si es remoto
        if resp.status_code == 200:
            actividades_list = resp.json()
        else:
            actividades_list = []
    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar las actividades: {e}")
        actividades_list = []

    # Crear diccionario id → nombre
    actividades_bd = {a["id_actividad_empresarial"]: a["actividad_texto"] for a in actividades_list}
    nombres = sorted(list(actividades_bd.values()))

    # Container con scroll
    # Container con scroll vertical usando selectbox
    with st.container():
        
        if nombres:
            actividad_nombre = st.selectbox(
                "Selecciona actividad:",
                options=nombres,
                key="select_act"
            )
            id_actividad = [k for k, v in actividades_bd.items() if v == actividad_nombre][0]
        else:
            st.info("No hay actividades disponibles")
            actividad_nombre = None
            id_actividad = None
        
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <style>
        div[data-testid="stRadio"] > div {
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        

with col3:
    st.write("")  # Espaciador
    st.write("")  # Espaciador
    if st.button("🚀 ANALIZAR ZONA", type="primary", use_container_width=True):
        with st.spinner("🔄 Analizando..."):
            rec = api.obtener_recomendacion(
                st.session_state.latitud_seleccionada,
                st.session_state.longitud_seleccionada,
                radio_km,
                id_actividad
            )
            
            negocios = api.obtener_negocios_por_radio(
                st.session_state.latitud_seleccionada,
                st.session_state.longitud_seleccionada,
                radio_km
            )
            
            similares = [n for n in negocios if n.get('id_actividad_empresarial') == id_actividad] if negocios else []
            
            # GUARDAR en sesión
            st.session_state.datos_analisis = {
                'recomendacion': rec,
                'negocios': negocios,
                'similares': similares,
                'radio': radio_km,
                'id_actividad': id_actividad
            }
            st.session_state.mostrar_resultados = True
            st.rerun()

st.markdown("---")

# ========== RESULTADOS (SI EXISTEN) ==========
if st.session_state.mostrar_resultados and st.session_state.datos_analisis:
    datos = st.session_state.datos_analisis
    rec = datos['recomendacion']
    
    if rec:
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("🏪 Total de Negocios", rec.get('total_en_radio', 0))
        col2.metric("🎯 Competidores Directos", rec.get('similares', 0))
        col3.metric("📊 Densidad/km²", f"{rec.get('similares', 0) / (datos['radio']**2):.2f}")
        
        # Recomendación
        texto = rec.get('recomendacion', '')
        clase = "buena-oportunidad" if "Buena" in texto else "zona-saturada"
        icono = "🎉" if "Buena" in texto else "⚠️"
        st.markdown(f'<div class="recomendacion-box {clase}">{icono} {texto}</div>', unsafe_allow_html=True)
        
        st.markdown("---")

# ========== MAPA (SIEMPRE VISIBLE) ==========
st.markdown("## 🗺️ Mapa Interactivo")

# Determinar qué mapa mostrar
if st.session_state.mostrar_resultados and st.session_state.datos_analisis:
    # Mostrar mapa con RESULTADOS
    datos = st.session_state.datos_analisis
    negocios = datos.get('negocios', [])
    similares = datos.get('similares', [])
    
    if negocios and len(negocios) > 0:
        st.info(f"""
        **Leyenda:**
        - 🔴 **Estrella Roja:** Tu ubicación
        - 🟠 **Naranjas:** Competidores directos ({len(similares)})
        - 🟢 **Verdes:** Otros negocios
        - 🔵 **Círculo:** Radio de búsqueda ({datos['radio']} km)
        
        **Total en mapa:** {len(negocios)} negocios
        """)
        
        # Crear mapa con resultados
        mapa = MapGenerator.crear_mapa_recomendacion(
            st.session_state.latitud_seleccionada,
            st.session_state.longitud_seleccionada,
            datos['radio'],
            negocios,
            similares
        )
    else:
        # Si no hay negocios, mostrar mapa vacío con mensaje
        st.warning("⚠️ No se encontraron negocios en esta zona")
        mapa = folium.Map(
            location=[st.session_state.latitud_seleccionada, st.session_state.longitud_seleccionada],
            zoom_start=13,
            tiles="OpenStreetMap"
        )
        folium.Marker(
            location=[st.session_state.latitud_seleccionada, st.session_state.longitud_seleccionada],
            popup="📍 Tu ubicación",
            icon=folium.Icon(color="red", icon="star")
        ).add_to(mapa)

else:
    # Mostrar mapa de SELECCIÓN (antes de analizar)
    st.info("👆 Haz **click en el mapa** para cambiar la ubicación, luego configura los parámetros arriba y presiona **ANALIZAR**")
    
    mapa = folium.Map(
        location=[st.session_state.latitud_seleccionada, st.session_state.longitud_seleccionada],
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    folium.Marker(
        location=[st.session_state.latitud_seleccionada, st.session_state.longitud_seleccionada],
        popup="📍 Ubicación seleccionada",
        tooltip="Tu ubicación",
        icon=folium.Icon(color="red", icon="star")
    ).add_to(mapa)
    
    # Plugin para detectar clicks
    mapa.add_child(folium.LatLngPopup())

# Mostrar el mapa (sin key para que persista)
map_data = st_folium(mapa, width=1200, height=600)

# Actualizar coordenadas si hubo click (solo en modo selección)
if not st.session_state.mostrar_resultados:
    if map_data and map_data.get('last_clicked'):
        nueva_lat = map_data['last_clicked']['lat']
        nueva_lon = map_data['last_clicked']['lng']
        
        if (abs(nueva_lat - st.session_state.latitud_seleccionada) > 0.0001 or 
            abs(nueva_lon - st.session_state.longitud_seleccionada) > 0.0001):
            
            st.session_state.latitud_seleccionada = nueva_lat
            st.session_state.longitud_seleccionada = nueva_lon
            st.success(f"✅ Nueva ubicación: {nueva_lat:.6f}, {nueva_lon:.6f}")
            st.rerun()

# Mostrar coordenadas actuales
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.metric("📍 Latitud", f"{st.session_state.latitud_seleccionada:.6f}")
with col2:
    st.metric("📍 Longitud", f"{st.session_state.longitud_seleccionada:.6f}")
with col3:
    if st.session_state.mostrar_resultados:
        if st.button("🔄 Nueva Búsqueda", use_container_width=True):
            st.session_state.mostrar_resultados = False
            st.session_state.datos_analisis = None
            st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center;color:#666;">🔍 Simulador de Negocios - Baja California</div>', unsafe_allow_html=True)