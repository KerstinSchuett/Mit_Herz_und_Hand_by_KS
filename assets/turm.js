/* Wattmusikanten-Turm: die Original-Illustration als ein Stück,
   in feinen Streifen verformt – der Turm schwankt von unten nach oben, ohne Nähte. */
(() => {
  const cv = document.getElementById('turm'); if (!cv) return;
  const ctx = cv.getContext('2d');
  const IW = 455, IH = 681;                 // Bildmaße in Original-Pixeln
  const VW = 560, VH = 712, FUSS = 702;     // Bühne
  const img = new Image(); img.decoding = 'async';
  const basis = (document.currentScript && document.currentScript.src) ? document.currentScript.src.replace(/turm\.js.*$/, 'turm/') : 'assets/turm/';
  img.onload = start; img.src = basis + 'turm.webp';

  let scale = 1, ox = 0, oy = 0, dpr = 1;
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    const r = cv.getBoundingClientRect();
    cv.width = Math.max(1, Math.round(r.width * dpr)); cv.height = Math.max(1, Math.round(r.height * dpr));
    scale = Math.min(r.width / VW, r.height / VH);
    ox = (r.width - VW * scale) / 2; oy = r.height - VH * scale;
  }
  window.addEventListener('resize', () => { resize(); if (!spielt && img.complete) zeichne(); });
  resize();

  const TAU = Math.PI * 2;
  const ruhig = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let spielt = !ruhig, sichtbar = true, laeuft = false, zeit = 0, letzte = performance.now(), schubs = [];

  cv.addEventListener('pointerdown', e => {
    if (ruhig) return;
    const r = cv.getBoundingClientRect();
    if (schubs.length >= 2) schubs.shift();
    schubs.push({ t: zeit, s: (e.clientX - r.left) < r.width / 2 ? 1 : -1 });
  });

  // Seitliche Auslenkung in Höhe h (0 = Füße der Kuh, 1 = Krabbe), verzögert nach oben
  function auslenkung(t, h) {
    const k = Math.pow(h, 1.5), d = h * .7;
    let x = 22 * k * Math.sin(TAU * (t - d) / 4) * (.75 + .25 * Math.sin(TAU * (t - d) / 8));
    for (const s of schubs) { const dt = t - s.t - d * .6; if (dt > 0) x += s.s * 45 * k * Math.exp(-dt * 1.5) * Math.sin(dt * 7); }
    return Math.max(-48, Math.min(48, x));
  }
  function schatten(x, y, rx, ry, a) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, rx);
    g.addColorStop(0, `rgba(30,42,51,${a})`); g.addColorStop(1, 'rgba(30,42,51,0)');
    ctx.save(); ctx.translate(x, y); ctx.scale(1, ry / rx); ctx.translate(-x, -y);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, rx, 0, TAU); ctx.fill(); ctx.restore();
  }

  function zeichne() {
    const now = performance.now();
    if (spielt) zeit += Math.min(.05, (now - letzte) / 1000);
    letzte = now;
    schubs = schubs.filter(s => zeit - s.t < 6);
    const t = zeit;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.setTransform(dpr * scale, 0, 0, dpr * scale, dpr * ox, dpr * oy);

    const hop = Math.sin(TAU * t / 2 - Math.PI / 2);        // Atmen/Wippen
    const streck = 1 + .018 * (.5 + .5 * hop);               // Turm streckt sich leicht
    const x0 = (VW - IW) / 2, hoehe = IH * streck, top = FUSS - hoehe;
    schatten(VW / 2 + auslenkung(t, .15) * .4, FUSS + 2, 200, 16, .2);

    // in Streifen zeichnen: jede Zeile etwas versetzt
    const STREIFEN = 4, sw = img.naturalWidth / IW;
    for (let y = 0; y < IH; y += STREIFEN) {
      const h = 1 - (y + STREIFEN / 2) / IH;             // 1 oben, 0 unten
      const dx = auslenkung(t, h);
      const sy = Math.min(STREIFEN, IH - y);
      ctx.drawImage(img, 0, y * sw, img.naturalWidth, sy * sw, x0 + dx, top + y * streck, IW, sy * streck + .6);
    }
    if (spielt && sichtbar) requestAnimationFrame(zeichne); else laeuft = false;
  }
  function start() {
    resize();
    if (ruhig) { zeichne(); return; }
    if ('IntersectionObserver' in window) new IntersectionObserver(es => {
      sichtbar = es[0].isIntersecting; letzte = performance.now();
      if (sichtbar && !laeuft) { laeuft = true; requestAnimationFrame(zeichne); }
    }).observe(cv);
    else { laeuft = true; requestAnimationFrame(zeichne); }
  }
})();
