# TRABAJO PRÁCTICO INTEGRADOR: MODELOS DE APRENDIZAJE AUTOMÁTICO
**Propuesta del Proyecto, Enfoque Multi-Modelo y Evaluación de Alternativas (Entrega 1 - Recombinada)**

---

## Integrantes del Grupo
* **Integrante 1:** Lucas Barreu
* **Integrante 2:** Franco Quiroga
* **Integrante 3:** Marcelo Pérez Cazal

---

## 1. Ficha Técnica del Proyecto Seleccionado

| Campo | Definición Técnica |
| :--- | :--- |
| **Nombre del proyecto** | Ecosistema Inteligente de Planificación Logística, Presupuestación y Demanda Espacio-Temporal para el Banco Municipal de Semillas / ProHuerta (Chascomús) |
| **Problema** | En las campañas estacionales de entrega de semillas agroecológicas (Otoño-Invierno y Primavera-Verano) en Chascomús, la cantidad y diversidad de variedades que solicitará cada participante varía ampliamente según sus características socio-productivas, el tipo de huerta y las dimensiones de su predio. La falta de anticipación dificulta la preparación óptima de insumos, la asignación presupuestaria y la programación de asistencia técnica territorial. |
| **Usuario de la predicción** | Coordinadores logísticos, promotores territoriales del Banco de Intercambio de Semillas y la Dirección de Ambiente y Desarrollo Sustentable de la Municipalidad de Chascomús. |
| **Decisiones que permitirá tomar** | **En Logística y Stock:** Anticipar la demanda alta ($\ge 75\%$ de cobertura) para empaquetado previo de kits completos vs. kits básicos estándar.<br>**En Presupuestación Financiera:** Calcular el costo financiero estimado asignando un valor fijo indexado por variedad/sobre de semilla.<br>**En Planificación Territorial:** Visualizar en un **mapa 3D** las zonas/barrios con mayor incremento de demanda respecto a su histórico.<br>**En Recomendación Agroecológica:** Sugerir pautas de cultivo y riego personalizadas según la anomalía y porcentaje de precipitaciones históricas de la zona. |
| **Qué representa cada fila** | Una solicitud individual de retiro de semillas realizada por un responsable de huerta (familiar o institucional) en una temporada y localidad específica. |
| **Momento exacto de la predicción** | Al momento en que el participante completa el formulario de inscripción/solicitud, antes de la selección, empaquetado, asignación presupuestaria y entrega física de los insumos. |
| **Arquitectura de Modelos** | **Modelo 1 (Principal):** Regresión para `% Cobertura_Catalogo` y Clasificación para `Alerta_Alta_Demanda` ($\ge 75\%$).<br>**Modelo 2:** Estimador de Presupuesto ($) multiplicando la demanda por un valor unitario fijo.<br>**Modelo 3:** Agregación espacio-temporal de demanda proyectada por `Barrio_Localidad`.<br>**Módulo Prescripcional:** Motor de recomendación alimentado por el histórico de lluvias acumuladas. |
| **Justificación del umbral ($\ge 75\%$)** | Un $75\%$ de cobertura equivale a solicitar al menos 3 de cada 4 variedades del catálogo oficial. Es el punto de inflexión operativo en el que al programa le conviene empaquetar de forma anticipada el kit completo en lugar de armarlo a pedido en mostrador. |
| **Fuente de datos** | Formularios de inscripción del ProHuerta / Banco de Semillas de Chascomús (temporadas 2022 a 2026, $N = 2.730$ registros) junto a datos pluviométricos históricos locales. |
| **Variables disponibles ($t=0$)** | Predictores socio-productivos y geográficos: Temporada, Oferta del Catálogo, Tipo de Huerta, Tipo de Localización, Experiencia, Superficie ($m^2$), Destino, Ocupación, Barrio/Localidad y Precipitaciones Históricas. |
| **Posibles fugas (Data Leakage)** | `Presupuesto_Estimado` y la cantidad exacta bruta solicitada (se remueven de los predictores en la etapa de entrenamiento), así como métricas de germinación posteriores. |

---

## 2. Evaluación de Alternativas Consideradas

De acuerdo con las sugerencias docentes y el análisis de factibilidad, se evaluaron tres líneas de desarrollo:

