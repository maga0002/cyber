(function () {
  const donker = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const tekst = donker ? "#cbd5e1" : "#334155";
  const raster = donker ? "rgba(255,255,255,.1)" : "rgba(0,0,0,.08)";

  function alfa(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
  }

  document.querySelectorAll("canvas[data-nist]").forEach((canvas) => {
    const cfg = JSON.parse(canvas.dataset.nist);
    const datasets = cfg.datasets.map((d) => {
      const basis = { label: d.label, data: d.data, borderColor: d.kleur, backgroundColor: d.kleur, spanGaps: true };
      if (cfg.type === "radar") {
        return Object.assign(basis, {
          backgroundColor: d.stippel ? "transparent" : alfa(d.kleur, 0.18),
          borderDash: d.stippel ? [6, 4] : [], borderWidth: 2, pointRadius: d.stippel ? 0 : 3,
        });
      }
      if (cfg.type === "line") {
        return Object.assign(basis, { borderWidth: d.dik ? 3 : 1.5, pointRadius: d.dik ? 4 : 2, tension: 0.2 });
      }
      return Object.assign(basis, { borderRadius: 4, borderWidth: 0 });
    });

    const schaal = { min: 0, max: 5, ticks: { stepSize: 1, color: tekst }, grid: { color: raster } };
    const options = {
      responsive: true,
      maintainAspectRatio: false,
      animation: window.matchMedia("print").matches ? false : undefined,
      plugins: {
        legend: { position: "bottom", labels: { color: tekst, boxWidth: 12 } },
        tooltip: cfg.titels ? { callbacks: { title: (items) => cfg.labels[items[0].dataIndex] + " " + cfg.titels[items[0].dataIndex] } } : {},
      },
    };
    if (cfg.type === "radar") {
      options.scales = { r: Object.assign({}, schaal, {
        beginAtZero: true, angleLines: { color: raster },
        pointLabels: { color: tekst, font: { size: 13, weight: "600" } },
        ticks: { stepSize: 1, color: tekst, backdropColor: "transparent" },
      }) };
    } else {
      options.scales = { y: schaal, x: { ticks: { color: tekst }, grid: { display: false } } };
    }
    new Chart(canvas, { type: cfg.type, data: { labels: cfg.labels, datasets }, options });
  });

  // Grafieken opnieuw schalen voor afdrukken
  window.addEventListener("beforeprint", () => {
    for (const id in Chart.instances) Chart.instances[id].resize();
  });
})();
