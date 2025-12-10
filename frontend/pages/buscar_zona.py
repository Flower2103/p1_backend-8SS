"""
🔍 Página de Búsqueda por Zona y Recomendación
Permite buscar negocios en un radio y obtener recomendaciones de apertura
"""

import streamlit as st
import sys
import os
from streamlit_folium import st_folium
import folium

# Agregar la carpeta utils al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from api_client import api
from map_generator import MapGenerator

# ========== CONFIGURACIÓN DE LA PÁGINA ==========
st.set_page_config(
    page_title="Buscar Zona - Simulador BC",
    page_icon="🔍",
    layout="wide"
)

# ========== ESTILOS CUSTOM ==========
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

# ========== HEADER ==========
st.title("🔍 Buscar Zona y Recomendación")
st.markdown("Selecciona una ubicación en el mapa y analiza la densidad de negocios")
st.markdown("---")

# ========== VARIABLES DE SESIÓN ==========
if 'latitud_seleccionada' not in st.session_state:
    st.session_state.latitud_seleccionada = 32.5149
if 'longitud_seleccionada' not in st.session_state:
    st.session_state.longitud_seleccionada = -117.0382

# ========== SIDEBAR: CONFIGURACIÓN ==========
with st.sidebar:
    st.markdown("### ⚙️ Configuración de Búsqueda")
    
    # Método de selección de ubicación
    metodo = st.radio(
        "¿Cómo deseas buscar la ubicación?",
        ["🗺️ Seleccionar en el Mapa", "📍 Coordenadas Manuales", "🔍 Buscar por Nombre"],
        key="metodo_ubicacion"
    )
    
    st.markdown("---")

# ========== SECCIÓN: SELECCIÓN DE UBICACIÓN ==========
st.markdown("## 📍 Paso 1: Selecciona la Ubicación")

