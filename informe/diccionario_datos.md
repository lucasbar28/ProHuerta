# Diccionario de datos

## `solicitudes_v2.csv`

| Variable | Tipo | Descripción |
|---|---|---|
| `id_solicitud` | texto | Identificador único: año-temporada-fila. |
| `archivo_origen` | texto | Archivo Excel de origen. |
| `hoja_origen` | texto | Hoja del Excel. |
| `fila_origen` | entero | Fila de datos en el Excel (incluye encabezado). |
| `referencia` | texto | Referencia original cuando existe. |
| `anio` | entero | Año de la campaña. |
| `temporada` | texto | `OI` u `PV`. |
| `esquema_entrega` | texto | `kit_generico` (2022–2023) o `especifico` (2024–2026). |
| `contenido_kit` | texto | `generico_10` o `especifico`. |
| `target_modelo` | texto | `volumen` para kits genéricos; `cobertura` para específicos. |
| `target_cobertura_valido` | booleano | `True` solo en la era específica. |
| `barrio_raw` | texto | Barrio tal como aparece en el formulario. |
| `barrio_norm` | texto | Barrio normalizado para joins y mapa. |
| `barrio_nombre` | texto | Nombre para mostrar. |
| `localidad_raw` | texto | Localidad original. |
| `localidad_norm` | texto | Localidad normalizada. |
| `lat` | decimal | Latitud (solo 2022–2023). |
| `lng` | decimal | Longitud (solo 2022–2023). |
| `tipo_localizacion` | texto | `urbana`, `periurbana`, `rural`, `no especificado`. |
| `tipo_huerta` | texto | `familiar`, `institucional`, `no especificado`. |
| `experiencia` | texto | `primera vez`, `1 a 3 años`, `más de 3 años`, `no especificado`. |
| `superficie` | texto | `hasta 5 m2`, `entre 6 y 20 m2`, `más de 20 m2`, `no especificado`. |
| `destino` | texto | `autoconsumo`, `autoconsumo e intercambio`, `venta / excedentes`, `no especificado`. |
| `ocupacion` | texto | Ocupación agrupada. |
| `anio_vinculacion` | entero | Año de vinculación al programa (2022–2023). |
| `antiguedad_programa` | entero | Años vinculado al programa. |
| `kits` | decimal | Kits entregados en 2022–2023; nulo si no hay dato. |
| `cantidad_variedades` | decimal | Especies distintas solicitadas en 2024–2026. |
| `especies_equivalentes` | decimal | `kits × 10` o `cantidad_variedades`. |
| `oferta_catalogo` | entero | Especies ofrecidas en la temporada. |
| `cobertura_catalogo` | decimal | `min(100, especies_equivalentes / oferta × 100)`, solo era específica. |
| `cobertura_equivalente_generica` | decimal | 100 si el kit genérico tiene al menos 1 kit; 0 si tiene 0. |
| `alerta_alta_demanda` | entero | 1 si cobertura ≥ 75; nulo en era genérica. |
| `presupuesto_estimado` | decimal | `especies_equivalentes × 500`. |
| `flags_calidad` | texto | Alertas de calidad separadas por `;`. |

## `solicitud_especies.csv`

Una fila por solicitud y especie observada (2024–2026).

| Variable | Descripción |
|---|---|
| `id_solicitud` | Solicitud de origen. |
| `anio`, `temporada` | Campaña. |
| `barrio_norm`, `barrio_nombre` | Barrio normalizado y visible. |
| `tipo_huerta`, `tipo_localizacion`, `experiencia`, `superficie`, `destino`, `ocupacion` | Perfil del solicitante. |
| `especie` | Especie canónica. |
| `especie_nombre` | Nombre para mostrar. |
| `especie_raw` | Texto original del formulario. |
| `cantidad_sobres` | Sobres solicitados (1 por especie observada). |
| `origen` | `observada`. |
| `metodo` | `observada`. |
| `fuente_archivo` | Archivo de origen. |

## `solicitud_especies_imputada.csv`

Una fila por solicitud genérica y especie de la canasta OI.

| Variable | Descripción |
|---|---|
| `id_solicitud` | Solicitud genérica de origen. |
| `especie`, `especie_nombre` | Especie de la canasta. |
| `cantidad_sobres` | `kits` de la solicitud. |
| `origen` | `imputada`. |
| `metodo` | `top10_OI_2025_2026`. |
| `confianza` | `baja`. |
| `canasta_version` | Versión de la canasta. |

## `catalogo_temporada.csv`

| Variable | Descripción |
|---|---|
| `anio`, `temporada` | Campaña. |
| `esquema_entrega` | `kit_generico` o `especifico`. |
| `oferta_catalogo` | Especies ofrecidas. |
| `especies_por_kit` | 10 para kits genéricos. |
| `valor_sobre` | 500 pesos por sobre. |
| `fuente` | Archivo de origen. |

## Fórmulas

- `especies_equivalentes = kits × 10` en 2022–2023.
- `especies_equivalentes = cantidad_variedades` en 2024–2026.
- `presupuesto_estimado = especies_equivalentes × 500`.
- `cobertura_catalogo = min(100, especies_equivalentes / oferta_catalogo × 100)`.
- `alerta_alta_demanda = 1` si `cobertura_catalogo >= 75`, si no `0`.
