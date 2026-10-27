El núcleo técnico ya está funcionando: pipeline de datos, modelos, API Flask, dashboard Deck.gl, proyecciones, gráficos y sidebar validados localmente. Lo que falta es cerrar la entrega, corregir documentación y asegurar el despliegue.
Prioridad alta
1. Informe final integrado: no existe. Falta un documento único con problema, objetivos, usuarios, datos, limpieza, EDA, modelos, métricas, umbral/costos, Modelo 2, Modelo 3, arquitectura, capturas del dashboard, despliegue, conclusiones, limitaciones y trabajo futuro.
2. Actualizar la Entrega 2: está desactualizada e inconsistente.
- Dice 2.730 filas y split 1.638/546/546; el modelo real usa 1.487 filas y split 892/297/298 (informe/Entrega_2...:18 vs. modelos/metadata_modelos.json:5).
- Los baselines y métricas no coinciden con los modelos finales.
- Menciona Barrio_Localidad y Precipitaciones_Hist_mm como predictores, pero el modelo real no los usa (informe/Entrega_2...:64-65).
- Menciona notebooks/entrenamiento.ipynb, que no existe (informe/Entrega_2...:107).
- El archivo quedó con nombre (1) y el original figura eliminado en Git; conviene limpiar nombre y contenido.
3. Despliegue en Vercel: no está hecho ni verificado.
- vercel no está instalado/autenticado.
- vercel.json no declara includeFiles para templates/, static/, datos/preparados/ y modelos/; hay que confirmar que el bundle de @vercel/python los incluya.
- Falta fijar versión de Python/runtime compatible con las dependencias exactas.
- Falta una URL pública y smoke tests de /, /api/health, /api/mapa_completo y /api/consulta_especifica.
- Falta .vercelignore para excluir datos crudos, informe/ y __pycache__.
4. Privacidad de datos: los Excel originales contienen datos sensibles, por ejemplo Mail del beneficiario en el archivo 2023. Están sin trackear en Git, pero un git add . o un deploy de Vercel podría incluirlos. Hay que excluirlos explícitamente.
5. README: está vacío (README.md:1). Falta instalación, ejecución, estructura del proyecto, comandos de reproducción, endpoints, versiones y despliegue.
6. Notebook: la guía técnica pide entrenamiento en Jupyter (tareapendiente.md:11), pero solo existe entrenar_guardar_modelos.py. Hay que crear el notebook o justificar formalmente el script como equivalente.
Metodología y alcance
 7. Módulo de precipitaciones/recomendación agroecológica: estaba prometido en la propuesta (informe/Entrega1_propuesta.md:20) y en la Entrega 2, pero no está implementado. Hay que decidir si se implementa o se declara fuera de alcance con justificación.
 8. Polígonos reales de barrios: el mapa usa halos circulares aproximados, no límites oficiales. Si la cátedra exige polígonos, falta reemplazarlos; si no, debe quedar muy explícito en el informe.
 9. Series históricas mezcladas: los gráficos de ciudad/barrio incluyen 2022–2023 con kits genéricos imputados y 2024–2026 con especies observadas (app.py:167). Eso genera saltos fuertes, por ejemplo OI 2022: 4.540 paquetes, OI 2023: 9.540, OI 2025: 1.831. Conviene limitar los gráficos a 2024–2026 o separar visualmente ambas eras.
10. Explicar el diseño del modelo: el modelo no usa barrio ni año como predictores; proyecta perfiles individuales y luego agrega por barrio (app.py:113). Eso debe estar documentado para que no parezca una omisión.
11. Documentar Modelo 2 y Modelo 3: están implementados en código, pero faltan secciones formales con fórmulas, ejemplos y limitaciones.
12. Aclarar 2026 y 2027–2028:
- 2026 se muestra como proyección desde el perfil 2025, no como dato observado de 2026.
- 2027–2028 son escenarios base que repiten la oferta 2026, no pronósticos validados.
- El resumen ciudad suma solo barrios con datos (29 de 31); hay que aclarar el denominador o imputar faltantes.
13. Discutir el desempeño real: R² 0,1477 y recall de la regresión convertida en alerta 0,099 son bajos. No es un error, pero el informe debe explicar que el uso es agregado/planificación y que la alerta operativa sale del clasificador, no de la regresión.
14. Faltan gráficos de EDA en los informes: hay tablas, pero no visualizaciones de distribuciones, correlaciones, evolución temporal ni comparación de modelos.
Cierre
15. Tests mínimos: no hay pruebas automatizadas de carga de modelos, endpoints ni inferencia. No es obligatorio, pero reduce riesgo antes de la entrega.
16. Git: hay cambios actuales sin commit y archivos nuevos sin trackear. Si la entrega es por GitHub, falta commit/push limpio, sin datos crudos ni archivos temporales.
Orden recomendado
1. Corregir y cerrar el informe final + Entrega 2.
2. Preparar Vercel: .vercelignore, includeFiles, runtime y smoke tests.
3. Completar README y notebook.
4. Decidir alcance de precipitaciones/polígonos y corregir series históricas.
5. Commit/push final.