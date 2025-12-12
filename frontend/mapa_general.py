"""
Generador de mapas interactivos con Folium.
"""

import folium
from folium.plugins import MarkerCluster
import streamlit as st


class MapGenerator:
    """Clase para generar mapas interactivos de negocios"""
    
    # Coordenadas del centro de Baja California
    BC_CENTER = [30.8406, -115.2838]
    
    # Colores por tipo de negocio (puedes personalizar)
    COLORES_ACTIVIDAD = {
        "default": "blue",
        "restaurante": "red",
        "tienda": "green",
        "servicio": "orange",
        "salud": "purple"
    }
    
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
    def agregar_marcador(mapa, latitud, longitud, popup_text, color="blue", icon="info-sign"):
        """
        Agrega un marcador individual al mapa.
        
        Args:
            mapa (folium.Map): Mapa donde agregar el marcador
            latitud (float): Latitud
            longitud (float): Longitud
            popup_text (str): Texto del popup
            color (str): Color del marcador
            icon (str): Icono del marcador
        """
        folium.Marker(
            location=[latitud, longitud],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=popup_text,
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(mapa)
    
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
        # Crear mapa base
        if center is None and len(negocios) > 0:
            # Centrar en el primer negocio
            center = [negocios[0]['latitud'], negocios[0]['longitud']]
        
        mapa = MapGenerator.crear_mapa_base(center=center, zoom_start=zoom_start)
        
        # Usar cluster si hay muchos marcadores
        if usar_cluster and len(negocios) > 50:
            marker_cluster = MarkerCluster().add_to(mapa)
            parent = marker_cluster
        else:
            parent = mapa
        
        # Agregar marcadores
        for negocio in negocios:
            try:
                lat = float(negocio.get('latitud', 0))
                lon = float(negocio.get('longitud', 0))
                
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
                
            except (ValueError, KeyError, TypeError) as e:
                # Saltar negocios con coordenadas inválidas
                continue
        
        return mapa
    
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
        ids_similares = {n.get('id_registro') for n in negocios_similares}
        
        # Agregar negocios con colores diferenciados
        for negocio in negocios_totales:
            try:
                lat = float(negocio.get('latitud', 0))
                lon = float(negocio.get('longitud', 0))
                id_neg = negocio.get('id_registro')
                
                # Determinar si es competidor directo
                es_competidor = id_neg in ids_similares
                color = "orange" if es_competidor else "green"
                icon = "exclamation-triangle" if es_competidor else "store"
                
                nombre = negocio.get('nombre_comercial', 'Sin nombre')
                actividad = negocio.get('actividad_texto', 'Sin actividad')
                
                tipo_texto = "🔴 COMPETIDOR DIRECTO" if es_competidor else "🟢 Otro tipo de negocio"
                
                popup_html = f"""
                <div style="font-family: Arial; width: 220px;">
                    <h4 style="margin: 0; color: {'#d9534f' if es_competidor else '#5cb85c'};">
                        {nombre}
                    </h4>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>{tipo_texto}</b></p>
                    <p style="margin: 3px 0;"><b>Actividad:</b> {actividad}</p>
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
                
            except (ValueError, KeyError, TypeError):
                continue
        
        return mapa