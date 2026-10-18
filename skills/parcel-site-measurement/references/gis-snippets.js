// Browser-console snippets for ArcGIS JS 3.x county map viewers (example: BCPAO MapView; adapt hosts and service names to your county).
// Run them with the browser's javascript tool on the map tab.

// 1. Parcel geometry, spatial reference and map state
(() => {
  const g = map.graphics.graphics[0].geometry;
  return {
    wkid: map.spatialReference.wkid,          // BCPAO: 2881 = NAD83 HARN FL East, US survey ft
    rings: g.rings.map(r => r.map(p => [+p[0].toFixed(2), +p[1].toFixed(2)])),
    extent: map.extent.toJson(), level: map.getLevel(), scale: map.getScale(),
    layers: map.layerIds.map(id => id + '|' + map.getLayer(id).url)
  };
})();

// 2. Full-screen aerial overlay with parcel line and labeled grid (local coords = E-OX, N-OY)
window.OX = 758000; window.OY = 1418550;           // pick a round origin near the site
window.showAerY = async function (x0, y0, w, h, step, year, gamma) {
  let cv = document.getElementById('aerov');
  if (!cv) { cv = document.createElement('canvas'); cv.id = 'aerov'; cv.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000'; document.body.appendChild(cv); }
  const W = 1100, H = 900; cv.width = W; cv.height = H; cv.style.display = 'block';
  const s = Math.min(W / w, H / h), pw = Math.round(w * s), ph = Math.round(h * s);
  let bm;
  for (let i = 0; i < 5; i++) {               // server rate-limits: retry 403s
    try {
      const u = `https://www.bcpao.us/arcgis/rest/services/Brevard_Aerials_${year}/MapServer/export?dpi=96&format=png24&bbox=${OX + x0},${OY + y0},${OX + x0 + w},${OY + y0 + h}&bboxSR=2881&imageSR=2881&size=${pw},${ph}&f=image`;
      const r = await fetch(u); if (r.status !== 200) throw 1; bm = await createImageBitmap(await r.blob()); break;
    } catch (e) { await new Promise(z => setTimeout(z, 900)); }
  }
  const x = cv.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, W, H); x.drawImage(bm, 0, 0, pw, ph);
  if (gamma) { const d = x.getImageData(0, 0, pw, ph), a = d.data; for (let i = 0; i < a.length; i += 4) for (let k = 0; k < 3; k++) a[i + k] = Math.min(255, Math.pow(a[i + k] / 255, gamma) * 255); x.putImageData(d, 0, 0); }
  const ring = map.graphics.graphics[0].geometry.rings[0];
  const P = (E, N) => [(E - OX - x0) * s, ph - (N - OY - y0) * s];
  x.strokeStyle = 'red'; x.lineWidth = 2; x.beginPath(); ring.forEach((p, i) => { const [a, c] = P(p[0], p[1]); i ? x.lineTo(a, c) : x.moveTo(a, c); }); x.stroke();
  x.strokeStyle = 'rgba(255,255,0,0.4)'; x.lineWidth = 1; x.font = 'bold 13px sans-serif'; x.fillStyle = 'yellow';
  for (let gx = Math.ceil(x0 / step) * step; gx <= x0 + w; gx += step) { const px = (gx - x0) * s; x.beginPath(); x.moveTo(px, 0); x.lineTo(px, ph); x.stroke(); x.fillText(gx, px + 2, 13); }
  for (let gy = Math.ceil(y0 / step) * step; gy <= y0 + h; gy += step) { const py = ph - (gy - y0) * s; x.beginPath(); x.moveTo(0, py); x.lineTo(pw, py); x.stroke(); x.fillText(gy, 2, py - 2); }
  return { s, pw, ph };   // screenshot px per ft = s * (screenshot width / viewport width)
};
window.hideAer = () => { const c = document.getElementById('aerov'); if (c) c.style.display = 'none'; };
// usage: await showAerY(-20, 85, 100, 90, 5, 2025, 0.6)   // try every aerial year that responds (BCPAO: 2025, 2026)

