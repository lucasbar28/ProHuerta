# Resultados de modelos de demanda de semillas

Generado el 2026-10-24 por `entrenar_guardar_modelos.py`.

## 1. Alcance y unidad

- Unidad de predicción: **sobre equivalente = variedad solicitada**.
- Target de regresión: `especies_equivalentes` (sobres/variedades por solicitud).
- Precio fijo: **$500 por sobre**; presupuesto = sobres × 500.
- La oferta del catálogo **no** es predictora ni target: ese cálculo pertenece al módulo de cobertura de catálogo y no a esta proyección de semillas.
- Entrenamiento: solicitudes específicas 2024-2026. Se excluyen 2022-2023 porque son kits genéricos con especies imputadas (`kits × 10`), no variedades observadas.

## 2. Variables usadas

- `anio_idx` (año - 2024), `temporada` y perfil socio-productivo: tipo de huerta, localización, experiencia, superficie, destino y ocupación.
- Se excluyen `barrio`, `oferta_catalogo`, `cobertura_catalogo`, `presupuesto_estimado` y cualquier variable derivada del target para evitar fuga de información.

## 3. Partición 60/20/20

- Entrenamiento: 892 filas.
- Validación: 297 filas.
- Test: 298 filas.
- Total: 1487 filas.
- Estratificación: temporada + año + tercil de demanda. Cada combinación conserva la proporción de años, temporadas y niveles de demanda.

## 4. Comparación de modelos

Criterio de selección: menor RMSE en validación.

| Variante | RMSE | MAE | R2 |
|---|---:|---:|---:|
| KNeighborsRegressor: k=41, weights=uniform | 3.543 | 2.669 | 0.1957 |
| KNeighborsRegressor: k=21, weights=uniform | 3.583 | 2.693 | 0.1775 |
| Ridge: alpha=1000.0 | 3.605 | 2.706 | 0.1669 |
| RandomForestRegressor: depth=6, leaf=3, features=sqrt | 3.626 | 2.699 | 0.1575 |
| RandomForestRegressor: depth=6, leaf=5, features=sqrt | 3.632 | 2.711 | 0.1549 |
| RandomForestRegressor: depth=4, leaf=3, features=sqrt | 3.634 | 2.718 | 0.1538 |
| RandomForestRegressor: depth=4, leaf=10, features=sqrt | 3.635 | 2.714 | 0.1534 |
| RandomForestRegressor: depth=4, leaf=5, features=sqrt | 3.635 | 2.718 | 0.1532 |
| RandomForestRegressor: depth=None, leaf=5, features=sqrt | 3.641 | 2.706 | 0.1505 |
| RandomForestRegressor: depth=6, leaf=10, features=sqrt | 3.644 | 2.719 | 0.1490 |
| RandomForestRegressor: depth=None, leaf=10, features=sqrt | 3.649 | 2.719 | 0.1466 |
| RandomForestRegressor: depth=4, leaf=20, features=sqrt | 3.649 | 2.727 | 0.1465 |

Modelo seleccionado: **KNeighborsRegressor** con `{"n_neighbors": 41, "weights": "uniform"}`.
Validación cruzada de 5 folds sobre train: RMSE = 2.865.

## 5. Desempeño y sobreajuste

| Conjunto | RMSE | MAE | R2 |
|---|---:|---:|---:|
| Train | 2.793 | 2.119 | 0.4466 |
| Validación (crudo) | 3.543 | 2.669 | 0.1957 |
| Validación (calibrado) | 3.498 | 2.652 | 0.2158 |
| Test (crudo) | 3.327 | 2.574 | 0.0999 |
| Test (calibrado) | 3.393 | 2.602 | 0.0644 |

- Brecha train-test de R2: **0.3822**.
- Si la brecha es grande, el modelo está memorizando; por eso se comparan árboles regularizados, modelos lineales y un baseline dummy.

## 6. Calibración

Factor de calibración por temporada aplicado a la predicción cruda, estimado en validación:

| Temporada | Factor |
|---|---:|
| OI | 1.0815 |
| PV | 1.0745 |

## 7. Backtest temporal

Se reentrena el modelo seleccionado solo con 2024-2025 y se evalúa en 2026, para medir comportamiento fuera del año de entrenamiento.

| Métrica | Modelo | Baseline naive |
|---|---:|---:|
| RMSE | 5.296 | 5.500 |
| MAE | 4.006 | 4.073 |

## 8. Baseline esperado y regla de alerta

- Para cada barrio y temporada se calcula la **media anual histórica de sobres** usando todos los años con barrio disponible; las solicitudes esperadas parten del **último año observado**.
- `crecimiento_temporada` = mediana de las variaciones interanuales de la demanda específica de la temporada, acotada a [-5%, +5%].
- `esperado(anio) = media_anual_sobres × (1 + crecimiento_temporada)^(anio - último_año_observado)`.
- `predicho(anio) = solicitudes_esperadas(anio) × predicción_media_por_solicitud(anio)`.
- `solicitudes_esperadas(anio) = solicitudes_del_último_año_observado × (1 + crecimiento_temporada)^(anio - último_año_observado)`.
- `alerta_sobredemanda = 1` si `predicho > esperado × (1 + 10%)` **y** `predicho - esperado >= 10 sobres`; si no, 0.
- El baseline ya incorpora el crecimiento esperado; el margen de 10% y el mínimo de 10 sobres evitan alertas por ruido en barrios pequeños.

| Temporada | Crecimiento anual usado |
|---|---:|
| OI | 5.00% |
| PV | 5.00% |

## 9. Limitaciones

- El modelo predice demanda por solicitud; para proyectar el total se usan las solicitudes esperadas del baseline.
- 2024 y 2025 OI no tienen barrio, por lo que el baseline barrial usa solo los años con barrio disponible. Esto se explicita en la UI.
- 2027-2028 no tienen perfiles futuros observados: se aplican los perfiles históricos de cada barrio/temporada. Es un escenario, no una extrapolación de tendencia.
- La alerta es una regla de decisión sobre la predicción vs. el baseline; no es una probabilidad calibrada de eventos futuros.
- El precio de $500 por sobre es fijo por supuesto del trabajo, no un precio de mercado observado.

## 10. Artefactos

- `modelos/modelo_regresion.joblib`
- `modelos/metadata_modelos.json`
- `informe/comparacion_regresion.csv`
- `informe/predicciones_test.csv`