| Campo | A. Ecosistema de Cobertura y Demanda (SELECCIONADA) | B. Éxito de Germinación y Cultivo | C. Volumen Único de Kits Entregados |
| :--- | :--- | :--- | :--- |
| **Problema** | Anticipar la diversidad solicitada, presupuestar costos y mapear espacialmente la demanda en 3D. | Detectar huertas con riesgo de baja germinación para enviar asistencia técnica preventiva. | Anticipar el total de cajas físicas a despachar por punto de entrega. |
| **Usuario** | Coordinadores logísticos, financistas municipales y promotores técnicos. | Promotores técnicos de campo. | Coordinadores generales de transporte. |
| **Decisión** | Armado previo de kits, asignación de presupuesto y planificación barrial con alertas climáticas. | Programar visitas prioritarias de acompañamiento técnico post-siembra. | Planificar la compra y flete de insumos generales por zona. |
| **Métrica Principal** | Cobertura Porcentual (%), Alerta Binaria ($\ge 75\%$), Costo Estimado ($) y Demanda/Barrio. | Porcentaje de especies sembradas que germinaron (%). | Cantidad total de kits físicos entregados. |
| **Fuente y Tamaño** | Registros 2022–2026: **2.730 solicitudes** procesadas e integradas. | Seguimientos 2023–2024: menos de 100 registros con dato real de germinación. | Registros 2022–2023: 1.045 filas. |
| **Riesgos** | Variaciones bruscas en el stock nacional/provincial provisto. | Muestra insuficiente ($<100$ casos) y alto sesgo de respuesta. | El $90\%$ de los registros retira exactamente 1 kit (varianza casi nula). |
| **Veredicto** | **ELEGIDA Y AMPLIADA** | **DESCARTADA** | **DESCARTADA** |

---

## 3. Arquitectura del Flujo de Trabajo (Entrenamiento vs. Predicción)

Para cumplir con las buenas prácticas de desarrollo y los requisitos del curso, el flujo del sistema se estructura en dos fases totalmente aisladas:

1. **Fase Offline / Batch (Entrenamiento y Generación de Artefactos):**
   * Limpieza de datos, ingeniería de variables y balanceo.
   * Entrenamiento de los distintos algoritmos de machine learning en Jupyter Notebooks (`notebooks/entrenamiento.ipynb`).
   * Exportación de los pipelines entrenados en formato serilizado (`modelos/modelo_regresion.joblib` y `modelos/modelo_clasificacion.joblib`).
2. **Fase Online / Producción (Aplicación Web Flask):**
   * El archivo `app.py` **NO entrena modelos en tiempo de ejecución**.
   * Carga los artefactos `.joblib` previamente compilados.
   * Procesa las entradas del usuario desde la interfaz HTML (`templates/index.html`), ejecuta la función `.predict()` y proyecta los resultados (incluyendo la vista geoespacial 3D).

---

## 4. Esquema de Costos para la Toma de Decisiones

En la gestión del Banco de Semillas, la matriz de confusión del clasificador tiene implicancias sociales y presupuestarias directas:

* **Falso Positivo (FP):** El modelo predice **Alta Demanda ($\ge 75\%$)**, pero el participante solicita un kit acotado.
  * *Consecuencia:* Se empaquetó un kit completo por adelantado. Los sobres no retirados se reasignan rápidamente al siguiente solicitante.
  * *Costo asignado:* **1 unidad** (costo operativo menor de almacenamiento temporal).
* **Falso Negativo (FN):** El modelo predice **Demanda Estándar ($< 75\%$)**, pero el participante solicitaba un kit completo.
  * *Consecuencia:* Faltan variedades en el mostrador. La familia se retira con insumos incompletos, afectando la diversidad de la huerta familiar.
  * *Costo asignado:* **2 unidades** (el doble por el impacto en la seguridad alimentaria).

$$\text{Costo Total del Sistema} = (1 \times \text{FP}) + (2 \times \text{FN})$$

---

## 5. Bitácora de Ajustes y Planificación (Corto y Mediano Plazo)

| h/Fecha | Decisión / Ajuste | Justificación Técnico-Metodológica | Estado |
| :--- | :--- | :--- | :--- |
| **15/10/2026** | Selección de `Cobertura_Catalogo` y `Alerta_Alta_Demanda` como baseline. | Permite normalizar las solicitudes independientemente de la oferta cambiante de cada temporada. | Implementada |
| **20/10/2026** | Separación estricta de la fase de entrenamiento y desacople de `app.py`. | Garantiza tiempos de respuesta en milisegundos en producción y evita recalcular modelos por cada petición HTTP. | Implementada |
| **20/10/2026** | Incorporación de Modelo Financiero (Presupuesto con Valor Fijo). | Permite estimar el costo económico de las partidas asignando un valor fijo indexado por sobre de semilla. | Planificada (Corto Plazo) |
| **20/10/2026** | Integración de Precipitaciones Históricas de Chascomús. | Permite incorporar un módulo prescripcional para recomendar pautas de riego y protección del cultivo. | Planificada (Corto Plazo) |
| **20/10/2026** | Desarrollo de Mapa 3D de Demanda por Barrio (`Barrio_Localidad`). | Visualizar mediante barras extruidas en 3D el incremento porcentual de la demanda proyectada respecto al histórico local. | Planificada (Mediano Plazo) | 