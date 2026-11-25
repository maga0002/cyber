(function () {
  // Herkenbare statuswaarden krijgen een vaste kleur (stoplicht).
  // Per groep meerdere tinten, zodat bijv. "Deels" en "Gepland" niet dezelfde kleur krijgen.
  const STATUS = [
    { tinten: ["#1f9d55", "#4ec27f", "#137a40"], woorden: ["gereed", "voldoet", "groen", "ok", "afgerond", "ja", "compliant", "laag", "geïmplementeerd", "geimplementeerd", "done", "actief"] },
    { tinten: ["#e3a008", "#f2c14e", "#b97d00", "#f59e0b"], woorden: ["deels", "gedeeltelijk", "in uitvoering", "oranje", "bezig", "midden", "middel", "gemiddeld", "partial", "in progress", "gepland"] },
    { tinten: ["#d64545", "#ef7b7b", "#a92f2f"], woorden: ["open", "niet", "rood", "nee", "hoog", "kritiek", "non-compliant", "ontbreekt", "te laat", "achterstand"] },
  ];
  const PALET = ["#2563eb", "#7c3aed", "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5", "#0d9488", "#9333ea", "#ca8a04"];

  function kleurenVoor(labels) {
    const gebruikt = STATUS.map(() => 0);
    return labels.map((label, i) => {
      const l = String(label).toLowerCase().trim();
      const s = STATUS.findIndex((g) => g.woorden.some((w) => l === w || l.startsWith(w + " ") || l.startsWith(w + "-") || l.startsWith(w + " (")));
      if (s === -1) return PALET[i % PALET.length];
      const t = STATUS[s].tinten;
      return t[gebruikt[s]++ % t.length];
    });
  }

  const donker = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const tekstKleur = donker ? "#cbd5e1" : "#334155";
  const rasterKleur = donker ? "rgba(255,255,255,.08)" : "rgba(0,0,0,.06)";

  document.querySelectorAll("canvas[data-grafiek]").forEach((canvas) => {
    const cfg = JSON.parse(canvas.dataset.grafiek);
    const kleuren = kleurenVoor(cfg.labels);
    const filterUrl = canvas.dataset.filterUrl;
    new Chart(canvas, {
      type: cfg.type,
      data: { labels: cfg.labels, datasets: [{ data: cfg.waarden, backgroundColor: kleuren, borderWidth: cfg.type === "doughnut" ? 2 : 0, borderColor: donker ? "#1e293b" : "#fff", borderRadius: cfg.type === "bar" ? 4 : 0 }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: cfg.type === "doughnut" ? "62%" : undefined,
        plugins: {
          legend: { display: cfg.type === "doughnut" && !cfg.mini, position: "right", labels: { color: tekstKleur, boxWidth: 12 } },
          tooltip: { enabled: true },
        },
        scales: cfg.type === "bar" ? {
          x: { ticks: { color: tekstKleur }, grid: { display: false } },
          y: { beginAtZero: true, ticks: { color: tekstKleur, precision: 0 }, grid: { color: rasterKleur } },
        } : undefined,
        onClick: filterUrl ? (evt, items) => {
          if (!items.length) return;
          const label = cfg.labels[items[0].index];
          window.location = filterUrl + "&f_waarde=" + encodeURIComponent(label);
        } : undefined,
        onHover: filterUrl ? (evt, items) => { evt.native.target.style.cursor = items.length ? "pointer" : "default"; } : undefined,
      },
    });
  });

  // Eenvoudig zoeken in de gegevenstabel
  const zoek = document.getElementById("zoek");
  const tabel = document.getElementById("gegevens");
  if (zoek && tabel) {
    zoek.addEventListener("input", () => {
      const q = zoek.value.toLowerCase();
      tabel.querySelectorAll("tbody tr").forEach((tr) => {
        tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
      });
    });
    // Sorteren door op kolomkop te klikken
    tabel.querySelectorAll("th").forEach((th) => {
      th.addEventListener("click", () => {
        const idx = Number(th.dataset.kolom);
        const asc = th.dataset.sort !== "asc";
        tabel.querySelectorAll("th").forEach((t) => delete t.dataset.sort);
        th.dataset.sort = asc ? "asc" : "desc";
        const rijen = Array.from(tabel.tBodies[0].rows);
        rijen.sort((a, b) => {
          const x = a.cells[idx].textContent.trim(), y = b.cells[idx].textContent.trim();
          const nx = parseFloat(x.replace(",", ".")), ny = parseFloat(y.replace(",", "."));
          const r = !isNaN(nx) && !isNaN(ny) ? nx - ny : x.localeCompare(y, "nl");
          return asc ? r : -r;
        });
        rijen.forEach((r) => tabel.tBodies[0].appendChild(r));
      });
    });
  }
})();
