# TRABAJO PRÁCTICO INTEGRADOR: MODELOS DE APRENDIZAJE AUTOMÁTICO
**Entrega 2: Preparación de Datos, Diccionario de Variables, Protocolo de Evaluación, Baselines y Multi-Modelo**

---

## Integrantes del Grupo
* **Integrante 1:** Lucas Barreu
* **Integrante 2:** Franco Quiroga
* **Integrante 3:** Marcelo Pérez Cazal

---

## 1. Protocolo de División de Datos (Data Split Protocol)

Para prevenir cualquier tipo de **fuga de información (Data Leakage)**, el dataset consolidado de **2.730 solicitudes** se dividió en tres conjuntos independientes antes de aplicar transformaciones o ajuste de parámetros.

### 1.1 Esquema de Partición
* **Conjunto de Entrenamiento (Train - 60%):** 1.638 observaciones. Utilizado exclusivamente para ajustar codificadores, escaladores y entrenar los modelos.
* **Conjunto de Validación (Validation - 20%):** 546 observaciones. Utilizado para la selección de hiperparámetros y optimización de umbrales.
* **Conjunto de Evaluación Final (Test - 20%):** 546 observaciones. Reservado a ciegas para la evaluación final del rendimiento.

### 1.2 Criterio de Estratificación
La partición se realizó aplicando **estratificación multivariable combinada** (`random_state=42`) sobre la variable objetivo binaria (`Alerta_Alta_Demanda`) y la campaña estacional (`Temporada`).

---

## 2. Limpieza de Datos, Feature Engineering y Análisis de Casos Especiales

### 2.1 Reglas de Limpieza y Estandarización Aplicadas
1. **Tratamiento de `Experiencia_Huerta_Clean`:** Estandarización ordinal en 3 niveles: `es la primera vez` (0), `1 a 3 años` (1), `más de 3 años` (2).
2. **Estandarización de `Superficie_Clean`:** Conversión de rangos de texto a categorías uniformes de metros cuadrados (`hasta 5 m2`, `entre 6 y 20 m2`, `más de 20 m2`).
3. **Consolidación de `Tipo_Huerta`:** Unificación de registros en `familiar` vs. `institucional`.
4. **Tratamiento de `Barrio_Localidad` y `Ocupacion_Clean`:** Limpieza de texto y categorización para análisis geográfico y socioeconómico.

### 2.2 Relación entre `Cantidad_Variedades`, `Oferta_Catalogo` y `Tipo_Huerta`
Durante el análisis de datos se identificó que en ciertos registros la `Cantidad_Variedades` solicitada supera el valor de `Oferta_Catalogo` de la temporada (por ejemplo, pidiéndose 25 o 32 sobres cuando el catálogo familiar es de 18 o 17 especies).

* **Explicación del Dominio:** El $100\%$ de los casos donde la cantidad demandada supera la oferta base corresponden a **Huertas Institucionales** (escuelas, comedores comunitarios o centros de salud), las cuales requieren kits múltiples o partidas reforzadas.
* **Tratamiento en la Target (`Cobertura_Catalogo`):** La relación se calcula como:
  $$\text{Cobertura\_Catalogo} = \min\left(100.0, \, \frac{\text{Cantidad\_Variedades}}{\text{Oferta\_Catalogo}} \times 100\right)$$
  De esta forma, cualquier solicitud que iguale o supere el catálogo completo representa el tope máximo de cobertura ($100\%$) y activa la `Alerta_Alta_Demanda = 1`.

### 2.3 Variables Excluidas para Evitar Data Leakage
* `Presupuesto_Estimado`: Se excluye de los predictores en el modelo de regresión de cobertura por presentar dependencia matemática directa con la cantidad de variedades, reservándose para el modelo financiero derivado.
* `Cantidad_Variedades` bruta: Excluida de los predictores del modelo principal por ser el insumo directo del cálculo de la target.

---

## 3. Diccionario de Variables Ampliado (Data Dictionary)

