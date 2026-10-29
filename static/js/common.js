/* ProHuerta · utilidades compartidas por todas las vistas.
   - Estado de filtros (temporada, año, variable, barrio) persistente entre vistas
     (querystring > localStorage > valores por defecto).
   - Acceso a la API y formato de números.
   - Navbar: menú móvil y período visible (solo en el mapa). */
(function () {
  'use strict';

  var LS_KEY = 'ph.state.v1';
  var SEASONS = { OI: 'Otoño – Invierno', PV: 'Primavera – Verano' };
  var VARIABLES = {
    paquetes: { label: 'Sobres equivalentes', unit: 'sobres' },
    solicitudes: { label: 'Solicitudes', unit: 'solicitudes' },
    presupuesto: { label: 'Presupuesto ($)', unit: '$' }
  };

  var nf0 = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 0 });
  var nf1 = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 1 });
  var isNum = function (v) { return typeof v === 'number' && isFinite(v); };

  var PH = (window.PH = {
    SEASONS: SEASONS,
    VARIABLES: VARIABLES,
    periods: [],
    health: null,
    state: { temporada: 'PV', anio: 2027, variable: 'paquetes', barrio: '' },
    isNum: isNum
  });

  /* ── Formato ── */
  PH.fmt = {
    n0: function (v) { return isNum(v) ? nf0.format(v) : '—'; },
    n1: function (v) { return isNum(v) ? nf1.format(v) : '—'; },
    money: function (v) { return isNum(v) ? '$' + nf0.format(v) : '—'; },
    pct: function (v, signed) {
      if (!isNum(v)) return '—';
      var s = nf1.format(Math.abs(v)) + '%';
      if (signed === false) return (v < 0 ? '−' : '') + s;
      return (v > 0 ? '+' : v < 0 ? '−' : '') + s;
    },
    value: function (v, variable) { return variable === 'presupuesto' ? PH.fmt.money(v) : PH.fmt.n0(v); }
  };

  PH.esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  /* ── Estado persistente ── */
  function readState() {
    var s = { temporada: 'PV', anio: 2027, variable: 'paquetes', barrio: '' };
    try {
      var saved = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
      if (saved) Object.keys(s).forEach(function (k) { if (saved[k] != null) s[k] = saved[k]; });
    } catch (e) { /* sin storage: se usan valores por defecto */ }
    var q = new URLSearchParams(location.search);
    if (q.get('temporada')) s.temporada = q.get('temporada').toUpperCase();
    if (q.get('anio')) s.anio = parseInt(q.get('anio'), 10) || s.anio;
    if (q.get('variable')) s.variable = q.get('variable');
    if (q.get('barrio') != null && q.has('barrio')) s.barrio = q.get('barrio');
    return s;
  }
  function saveState() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(PH.state)); } catch (e) { /* ignorar */ }
  }

  function syncNavbar() {
    var s = PH.state;
    var ps = document.getElementById('pp-season'), py = document.getElementById('pp-year');
    if (ps) ps.textContent = SEASONS[s.temporada] || s.temporada;
    if (py) py.textContent = s.anio;
    var qs = '?temporada=' + encodeURIComponent(s.temporada) + '&anio=' + encodeURIComponent(s.anio) +
      '&variable=' + encodeURIComponent(s.variable) + (s.barrio ? '&barrio=' + encodeURIComponent(s.barrio) : '');
    // Solo el enlace al mapa conserva el estado (el resto de las vistas no usa estos filtros).
    document.querySelectorAll('a[data-nav="mapa"]').forEach(function (a) {
      var base = a.getAttribute('href').split('?')[0];
      a.setAttribute('href', base + qs);
    });
    var url = location.pathname + qs;
    if (history.replaceState) history.replaceState(null, '', url);
  }

  /* ── API ── */
  PH.api = function (path, params) {
    var qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetch(path + qs, { headers: { Accept: 'application/json' } }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' en ' + path);
      return r.json();
    });
  };
  var cache = {};
  PH.mapa = function (anio, temporada) {
    var key = anio + '-' + temporada;
    if (!cache[key]) {
      cache[key] = PH.api('/api/mapa_completo', { anio: anio, temporada: temporada }).catch(function (e) {
        delete cache[key]; throw e;
      });
    }
    return cache[key];
  };

  /* ── Lógica de dominio compartida ── */
  PH.estado = function (b) {
    if (!b || b.sin_datos || b.estado_alerta === 'sin_datos') return { label: 'Sin datos', cls: 'gray', key: 'sin_datos' };
    if (b.estado_alerta === 'aumento_relevante') return { label: 'Alerta: aumento significativo', cls: 'red', key: 'alerta' };
    if (b.estado_alerta === 'sin_alerta') return { label: 'Sin alerta', cls: 'green', key: 'sin_alerta' };
    if (b.estado_alerta === 'observado') return { label: 'Dato observado', cls: 'blue', key: 'observado' };
    return { label: b.estado_alerta || '—', cls: 'gray', key: 'otro' };
  };

  /* Referencia y proyección de un barrio según la variable elegida. */
  PH.metric = function (b, variable, precio) {
    precio = precio || 500;
    var hist, proy;
    if (variable === 'solicitudes') {
      hist = b.solicitudes_historicas; proy = b.solicitudes;
    } else if (variable === 'presupuesto') {
      hist = isNum(b.historico_paquetes) ? b.historico_paquetes * precio : null;
      proy = isNum(b.proyectado_paquetes) ? b.proyectado_paquetes * precio : null;
    } else {
      hist = b.historico_paquetes; proy = b.proyectado_paquetes;
    }
    var pct = isNum(hist) && hist > 0 && isNum(proy) ? ((proy - hist) / hist) * 100 : null;
    return { hist: isNum(hist) ? hist : null, proy: isNum(proy) ? proy : null, pct: pct };
  };

  PH.deltaClass = function (pct) { return !isNum(pct) ? 'flat' : pct > 0.05 ? 'up' : pct < -0.05 ? 'down' : 'flat'; };

  /* ── Filtros ── */
  function yearsFor(temporada) {
    var ys = PH.periods.filter(function (p) { return p.temporada === temporada; }).map(function (p) { return p.anio; });
    return ys.filter(function (v, i) { return ys.indexOf(v) === i; }).sort();
  }
  function fillYears(sel, temporada, preferred) {
    var ys = yearsFor(temporada);
    sel.innerHTML = ys.map(function (y) {
      var proj = (PH.health && (PH.health.anios_proyeccion || []).indexOf(y) >= 0);
      return '<option value="' + y + '">' + y + (proj ? ' (proyección)' : '') + '</option>';
    }).join('');
    var pick = ys.indexOf(preferred) >= 0 ? preferred : (ys.indexOf(2027) >= 0 ? 2027 : ys[ys.length - 1]);
    sel.value = pick;
    var hint = document.getElementById('f-anio-hint');
    if (hint) hint.textContent = (PH.health && PH.health.anios_proyeccion) ?
      PH.health.anios_proyeccion.join('–') + ': escenarios base con crecimiento esperado; hasta ' + (PH.health.anios_proyeccion[0] - 1) + ': datos observados.' : '';
    return parseInt(sel.value, 10);
  }

  /* init({ onApply(state), barrios: bool }) → arma filtros y dispara la primera carga */
  PH.init = function (opts) {
    opts = opts || {};
    PH.state = readState();
    var selT = document.getElementById('f-temporada'), selA = document.getElementById('f-anio'),
      selV = document.getElementById('f-variable'), selB = document.getElementById('f-barrio'),
      btn = document.getElementById('f-apply');

    return Promise.all([PH.api('/api/filtros'), PH.api('/api/health').catch(function () { return null; })]).then(function (res) {
      PH.periods = res[0].periodos || [];
      PH.precio = res[0].precio_sobre || 500;
      PH.margen = res[0].margen_sobredemanda;
      PH.diffMin = res[0].diferencia_minima_sobres;
      PH.barrios = res[0].barrios || [];
      PH.health = res[1];

      var foot = document.getElementById('footer-model');
      if (foot && PH.health && PH.health.model_version) foot.textContent = 'Modelo ' + PH.health.model_version + ' · ' + PH.health.filas_modeladas + ' solicitudes modeladas';

      if (selT) selT.value = PH.state.temporada;
      if (selA) PH.state.anio = fillYears(selA, selT ? selT.value : PH.state.temporada, PH.state.anio);
      if (selV) selV.value = VARIABLES[PH.state.variable] ? PH.state.variable : 'paquetes';
      if (selB) {
        PH.barrios.slice().sort(function (a, b) { return a.barrio_nombre.localeCompare(b.barrio_nombre, 'es'); }).forEach(function (b) {
          var o = document.createElement('option'); o.value = b.barrio_norm; o.textContent = b.barrio_nombre; selB.appendChild(o);
        });
        selB.value = PH.state.barrio || '';
      }
      if (selT && selA) selT.addEventListener('change', function () { fillYears(selA, selT.value, parseInt(selA.value, 10)); });

      function apply() {
        if (selT) PH.state.temporada = selT.value;
        if (selA) PH.state.anio = parseInt(selA.value, 10);
        if (selV) PH.state.variable = selV.value;
        if (selB) PH.state.barrio = selB.value;
        saveState(); syncNavbar();
        if (opts.onApply) opts.onApply(PH.state);
      }
      if (btn) btn.addEventListener('click', apply);
      saveState(); syncNavbar();
      if (opts.onApply) opts.onApply(PH.state);
    }).catch(function (err) {
      console.error(err);
      var m = document.querySelector('.page');
      if (m) m.insertAdjacentHTML('afterbegin', '<div class="callout warn" style="margin-bottom:14px">No se pudo contactar con la API (' + PH.esc(err.message) + '). Verificá que el servidor esté activo.</div>');
    });
  };

  /* ── Navbar: menú móvil ── */
  document.addEventListener('DOMContentLoaded', function () {
    var t = document.getElementById('nav-toggle'), n = document.getElementById('nav');
    if (t && n) t.addEventListener('click', function () { n.classList.toggle('open'); });
  });
})();