if metodo == "🗺️ Seleccionar en el Mapa":
    st.info("👆 Haz **click en el mapa** para seleccionar la ubicación de tu negocio")
    
    # Crear mapa interactivo
    mapa_seleccion = folium.Map(
        location=[st.session_state.latitud_seleccionada, st.session_state.longitud_seleccionada],
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    # Agregar marcador actual
    folium.Marker(
        location=[st.session_state.latitud_seleccionada, st.session_state.longitud_seleccionada],
        popup="📍 Ubicación seleccionada",
        tooltip="Tu ubicación",
        icon=folium.Icon(color="red", icon="star")
    ).add_to(mapa_seleccion)
    
    # Agregar plugin para detectar clicks
    mapa_seleccion.add_child(folium.LatLngPopup())
    
    # Mostrar mapa y capturar clicks
    map_data = st_folium(
        mapa_seleccion,
        width=1200,
        height=500,
        key="mapa_seleccion"
    )
    
    # Actualizar coordenadas cuando se hace click
    if map_data and map_data.get('last_clicked'):
        lat_click = map_data['last_clicked']['lat']
        lon_click = map_data['last_clicked']['lng']
        
        # Solo actualizar si cambió la ubicación
        if (abs(lat_click - st.session_state.latitud_seleccionada) > 0.0001 or 
            abs(lon_click - st.session_state.longitud_seleccionada) > 0.0001):
            
            st.session_state.latitud_seleccionada = lat_click
            st.session_state.longitud_seleccionada = lon_click
            
            st.success(f"✅ **Nueva ubicación seleccionada:** {lat_click:.6f}, {lon_click:.6f}")
        
    # Mostrar coordenadas actuales
    col_coord1, col_coord2 = st.columns(2)
    with col_coord1:
        st.metric("📍 Latitud", f"{st.session_state.latitud_seleccionada:.6f}")
    with col_coord2:
        st.metric("📍 Longitud", f"{st.session_state.longitud_seleccionada:.6f}")

elif metodo == "📍 Coordenadas Manuales":
    col1, col2 = st.columns(2)
    
    with col1:
        latitud = st.number_input(
            "Latitud:",
            value=st.session_state.latitud_seleccionada,
            format="%.6f",
            step=0.0001,
            key="lat_manual"
        )
    
    with col2:
        longitud = st.number_input(
            "Longitud:",
            value=st.session_state.longitud_seleccionada,
            format="%.6f",
            step=0.0001,
            key="lon_manual"
        )
    
    st.session_state.latitud_seleccionada = latitud
    st.session_state.longitud_seleccionada = longitud
    
    st.info(f"📍 Ubicación seleccionada: **{latitud:.6f}, {longitud:.6f}**")

else:  # Buscar por nombre
    st.markdown("### 🔍 Búsqueda Predictiva")
    
    nombre_busqueda = st.text_input(
        "Escribe el nombre del negocio (mínimo 3 caracteres):",
        placeholder="Ej: Oxxo, Soriana, Farmacia...",
        key="buscar_nombre"
    )
    
    if len(nombre_busqueda) >= 3:
        with st.spinner("Buscando..."):
            resultados = api.buscar_por_nombre(nombre_busqueda)
            
            if resultados and len(resultados) > 0:
                st.success(f"✅ Se encontraron {len(resultados)} resultados")
                
                opciones = {
                    f"{r.get('nombre_comercial', 'Sin nombre')} (ID: {r.get('id_registro', 'N/A')})": r
                    for r in resultados
                }
                
                seleccion = st.selectbox(
                    "Selecciona un negocio:",
                    options=list(opciones.keys()),
                    key="select_negocio"
                )
                
                if seleccion:
                    negocio_seleccionado = opciones[seleccion]
                    id_negocio = negocio_seleccionado.get('id_registro')
                    
                    with st.spinner("Cargando detalles..."):
                        detalle = api.obtener_negocio_por_id(id_negocio)
                        
                        if detalle:
                            lat = float(detalle.get('latitud', 0))
                            lon = float(detalle.get('longitud', 0))
                            
                            st.session_state.latitud_seleccionada = lat
                            st.session_state.longitud_seleccionada = lon
                            
                            st.success(f"""
                            ✅ **Negocio seleccionado:**
                            - **Nombre:** {detalle.get('nombre_comercial', 'N/A')}
                            - **Actividad:** {detalle.get('actividad_texto', 'N/A')}
                            - **Coordenadas:** {lat:.6f}, {lon:.6f}
                            """)
            else:
                st.warning("⚠️ No se encontraron resultados")
    elif len(nombre_busqueda) > 0:
        st.info("ℹ️ Escribe al menos 3 caracteres para buscar")

st.markdown("---")

# ========== SECCIÓN: PARÁMETROS DE BÚSQUEDA ==========
st.markdown("## 🎯 Paso 2: Define los Parámetros")

col_param1, col_param2 = st.columns(2)

with col_param1:
    st.markdown("### 📏 Radio de Búsqueda")
    radio_km = st.slider(
        "Selecciona el radio en kilómetros:",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        format="%.1f km",
        key="radio_slider"
    )
    
    st.info(f"""
    **Radio seleccionado:** {radio_km} km
    
    💡 **Recomendaciones:**
    - **0.5-2 km:** Zona muy local (colonia)
    - **2-5 km:** Zona urbana amplia
    - **5-10 km:** Región extensa
    """)

with col_param2:
    st.markdown("### 🏪 Tipo de Negocio")
    
    actividades_ejemplo = {
        "6111 - Restaurantes": 6111,
        "4621 - Tienda de Abarrotes": 4621,
        "4641 - Farmacia": 4641,
        "8121 - Salón de Belleza": 8121,
        "7211 - Hotel": 7211,
        "4661 - Ferretería": 4661,
        "Otro (Ingresar ID manualmente)": -1
    }
    
    tipo_seleccionado = st.selectbox(
        "Selecciona el tipo de negocio que deseas abrir:",
        options=list(actividades_ejemplo.keys()),
        key="tipo_negocio"
    )
    
    if actividades_ejemplo[tipo_seleccionado] == -1:
        id_actividad = st.number_input(
            "Ingresa el ID de actividad empresarial:",
            min_value=1,
            value=6111,
            step=1,
            key="id_actividad_manual"
        )
    else:
        id_actividad = actividades_ejemplo[tipo_seleccionado]
    
    st.info(f"**ID de actividad seleccionado:** {id_actividad}")

st.markdown("---")

# ========== BOTÓN DE ANÁLISIS ==========
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    boton_analizar = st.button(
        "🚀 ANALIZAR ZONA Y OBTENER RECOMENDACIÓN",
        type="primary",
        use_container_width=True
    )

# ========== ANÁLISIS Y RESULTADOS ==========
if boton_analizar:
    st.markdown("---")
    st.markdown("## 📊 Resultados del Análisis")
    
    with st.spinner("🔄 Analizando zona..."):
        # Obtener recomendación
        recomendacion = api.obtener_recomendacion(
            st.session_state.latitud_seleccionada,
            st.session_state.longitud_seleccionada,
            radio_km,
            id_actividad
        )
        
        # Obtener negocios del radio
        negocios_radio = api.obtener_negocios_por_radio(
            st.session_state.latitud_seleccionada,
            st.session_state.longitud_seleccionada,
            radio_km
        )
        
        # Filtrar similares
        negocios_similares = [
            n for n in negocios_radio 
            if n.get('id_actividad_empresarial') == id_actividad
        ] if negocios_radio else []
    
    if recomendacion:
        # Métricas
        col_met1, col_met2, col_met3 = st.columns(3)
        
        with col_met1:
            st.metric(
                label="🏪 Total de Negocios",
                value=recomendacion.get('total_en_radio', 0)
            )
        
        with col_met2:
            similares = recomendacion.get('similares', 0)
            st.metric(
                label="🎯 Competidores Directos",
                value=similares,
                delta=f"{similares} del mismo tipo",
                delta_color="inverse"
            )
        
        with col_met3:
            densidad = (similares / radio_km**2) if radio_km > 0 else 0
            st.metric(
                label="📊 Densidad",
                value=f"{densidad:.2f}",
                help="Competidores por km²"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recomendación
        recomendacion_texto = recomendacion.get('recomendacion', 'Sin datos')
        
        if "Buena oportunidad" in recomendacion_texto:
            st.markdown(f"""
            <div class="recomendacion-box buena-oportunidad">
                🎉 {recomendacion_texto}
                <br><br>
                ✅ Esta zona tiene baja densidad de competidores directos.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="recomendacion-box zona-saturada">
                ⚠️ {recomendacion_texto}
                <br><br>
                🔴 Esta zona tiene alta densidad de competidores.
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Mapa interactivo
        st.markdown("## 🗺️ Visualización en Mapa")
        
        if negocios_radio:
            st.info(f"""
            **Leyenda:**
            - 🔴 **Estrella Roja:** Tu ubicación propuesta
            - 🟠 **Marcadores Naranjas:** Competidores directos ({similares})
            - 🟢 **Marcadores Verdes:** Otros tipos de negocios
            - 🔵 **Círculo Azul:** Radio de búsqueda ({radio_km} km)
            """)
            
            mapa = MapGenerator.crear_mapa_recomendacion(
                st.session_state.latitud_seleccionada,
                st.session_state.longitud_seleccionada,
                radio_km,
                negocios_radio,
                negocios_similares
            )
            
            st_folium(mapa, width=1200, height=600)
        else:
            st.warning("⚠️ No se encontraron negocios en esta zona")
    else:
        st.error("❌ No se pudo obtener la recomendación.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem 0;">
    <p>🔍 Análisis de densidad de negocios en Baja California</p>
</div>
""", unsafe_allow_html=True)