| Nombre de Variable | Tipo de Dato | Rol | Valores Posibles / Descripción |
| :--- | :--- | :--- | :--- |
| `Cobertura_Catalogo` | Numérico ($\mathbb{R}$) | **Target Regresión Principal ($y_1$)** | Porcentaje ($0.0\%$ a $100.0\%$) del catálogo estacional solicitado. |
| `Alerta_Alta_Demanda` | Binario ($\{0, 1\}$) | **Target Clasificación ($y_2$)** | $1$ si `Cobertura_Catalogo` $\ge 75\%$; $0$ en otro caso. |
| `Año` | Entero ($\mathbb{N}$) | Predictor ($X_1$) | Año de la solicitud ($2022$ a $2026$). |
| `Temporada` | Categórico | Predictor ($X_2$) | `OI` (Otoño-Invierno), `PV` (Primavera-Verano). |
| `Oferta_Catalogo` | Entero ($\mathbb{N}$) | Predictor ($X_3$) | Cantidad oficial de variedades del catálogo de la temporada ($7$ a $18$). |
| `Tipo_Huerta` | Categórico | Predictor ($X_4$) | `familiar`, `institucional`. |
| `Tipo_Localizacion` | Categórico | Predictor ($X_5$) | `urbana`, `periurbana`, `rural`. |
| `Experiencia_Huerta_Clean`| Ordinal | Predictor ($X_6$) | `es la primera vez`, `1 a 3 años`, `más de 3 años`. |
| `Superficie_Clean` | Categórico | Predictor ($X_7$) | `hasta 5 m2`, `entre 6 y 20 m2`, `más de 20 m2`. |
| `Destino_Clean` | Categórico | Predictor ($X_8$) | `autoconsumo`, `autoconsumo e intercambio`, `venta / excedentes`. |
| `Ocupacion_Clean` | Categórico | Predictor ($X_9$) | Ocupación laboral (`empleado/a`, `jubilado/a`, `desempleado/a`, etc.). |
| `Barrio_Localidad` | Categórico | Predictor ($X_{10}$) | Barrio o localidad dentro del partido de Chascomús. |
| `Precipitaciones_Hist_mm` | Numérico ($\mathbb{R}$) | Predictor Secundario ($X_{11}$) | Promedio histórico de precipitaciones acumuladas ($mm$) para la temporada. |

---

## 4. Métricas y Protocolo de Evaluación

### 4.1 Métricas de Regresión (`Cobertura_Catalogo`)
* **RMSE (Root Mean Squared Error):** Métrica principal. Penaliza con mayor severidad los errores grandes.
* **MAE (Mean Absolute Error):** Métrica interpretable en puntos porcentuales directos.
* **$R^2$ Score:** Porcentaje de varianza explicada.

### 4.2 Métricas de Clasificación (`Alerta_Alta_Demanda`)
* **Recall (Sensibilidad):** Métrica prioritaria para minimizar los Falsos Negativos (solicitantes de kit completo no detectados).
* **F2-Score:** Métrica sintética que pondera con mayor peso el Recall sobre Precision ($F_2$).
* **Matriz de Costo Total:** $\text{Costo Total} = (1 \times \text{FP}) + (2 \times \text{FN})$.

---

## 5. Modelos Baseline y Resultados Iniciales

### 5.1 Regresión (Baseline Ingenuo: Predicción de la Media)
El modelo predice constantemente el valor promedio de `Cobertura_Catalogo` de entrenamiento ($\bar{y}_{\text{train}} = 79.77\%$).

| Métrica | Conjunto de Entrenamiento | Conjunto de Validación |
| :--- | :---: | :---: |
| **RMSE** | $26.40\%$ | $26.39\%$ |
| **MAE** | $20.12\%$ | $20.15\%$ |
| **$R^2$ Score** | $0.000$ | $-0.001$ |

### 5.2 Clasificación (Baseline Ingenuo: Clase Mayoritaria vs. Aleatorio Estratificado)

| Modelo Baseline | Precision (Clase 1) | Recall (Clase 1) | F1-Score | F2-Score | Falsos Negativos (FN) | Costo Total ($1\text{FP} + 2\text{FN}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Clase Mayoritaria ($y=1$)** | $0.612$ | $1.000$ | $0.759$ | $0.887$ | $0$ | **$212$** |
| **Aleatorio Estratificado** | $0.610$ | $0.612$ | $0.611$ | $0.612$ | $82$ | **$248$** |

---

## 6. Integración en la Arquitectura de Aplicación (`app.py`)

Para garantizar el cumplimiento de las especificaciones técnicas del curso:
1. El archivo `app.py` **cargas los modelos previamente entrenados y guardados en la carpeta `modelos/`** (`modelo_regresion.joblib` y `modelo_clasificacion.joblib`).
2. Se asegura un desacople total entre el pipeline de entrenamiento (`notebooks/entrenamiento.ipynb` / `entrenar_guardar_modelos.py`) y la inferencia web en tiempo real.
3. Se proyecta incorporar en el backend el cálculo del **Modelo Financiero de Presupuesto** y el motor de **Recomendación Pluviométrica** para los desarrollos inmediatos. 