/* ProHuerta · vista "Mapa de demanda".
   Datos: GET /api/mapa_completo?anio=&temporada=  (una sola llamada por filtro).
   Render: deck.gl (mapa 3D) + Chart.js (comparativa y tendencia).
   Depende de: common.js (PH), deck.gl y Chart.js cargados por CDN. */
(function () {
  'use strict';

  var COL = {
    ref: [154, 169, 194, 235],
    blue: [47, 140, 255, 240],
    green: [61, 220, 132, 235],
    amber: [255, 176, 32, 240],
    red: [255, 77, 79, 250],
    gray: [120, 132, 155, 200]
  };
  var DEFAULT_VIEW = { longitude: -58.0105, latitude: -35.5745, zoom: 13.1, pitch: 52, bearing: -12, minZoom: 10.5, maxZoom: 17, maxPitch: 75 };

  var el = function (id) { return document.getElementById(id); };
  var state = { data: null, rows: [], byNorm: {}, selected: null, maxVal: 1 };
  var vs = Object.assign({}, DEFAULT_VIEW);
  var deckgl = null, charts = { bar: null, line: null };

  /* ───────── Preparación de datos ───────── */
  function classify(r) {
    if (r.sin_datos) return 'gray';
    if (r.estado === 'alerta') return 'red';
    if (r.pct == null) return 'ref';
    return r.pct > 5 ? 'amber' : r.pct < -5 ? 'blue' : 'green';
  }

  function buildRows(data, variable) {
    return data.barrios.map(function (b) {
      var m = PH.metric(b, variable, data.precio_sobre);
      var est = PH.estado(b);
      var r = { b: b, norm: b.barrio_norm, name: b.barrio_nombre, hist: m.hist, proy: m.proy, pct: m.pct,
        estado: est.key, estadoInfo: est, sin_datos: !!b.sin_datos, lat: b.lat, lng: b.lng, radio: b.radio_m || 260 };
      r.cls = classify(r);
      return r;
    });
  }

  function offsetLngLat(r, eastMeters) {
    var dLng = eastMeters / (111320 * Math.cos(r.lat * Math.PI / 180));
    return [r.lng + dLng, r.lat];
  }

  /* ───────── Mapa ───────── */
  function layers() {
    var D = deck, rows = state.rows, sel = state.selected, scale = 1100 / (state.maxVal || 1);
    var out = [];
    var bm = window.PH_BASEMAP;
    if (bm && bm.image && bm.bounds) {
      out.push(new D.BitmapLayer({ id: 'basemap', image: bm.image, bounds: bm.bounds, opacity: 1 }));
    }
    var fc = {
      type: 'FeatureCollection',
      features: rows.filter(function (r) { return r.b.geometry; }).map(function (r) {
        return { type: 'Feature', geometry: r.b.geometry, properties: { norm: r.norm } };
      })
    };
    out.push(new D.GeoJsonLayer({
      id: 'poligonos', data: fc, pickable: true, stroked: true, filled: true, lineWidthMinPixels: 1.4,
      getFillColor: function (f) {
        var r = state.byNorm[f.properties.norm]; var isSel = f.properties.norm === sel;
        if (isSel) return [255, 255, 255, 90];
        if (!r || r.sin_datos) return [120, 130, 150, 26];
        var c = COL[r.cls] || COL.ref; return [c[0], c[1], c[2], r.cls === 'red' ? 105 : 62];
      },
      getLineColor: function (f) {
        var r = state.byNorm[f.properties.norm];
        if (f.properties.norm === sel) return [255, 255, 255, 255];
        if (!r || r.sin_datos) return [140, 150, 170, 110];
        var c = COL[r.cls] || COL.ref; return [c[0], c[1], c[2], 190];
      },
      updateTriggers: { getFillColor: [sel, state.version], getLineColor: [sel, state.version] },
      autoHighlight: true, highlightColor: [255, 255, 255, 55]
    }));

    var withData = rows.filter(function (r) { return !r.sin_datos; });
    var east = 85;
    out.push(new D.ColumnLayer({
      id: 'col-ref', data: withData.filter(function (r) { return r.hist > 0; }), diskResolution: 4, angle: 45,
      radius: 62, extruded: true, pickable: true, elevationScale: scale,
      getPosition: function (r) { return offsetLngLat(r, -east); }, getElevation: function (r) { return r.hist; },
      getFillColor: function (r) { return r.norm === sel ? [210, 222, 240, 255] : COL.ref; },
      material: { ambient: 0.5, diffuse: 0.7, shininess: 30 }, updateTriggers: { getFillColor: [sel, state.version], getElevation: [state.version] }
    }));
    out.push(new D.ColumnLayer({
      id: 'col-proy', data: withData.filter(function (r) { return r.proy > 0; }), diskResolution: 4, angle: 45,
      radius: 72, extruded: true, pickable: true, elevationScale: scale,
      getPosition: function (r) { return offsetLngLat(r, east); }, getElevation: function (r) { return r.proy; },
      getFillColor: function (r) { var c = COL[r.cls] || COL.blue; return r.norm === sel ? [Math.min(255, c[0] + 25), Math.min(255, c[1] + 25), Math.min(255, c[2] + 25), 255] : c; },
      material: { ambient: 0.5, diffuse: 0.75, shininess: 34 }, updateTriggers: { getFillColor: [sel, state.version], getElevation: [state.version] }
    }));

    // Etiquetas: barrios más relevantes + el seleccionado (evita saturar el mapa).
    var key = function (r) { return Math.max(r.hist || 0, r.proy || 0); };
    var top = withData.slice().sort(function (a, b) { return key(b) - key(a); }).slice(0, 8).map(function (r) { return r.norm; });
    if (sel && top.indexOf(sel) < 0) top.push(sel);
    var labels = rows.filter(function (r) { return top.indexOf(r.norm) >= 0; }).map(function (r) {
      var text = r.name + (r.pct != null ? '  ' + PH.fmt.pct(r.pct) : '');
      return { r: r, text: text, pos: [r.lng, r.lat, key(r) * scale + 80] };
    });
    out.push(new D.TextLayer({
      id: 'etiquetas', data: labels, getPosition: function (d) { return d.pos; }, getText: function (d) { return d.text; },
      getSize: 13, sizeUnits: 'pixels', billboard: true, characterSet: 'auto', fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600,
      getColor: [245, 248, 255, 255], background: true, backgroundPadding: [7, 3],
      getBackgroundColor: function (d) { return d.r.norm === sel ? [47, 140, 255, 235] : d.r.cls === 'red' ? [150, 28, 34, 235] : [10, 18, 36, 215]; },
      getTextAnchor: 'middle', getAlignmentBaseline: 'bottom', pickable: false, parameters: { depthTest: false },
      updateTriggers: { getBackgroundColor: [sel, state.version] }
    }));
    return out;
  }

  function tooltip(info) {
    var o = info && info.object; if (!o) return null;
    var norm = o.norm || (o.properties && o.properties.norm), r = state.byNorm[norm]; if (!r) return null;
    var v = PH.state.variable, f = function (x) { return PH.fmt.value(x, v); };
    var html = '<b style="font-size:13px">' + PH.esc(r.name) + '</b><br>' +
      (r.sin_datos ? '<span style="color:#93a4bf">Sin datos para esta temporada</span>' :
        '<span style="color:#9aa9c2">Referencia</span> ' + f(r.hist) + '<br>' +
        (r.proy != null ? '<span style="color:#7fb8ff">Proyección</span> ' + f(r.proy) + '<br>Variación <b>' + PH.fmt.pct(r.pct) + '</b><br>' : '') +
        '<span style="color:#93a4bf">' + PH.esc(r.estadoInfo.label) + '</span>');
    return { html: html, style: { backgroundColor: 'rgba(8,14,28,.96)', border: '1px solid rgba(120,165,230,.4)', borderRadius: '10px', color: '#eef3fb', padding: '9px 12px', fontSize: '12px', lineHeight: '1.5', fontFamily: 'Inter, system-ui, sans-serif' } };
  }

  function initDeck() {
    if (typeof deck === 'undefined') { el('map-loading').textContent = 'No se pudo cargar deck.gl (revisá la conexión a internet).'; return; }
    deckgl = new deck.DeckGL({
      container: el('map'), views: new deck.MapView({ repeat: false }), viewState: vs, controller: true,
      layers: [], getTooltip: tooltip, parameters: { clearColor: [0.03, 0.05, 0.1, 1] },
      onViewStateChange: function (e) { vs = e.viewState; deckgl.setProps({ viewState: vs }); },
      onClick: function (info) {
        var o = info && info.object; var norm = o && (o.norm || (o.properties && o.properties.norm));
        if (norm) select(norm);
      }
    });
    var move = function (d) { vs = Object.assign({}, vs, { zoom: Math.max(DEFAULT_VIEW.minZoom, Math.min(DEFAULT_VIEW.maxZoom, vs.zoom + d)), transitionDuration: 250 }); deckgl.setProps({ viewState: vs }); };
    el('zoom-in').onclick = function () { move(0.6); };
    el('zoom-out').onclick = function () { move(-0.6); };
    el('zoom-reset').onclick = function () { vs = Object.assign({}, DEFAULT_VIEW, { transitionDuration: 400 }); deckgl.setProps({ viewState: vs }); };
    if (!window.PH_BASEMAP) el('map-attrib').style.display = 'none';
  }

  function refreshMap() { if (deckgl) deckgl.setProps({ layers: layers() }); }

  /* ───────── Panel de detalle ───────── */
  function ico(c) { return '<i class="bi ' + c + '"></i>'; }

  function renderDetalle() {
    var box = el('detalle'), r = state.byNorm[state.selected];
    if (!r) { box.innerHTML = '<div class="empty">Seleccioná un barrio en el mapa.</div>'; return; }
    var d = state.data, v = PH.state.variable, b = r.b, f = function (x) { return PH.fmt.value(x, v); };
    var proj = !!d.es_proyeccion;
    var chips = '<span class="chip ' + r.estadoInfo.cls + '">' + (r.estado === 'alerta' ? ico('bi-exclamation-triangle-fill') : '') + PH.esc(r.estadoInfo.label) + '</span>';
    if (b.muestra_limitada) chips += ' <span class="chip amber" title="' + PH.esc(b.motivo_muestra || '') + '">Muestra limitada</span>';

    if (r.sin_datos) {
      box.innerHTML = '<h2>' + ico('bi-geo-alt-fill') + PH.esc(r.name) + '</h2>' + chips +
        '<p class="detail-text" style="margin-top:12px">' + PH.esc(b.motivo_alerta || 'No hay solicitudes con barrio para esta temporada.') + '</p>';
      return;
    }
    var refYear = b.anio_referencia || '—';
    var nums = '<div class="detail-nums"><div><div class="kpi-label">' + (proj ? 'Demanda de referencia (' + refYear + ')' : 'Observado ' + d.anio) +
      '</div><div class="big">' + f(r.hist) + '</div></div>' +
      (proj ? '<div><div class="kpi-label">Proyección ' + d.anio + '</div><div class="big" style="color:' + (r.cls === 'red' ? 'var(--red)' : 'var(--blue)') + '">' + f(r.proy) + '</div></div>' : '<div><div class="kpi-label">Solicitudes</div><div class="big">' + PH.fmt.n0(b.solicitudes_historicas) + '</div></div>') + '</div>';
    var diff = (r.proy != null && r.hist != null) ? r.proy - r.hist : null;
    var variation = proj && r.pct != null ?
      '<div class="detail-var"><div class="pct ' + PH.deltaClass(r.pct) + '">' + (r.pct > 0 ? ico('bi-arrow-up-right') : r.pct < 0 ? ico('bi-arrow-down-right') : '') + ' ' + PH.fmt.pct(r.pct) + '</div>' +
      '<div class="kpi-small">proyectado vs. referencia (' + (diff > 0 ? '+' : diff < 0 ? '−' : '') + PH.fmt.value(Math.abs(diff), v) + ')</div></div>' : '';
    var esp = (b.top_especies || []).slice(0, 5).map(function (e) { return '<li><span>' + PH.esc(e.nombre) + '</span><span>' + PH.fmt.n0(e.solicitudes) + ' solic.</span></li>'; }).join('');
    box.innerHTML = '<h2>' + ico('bi-geo-alt-fill') + PH.esc(r.name) + '</h2>' + chips + nums + variation +
      '<p class="detail-text">' + PH.esc(b.motivo_alerta || '') + (b.motivo_muestra ? ' ' + PH.esc(b.motivo_muestra) : '') + '</p>' +
      (esp ? '<div class="kpi-label" style="margin-top:10px">Especies más solicitadas</div><ul class="mini-list">' + esp + '</ul>' : '') +
      '<div class="kpi-small" style="margin-top:10px">Base: ' + PH.fmt.n0(b.n_solicitudes_historicas) + ' solicitudes en ' + PH.fmt.n0(b.n_anios_historicos) + ' año(s)' +
      (b.crecimiento_anual != null && proj ? ' · crecimiento anual supuesto ' + PH.fmt.pct(b.crecimiento_anual * 100) : '') + '</div>';
  }

  /* ───────── Resumen, prioridades e insights ───────── */
  function renderResumen() {
    var d = state.data, v = PH.state.variable, proj = !!d.es_proyeccion;
    var valid = state.rows.filter(function (r) { return !r.sin_datos; });
    var sum = function (k) { return valid.reduce(function (a, r) { return a + (PH.isNum(r[k]) ? r[k] : 0); }, 0); };
    var hist = sum('hist'), proy = sum('proy');
    el('kpi-total').textContent = PH.fmt.value(proj ? proy : hist, v);
    el('kpi-total').previousElementSibling.textContent = proj ? 'Demanda total proyectada' : 'Demanda total observada';
    var dl = el('kpi-delta');
    if (proj && hist > 0) {
      var p = (proy - hist) / hist * 100; dl.textContent = PH.fmt.pct(p); dl.className = 'delta ' + PH.deltaClass(p);
      el('kpi-delta-note').textContent = 'vs. referencia ' + PH.fmt.value(hist, v);
    } else { dl.textContent = '—'; dl.className = 'delta flat'; el('kpi-delta-note').textContent = proj ? '' : 'Dato observado, sin comparación'; }
    var al = valid.filter(function (r) { return r.estado === 'alerta'; }).length;
    var chip = el('kpi-alertas');
    if (proj) { chip.className = 'chip ' + (al ? 'red' : 'green'); chip.innerHTML = ico(al ? 'bi-exclamation-triangle-fill' : 'bi-check-circle-fill') + ' ' + al + ' de ' + valid.length + ' barrios en alerta'; }
    else { chip.className = 'chip gray'; chip.textContent = valid.length + ' barrios con datos'; }
    var rs = d.resumen_territorial || {};
    el('kpi-nota').textContent = 'Solo barrios mapeados con datos (' + valid.length + ' de ' + state.rows.length + '). ' +
      (PH.state.variable === 'presupuesto' ? 'Precio fijo de $' + PH.fmt.n0(d.precio_sobre) + ' por sobre.' : '');

    var pr = el('prioridades');
    var alertas = valid.filter(function (r) { return r.estado === 'alerta'; }).sort(function (a, b) { return (b.proy - b.hist) - (a.proy - a.hist); }).slice(0, 5);
    pr.innerHTML = alertas.length ? alertas.map(function (r) {
      return '<li><span>' + PH.esc(r.name) + ' <span class="up">' + PH.fmt.pct(r.pct) + '</span></span><a href="#" data-sel="' + PH.esc(r.norm) + '" class="chip red" style="padding:2px 10px">Ver</a></li>';
    }).join('') : '<li class="kpi-small" style="border:0">' + (proj ? 'Ningún barrio supera el umbral de sobredemanda.' : 'Las alertas se calculan solo para años proyectados.') + '</li>';
    pr.querySelectorAll('[data-sel]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); select(a.getAttribute('data-sel')); }); });
    void rs;
  }

  function renderInsights() {
    var d = state.data, v = PH.state.variable, ul = el('insights'), proj = !!d.es_proyeccion;
    var valid = state.rows.filter(function (r) { return !r.sin_datos; });
    var items = [];
    var names = function (arr) { return arr.slice(0, 3).map(function (r) { return PH.esc(r.name); }).join(', '); };
    if (proj) {
      var hist = valid.reduce(function (a, r) { return a + (r.hist || 0); }, 0), proy = valid.reduce(function (a, r) { return a + (r.proy || 0); }, 0);
      var p = hist > 0 ? (proy - hist) / hist * 100 : null;
      if (p != null) items.push(p >= 0 ? ['g', 'Demanda total en aumento (' + PH.fmt.pct(p) + ') frente a la referencia.'] : ['b', 'Demanda total proyectada a la baja (' + PH.fmt.pct(p) + ') frente a la referencia.']);
      var al = valid.filter(function (r) { return r.estado === 'alerta'; });
      items.push(al.length ? ['a', 'Mayor atención en ' + names(al) + '.'] : ['g', 'Ningún barrio supera el umbral de sobredemanda (+' + Math.round((PH.margen || 0.1) * 100) + '% y ≥ ' + (PH.diffMin || 10) + ' sobres).']);
      var down = valid.filter(function (r) { return r.pct != null && r.pct < -10; }).sort(function (a, b) { return a.pct - b.pct; });
      if (down.length) items.push(['b', 'Caídas marcadas previstas en ' + names(down) + '.']);
      var lim = valid.filter(function (r) { return r.b.muestra_limitada; }).length;
      if (lim) items.push(['a', lim + ' de ' + valid.length + ' barrios tienen muestra histórica limitada: leer con cautela.']);
    } else {
      items.push(['b', 'Año observado: se muestran datos reales por barrio, sin proyección ni alertas.']);
      var top = valid.slice().sort(function (a, b) { return (b.hist || 0) - (a.hist || 0); });
      if (top.length) items.push(['g', 'Mayor volumen: ' + names(top) + '.']);
    }
    ul.innerHTML = items.map(function (i) { return '<li><span class="dot ' + i[0] + '">' + (i[0] === 'g' ? '✓' : i[0] === 'a' ? '!' : 'i') + '</span><span>' + i[1] + '</span></li>'; }).join('');
    void v;
  }

  /* ───────── Gráficos ───────── */
  function chartDefaults() {
    if (typeof Chart === 'undefined') return false;
    Chart.defaults.color = '#93a4bf'; Chart.defaults.borderColor = 'rgba(120,165,230,.12)';
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif'; Chart.defaults.font.size = 11;
    return true;
  }
  var rgba = function (c, a) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + (a == null ? c[3] / 255 : a) + ')'; };

  function renderBarras() {
    if (!chartDefaults()) return;
    var v = PH.state.variable, proj = !!state.data.es_proyeccion;
    var valid = state.rows.filter(function (r) { return !r.sin_datos; });
    var key = function (r) { return proj ? (r.proy || 0) : (r.hist || 0); };
    var top = valid.slice().sort(function (a, b) { return key(b) - key(a); }).slice(0, 12);
    if (state.selected && !top.some(function (r) { return r.norm === state.selected; })) { var s = state.byNorm[state.selected]; if (s && !s.sin_datos) top.push(s); }
    var ds = [{ label: proj ? 'Referencia' : 'Observado', data: top.map(function (r) { return r.hist; }), backgroundColor: rgba(COL.ref, 0.75), borderRadius: 4 }];
    if (proj) ds.push({ label: 'Proyección ' + state.data.anio, data: top.map(function (r) { return r.proy; }), backgroundColor: top.map(function (r) { return rgba(COL[r.cls] || COL.blue, 0.92); }), borderRadius: 4 });
    el('bar-hint').textContent = 'Top ' + top.length + ' por ' + (proj ? 'proyección' : 'volumen') + ' · clic para ver detalle';
    var cfg = {
      type: 'bar', data: { labels: top.map(function (r) { return r.name; }), datasets: ds },
      options: {
        responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
        plugins: { legend: { position: 'top', align: 'start', labels: { boxWidth: 10, boxHeight: 10 } },
          tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': ' + PH.fmt.value(c.parsed.y, v); } } } },
        scales: { x: { grid: { display: false }, ticks: { maxRotation: 55, minRotation: 0, autoSkip: false, font: { size: 10 } } }, y: { beginAtZero: true, ticks: { callback: function (x) { return PH.fmt.value(x, v); } } } },
        onClick: function (e, els) { if (els.length) select(top[els[0].index].norm); },
        onHover: function (e, els) { e.native.target.style.cursor = els.length ? 'pointer' : 'default'; }
      }
    };
    if (charts.bar) { charts.bar.destroy(); }
    charts.bar = new Chart(el('chart-barras'), cfg);
  }

  function renderTendencia() {
    if (!chartDefaults()) return;
    var d = state.data, v = PH.state.variable, p = d.precio_sobre || 500;
    var pick = function (o, kind) {
      if (v === 'solicitudes') return kind === 'obs' ? o.solicitudes : o.solicitudes_esperadas;
      var q = kind === 'obs' ? o.paquetes : null; return q;
    };
    var obs = (d.serie_ciudad_territorial || []).map(function (o) { return { anio: o.anio, val: v === 'solicitudes' ? o.solicitudes : v === 'presupuesto' ? o.presupuesto : o.paquetes }; });
    var esc = (d.escenarios_ciudad || []).map(function (o) {
      return { anio: o.anio, ref: v === 'solicitudes' ? null : v === 'presupuesto' ? o.presupuesto_referencia : o.demanda_referencia_paquetes,
        proy: v === 'solicitudes' ? o.solicitudes_esperadas : v === 'presupuesto' ? o.presupuesto_proyectado : o.demanda_proyectada_paquetes };
    });
    void pick; void p;
    var years = obs.map(function (o) { return o.anio; }).concat(esc.map(function (o) { return o.anio; }));
    years = years.filter(function (y, i) { return years.indexOf(y) === i; }).sort();
    var at = function (arr, y, k) { var f = arr.filter(function (o) { return o.anio === y; })[0]; return f ? f[k] : null; };
    var lastObs = obs.length ? obs[obs.length - 1] : null;
    var obsData = years.map(function (y) { return at(obs, y, 'val'); });
    var projData = years.map(function (y) { return y === (lastObs && lastObs.anio) ? lastObs.val : at(esc, y, 'proy'); });
    var refData = years.map(function (y) { return y === (lastObs && lastObs.anio) ? lastObs.val : at(esc, y, 'ref'); });
    var datasets = [{ label: 'Observado', data: obsData, borderColor: '#3ddc84', backgroundColor: 'rgba(61,220,132,.12)', fill: true, tension: .3, pointRadius: 4, spanGaps: false }];
    if (esc.length) {
      if (v !== 'solicitudes') datasets.push({ label: 'Esperado (baseline)', data: refData, borderColor: '#ffb020', borderDash: [6, 5], tension: .25, pointRadius: 3, spanGaps: true });
      datasets.push({ label: 'Proyectado', data: projData, borderColor: '#ff6b6d', backgroundColor: 'rgba(255,77,79,.10)', tension: .25, pointRadius: 4, pointStyle: 'rectRot', spanGaps: true });
    }
    var cfg = {
      type: 'line', data: { labels: years, datasets: datasets },
      options: { responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
        plugins: { legend: { position: 'top', align: 'start', labels: { boxWidth: 10, boxHeight: 10 } }, tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': ' + PH.fmt.value(c.parsed.y, v); } } } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { callback: function (x) { return PH.fmt.value(x, v); } } } } }
    };
    if (charts.line) { charts.line.destroy(); }
    charts.line = new Chart(el('chart-tendencia'), cfg);
  }

  /* ───────── Selección y carga ───────── */
  function select(norm) {
    if (!state.byNorm[norm]) return;
    state.selected = norm; PH.state.barrio = norm;
    try { localStorage.setItem('ph.state.v1', JSON.stringify(PH.state)); } catch (e) { /* ignorar */ }
    var sb = el('f-barrio'); if (sb) sb.value = norm;
    state.version++; refreshMap(); renderDetalle(); renderBarras();
  }

  function load(st) {
    el('map-loading').classList.remove('hide'); el('map-loading').textContent = 'Cargando datos…';
    PH.mapa(st.anio, st.temporada).then(function (data) {
      state.data = data; state.rows = buildRows(data, st.variable); state.byNorm = {};
      state.rows.forEach(function (r) { state.byNorm[r.norm] = r; });
      state.maxVal = Math.max.apply(null, [1].concat(state.rows.map(function (r) { return Math.max(r.hist || 0, r.proy || 0); })));
      var valid = state.rows.filter(function (r) { return !r.sin_datos; });
      // Selección: la elegida si tiene datos. Si no, el caso más relevante para decidir:
      // el barrio en alerta con mayor exceso; si no hay alertas, el de mayor volumen con muestra confiable
      // (evita destacar variaciones enormes sobre bases mínimas).
      var keep = st.barrio && state.byNorm[st.barrio] && !state.byNorm[st.barrio].sin_datos ? st.barrio : null;
      if (!keep && valid.length) {
        var vol = function (r) { return data.es_proyeccion ? (r.proy || 0) : (r.hist || 0); };
        var alertas = valid.filter(function (r) { return r.estado === 'alerta'; }).sort(function (x, y) { return (y.proy - y.hist) - (x.proy - x.hist); });
        var fiables = valid.filter(function (r) { return !r.b.muestra_limitada; }).sort(function (x, y) { return vol(y) - vol(x); });
        var any = valid.slice().sort(function (x, y) { return vol(y) - vol(x); });
        keep = (alertas[0] || fiables[0] || any[0]).norm;
      }
      state.selected = keep; state.version = (state.version || 0) + 1;
      refreshMap(); renderDetalle(); renderResumen(); renderInsights(); renderBarras(); renderTendencia();
      el('map-loading').classList.add('hide');
    }).catch(function (err) {
      console.error(err); el('map-loading').classList.remove('hide'); el('map-loading').textContent = 'No se pudieron cargar los datos: ' + err.message;
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    state.version = 0; initDeck();
    PH.init({ onApply: load });
  });
})();