// 3. Automatic pool / deck fit: largest connected component + minimum-area rotated rectangle
window.fitShape = async function (bbox, test, ftPerPx) {   // bbox=[xmin,ymin,xmax,ymax] in state-plane ft
  const W = Math.round((bbox[2] - bbox[0]) / ftPerPx), H = Math.round((bbox[3] - bbox[1]) / ftPerPx);
  const u = `https://www.bcpao.us/arcgis/rest/services/Brevard_Aerials_2026/MapServer/export?dpi=96&format=png24&bbox=${bbox.join(',')}&bboxSR=2881&imageSR=2881&size=${W},${H}&f=image`;
  const bm = await createImageBitmap(await (await fetch(u)).blob());
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.drawImage(bm, 0, 0);
  const id = x.getImageData(0, 0, W, H).data, set = new Uint8Array(W * H);
  for (let i = 0; i < W * H; i++) if (test(id[i * 4], id[i * 4 + 1], id[i * 4 + 2])) set[i] = 1;
  const seen = new Uint8Array(W * H); let best = [];
  for (let k = 0; k < W * H; k++) { if (!set[k] || seen[k]) continue; const comp = [], st = [k]; seen[k] = 1;
    while (st.length) { const cc = st.pop(); comp.push(cc); const cx = cc % W, cy = (cc / W) | 0;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = cx + dx, ny = cy + dy; if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue; const nk = ny * W + nx; if (set[nk] && !seen[nk]) { seen[nk] = 1; st.push(nk); } } }
    if (comp.length > best.length) best = comp; }
  let r = null;
  for (let a = 0; a < 180; a += 0.5) { const t = a * Math.PI / 180, co = Math.cos(t), si = Math.sin(t); let u0 = 1e9, u1 = -1e9, v0 = 1e9, v1 = -1e9;
    for (const k of best) { const px = k % W, py = (k / W) | 0, uu = px * co + py * si, vv = -px * si + py * co; if (uu < u0) u0 = uu; if (uu > u1) u1 = uu; if (vv < v0) v0 = vv; if (vv > v1) v1 = vv; }
    const A = (u1 - u0) * (v1 - v0); if (!r || A < r.A) r = { A, a, u0, u1, v0, v1 }; }
  const t = r.a * Math.PI / 180, co = Math.cos(t), si = Math.sin(t);
  const corners = [[r.u0, r.v0], [r.u1, r.v0], [r.u1, r.v1], [r.u0, r.v1]].map(([u, v]) => [u * co - v * si, u * si + v * co])
    .map(([px, py]) => [+(bbox[0] + px * ftPerPx).toFixed(1), +(bbox[3] - py * ftPerPx).toFixed(1)]);
  return { L1: +((r.u1 - r.u0) * ftPerPx).toFixed(1), L2: +((r.v1 - r.v0) * ftPerPx).toFixed(1), angle: r.a, corners };
};
// pool:  await fitShape([758010,1418555,758250,1418755], (r,g,b) => b>r+35 && b>g && b>120, 0.2)
// deck:  test = (r,g,b) => (r>185&&g>175&&b>140&&Math.abs(r-g)<35&&(r-b)<70) || (b>r+35&&b>g&&b>120)

// 4. Draw a fitted polygon back on the live map to confirm with the person
// map.graphics.add(new esri.Graphic(new esri.geometry.Polygon({rings:[[...corners, corners[0]]], spatialReference: map.spatialReference}),
//   new esri.symbol.SimpleFillSymbol('solid', new esri.symbol.SimpleLineSymbol('solid', new esri.Color([255,0,255]), 2), new esri.Color([0,0,0,0]))));

// 5. Site video (Google Photos → YouTube embed): click the player, then keys: '0' = start, 'k' = play/pause.
//    Take zoomed screenshots every ~1 s; deliberately review the first 5 seconds.
