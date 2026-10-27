# Auditoría de datos ProHuerta

Generado por `preparar_datos.py` el 2026-10-22.

## 1. Fuentes y filas

| Año | Temporada | Archivo | Hoja | Filas |
|---:|---|---|---|---:|
| 2022 | OI | 2022 registro de huerta otoño-invierno 2022.xlsx | general | 488 |
| 2023 | OI | 2023 Relevamiento otoño invierno para filtrar.xlsx | DATOS | 750 |
| 2024 | PV | 2024 retiro de semillas prim-ver. 2024. + seguiminento + devolución.xlsx | familiares | 273 |
| 2025 | OI | 2025 RETIRO de semillas 2025 por primera vez OI 2025 (respuestas).xlsx | Respuestas de formulario 1 | 295 |
| 2025 | PV | 2025 retiro de semillas por primera vez PV 2025 (respuestas).xlsx | Respuestas de formulario 1 | 464 |
| 2026 | OI | 2026 Retiro de semillas por primera vez O-I 2026 (respuestas).xlsx | Respuestas de formulario 1 | 237 |
| 2026 | PV | 2026 Retiro de semillas P-V 2026 (respuestas).xlsx | Respuestas de formulario 1 | 223 |

Total de solicitudes: **2730**.
Kits genéricos (2022–2023): **1238**.
Entregas específicas (2024–2026): **1492**.

## 2. Reconciliación y calidad

| Control | Valor |
|---|---:|
| Solicitudes totales | 2730 |
| Filas de 2022–2023 sin dato de kits | 193 |
| Filas de 2022–2023 con 0 kits reales | 8 |
| Filas de 2024–2026 sin texto de especies | 5 |
| Filas de 2024–2026 con 0 especies | 1 |
| Solicitudes con barrio sin dato | 786 |
| Solicitudes con coordenadas | 969 |
| Solicitudes genéricas con demanda imputada | 1037 |
| Sobres equivalentes imputados (kits × 10) | 14080 |

El CSV anterior calculaba `Cantidad_Variedades = max(kits, 1) × 7` para 2022–2023. Esta versión conserva `kits` como dato original, deja nulos los faltantes y usa `especies_equivalentes = kits × 10`, que es la regla acordada para el kit genérico.

## 3. Distribución por esquema

| Esquema | Filas | Cobertura media | Alerta media | Especies equivalentes medias | Presupuesto total |
|---|---:|---:|---:|---:|---:|
| especifico | 1492 | 62.84 | 0.409 | 7.74 | 5,754,500 |
| kit_generico | 1238 | nan | <NA> | 13.47 | 7,040,000 |

## 4. Distribución por año y temporada

| Año | Temporada | Filas | Cobertura media | Alerta media | Especies equivalentes medias |
|---:|---|---:|---:|---:|---:|
| 2022 | OI | 488 | nan | <NA> | 14.06 |
| 2023 | OI | 750 | nan | <NA> | 13.21 |
| 2024 | PV | 273 | 62.14 | 0.385 | 5.59 |
| 2025 | OI | 295 | 69.43 | 0.478 | 6.25 |
| 2025 | PV | 464 | 69.45 | 0.545 | 8.33 |
| 2026 | OI | 237 | 49.54 | 0.177 | 8.52 |
| 2026 | PV | 223 | 55.43 | 0.309 | 10.23 |

## 5. Canasta OI de referencia

Construida con las solicitudes observadas de 2025 OI y 2026 OI (451 solicitudes como máximo por especie).

| Rank | Especie | Solicitudes | % de solicitudes | En canasta top 10 |
|---:|---|---:|---:|---|
| 1 | Perejil | 451 | 85.1% | Sí |
| 2 | Acelga | 441 | 83.2% | Sí |
| 3 | Lechuga | 429 | 80.9% | Sí |
| 4 | Cebolla | 348 | 65.7% | Sí |
| 5 | Remolacha | 345 | 65.1% | Sí |
| 6 | Espinaca | 340 | 64.2% | Sí |
| 7 | Flor | 249 | 47.0% | Sí |
| 8 | Rabanito | 247 | 46.6% | Sí |
| 9 | Habas | 237 | 44.7% | Sí |
| 10 | Rúcula | 155 | 29.2% | Sí |
| 11 | Puerro | 119 | 22.5% | No |
| 12 | Caléndula | 99 | 18.7% | No |
| 13 | Brócoli | 85 | 16.0% | No |
| 14 | Zanahoria | 78 | 14.7% | No |
| 15 | Arveja | 76 | 14.3% | No |

