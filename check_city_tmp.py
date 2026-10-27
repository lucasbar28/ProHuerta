from app import app
import json
c = app.test_client()
r = c.get('/api/mapa_completo?anio=2027&temporada=vera')
d = json.loads(r.data)
h = d.get('serie_ciudad_territorial') or []
for x in h:
    print(x['anio'], x.get('paquetes'), x.get('tipo'))
