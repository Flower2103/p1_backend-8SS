from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # Permite fetch desde cualquier origen si es necesario

# ---------- CONFIGURACIÓN DE ARCHIVOS ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Asegúrate de que bd_negocios.xlsx esté dentro de la carpeta 'data'
RUTA_EXCEL = os.path.join(BASE_DIR, "data", "bd_negocios.xlsx")


def cargar_y_unir_datos():
    """
    Carga la hoja principal y las de referencia, las une.
    Incluye manejo de errores explícito para depuración.
    """
    print("--- INICIANDO CARGA DE DATOS ---")
    
    # 1. Cargar el archivo Excel
    try:
        xls = pd.ExcelFile(RUTA_EXCEL)
        print(f"✅ Archivo encontrado en: {RUTA_EXCEL}")
    except FileNotFoundError:
        print(f"❌ ERROR: Archivo no encontrado en la ruta: {RUTA_EXCEL}. Verifica la carpeta 'data'.")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ ERROR: No se pudo abrir el archivo Excel. Asegúrate de que no está abierto. Detalle: {e}")
        return pd.DataFrame()
        
    # 2. Cargar la hoja principal
    try:
        hoja_principal_nombre = 'bd_normalizada'
        df_principal = xls.parse(hoja_principal_nombre)
        df_principal.columns = df_principal.columns.str.lower()
        print(f"✅ Hoja '{hoja_principal_nombre}' cargada. Columnas: {list(df_principal.columns)[:5]}...")
        
        # CRÍTICO: Verificar columnas clave
        columnas_esenciales = [
            'latitud', 'longitud', 'id_registro', 
            'id_actividad_empresarial', 'id_nombres_establecimientos'
        ]
        faltantes = [col for col in columnas_esenciales if col not in df_principal.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas esenciales en '{hoja_principal_nombre}': {faltantes}")
            
    except Exception as e:
        print(f"❌ ERROR CRÍTICO al cargar la hoja principal '{hoja_principal_nombre}': {e}")
        return pd.DataFrame()
    
    # 3. Definición de Referencias y Unión
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
        },
        # ... (Añade el resto de referencias si las necesitas)
    }
    
    for hoja, cols in referencias.items():
        try:
            # Cargar referencia
            df_ref = xls.parse(hoja)
            df_ref.columns = df_ref.columns.str.lower()
            
            # Validar columnas en referencia
            if cols['id'] not in df_ref.columns or cols['texto'] not in df_ref.columns:
                raise KeyError(
                    f"Columnas ID/TEXTO faltantes en '{hoja}'. "
                    f"Se buscó ID: '{cols['id']}' y TEXTO: '{cols['texto']}'."
                )
            
            # Validar columna de unión en principal
            if cols['id'] not in df_final.columns:
                raise KeyError(
                    f"Columna de unión '{cols['id']}' faltante en la hoja principal para unir con '{hoja}'."
                )

            # Realizar la unión
            df_ref_indexed = df_ref.set_index(cols['id'])
            df_final = df_final.join(
                df_ref_indexed[cols['texto']].rename(cols['final']),
                on=cols['id']
            )
            print(f"✅ Unión con hoja '{hoja}' exitosa. Nueva columna: '{cols['final']}'")

        except Exception as e:
            print(f"❌ ERROR CRÍTICO al unir la hoja '{hoja}': {e}")
            return pd.DataFrame()  # Fallo al cargar o unir

    print(f"--- CARGA FINALIZADA ---")

    # Filtramos filas con latitud/longitud nulas
    df_final = df_final.dropna(subset=['latitud', 'longitud'])
    print(f"Filas limpias para mapeo: {len(df_final)}")

    return df_final

# Cargar el DataFrame globalmente una sola vez al inicio
df_completo = cargar_y_unir_datos()


# ---------------- RUTAS (Todas usan df_completo) ----------------
@app.route("/")
def index():
    return "API de Negocios BC funcionando ✅"