## 6. Top de especies observadas

### OI

| Especie | Solicitudes |
|---|---:|
| Perejil | 451 |
| Acelga | 441 |
| Lechuga | 429 |
| Cebolla | 348 |
| Remolacha | 345 |
| Espinaca | 340 |
| Flor | 249 |
| Rabanito | 247 |
| Habas | 237 |
| Rúcula | 155 |

### PV

| Especie | Solicitudes |
|---|---:|
| Tomate | 775 |
| Lechuga | 761 |
| Albahaca | 725 |
| Acelga | 717 |
| Perejil | 712 |
| Rúcula | 662 |
| Morrón | 583 |
| Zapallo de tronco | 516 |
| Berenjena | 476 |
| Rabanito | 292 |

## 7. Top de barrios

| Barrio | Solicitudes | Con coordenadas | Años |
|---|---:|---:|---|
| Sin dato | 786 | 3 | 2022, 2023, 2024, 2025, 2026 |
| Centro | 181 | 114 | 2022, 2023, 2025, 2026 |
| El Hueco | 176 | 102 | 2022, 2023, 2025, 2026 |
| San Cayetano | 156 | 67 | 2022, 2023, 2025, 2026 |
| Noria Chica | 144 | 71 | 2022, 2023, 2025, 2026 |
| Ipora | 120 | 70 | 2022, 2023, 2025, 2026 |
| 30 de Mayo | 86 | 35 | 2022, 2023, 2025, 2026 |
| Fátima | 75 | 46 | 2022, 2023, 2025, 2026 |
| Acceso Norte | 67 | 45 | 2022, 2023, 2025, 2026 |
| F. Moreno | 60 | 56 | 2022, 2023, 2026 |
| San Luis | 58 | 26 | 2022, 2023, 2025, 2026 |
| Escribano | 54 | 33 | 2022, 2023, 2025, 2026 |
| El Algarrobo | 52 | 33 | 2022, 2023, 2025, 2026 |
| Barrio Jardín | 42 | 24 | 2022, 2023, 2025, 2026 |
| Lomas Altas | 39 | 10 | 2022, 2023, 2025, 2026 |

## 8. Flags de calidad

| Flag | Filas |
|---|---:|
| sin_coordenadas | 1761 |
| demanda_especies_imputada | 1037 |
| experiencia_no_especificada | 868 |
| barrio_sin_dato | 786 |
| sin_dato_kits | 193 |
| superficie_no_especificada | 46 |
| destino_no_especificado | 42 |
| localidad_fuera_chascomus | 28 |
| cero_kits | 8 |
| sin_especies | 5 |
| ocupacion_no_especificada | 3 |
| cero_especies | 1 |
| tokens_invalidos:4 paquetes | 1 |

## 9. Supuestos y limitaciones

- `valor_sobre = 500` es constante para todas las temporadas.
- Cada kit genérico de 2022–2023 contiene 10 especies surtidas.
- La canasta de 10 especies para 2022–2023 es una **imputación** basada en 2025 OI + 2026 OI; no es un dato observado.
- 2024 no tiene barrio en el formulario original; 2025 OI tampoco. Esas filas quedan con `barrio_sin_dato`.
- 2024 no tiene tipo de huerta en el formulario original; queda `no especificado`.
- Las filas 2022–2023 no tienen experiencia hortícola detallada; solo se marca `primera vez` cuando el formulario lo indica.
- No se eliminó ninguna fila.

## 10. Archivos generados

| Archivo | Contenido |
|---|---|
| `datos/preparados/solicitudes_v2.csv` | Una fila por solicitud, con targets y flags. |
| `datos/preparados/solicitud_especies.csv` | Especies observadas 2024–2026. |
| `datos/preparados/solicitud_especies_imputada.csv` | Canasta imputada 2022–2023. |
| `datos/preparados/solicitud_especies_completa.csv` | Unión de observadas e imputadas. |
| `datos/preparados/canasta_oi_referencia.csv` | Ranking de especies OI. |
| `datos/preparados/catalogo_temporada.csv` | Oferta y precio por temporada. |
| `datos/preparados/dim_barrios.csv` | Barrios, conteos y centroides. |
| `informe/diccionario_datos.md` | Diccionario y fórmulas. |

## 11. Reproducibilidad

```powershell
python preparar_datos.py
```
