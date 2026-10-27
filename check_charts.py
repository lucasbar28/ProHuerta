from app import app
import json
c = app.test_client()
r = c.get('/api/mapa_completo?anio=2026&temporada=PV')
d = json.loads(r.data)
series = d.get('serie_ciudad_territorial') or d.get('serie_ciudad')
scenarios = d.get('escenarios_ciudad')
print(series)
print(scenarios)
