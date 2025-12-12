"""
Cliente API para comunicación con el backend Flask.
Todas las llamadas al servidor pasan por aquí.
VERSIÓN CORREGIDA - Manejo de errores JSON mejorado
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
        Incluye manejo de errores mejorado.
        """
        url_completa = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(
                url_completa,
                params=params,
                timeout=30
            )
            
            # Verificar status code ANTES de intentar parsear JSON
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as json_error:
                    st.error(f"❌ Error al parsear JSON del servidor")
                    st.error(f"URL: {url_completa}")
                    st.error(f"Respuesta recibida: {response.text[:200]}")
                    return None
            else:
                st.error(f"❌ Error del servidor (código {response.status_code})")
                st.error(f"URL: {url_completa}")
                try:
                    error_data = response.json()
                    st.error(f"Detalle: {error_data}")
                except:
                    st.error(f"Respuesta: {response.text[:200]}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error("❌ **No se pudo conectar con el servidor**")
            st.error(f"Intentando conectar a: {url_completa}")
            st.info("💡 Verifica que Flask esté corriendo:")
            st.code("cd backend\npython app.py", language="bash")
            return None
            
        except requests.exceptions.Timeout:
            st.error("⏱️ **La petición tardó demasiado**")
            st.info("💡 Intenta con un área más pequeña o espera unos segundos")
            return None
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ **Error de conexión:** {e}")
            return None
            
        except Exception as e:
            st.error(f"❌ **Error inesperado:** {e}")
            st.error(f"URL: {url_completa}")
            return None
    
    def health_check(self):
        """Verifica si el backend está funcionando (SIN CACHE para diagnóstico)"""
        return self._get("/")
    
    @st.cache_data(ttl=3600)
    def obtener_todos_negocios(_self):
        """Obtiene todos los negocios (usar con precaución, son 138k registros)"""
        return _self._get("/excel/negocio")
    
    def obtener_negocio_por_id(self, id_negocio):
        """Obtiene un negocio específico por su ID"""
        return self._get(f"/excel/negocio/{id_negocio}")
    
    @st.cache_data(ttl=600)
    def obtener_negocios_por_radio(_self, latitud, longitud, radio_km):
        """
        Obtiene todos los negocios dentro de un radio.
        
        Args:
            latitud (float): Latitud del centro
            longitud (float): Longitud del centro
            radio_km (float): Radio en kilómetros
            
        Returns:
            list: Lista de negocios en la zona o None si hay error
        """
        params = {
            "latitud": latitud,
            "longitud": longitud,
            "radio_km": radio_km
        }
        resultado = _self._get("/excel/negocio/por-radio", params=params)
        
        # Asegurar que siempre devuelve lista o None (nunca dict con error)
        if resultado is None:
            return None
        elif isinstance(resultado, list):
            return resultado
        else:
            st.warning(f"⚠️ Respuesta inesperada del servidor: {type(resultado)}")
            return None
    
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
        resultado = _self._get("/excel/negocio/por-actividad", params=params)
        
        if resultado is None:
            return None
        elif isinstance(resultado, list):
            return resultado
        else:
            return None
    
    @st.cache_data(ttl=300)
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
                "recomendacion": str
            } o None si hay error
        """
        params = {
            "latitud": latitud,
            "longitud": longitud,
            "radio_km": radio_km,
            "id_actividad_empresarial": id_actividad
        }
        return _self._get("/excel/negocio/recomendacion-radio", params=params)
    
    @st.cache_data(ttl=3600)
    def obtener_datos_mapa(_self):
        """
        Obtiene datos ligeros para pintar el mapa.
        Solo coordenadas e IDs, sin todos los detalles.
        
        Returns:
            list: Lista con {id_registro, latitud, longitud, id_actividad_empresarial}
        """
        resultado = _self._get("/excel/negocio/mapa")
        
        if resultado is None:
            return []
        elif isinstance(resultado, list):
            return resultado
        else:
            return []
    
    def buscar_por_nombre(self, nombre):
        """
        Búsqueda predictiva por nombre de negocio.
        Mínimo 3 caracteres.
        
        Args:
            nombre (str): Texto a buscar
            
        Returns:
            list: Top 10 resultados con nombre e ID
        """
        if len(nombre.strip()) < 3:
            return []
        
        params = {"nombre": nombre}
        resultado = self._get("/excel/negocio/buscar-nombre", params=params)
        
        if resultado is None:
            return []
        elif isinstance(resultado, list):
            return resultado
        else:
            return []


# Instancia global del cliente
api = APIClient()