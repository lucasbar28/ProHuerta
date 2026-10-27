# Auditoría de Datos y Reconciliación - ProHuerta Chascomús

---

## Integrantes del Grupo
* **Integrante 1:** Lucas Barreu
* **Integrante 2:** Franco Quiroga
* **Integrante 3:** Marcelo Pérez Cazal

---

## 1. Fuentes y Volumetría Histórica

El pipeline de preparación (`preparar_datos.py`) consolida la información histórica de entregas de semillas en el Partido de Chascomús abarcando 7 campañas estacionales:

| Año | Temporada | Archivo de Origen | Hoja / Pestaña | Filas Procesadas |
| :---: | :---: | :--- | :--- | :---: |
| 2022 | OI | `2022 registro de huerta otoño-invierno 2022.xlsx` | general | 488 |
| 2023 | OI | `2023 Relevamiento otoño invierno para filtrar.xlsx` | DATOS | 750[cite: 25] |
| 2024 | PV | `2024 retiro de semillas prim-ver. 2024. + seguiminento + devolución.xlsx` | familiares | 273[cite: 25] |
| 2025 | OI | `2025 RETIRO de semillas 2025 por primera vez OI 2025 (respuestas).xlsx` | Respuestas de formulario 1 | 295[cite: 25] |
| 2025 | PV | `2025 retiro de semillas por primera vez PV 2025 (respuestas).xlsx` | Respuestas de formulario 1 | 464[cite: 25] |
| 2026 | OI | `2026 Retiro de semillas por primera vez O-I 2026 (respuestas).xlsx` | Respuestas de formulario 1 | 237[cite: 25] |
| 2026 | PV | `2026 Retiro de semillas P-V 2026 (respuestas).xlsx` | Respuestas de formulario 1 | 223[cite: 25] |

* **Total de solicitudes consolidadas:** **2.730 registros**[cite: 25].
* **Kits genéricos (Era 2022–2023):** **1.238 registros**[cite: 25].
* **Entregas específicas (Era 2024–2026):** **1.492 registros**[cite: 25].

---

## 2. Controles de Calidad y Reconciliación

| Métrica de Control Técnico | Valor Absoluto / Resultado |
| :--- | :---: |
| Solicitudes totales validadas | 2.730[cite: 25] |
| Registros 2022–2023 sin dato explícito de kits | 193[cite: 25] |
| Registros 2022–2023 con 0 kits reales | 8[cite: 25] |
| Registros 2024–2026 sin texto descriptivo de especies | 5[cite: 25] |
| Registros 2024–2026 con conteo de 0 especies | 1[cite: 25] |
| Solicitudes sin asignación de barrio (`sin_dato`) | 786[cite: 25] |
| Solicitudes con geolocalización (coordenadas) | 969[cite: 25] |
| Solicitudes genéricas con demanda imputada por canasta | 1.037[cite: 25] |
| Sobres equivalentes totales imputados (`kits` $\times$ 10) | 14.080[cite: 25] |

---

## 3. Distribución por Esquema y Campaña

| Esquema de Entrega | Filas Totales | Cobertura Media (%) | Alerta Media | Especies Equivalentes Medias | Presupuesto Estimado ($) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Específico (2024–2026)** | 1.492[cite: 25] | 62.84%[cite: 25] | 0.409[cite: 25] | 7.74[cite: 25] | $5.754.500[cite: 25] |
| **Kit Genérico (2022–2023)** | 1.238[cite: 25] | N/A (Imputada) | N/A | 13.47[cite: 25] | $7.040.000[cite: 25] |

---

## 4. Top de Especies Canónicas Observadas (Otoño-Invierno)

Construido sobre las solicitudes observadas de las temporadas OI 2025 y OI 2026:

1. **Perejil:** 451 solicitudes (85.1%)[cite: 25]
2. **Acelga:** 441 solicitudes (83.2%)[cite: 25]
3. **Lechuga:** 429 solicitudes (80.9%)[cite: 25]
4. **Cebolla:** 348 solicitudes (65.7%)[cite: 25]
5. **Remolacha:** 345 solicitudes (65.1%)[cite: 25]
6. **Espinaca:** 340 solicitudes (64.2%)[cite: 25]
7. **Flor:** 249 solicitudes (47.0%)[cite: 25]
8. **Rabanito:** 247 solicitudes (46.6%)[cite: 25]
9. **Habas:** 237 solicitudes (44.7%)[cite: 25]
10. **Rúcula:** 155 solicitudes (29.2%)[cite: 25] 