# 📍💻 Simluador de apertura de Negocios
Link: [Link a este design doc](#)

Author(s): Flor Mayon.

Status: in progress.

Ultima actualización: 14/10/2025

## 📘 Contenido
- Goals
- Non-Goals
- Background
- Overview
- Detailed Design
  - Solucion 1
    - Frontend
    - Backend
  - Solucion 2
    - Frontend
    - Backend
- Consideraciones
- Métricas

## Links
- [Un link](#)
- [Otro link](#)

## 🎯 Objetivo
Crear un "simulador de apertura de negocios" del Estado de B.C. para que el usuario pueda seleccionar una zona y tipo de negocio. El sistema analizará datos historicos y la densidad de negocios (cantidad en una zona determinada) para ofrecer una recomendacion simple sobre si es una buena oportunidad o es una zona saturada. También, se genera un mapa interactivo con la ubicación de los negocios.


## ✅ Goals
- Analizar la densidad de negocios existenes utilizando Pandas.
- El usuario puede seleccionar la zona y tipo de negocio.
- Devolver una recomendacion simple: buena oportunidad o zona sautrada.
- Visualizar los negocios en un mapa interactivo.

## 🚫 Non-Goals
- No se realizan predicciones con modelos de IA.
- No incluye autenticación de usuarios.
- No almacena informacion en tiempo real.

## 🧠 Background
El proyecto se basa en un archivo Excel de Inegi, aproximadamente 138 100 registros de negocios. Cada registro incluye diferente información como el nombre del negocio, actividad empresarial, dirección, numero de empleados, coordenadas, fecha de registro, entre otros.

## 🧩 Overview
El sistema permite al usuario seleccionar una zona del estado de BC y el tipo de negocio desde una interfaz web. El sistema filtra los negocios existentes en una zona y calcula cuantos son similares al seleccionado inicialmente para después visualizar una recomendación basada en la densidad. 

## Detailed Design
## 🐍 Lenguaje
 - **Python 3.10+**
   
## Solution 1
### Frontend
- Streamlit.
- Pandas.
### Backend
- Flask.
- Pandas.

## Solution 2
### Frontend
- HTML + JavaScript.
### Backend
- Flask.

## Consideraciones
- El archivo Excel debe estar estructurado y normalizado.
- Las zonas y tipo de negocio deben estar definidas correctamente.
- EL analisis es simple, pueden haber factores externos no considerados como la población.
- Puede escalar a modelos de IA.

## Métricas
- Cantidad de negocios similares en una zona.
- Total de negocios en una zona.
- Tiempo de respuesta del backend.
