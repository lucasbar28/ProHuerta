# ProHuerta Chascomús: Predicción de Demanda Logística 

![Estado](https://img.shields.io/badge/Estado-Finalizado-success)
![Versión](https://img.shields.io/badge/Versión-1.0-blue)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.9.1-orange)

Sistema Inteligente de Predicción de Demanda de Variedades y Planificación Logística para el Banco de Intercambio de Semillas del programa ProHuerta en Chascomús. 

Este proyecto fue desarrollado como Trabajo Práctico Integrador para el curso de **Modelos de Aprendizaje Automático** (Ciencia de Datos e IA - Instituto N°57).

**Autores (Grupo 3):** Barreu - Pérez Cazal - Quiroga

---

## 🎯 Objetivo del Proyecto

El programa ProHuerta arma y prepara kits de semillas sin conocer con antelación la diversidad de variedades que solicitará cada huertero/a. Este sistema predice la cantidad de sobres solicitados y emite una alerta de **Alta Demanda** en el momento en que el usuario completa el formulario de inscripción, permitiendo al equipo logístico anticipar el armado de kits completos vs. estandarizados y evitar faltantes.

## 🚀 Despliegue en Producción (Demo)

La aplicación se encuentra desplegada y funcionando en la nube mediante Vercel. 
No requiere base de datos ni entrenamiento en vivo. Realiza inferencias en milisegundos cargando los modelos pre-entrenados.

🔗 **[INGRESAR A LA APLICACIÓN WEB AQUÍ](https://pro-huerta.vercel.app/)**

## 🧠 Arquitectura de Modelos

Todo el preprocesamiento está encapsulado en `Pipelines` de Scikit-Learn, utilizando `StandardScaler` para variables numéricas y `OneHotEncoder` para categóricas, previniendo fugas de datos.

* **Regresión (Estimación Numérica):** `KNeighborsRegressor` (k=41) para predecir la cantidad de sobres equivalentes.
* **Clasificación (Sistema de Alertas):** `DecisionTreeClassifier` para predecir directamente sobre un umbral del 75% de cobertura, complementado con una regla de negocio sobre el regresor.
* **Clima (Evaluación de Lluvias):** `LinearRegression` simple, corregida para evitar *target leakage*, basándose puramente en milímetros de precipitación.

## 💻 Instrucciones de Instalación Local

Si deseas ejecutar este proyecto en tu entorno local:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/lucasbar28/nombre-de-tu-repo.git
   cd nombre-de-tu-repo
   ```

2. **Crear un entorno virtual (Recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación (Backend Flask):**
   ```bash
   python app.py
   ```
   *La aplicación estará disponible en `http://localhost:5000`*

## 📁 Estructura del Repositorio

* `/app.py`: Archivo principal del backend Flask.
* `/modelos/`: Contiene los modelos serializados en formato `.joblib` y `metadata_modelos.json`.
* `/informes/`: Contiene el `informe_final.pdf` con la justificación técnica, métricas (RMSE, MAE) y auditoría de datos, además de reportes previos.
* `/notebooks/`: Cuadernos Jupyter con el EDA (Análisis Exploratorio), entrenamiento desde cero y limpieza del dataset.
* `/templates/` y `/static/`: Archivos frontend (HTML, CSS, JS).

---
*Desarrollado para la optimización de recursos y el impacto social y alimentario en la comunidad de Chascomús.*