"""
🚀 API REST para Simulador de Negocios BC - VERSIÓN SIMPLIFICADA
Backend Flask con solo las funcionalidades esenciales que usa el frontend

Endpoints incluidos:
- ✅ GET / - Health check básico
- ✅ GET /excel/negocio/<id> - Obtener negocio por ID
- ✅ GET /excel/negocio/por-radio - Buscar en radio (CORREGIDO con Haversine)
- ✅ GET /excel/negocio/por-actividad - Filtrar por actividad
- ✅ GET /excel/negocio/recomendacion-radio - Recomendación de apertura
- ✅ GET /excel/negocio/mapa - Datos ligeros para mapa
- ✅ GET /excel/negocio/buscar-nombre - Búsqueda predictiva por nombre
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
import pandas as pd
import numpy as np
import os
import logging
from math import radians, sin, cos, sqrt, atan2

# ==================== CONFIGURACIÓN ====================
app = Flask(__name__)
CORS(app)
STREAMLIT_URL = "https://p1backend-8ss-kqefehuk3endd5fbq4muva.streamlit.app/" 
CORS(app, origins=[STREAMLIT_URL])

# Configuración de caché
cache_config = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 3600,
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_EXCEL = os.path.join(BASE_DIR, "data", "bd_negocios.xlsx")


# ==================== CÁLCULO DE DISTANCIAS CORREGIDO ====================
def calcular_distancias_vectorizadas(df, lat_centro, lon_centro):
    """
    Calcula distancias usando la fórmula de Haversine (considera curvatura de la Tierra).
    Versión vectorizada con NumPy para máximo rendimiento.
    
    Args:
        df (DataFrame): DataFrame con columnas 'latitud' y 'longitud'
        lat_centro (float): Latitud del punto central
        lon_centro (float): Longitud del punto central
    
    Returns:
        numpy.array: Array con distancias en kilómetros
    """
    R = 6371.0  # Radio de la Tierra en km
    
    # Convertir a radianes (vectorizado)
    lat1 = np.radians(lat_centro)
    lon1 = np.radians(lon_centro)
    lat2 = np.radians(df['latitud'].values)
    lon2 = np.radians(df['longitud'].values)
    
    # Diferencias
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Fórmula de Haversine vectorizada
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c


# ==================== CARGA DE DATOS ====================
@cache.cached(timeout=7200, key_prefix='datos_completos')
def cargar_y_unir_datos():
    """
    Carga la hoja principal y las de referencia, las une.
    Esta función está cacheada por 2 horas.
    """
    logger.info("="*60)
    logger.info("INICIANDO CARGA DE DATOS")
    logger.info("="*60)
    
    # 1. Verificar que el archivo existe
    if not os.path.exists(RUTA_EXCEL):
        logger.error(f"❌ Archivo no encontrado: {RUTA_EXCEL}")
        return pd.DataFrame()
    
    try:
        # 2. Cargar archivo Excel
        logger.info(f"📂 Cargando: {RUTA_EXCEL}")
        xls = pd.ExcelFile(RUTA_EXCEL)
        logger.info(f"✅ Archivo abierto")
        
    except Exception as e:
        logger.error(f"❌ Error al abrir Excel: {e}")
        return pd.DataFrame()
    
    # 3. Cargar hoja principal
    try:
        hoja_principal = 'bd_normalizada'
        df_principal = xls.parse(hoja_principal)
        df_principal.columns = df_principal.columns.str.lower()
        
        logger.info(f"✅ Hoja cargada: {len(df_principal):,} filas")
        
        # Verificar columnas esenciales
        columnas_esenciales = [
            'latitud', 'longitud', 'id_registro',
            'id_actividad_empresarial', 'id_nombres_establecimientos'
        ]
        
        faltantes = [col for col in columnas_esenciales if col not in df_principal.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas esenciales: {faltantes}")
        
    except Exception as e:
        logger.error(f"❌ Error al cargar hoja principal: {e}")
        return pd.DataFrame()
    
    # 4. Unir con tablas de referencia
    df_final = df_principal.copy()
    
    referencias = {
        'nombres_establecimientos': {
            'id': 'id_nombres_establecimientos',
            'texto': 'nombres_establecimientos',
            'final': 'nombre_comercial'
        },
        'actividad_empresarial': {
            'id': 'id_actividad_empresarial',
            'texto': 'nombre_actividad_empresarial',
            'final': 'actividad_texto'
        }
    }
    
    for hoja, cols in referencias.items():
        try:
            if hoja not in xls.sheet_names:
                logger.warning(f"⚠️ Hoja '{hoja}' no encontrada, saltando...")
                continue
            
            df_ref = xls.parse(hoja)
            df_ref.columns = df_ref.columns.str.lower()
            
            if cols['id'] not in df_ref.columns or cols['texto'] not in df_ref.columns:
                logger.warning(f"⚠️ Columnas faltantes en '{hoja}', saltando...")
                continue
            
            # Realizar unión
            df_ref_indexed = df_ref.set_index(cols['id'])
            df_final = df_final.join(
                df_ref_indexed[cols['texto']].rename(cols['final']),
                on=cols['id']
            )
            
            logger.info(f"✅ Unión con '{hoja}' exitosa")
            
        except Exception as e:
            logger.warning(f"⚠️ Error al unir '{hoja}': {e}")
            continue
    
    # 5. Limpiar datos
    filas_iniciales = len(df_final)
    df_final = df_final.dropna(subset=['latitud', 'longitud'])
    filas_finales = len(df_final)
    
    logger.info(f"✅ Limpieza: {filas_iniciales:,} → {filas_finales:,} filas")
    
    # 6. Crear índice para búsquedas rápidas
    if 'id_registro' in df_final.columns:
        df_final.set_index('id_registro', drop=False, inplace=True)
    
    logger.info("="*60)
    logger.info(f"✅ CARGA COMPLETADA: {len(df_final):,} registros")
    logger.info("="*60)
    
    return df_final


# Cargar datos al inicio
logger.info("🚀 Iniciando servidor...")
df_completo = cargar_y_unir_datos()

if df_completo.empty:
    logger.error("❌ ADVERTENCIA: No se pudieron cargar los datos")
else:
    logger.info(f"✅ Servidor listo con {len(df_completo):,} registros")


# ==================== RUTAS ====================

@app.route("/")
def index():
    """Health check básico"""
    return jsonify({
        "status": "OK",
        "message": "API de Negocios BC funcionando ✅",
        "registros_disponibles": len(df_completo)
    })


@app.route("/excel/negocio/<int:id_negocio>", methods=["GET"])
@cache.cached(timeout=3600, query_string=True)
def por_id(id_negocio):
    """
    Obtiene un negocio específico por su ID.
    Usado en: buscar_zona.py cuando seleccionas un negocio de la búsqueda
    """
    try:
        if id_negocio in df_completo.index:
            fila = df_completo.loc[id_negocio]
            return jsonify(fila.to_dict())
        else:
            return jsonify({"error": "Negocio no encontrado"}), 404
            
    except Exception as e:
        logger.error(f"Error en por_id({id_negocio}): {e}")
        return jsonify({"error": "Error interno"}), 500


@app.route("/excel/negocio/por-radio", methods=["GET"])
@cache.cached(timeout=600, query_string=True)
def por_radio():
    """
    ⭐ CORREGIDO: Ahora usa Haversine para distancias precisas
    
    Obtiene negocios dentro de un radio geográfico.
    Usado en: buscar_zona.py para el análisis de zona
    
    Query params:
        - latitud (float)
        - longitud (float)
        - radio_km (float)
    """
    try:
        lat = request.args.get("latitud", type=float)
        lon = request.args.get("longitud", type=float)
        radio = request.args.get("radio_km", type=float)
        
        if lat is None or lon is None or radio is None:
            return jsonify({"error": "Parámetros faltantes"}), 400
        
        # Validaciones básicas
        if not (-90 <= lat <= 90):
            return jsonify({"error": "Latitud inválida"}), 400
        
        if not (-180 <= lon <= 180):
            return jsonify({"error": "Longitud inválida"}), 400
        
        if radio <= 0 or radio > 100:
            return jsonify({"error": "Radio debe estar entre 0 y 100 km"}), 400
        
        # Calcular distancias con Haversine (CORREGIDO)
        distancias = calcular_distancias_vectorizadas(df_completo, lat, lon)
        
        # Filtrar por radio
        mask = distancias <= radio
        resultado = df_completo[mask].copy()
        resultado['distancia_km'] = distancias[mask]
        
        # Ordenar por distancia
        resultado = resultado.sort_values('distancia_km')
        
        # Siempre devolver lista (vacía si no hay resultados)
        # Esto evita que el frontend rompa cuando no hay negocios
        return jsonify(resultado.to_dict(orient="records"))
        
    except Exception as e:
        logger.error(f"Error en por_radio: {e}")
        return jsonify({"error": "Error interno"}), 500


@app.route("/excel/negocio/por-actividad", methods=["GET"])
@cache.cached(timeout=600, query_string=True)
def por_actividad():
    """
    Filtra negocios por tipo de actividad empresarial.
    Usado en: buscar_zona.py (si filtras por tipo)
    
    Query params:
        - id_actividad_empresarial (int)
    """
    try:
        id_act = request.args.get("id_actividad_empresarial", type=int)
        
        if id_act is None:
            return jsonify({"error": "Parámetro faltante"}), 400
        
        resultado = df_completo[df_completo["id_actividad_empresarial"] == id_act]
        
        # Siempre devolver lista
        return jsonify(resultado.to_dict(orient="records"))
        
    except Exception as e:
        logger.error(f"Error en por_actividad: {e}")
        return jsonify({"error": "Error interno"}), 500


@app.route("/excel/negocio/recomendacion-radio", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
def recomendacion():
    """
    ⭐ CORREGIDO: Ahora calcula densidad con distancias reales
    
    Genera recomendación de apertura de negocio.
    Usado en: buscar_zona.py para el análisis principal
    
    Query params:
        - latitud (float)
        - longitud (float)
        - radio_km (float)
        - id_actividad_empresarial (int)
    """
    try:
        lat = request.args.get("latitud", type=float)
        lon = request.args.get("longitud", type=float)
        radio = request.args.get("radio_km", type=float)
        id_act = request.args.get("id_actividad_empresarial", type=int)
        
        if None in [lat, lon, radio, id_act]:
            return jsonify({"error": "Parámetros faltantes"}), 400
        
        # Validaciones
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({"error": "Coordenadas inválidas"}), 400
        
        if radio <= 0 or radio > 100:
            return jsonify({"error": "Radio inválido"}), 400
        
        # Calcular distancias con Haversine (CORREGIDO)
        distancias = calcular_distancias_vectorizadas(df_completo, lat, lon)
        zona = df_completo[distancias <= radio]
        similares = zona[zona["id_actividad_empresarial"] == id_act]
        
        # Lógica de recomendación
        total_similares = len(similares)
        
        if total_similares <= 3:
            recomendacion = "Buena oportunidad"
        elif total_similares <= 10:
            recomendacion = "Oportunidad moderada"
        else:
            recomendacion = "Zona saturada"
        
        return jsonify({
            "total_en_radio": len(zona),
            "similares": total_similares,
            "recomendacion": recomendacion
        })
        
    except Exception as e:
        logger.error(f"Error en recomendacion: {e}")
        return jsonify({"error": "Error interno"}), 500


@app.route("/excel/negocio/mapa", methods=["GET"])
@cache.cached(timeout=3600)
def mapa():
    """
    Devuelve solo coordenadas e IDs para el mapa.
    Usado en: mapa_generator.py (si renderizas todos los negocios)
    """
    columnas = ["id_registro", "latitud", "longitud", "id_actividad_empresarial"]
    columnas_disponibles = [c for c in columnas if c in df_completo.columns]
    
    resultado = df_completo[columnas_disponibles]
    
    return jsonify(resultado.to_dict(orient="records"))


@app.route("/excel/negocio/buscar-nombre", methods=["GET"])
def buscar_por_nombre():
    """
    Búsqueda predictiva por nombre comercial.
    Usado en: buscar_zona.py cuando buscas por nombre de negocio
    
    Query params:
        - nombre (str): Mínimo 3 caracteres
    """
    try:
        texto = request.args.get("nombre", "").strip()
        
        if len(texto) < 3:
            return jsonify([])
        
        columna_nombre = "nombre_comercial"
        
        if columna_nombre not in df_completo.columns:
            return jsonify({"error": "Columna nombre_comercial no disponible"}), 500
        
        # Búsqueda case-insensitive
        mask = df_completo[columna_nombre].astype(str).str.upper().str.contains(
            texto.upper(), 
            na=False,
            regex=False
        )
        
        resultado = df_completo[mask].head(10)
        
        # Campos necesarios para el frontend
        campos = [columna_nombre, "id_registro"]
        if "actividad_texto" in resultado.columns:
            campos.append("actividad_texto")
        
        opciones = resultado[campos].to_dict(orient="records")
        
        return jsonify(opciones)
        
    except Exception as e:
        logger.error(f"Error en buscar_por_nombre: {e}")
        return jsonify({"error": "Error en búsqueda"}), 500

@app.route("/excel/actividades", methods=["GET"])
@cache.cached(timeout=3600)
def todas_actividades():
    """
    Devuelve lista de todas las actividades únicas para poblar Streamlit
    """
    if "id_actividad_empresarial" not in df_completo.columns or "actividad_texto" not in df_completo.columns:
        return jsonify([])

    actividades = df_completo[["id_actividad_empresarial", "actividad_texto"]].drop_duplicates()
    actividades = actividades.sort_values("actividad_texto")
    return jsonify(actividades.to_dict(orient="records"))

# ==================== MAIN ====================
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 5500))
    DEBUG = os.getenv("FLASK_ENV") != "production"
    
    logger.info("="*60)
    logger.info("🚀 Servidor Flask - Versión Simplificada")
    logger.info(f"🔌 Puerto: {PORT}")
    logger.info(f"💾 Caché: Habilitado")
    logger.info("="*60)
    
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=DEBUG
    )
