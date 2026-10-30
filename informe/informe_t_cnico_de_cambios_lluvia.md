# Informe Técnico: Actualización y Nuevas Funcionalidades del Sistema ProHuerta Chascomús

**Proyecto:** Pronóstico de Demanda de Semillas por Barrio · ProHuerta (Chascomús)  
**Equipo Integrante:** Barreu · Pérez Cazal · Quiroga  
**Fecha:** Octubre 2026  

---

## 1. Resumen Ejecutivo
Este documento detalla las modificaciones técnicas, la resolución de inconsistencias metodológicas y la incorporación del nuevo módulo de **Análisis Climático** dentro de la aplicación web basada en Flask. Las mejoras apuntan a consolidar la robustez analítica de los modelos de Aprendizaje Automático, aislar variables para evitar sesgos de información (*data leakage*) y unificar la experiencia visual en todo el panel de control municipal.

---

## 2. Integración del Control de Stock y Simulación de Solicitudes (`/inventario`)
Se consolidó la migración del subsistema de inventario y simulación de cobertura por solicitud dentro del núcleo principal de la aplicación (`app.py`), unificando las rutas de navegación y asegurando la compatibilidad con el entorno de despliegue (Vercel).

* **Modelos involucrados:** 
  * `modelo_regresion_cobertura.joblib` (estimación continua de la cobertura porcentual del catálogo).
  * `modelo_clasificacion.joblib` (predicción directa de la clase de alta demanda).
* **Lógica implementada:** La vista procesa un formulario interactivo que recolecta atributos cualitativos y cuantitativos de la huerta (superficie, experiencia, destino, ocupación, temporada y año), devolviendo una estimación porcentual comparada contra la oferta oficial de la temporada.

---

## 3. Desarrollo del Módulo de Análisis Climático y Purgado de Modelo (`/lluvias`)

Una de las contribuciones metodológicas clave de esta iteración consistió en resolver un problema de **fuga de datos (*data leakage*)** detectado originalmente en el modelo de precipitaciones.

### A. Corrección Metodológica (Eliminación de *Data Leakage*)
* **El problema inicial:** La versión preliminar del modelo utilizaba la variable `Oferta_Catalogo` para predecir la cobertura ante distintos escenarios de lluvia. Dado que la cobertura se define matemáticamente en función del catálogo ofrecido, esto generaba un sesgo artificial y ocultaba el impacto genuino de las condiciones climáticas.
* **La solución:** Se reentrenó el modelo de regresión lineal (`modelo_lluvias.joblib`) aislando la variable independiente, utilizando **exclusivamente los milímetros de precipitación histórica (`Precipitaciones_Hist_mm`)** frente al porcentaje de cobertura real observado.
* **Resultado del reentrenamiento:**
  * **Coeficiente:** $0.0133$ (cada $100\text{ mm}$ adicionales de lluvia incrementan la cobertura estimada en un $1.33\%$).
  * **Intercepto:** $55.4973\%$ (cobertura base independiente del volumen hídrico).

### B. Implementación en el Backend (`app.py` y `logica_lluvias.py`)
* Se creó la ruta `/lluvias` soportando métodos `GET` y `POST`.
* Se desacopló la función de estimación climática (`estimar_cobertura_clima`), la cual ahora procesa un único parámetro de entrada (`precipitaciones`), retornando un porcentaje acotado lógicamente entre $0\%$ y $100\%$.

### C. Diseño de la Vista (`lluvias.html`)
* **Estructura visual:** Se mantuvo la simetría de contenedores bicolumna `.grid-2` y `.panel` utilizada en todo el proyecto para garantizar coherencia estética.
* **Semáforo dinámico de impacto:** La barra de progreso de cobertura adapta sus tonos de color según umbrales de severidad hídrica (alerta por sequía o rendimiento óptimo).
* **Contexto Hídrico Automatizado:** La interfaz evalúa los milímetros ingresados en tiempo real y clasifica el escenario en tres categorías institucionales:
  1. *Escenario de sequía.*
  2. *Régimen de lluvias promedio.*
  3. *Temporada de precipitaciones intensas.*

---

## 4. Unificación de Navegación y Estándares UI
* Se actualizaron los enlaces globales mediante un diccionario centralizado (`NAV_URLS`) inyectado por un procesador de contexto en Flask, permitiendo una transición fluida entre las vistas de *Portada*, *Inicio*, *Mapa de Demanda*, *Control de Stock*, *Informe de Datos* y *Análisis Climático*.
* Se garantizó el uso exclusivo de sintaxis Jinja2 compatible y la correcta gesión de formularios con persistencia de estado para evitar recargas vacías en los selectores de año y temporada.

---
*Informe generado automáticamente para el seguimiento del Trabajo Práctico Integrador de Aprendizaje Automático y Ciencia de Datos.*