"""
Cliente API para comunicación con el backend Flask.
Todas las llamadas al servidor pasan por aquí.
"""

import requests
import streamlit as st

# Configuración de la URL base del backend
API_BASE_URL = "http://localhost:5500"


class APIClient:
    """Cliente para consumir la API REST del backend Flask"""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
    
    def _get(self, endpoint, params=None):
        """
        Método privado para realizar peticiones GET.
        Incluye manejo de errores y cache de Streamlit.
        """
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.error("❌ No se pudo conectar con el servidor. ¿Está corriendo Flask en el puerto 5500?")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ La petición tardó demasiado. Intenta con un área más pequeña.")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Error del servidor: {e}")
            return None
        except Exception as e:
            st.error(f"❌ Error inesperado: {e}")
            return None
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def health_check(_self):
        """Verifica si el backend está funcionando"""
        return _self._get("/")
    
    @st.cache_data(ttl=3600)
    def obtener_todos_negocios(_self):
        """Obtiene todos los negocios (usar con precaución, son 138k registros)"""
        return _self._get("/excel/negocio")
    
    def obtener_negocio_por_id(self, id_negocio):
        """Obtiene un negocio específico por su ID"""
        return self._get(f"/excel/negocio/{id_negocio}")
    
    @st.cache_data(ttl=600)  # Cache por 10 minutos
    def obtener_negocios_por_radio(_self, latitud, longitud, radio_km):
        """
        Obtiene todos los negocios dentro de un radio.
        
        Args:
            latitud (float): Latitud del centro
            longitud (float): Longitud del centro
            radio_km (float): Radio en kilómetros
            
        Returns:
            list: Lista de negocios en la zona
        """
        params = {
            "latitud": latitud,
            "longitud": longitud,
            "radio_km": radio_km
        }
        return _self._get("/excel/negocio/por-radio", params=params)
    
    @st.cache_data(ttl=600)
    def obtener_negocios_por_actividad(_self, id_actividad):
        """
        Filtra negocios por tipo de actividad empresarial.
        
        Args:
            id_actividad (int): ID de la actividad empresarial
            
        Returns:
            list: Lista de negocios con esa actividad
        """
        params = {"id_actividad_empresarial": id_actividad}
        return _self._get("/excel/negocio/por-actividad", params=params)
    
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def obtener_recomendacion(_self, latitud, longitud, radio_km, id_actividad):
        """
        Obtiene la recomendación de apertura de negocio.
        
        Args:
            latitud (float): Latitud del centro
            longitud (float): Longitud del centro
            radio_km (float): Radio en kilómetros
            id_actividad (int): Tipo de negocio a evaluar
            
        Returns:
            dict: {
                "total_en_radio": int,
                "similares": int,
                "recomendacion": str ("Buena oportunidad" o "Zona saturada")
            }
        """
        params = {
            "latitud": latitud,
            "longitud": longitud,
            "radio_km": radio_km,
            "id_actividad_empresarial": id_actividad
        }
        return _self._get("/excel/negocio/recomendacion-radio", params=params)
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora (datos estáticos)
    def obtener_datos_mapa(_self):
        """
        Obtiene datos ligeros para pintar el mapa.
        Solo coordenadas e IDs, sin todos los detalles.
        
        Returns:
            list: Lista con {id_registro, latitud, longitud, id_actividad_empresarial}
        """
        return _self._get("/excel/negocio/mapa")
    
    def buscar_por_nombre(self, nombre):
        """
        Búsqueda predictiva por nombre de negocio.
        Mínimo 3 caracteres.
        
        Args:
            nombre (str): Texto a buscar
            
        Returns:
            list: Top 5 resultados con nombre e ID
        """
        if len(nombre.strip()) < 3:
            return []
        
        params = {"nombre": nombre}
        return self._get("/excel/negocio/buscar-nombre", params=params)


# Instancia global del cliente
api = APIClient()