@app.route("/pagina/hello")
def hello():
    return render_template("hello.html")

# 1️⃣ TODOS LOS NEGOCIOS
@app.route("/excel/negocio", methods=["GET"])
def todos():
    return jsonify(df_completo.to_dict(orient="records"))

# 2️⃣ NEGOCIO POR ID
@app.route("/excel/negocio/<int:id_negocio>", methods=["GET"])
def por_id(id_negocio):
    fila = df_completo[df_completo["id_registro"] == id_negocio]
    if fila.empty:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify(fila.to_dict(orient="records")[0])

# 3️⃣ POR RADIO
@app.route("/excel/negocio/por-radio", methods=["GET"])
def por_radio():
    try:
        lat = float(request.args.get("latitud"))
        lon = float(request.args.get("longitud"))
        radio = float(request.args.get("radio_km"))

        df_completo["distancia"] = ((df_completo["latitud"] - lat) ** 2 + (df_completo["longitud"] - lon) ** 2) ** 0.5
        resultado = df_completo[df_completo["distancia"] <= (radio / 100)]  # Ajuste simple

        if resultado.empty:
            return jsonify({"mensaje": "No hay datos"}), 404

        return jsonify(resultado.to_dict(orient="records"))
    except:
        return jsonify({"error": "Parámetros inválidos"}), 400

# 4️⃣ POR ACTIVIDAD
@app.route("/excel/negocio/por-actividad", methods=["GET"])
def por_actividad():
    try:
        act = int(request.args.get("id_actividad_empresarial"))
        resultado = df_completo[df_completo["id_actividad_empresarial"] == act]

        if resultado.empty:
            return jsonify({"mensaje": "No hay datos"}), 404

        return jsonify(resultado.to_dict(orient="records"))
    except:
        return jsonify({"error": "Parámetros inválidos"}), 400

# 5️⃣ RECOMENDACIÓN
@app.route("/excel/negocio/recomendacion-radio", methods=["GET"])
def recomendacion():
    try:
        lat = float(request.args.get("latitud"))
        lon = float(request.args.get("longitud"))
        radio = float(request.args.get("radio_km"))
        act = int(request.args.get("id_actividad_empresarial"))

        df_completo["distancia"] = ((df_completo["latitud"] - lat) ** 2 + (df_completo["longitud"] - lon) ** 2) ** 0.5
        zona = df_completo[df_completo["distancia"] <= (radio / 100)]
        similares = zona[zona["id_actividad_empresarial"] == act]

        mensaje = "Zona saturada" if len(similares) > 10 else "Buena oportunidad"

        return jsonify({
            "total_en_radio": len(zona),
            "similares": len(similares),
            "recomendacion": mensaje
        })
    except:
        return jsonify({"error": "Parámetros inválidos"}), 400

# 6️⃣ MAPA (Datos ligeros solo para pintar)
@app.route("/excel/negocio/mapa", methods=["GET"])
def mapa():
    solo_coord = df_completo[["id_registro", "latitud", "longitud", "id_actividad_empresarial"]]
    return jsonify(solo_coord.to_dict(orient="records"))

# 7️⃣ BÚSQUEDA PREDICTIVA POR NOMBRE
@app.route("/excel/negocio/buscar-nombre", methods=["GET"])
def buscar_por_nombre():
    try:
        texto_busqueda = request.args.get("nombre", "").upper().strip()

        if len(texto_busqueda) < 3:
            return jsonify([])

        columna_nombre = "nombre_comercial"
        resultado = df_completo[
            df_completo[columna_nombre].astype(str).str.upper().str.contains(texto_busqueda)
        ]

        opciones = resultado[[columna_nombre, "id_registro"]].head(5).to_dict(orient="records")
        return jsonify(opciones)
    except Exception as e:
        return jsonify({"error": f"Error en el servidor: {str(e)}"}), 500

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)
