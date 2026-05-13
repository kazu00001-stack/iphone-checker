(function () {
  "use strict";

  const SITES = ["iosys", "mobile_mix", "ichome"];
  const SITE_LABELS = { iosys: "iosys", mobile_mix: "mobile-mix", ichome: "1丁目" };

  const yen = (n) => "¥" + n.toLocaleString("ja-JP");
  const signedYen = (n) => (n >= 0 ? "+" : "") + yen(n);

  function getMileRate() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = parseFloat(params.get("rate"));
    if (!Number.isNaN(fromQuery) && fromQuery >= 0) return fromQuery;
    return 1.0;
  }

  function capacitySortKey(capacity) {
    const m = String(capacity).match(/(\d+)\s*(TB|GB)/i);
    if (!m) return 0;
    let n = parseInt(m[1], 10);
    if (m[2].toUpperCase() === "TB") n *= 1024;
    return n;
  }

  function buildRows(payload, mileRate) {
    const appleMap = new Map();
    for (const m of payload.apple_models || []) {
      appleMap.set(`${m.name}|${m.capacity}`, m);
    }
    const quoteMap = new Map();
    for (const q of payload.quotes || []) {
      const k = `${q.name}|${q.capacity}`;
      if (!quoteMap.has(k)) quoteMap.set(k, {});
      const existing = quoteMap.get(k)[q.site];
      if (existing === undefined || q.price_jpy > existing) {
        quoteMap.get(k)[q.site] = q.price_jpy;
      }
    }

    const rows = [];
    for (const [k, apple] of appleMap.entries()) {
      const quotes = quoteMap.get(k) || {};
      let bestSite = null;
      let bestPrice = null;
      for (const [site, price] of Object.entries(quotes)) {
        if (bestPrice === null || price > bestPrice) {
          bestPrice = price;
          bestSite = site;
        }
      }
      const profit = bestPrice !== null ? bestPrice - apple.price_jpy : null;
      const miles = Math.round((apple.price_jpy * mileRate) / 100);
      rows.push({
        name: apple.name,
        capacity: apple.capacity,
        apple_price: apple.price_jpy,
        is_fallback: apple.is_fallback,
        quotes,
        best_site: bestSite,
        best_price: bestPrice,
        profit,
        miles,
      });
    }
    rows.sort((a, b) => {
      if (a.name !== b.name) return a.name.localeCompare(b.name);
      return capacitySortKey(a.capacity) - capacitySortKey(b.capacity);
    });
    return rows;
  }

  function renderTable(rows) {
    const tbody = document.getElementById("tbody");
    tbody.innerHTML = "";
    for (const r of rows) {
      const tr = document.createElement("tr");
      const cells = [];
      cells.push(`<td>${r.name}</td>`);
      cells.push(`<td>${r.capacity}</td>`);
      cells.push(
        `<td class="num">${yen(r.apple_price)}${r.is_fallback ? '<span class="badge">推定</span>' : ""}</td>`
      );
      for (const site of SITES) {
        const v = r.quotes[site];
        cells.push(`<td class="num">${v !== undefined ? yen(v) : "-"}</td>`);
      }
      if (r.best_price !== null) {
        cells.push(
          `<td class="num">${yen(r.best_price)} <span class="site">(${SITE_LABELS[r.best_site] || r.best_site})</span></td>`
        );
      } else {
        cells.push(`<td class="num">-</td>`);
      }
      if (r.profit !== null) {
        const cls = r.profit >= 0 ? "profit-pos" : "profit-neg";
        cells.push(`<td class="num ${cls}" data-order="${r.profit}">${signedYen(r.profit)}</td>`);
      } else {
        cells.push(`<td class="num" data-order="-99999999">-</td>`);
      }
      cells.push(`<td class="num">${r.miles.toLocaleString("ja-JP")}</td>`);
      tr.innerHTML = cells.join("");
      tbody.appendChild(tr);
    }

    if ($.fn.dataTable.isDataTable("#result-table")) {
      $("#result-table").DataTable().destroy();
    }
    $("#result-table").DataTable({
      pageLength: 50,
      order: [[7, "desc"]],
      language: { url: "https://cdn.datatables.net/plug-ins/2.0.8/i18n/ja.json" },
    });
  }

  async function load() {
    const status = document.getElementById("status");
    const wrapper = document.getElementById("table-wrapper");
    try {
      const resp = await fetch("data.json", { cache: "no-cache" });
      if (!resp.ok) throw new Error("data.json fetch HTTP " + resp.status);
      const data = await resp.json();
      const mileRate = getMileRate();
      document.getElementById("rate-input").value = mileRate.toFixed(1);
      document.getElementById("fetched-at").textContent = data.fetched_at || "未取得";
      const rows = buildRows(data, mileRate);
      renderTable(rows);
      status.textContent = "";
      wrapper.style.display = "";
    } catch (e) {
      status.innerHTML = `<p class="error">データの読み込みに失敗しました: ${e.message}</p>`;
      console.error(e);
    }
  }

  document.getElementById("rate-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const v = document.getElementById("rate-input").value;
    const params = new URLSearchParams(window.location.search);
    params.set("rate", v);
    window.location.search = params.toString();
  });

  load();
})();
