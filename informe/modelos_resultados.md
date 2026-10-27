# Evaluación de Modelos y Rendimiento Predictivo - ProHuerta Chascomús

---

## Integrantes del Grupo
* **Integrante 1:** Lucas Barreu
* **Integrante 2:** Franco Quiroga
* **Integrante 3:** Marcelo Pérez Cazal

---

## 1. Alcance y Definición de la Variable Objetivo (Target)
* **Unidad de Predicción:** Sobre equivalente (variedad solicitada).
* **Target de Regresión Principal:** `especies_equivalentes` / Cobertura porcentual del catálogo estacional.
* **Criterio Económico:** Valor fijo de referencia de **$500 ARS** por sobre equivalente para la proyección presupuestaria.
* **Filtro de Entrenamiento:** Se utilizan exclusivamente las solicitudes específicas (2024–2026, $N = 1.487$ registros limpios), excluyendo los kits genéricos de 2022–2023 para evitar sesgos por imputación masiva.

---

## 2. Protocolo de Partición y Prevención de Data Leakage
El conjunto de datos modelado se dividió bajo un esquema estricto de validación cruzada y partición estratificada:
* **Entrenamiento (Train - 60%):** 892 observaciones.
* **Validación (Validation - 20%):** 297 observaciones[cite: 30].
* **Evaluación Final (Test - 20%):** 298 observaciones[cite: 30].
* **Estratificación:** Combinada por temporada, año y tercil de demanda para preservar la proporción de clases y evitar fugas de información interanual.

---

## 3. Comparativa de Algoritmos Evaluados (Regresión)

| Algoritmo e Hiperparámetros | RMSE (Validación) | MAE (Validación) | $R^2$ (Validación) |
| :--- | :---: | :---: | :---: |
| **KNeighborsRegressor ($k=41$, weights=uniform)** | **3.543**[cite: 30] | **2.669**[cite: 30] | **0.1957**[cite: 30] |
| KNeighborsRegressor ($k=21$, weights=uniform) | 3.583[cite: 30] | 2.693[cite: 30] | 0.1775[cite: 30] |
| Ridge Regression ($\alpha=1000.0$) | 3.605[cite: 30] | 2.706[cite: 30] | 0.1669[cite: 30] |
| RandomForestRegressor (depth=6, leaf=3) | 3.626[cite: 30] | 2.699[cite: 30] | 0.1575[cite: 30] |
| RandomForestRegressor (depth=4, leaf=5) | 3.635[cite: 30] | 2.718[cite: 30] | 0.1532[cite: 30] |

* **Modelo Seleccionado:** **`KNeighborsRegressor`** con optimización de vecinos y ponderación uniforme, por ofrecer el menor error cuadrático medio en el conjunto de validación independiente[cite: 30].

---

## 4. Desempeño General y Calibración Estacional

| Conjunto de Evaluación | RMSE | MAE | $R^2$ Score |
| :--- | :---: | :---: | :---: |
| **Train** | 2.793[cite: 30] | 2.119[cite: 30] | 0.4466[cite: 30] |
| **Validación (Calibrado)** | 3.498[cite: 30] | 2.652[cite: 30] | 0.2158[cite: 30] |
| **Test (Calibrado)** | 3.393[cite: 30] | 2.602[cite: 30] | 0.0644[cite: 30] |

* **Factores de Calibración Aplicados:** Se ajustó un factor estacional específico para corregir desvíos globales en las predicciones crudas (**1.0815** para Otoño-Invierno y **1.0745** para Primavera-Verano)[cite: 30].

---

## 5. Reglas de Decisión Operativa y Sistema de Alertas
* **Criterio de Sobredemanda Barrial:** Se activa una alerta logística (`alerta_sobredemanda = 1`) cuando el volumen proyectado supera en un $10\%$ al baseline histórico esperado **y** la diferencia absoluta es igual o mayor a $10$ sobres equivalentes[cite: 30]. Esto previene falsas alarmas en asentamientos pequeños impulsadas por variaciones estacionales de baja significancia. 