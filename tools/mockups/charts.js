/* charts.js: tiny SVG chart helpers for the mock-up pages (illustrative only).
   Each page sets its numbers at the top, then calls these. */
const C = { ink: '#25342a', muted: '#5f6f63', grid: '#e3ece4', accent: '#2f7a5d', sage: '#9db8a6', alert: '#b93a3a', amber: '#d9922b' };
function svg(w, h, inner) { return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" preserveAspectRatio="none">${inner}</svg>`; }
// Vertical bars. values: numbers; opts.colors per bar optional
function bars(id, labels, values, opts = {}) {
  const W = 700, H = 300, pad = 30, max = Math.max(...values) * 1.15, bw = (W - pad * 2) / values.length;
  let g = '';
  for (let i = 0; i < 4; i++) g += `<line x1="${pad}" x2="${W - pad}" y1="${20 + i * 70}" y2="${20 + i * 70}" stroke="${C.grid}" stroke-width="2"/>`;
  values.forEach((v, i) => {
    const h = (v / max) * 230, x = pad + i * bw + bw * 0.18;
    g += `<rect x="${x}" y="${250 - h}" width="${bw * 0.64}" height="${h}" rx="4" fill="${(opts.colors && opts.colors[i]) || C.accent}"/>`;
    g += `<text x="${x + bw * 0.32}" y="285" font-size="18" fill="${C.muted}" text-anchor="middle">${labels[i]}</text>`;
  });
  document.getElementById(id).innerHTML = svg(W, H, g);
}
// Horizontal bars with value labels
function hbars(id, labels, values, fmt, colors) {
  const W = 700, H = 40 + labels.length * 52, max = Math.max(...values) * 1.1;
  let g = '';
  labels.forEach((l, i) => {
    const y = 14 + i * 52, w = (values[i] / max) * 400;
    g += `<text x="0" y="${y + 26}" font-size="20" fill="${C.ink}">${l}</text>`;
    g += `<rect x="190" y="${y + 6}" width="${w}" height="28" rx="4" fill="${(colors && colors[i]) || C.sage}"/>`;
    g += `<text x="${200 + w}" y="${y + 27}" font-size="19" fill="${C.muted}">${fmt(values[i])}</text>`;
  });
  document.getElementById(id).innerHTML = svg(W, H, g);
}
// Line chart: series = [{values, color, dash, name}] (name shows in the legend)
function lines(id, labels, series) {
  const W = 700, H = 300, pad = 30, all = series.flatMap(s => s.values), max = Math.max(...all) * 1.1, min = Math.min(...all) * 0.9;
  const x = i => pad + (i * (W - pad * 2)) / (labels.length - 1), y = v => 250 - ((v - min) / (max - min)) * 220;
  let g = '';
  for (let i = 0; i < 4; i++) g += `<line x1="${pad}" x2="${W - pad}" y1="${30 + i * 70}" y2="${30 + i * 70}" stroke="${C.grid}" stroke-width="2"/>`;
  series.forEach(s => {
    g += `<polyline fill="none" stroke="${s.color}" stroke-width="5" ${s.dash ? `stroke-dasharray="${s.dash}"` : ''} stroke-linejoin="round" points="${s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')}"/>`;
  });
  labels.forEach((l, i) => { g += `<text x="${x(i)}" y="288" font-size="18" fill="${C.muted}" text-anchor="middle">${l}</text>`; });
  let lx = pad;
  series.forEach(s => {
    if (!s.name) return;
    g += `<line x1="${lx}" x2="${lx + 28}" y1="12" y2="12" stroke="${s.color}" stroke-width="5" ${s.dash ? `stroke-dasharray="${s.dash}"` : ''}/>`;
    g += `<text x="${lx + 36}" y="18" font-size="18" fill="${C.muted}">${s.name}</text>`;
    lx += 60 + s.name.length * 10;
  });
  document.getElementById(id).innerHTML = svg(W, H, g);
}
