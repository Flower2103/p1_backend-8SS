"""
Generador de mapas interactivos con Folium.
Versión mejorada con mejor manejo de errores y validaciones.
"""

import folium
from folium.plugins import MarkerCluster
import streamlit as st


class MapGenerator:
    """Clase para generar mapas interactivos de negocios"""
    
    # Coordenadas del centro de Baja California
    BC_CENTER = [30.8406, -115.2838]
    
    @staticmethod
    def crear_mapa_base(center=None, zoom_start=10):
        """
        Crea un mapa base de Folium.
        
        Args:
            center (list): [lat, lon] del centro del mapa
            zoom_start (int): Nivel de zoom inicial
            
        Returns:
            folium.Map: Mapa base
        """
        if center is None:
            center = MapGenerator.BC_CENTER
        
        mapa = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles="OpenStreetMap"
        )
        
        return mapa
    
    @staticmethod
    def agregar_circulo_radio(mapa, latitud, longitud, radio_metros, color="blue"):
        """
        Agrega un círculo que representa el radio de búsqueda.
        
        Args:
            mapa (folium.Map): Mapa donde agregar el círculo
            latitud (float): Centro del círculo
            longitud (float): Centro del círculo
            radio_metros (float): Radio en metros
            color (str): Color del círculo
        """
        folium.Circle(
            location=[latitud, longitud],
            radius=radio_metros,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.2,
            popup=f"Radio: {radio_metros/1000:.2f} km"
        ).add_to(mapa)
    
    @staticmethod
    def crear_mapa_recomendacion(
        latitud_centro, 
        longitud_centro, 
        radio_km, 
        negocios_totales, 
        negocios_similares
    ):
        """
        Crea un mapa para la página de recomendación.
        Muestra el círculo de búsqueda y diferencia visualmente los competidores.
        
        Args:
            latitud_centro (float): Centro de búsqueda
            longitud_centro (float): Centro de búsqueda
            radio_km (float): Radio en km
            negocios_totales (list): Todos los negocios en el radio
            negocios_similares (list): Solo competidores directos
            
        Returns:
            folium.Map: Mapa con visualización diferenciada
        """
        # Validar parámetros
        if not negocios_totales:
            negocios_totales = []
        
        if not negocios_similares:
            negocios_similares = []
        
        # Crear mapa centrado
        mapa = MapGenerator.crear_mapa_base(
            center=[latitud_centro, longitud_centro],
            zoom_start=13
        )
        
        # Agregar círculo de radio
        MapGenerator.agregar_circulo_radio(
            mapa, 
            latitud_centro, 
            longitud_centro, 
            radio_km * 1000,  # Convertir km a metros
            color="blue"
        )
        
        # Marcador en el centro (ubicación propuesta)
        folium.Marker(
            location=[latitud_centro, longitud_centro],
            popup="📍 Ubicación Propuesta",
            tooltip="Tu ubicación",
            icon=folium.Icon(color="red", icon="star")
        ).add_to(mapa)
        
        # IDs de negocios similares para identificarlos
        ids_similares = {n.get('id_registro') for n in negocios_similares if n.get('id_registro')}
        
        # Contador de negocios agregados
        negocios_agregados = 0
        negocios_con_error = 0
        
        # Agregar negocios con colores diferenciados
        for negocio in negocios_totales:
            try:
                # Validar que el negocio tenga coordenadas
                if not negocio.get('latitud') or not negocio.get('longitud'):
                    negocios_con_error += 1
                    continue
                
                lat = float(negocio['latitud'])
                lon = float(negocio['longitud'])
                
                # Validar rangos
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    negocios_con_error += 1
                    continue
                
                id_neg = negocio.get('id_registro')
                
                # Determinar si es competidor directo
                es_competidor = id_neg in ids_similares
                color = "orange" if es_competidor else "green"
                icon = "exclamation-triangle" if es_competidor else "store"
                
                nombre = negocio.get('nombre_comercial', 'Sin nombre')
                actividad = negocio.get('actividad_texto', 'Sin actividad')
                distancia = negocio.get('distancia_km', 'N/A')
                
                tipo_texto = "🔴 COMPETIDOR DIRECTO" if es_competidor else "🟢 Otro tipo de negocio"
                
                # Formatear distancia
                if isinstance(distancia, (int, float)):
                    distancia_texto = f"{distancia:.2f} km"
                else:
                    distancia_texto = "N/A"
                
                popup_html = f"""
                <div style="font-family: Arial; width: 220px;">
                    <h4 style="margin: 0; color: {'#d9534f' if es_competidor else '#5cb85c'};">
                        {nombre}
                    </h4>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>{tipo_texto}</b></p>
                    <p style="margin: 3px 0;"><b>Actividad:</b> {actividad}</p>
                    <p style="margin: 3px 0;"><b>Distancia:</b> {distancia_texto}</p>
                    <p style="margin: 3px 0; font-size: 11px; color: gray;">
                        ID: {id_neg}
                    </p>
                </div>
                """
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=nombre,
                    icon=folium.Icon(color=color, icon=icon, prefix="fa")
                ).add_to(mapa)
                
                negocios_agregados += 1
                
            except (ValueError, KeyError, TypeError) as e:
                negocios_con_error += 1
                continue
        
        # Log de resultados
        if negocios_con_error > 0:
            st.warning(f"⚠️ {negocios_con_error} negocios no pudieron ser agregados al mapa (coordenadas inválidas)")
        
        if negocios_agregados == 0 and len(negocios_totales) > 0:
            st.error("❌ No se pudo agregar ningún negocio al mapa. Verifica que los datos tengan coordenadas válidas.")
        
        return mapa
    
    @staticmethod
    def crear_mapa_con_negocios(negocios, center=None, zoom_start=12, usar_cluster=True):
        """
        Crea un mapa con múltiples negocios.
        
        Args:
            negocios (list): Lista de diccionarios con datos de negocios
            center (list): Centro del mapa
            zoom_start (int): Zoom inicial
            usar_cluster (bool): Si usar clustering de marcadores
            
        Returns:
            folium.Map: Mapa con los negocios
        """
        # Validar entrada
        if not negocios:
            negocios = []
        
        # Crear mapa base
        if center is None and len(negocios) > 0:
            # Intentar centrar en el primer negocio válido
            for neg in negocios:
                if neg.get('latitud') and neg.get('longitud'):
                    try:
                        center = [float(neg['latitud']), float(neg['longitud'])]
                        break
                    except:
                        continue
        
        mapa = MapGenerator.crear_mapa_base(center=center, zoom_start=zoom_start)
        
        # Usar cluster si hay muchos marcadores
        if usar_cluster and len(negocios) > 50:
            marker_cluster = MarkerCluster().add_to(mapa)
            parent = marker_cluster
        else:
            parent = mapa
        
        # Agregar marcadores
        negocios_agregados = 0
        negocios_con_error = 0
        
        for negocio in negocios:
            try:
                if not negocio.get('latitud') or not negocio.get('longitud'):
                    negocios_con_error += 1
                    continue
                
                lat = float(negocio['latitud'])
                lon = float(negocio['longitud'])
                
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    negocios_con_error += 1
                    continue
                
                # Información del popup
                nombre = negocio.get('nombre_comercial', 'Sin nombre')
                actividad = negocio.get('actividad_texto', 'Sin actividad')
                id_registro = negocio.get('id_registro', 'N/A')
                
                popup_html = f"""
                <div style="font-family: Arial; width: 200px;">
                    <h4 style="margin: 0; color: #1e5fb8;">{nombre}</h4>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>Actividad:</b> {actividad}</p>
                    <p style="margin: 3px 0;"><b>ID:</b> {id_registro}</p>
                    <p style="margin: 3px 0; font-size: 11px; color: gray;">
                        📍 {lat:.4f}, {lon:.4f}
                    </p>
                </div>
                """
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=nombre,
                    icon=folium.Icon(color="blue", icon="store", prefix="fa")
                ).add_to(parent)
                
                negocios_agregados += 1
                
            except (ValueError, KeyError, TypeError) as e:
                negocios_con_error += 1
                continue
        
        # Mensajes informativos
        if negocios_con_error > 0:
            st.warning(f"⚠️ {negocios_con_error} negocios con coordenadas inválidas fueron omitidos")
        
        if negocios_agregados > 0:
            st.success(f"✅ {negocios_agregados} negocios agregados al mapa")
        elif len(negocios) > 0:
            st.error("❌ No se pudieron agregar negocios al mapa. Verifica los datos.")
        
        return mapa