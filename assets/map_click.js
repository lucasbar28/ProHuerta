(function () {
  window.addEventListener("message", function (event) {
    var payload = event.data;
    if (!payload || payload.type !== "prohuerta-barrio" || !payload.barrio) {
      return;
    }
    if (window.dash_clientside && window.dash_clientside.set_props) {
      window.dash_clientside.set_props("map-click-store", {
        data: { barrio: payload.barrio, ts: Date.now() },
      });
    }
  });
})();
