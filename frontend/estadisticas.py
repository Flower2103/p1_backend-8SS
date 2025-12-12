"""
📊 Página de Estadísticas y Análisis
Muestra gráficas y métricas sobre los negocios en Baja California
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import sys
import os

# Agregar la carpeta utils al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from api_client import api

# ========== CONFIGURACIÓN DE LA PÁGINA ==========
st.set_page_config(
    page_title="Estadísticas - Simulador BC",
    page_icon="📊",
    layout="wide"
)

# ========== HEADER ==========
st.title("📊 Estadísticas y Análisis de Negocios")
st.markdown("Análisis detallado de los negocios registrados en Baja California")
st.markdown("---")

# ========== CARGAR DATOS ==========
@st.cache_data(ttl=3600)
def cargar_datos_completos():
    """Carga todos los datos del mapa para análisis"""
    return api.obtener_datos_mapa()

with st.spinner("🔄 Cargando datos..."):
    datos = cargar_datos_completos()
    
    if not datos:
        st.error("❌ No se pudieron cargar los datos. Verifica que el backend esté funcionando.")
        st.stop()

# Convertir a DataFrame
df = pd.DataFrame(datos)

# ========== MÉTRICAS GENERALES ==========
st.markdown("## 📈 Métricas Generales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_negocios = len(df)
    st.metric(
        label="🏪 Total de Negocios",
        value=f"{total_negocios:,}",
        delta="Registros en BD"
    )

with col2:
    actividades_unicas = df['id_actividad_empresarial'].nunique()
    st.metric(
        label="📋 Tipos de Actividad",
        value=actividades_unicas,
        delta="Categorías"
    )

with col3:
    # Calcular promedio de negocios por coordenada única
    coords_unicas = df[['latitud', 'longitud']].drop_duplicates()
    densidad_promedio = len(df) / len(coords_unicas)
    st.metric(
        label="📍 Densidad Promedio",
        value=f"{densidad_promedio:.1f}",
        delta="Negocios/Ubicación"
    )

with col4:
    # Rango de latitudes (cobertura)
    lat_min = df['latitud'].min()
    lat_max = df['latitud'].max()
    cobertura = lat_max - lat_min
    st.metric(
        label="🗺️ Cobertura Geográfica",
        value=f"{cobertura:.2f}°",
        delta="Latitud"
    )

st.markdown("---")

# ========== SECCIÓN: TOP ACTIVIDADES ==========
st.markdown("## 🏆 Top 10 Actividades Empresariales Más Comunes")

col_filtro1, col_filtro2 = st.columns([3, 1])

with col_filtro1:
    st.markdown("Las actividades empresariales con mayor presencia en Baja California")

with col_filtro2:
    top_n = st.selectbox("Mostrar Top:", [5, 10, 15, 20], index=1)

# Contar actividades
conteo_actividades = df['id_actividad_empresarial'].value_counts().head(top_n)

# Crear gráfica de barras horizontales
fig_actividades = go.Figure()

fig_actividades.add_trace(go.Bar(
    y=[f"Actividad {id}" for id in conteo_actividades.index],
    x=conteo_actividades.values,
    orientation='h',
    marker=dict(
        color=conteo_actividades.values,
        colorscale='Blues',
        showscale=True,
        colorbar=dict(title="Cantidad")
    ),
    text=conteo_actividades.values,
    textposition='auto',
))

fig_actividades.update_layout(
    title=f"Top {top_n} Actividades con Más Negocios",
    xaxis_title="Cantidad de Negocios",
    yaxis_title="Tipo de Actividad",
    height=500,
    showlegend=False,
    hovermode='y unified'
)

st.plotly_chart(fig_actividades, use_container_width=True)

# Tabla de detalles
with st.expander("📋 Ver tabla detallada"):
    df_actividades = pd.DataFrame({
        'ID Actividad': conteo_actividades.index,
        'Cantidad de Negocios': conteo_actividades.values,
        'Porcentaje': [f"{(v/len(df)*100):.2f}%" for v in conteo_actividades.values]
    })
    st.dataframe(df_actividades, use_container_width=True)

st.markdown("---")

# ========== SECCIÓN: DISTRIBUCIÓN GEOGRÁFICA ==========
st.markdown("## 🗺️ Distribución Geográfica")

col_geo1, col_geo2 = st.columns(2)

with col_geo1:
    st.markdown("### 📍 Densidad por Latitud")
    
    # Histograma de latitudes
    fig_lat = px.histogram(
        df,
        x='latitud',
        nbins=50,
        title="Distribución de Negocios por Latitud",
        labels={'latitud': 'Latitud', 'count': 'Cantidad de Negocios'},
        color_discrete_sequence=['#1e5fb8']
    )
    
    fig_lat.update_layout(
        showlegend=False,
        height=400,
        xaxis_title="Latitud",
        yaxis_title="Cantidad de Negocios"
    )
    
    st.plotly_chart(fig_lat, use_container_width=True)
    
    # Estadísticas de latitud
    st.info(f"""
    **📊 Estadísticas de Latitud:**
    - Mínima: {df['latitud'].min():.4f}°
    - Máxima: {df['latitud'].max():.4f}°
    - Promedio: {df['latitud'].mean():.4f}°
    - Mediana: {df['latitud'].median():.4f}°
    """)

with col_geo2:
    st.markdown("### 📍 Densidad por Longitud")
    
    # Histograma de longitudes
    fig_lon = px.histogram(
        df,
        x='longitud',
        nbins=50,
        title="Distribución de Negocios por Longitud",
        labels={'longitud': 'Longitud', 'count': 'Cantidad de Negocios'},
        color_discrete_sequence=['#764ba2']
    )
    
    fig_lon.update_layout(
        showlegend=False,
        height=400,
        xaxis_title="Longitud",
        yaxis_title="Cantidad de Negocios"
    )
    
    st.plotly_chart(fig_lon, use_container_width=True)
    
    # Estadísticas de longitud
    st.info(f"""
    **📊 Estadísticas de Longitud:**
    - Mínima: {df['longitud'].min():.4f}°
    - Máxima: {df['longitud'].max():.4f}°
    - Promedio: {df['longitud'].mean():.4f}°
    - Mediana: {df['longitud'].median():.4f}°
    """)

st.markdown("---")

# ========== SECCIÓN: MAPA DE CALOR 2D ==========
st.markdown("## 🔥 Mapa de Calor de Densidad")

st.markdown("""
Este mapa muestra las zonas con mayor concentración de negocios en Baja California.
Las áreas más rojas/oscuras indican mayor densidad.
""")

# Crear bins para el mapa de calor
lat_bins = 50
lon_bins = 50

# Crear histograma 2D
fig_heatmap = go.Figure(go.Histogram2d(
    x=df['longitud'],
    y=df['latitud'],
    colorscale='Hot',
    nbinsx=lon_bins,
    nbinsy=lat_bins,
    colorbar=dict(title="Negocios")
))

fig_heatmap.update_layout(
    title="Densidad de Negocios en Baja California",
    xaxis_title="Longitud",
    yaxis_title="Latitud",
    height=600,
)

st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# ========== SECCIÓN: ANÁLISIS POR ZONA ==========
st.markdown("## 📊 Análisis por Zonas Geográficas")

# Dividir BC en cuadrantes
lat_medio = df['latitud'].median()
lon_medio = df['longitud'].median()

# Clasificar negocios por cuadrante
def clasificar_cuadrante(row):
    if row['latitud'] >= lat_medio and row['longitud'] >= lon_medio:
        return "Noreste"
    elif row['latitud'] >= lat_medio and row['longitud'] < lon_medio:
        return "Noroeste"
    elif row['latitud'] < lat_medio and row['longitud'] >= lon_medio:
        return "Sureste"
    else:
        return "Suroeste"

df['cuadrante'] = df.apply(clasificar_cuadrante, axis=1)

# Contar por cuadrante
conteo_cuadrantes = df['cuadrante'].value_counts()

col_zona1, col_zona2 = st.columns(2)

with col_zona1:
    # Gráfica de pastel
    fig_pie = px.pie(
        values=conteo_cuadrantes.values,
        names=conteo_cuadrantes.index,
        title="Distribución por Cuadrante",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Negocios: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

with col_zona2:
    # Gráfica de barras
    fig_barras_zona = px.bar(
        x=conteo_cuadrantes.index,
        y=conteo_cuadrantes.values,
        title="Cantidad de Negocios por Zona",
        labels={'x': 'Cuadrante', 'y': 'Cantidad de Negocios'},
        color=conteo_cuadrantes.values,
        color_continuous_scale='Viridis'
    )
    
    fig_barras_zona.update_layout(
        showlegend=False,
        xaxis_title="Cuadrante",
        yaxis_title="Cantidad de Negocios"
    )
    
    st.plotly_chart(fig_barras_zona, use_container_width=True)

# Tabla resumen por cuadrante
st.markdown("### 📋 Resumen por Cuadrante")

df_resumen_cuadrante = pd.DataFrame({
    'Cuadrante': conteo_cuadrantes.index,
    'Cantidad': conteo_cuadrantes.values,
    'Porcentaje': [f"{(v/len(df)*100):.2f}%" for v in conteo_cuadrantes.values],
    'Actividades Únicas': [
        df[df['cuadrante'] == cuad]['id_actividad_empresarial'].nunique() 
        for cuad in conteo_cuadrantes.index
    ]
})

st.dataframe(df_resumen_cuadrante, use_container_width=True)

st.markdown("---")

# ========== SECCIÓN: ANÁLISIS DE CONCENTRACIÓN ==========
st.markdown("## 🎯 Análisis de Concentración por Actividad")

st.markdown("""
Selecciona una actividad para ver su distribución geográfica específica.
""")

# Selector de actividad
actividades_disponibles = sorted(df['id_actividad_empresarial'].unique())
actividad_seleccionada = st.selectbox(
    "Selecciona una actividad empresarial:",
    actividades_disponibles,
    format_func=lambda x: f"Actividad ID: {x}"
)

# Filtrar por actividad
df_actividad = df[df['id_actividad_empresarial'] == actividad_seleccionada]

col_conc1, col_conc2, col_conc3 = st.columns(3)

with col_conc1:
    st.metric(
        "🏪 Negocios de este tipo",
        f"{len(df_actividad):,}"
    )

with col_conc2:
    porcentaje = (len(df_actividad) / len(df)) * 100
    st.metric(
        "📊 Porcentaje del total",
        f"{porcentaje:.2f}%"
    )

with col_conc3:
    # Calcular dispersión (desviación estándar de coordenadas)
    dispersion = (df_actividad['latitud'].std() + df_actividad['longitud'].std()) / 2
    st.metric(
        "📍 Dispersión Geográfica",
        f"{dispersion:.4f}°"
    )

# Scatter plot de la actividad seleccionada
fig_scatter = px.scatter(
    df_actividad,
    x='longitud',
    y='latitud',
    title=f"Ubicación de Negocios - Actividad {actividad_seleccionada}",
    labels={'longitud': 'Longitud', 'latitud': 'Latitud'},
    opacity=0.6,
    color_discrete_sequence=['#ff6b6b']
)

fig_scatter.update_traces(
    marker=dict(size=8, line=dict(width=1, color='white'))
)

fig_scatter.update_layout(
    height=500,
    hovermode='closest',
    xaxis_title="Longitud",
    yaxis_title="Latitud"
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ========== SECCIÓN: COMPARACIÓN ENTRE ACTIVIDADES ==========
st.markdown("## 📊 Comparación entre Actividades")

st.markdown("Compara la distribución de dos tipos de negocios diferentes")

col_comp1, col_comp2 = st.columns(2)

with col_comp1:
    actividad_1 = st.selectbox(
        "Primera actividad:",
        actividades_disponibles,
        format_func=lambda x: f"Actividad {x}",
        key="act1"
    )

with col_comp2:
    actividad_2 = st.selectbox(
        "Segunda actividad:",
        actividades_disponibles,
        format_func=lambda x: f"Actividad {x}",
        index=1 if len(actividades_disponibles) > 1 else 0,
        key="act2"
    )

if actividad_1 != actividad_2:
    # Filtrar datos
    df_act1 = df[df['id_actividad_empresarial'] == actividad_1]
    df_act2 = df[df['id_actividad_empresarial'] == actividad_2]
    
    # Crear gráfica comparativa
    fig_comparacion = go.Figure()
    
    fig_comparacion.add_trace(go.Scatter(
        x=df_act1['longitud'],
        y=df_act1['latitud'],
        mode='markers',
        name=f'Actividad {actividad_1}',
        marker=dict(size=6, color='blue', opacity=0.5)
    ))
    
    fig_comparacion.add_trace(go.Scatter(
        x=df_act2['longitud'],
        y=df_act2['latitud'],
        mode='markers',
        name=f'Actividad {actividad_2}',
        marker=dict(size=6, color='red', opacity=0.5)
    ))
    
    fig_comparacion.update_layout(
        title="Comparación de Ubicaciones",
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        height=500,
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_comparacion, use_container_width=True)
    
    # Tabla comparativa
    col_tabla1, col_tabla2 = st.columns(2)
    
    with col_tabla1:
        st.markdown(f"### 🔵 Actividad {actividad_1}")
        st.write(f"**Total:** {len(df_act1):,} negocios")
        st.write(f"**Porcentaje:** {(len(df_act1)/len(df)*100):.2f}%")
        st.write(f"**Lat. promedio:** {df_act1['latitud'].mean():.4f}°")
        st.write(f"**Lon. promedio:** {df_act1['longitud'].mean():.4f}°")
    
    with col_tabla2:
        st.markdown(f"### 🔴 Actividad {actividad_2}")
        st.write(f"**Total:** {len(df_act2):,} negocios")
        st.write(f"**Porcentaje:** {(len(df_act2)/len(df)*100):.2f}%")
        st.write(f"**Lat. promedio:** {df_act2['latitud'].mean():.4f}°")
        st.write(f"**Lon. promedio:** {df_act2['longitud'].mean():.4f}°")

else:
    st.warning("⚠️ Selecciona dos actividades diferentes para comparar")

st.markdown("---")

# ========== SECCIÓN: INSIGHTS Y CONCLUSIONES ==========
st.markdown("## 💡 Insights y Recomendaciones")

# Calcular insights automáticos
actividad_mas_comun = conteo_actividades.index[0]
cantidad_mas_comun = conteo_actividades.values[0]

cuadrante_mas_denso = conteo_cuadrantes.index[0]
cantidad_cuadrante = conteo_cuadrantes.values[0]

col_insight1, col_insight2 = st.columns(2)

with col_insight1:
    st.success(f"""
    ### 🏆 Actividad Dominante
    
    La actividad empresarial **#{actividad_mas_comun}** es la más común con 
    **{cantidad_mas_comun:,} negocios** ({(cantidad_mas_comun/len(df)*100):.1f}% del total).
    
    **Recomendación:** Esta actividad está saturada en BC. Considera nichos especializados 
    o ubicaciones menos competidas.
    """)

with col_insight2:
    st.info(f"""
    ### 📍 Zona con Mayor Densidad
    
    El cuadrante **{cuadrante_mas_denso}** tiene la mayor concentración con 
    **{cantidad_cuadrante:,} negocios** ({(cantidad_cuadrante/len(df)*100):.1f}% del total).
    
    **Recomendación:** Si buscas alto tráfico, esta zona es ideal. Si buscas 
    menos competencia, considera otras zonas.
    """)

# Actividades menos comunes (oportunidades)
actividades_menos_comunes = conteo_actividades.tail(5)

st.warning(f"""
### 🎯 Oportunidades Potenciales

Las siguientes actividades tienen **menos competencia** en BC:

{chr(10).join([f"- Actividad #{id}: {count} negocios" for id, count in actividades_menos_comunes.items()])}

**Recomendación:** Estas actividades podrían representar nichos con menor saturación, 
pero verifica la demanda antes de invertir.
""")

st.markdown("---")

# ========== FOOTER ==========
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>📊 Análisis estadístico basado en {count:,} registros de INEGI</p>
    <p style="font-size: 0.9rem;">Los datos son históricos y no garantizan resultados futuros</p>
</div>
""".format(count=len(df)), unsafe_allow_html=True)