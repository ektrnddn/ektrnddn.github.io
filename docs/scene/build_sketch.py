# Generates src/components/Sketch.astro from scene.html (the SVG) plus the star canvas.
import re, sys
S, out = sys.argv[1], sys.argv[2]
html = open(f"{S}/scene.html").read()
svg_inner = re.search(r'<svg[^>]*>(.*)</svg>', html, re.S).group(1)
svg_inner = re.sub(r'\s*<!--.*?-->', '', svg_inner)
# group layers for parallax: wrap each top-level <g class="..."> with a data-layer factor
factors = {'farfar': '0.1', 'range': '0.2', 'foothill': '0.4', 'near': '0.6', 'meadow': '1'}
def add_layer(m):
    cls = m.group(1).split()[0]
    return f'<g data-layer="{factors.get(cls, "1")}" class="l {m.group(1)}">'
svg_inner = re.sub(r'<g class="(farfar|range|foothill|near|meadow)">', add_layer, svg_inner)
component = '''---
// A night in the Georgian mountains, drawn in ink: a snow-capped range, forested
// ridges with a hilltop church, a meadow, and a small figure walking through it.
// Behind the drawing, a field of stars that scatters around the cursor and drifts
// back; nearby stars join into faint constellations, and a click sends them flying.
// The drawing layers also shift gently with the cursor.
---
<div class="sketch" data-sketch aria-hidden="true">
  <canvas data-stars></canvas>
  <svg viewBox="0 -20 1440 660" preserveAspectRatio="xMidYMax slice" fill="none" stroke-linecap="round" stroke-linejoin="round">
''' + svg_inner.strip('\n') + '''
  </svg>
</div>
<style>
  .sketch { position: relative; width: 100%; height: clamp(300px, 45.8vw, 660px); overflow: hidden; }
  canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
  svg { position: relative; width: 100%; height: 100%; display: block; }
  .l { will-change: transform; }
  .f { fill: #ffffff; stroke: none; }
  .s { fill: none; stroke-width: 1.2; }
  .h { fill: none; stroke-width: 1; opacity: .8; }
  .farfar .s { stroke: #d6d6d6; }
  .range .s { stroke: #3a3a3a; stroke-width: 1.3; }
  .foothill .s { stroke: #8f8f8f; stroke-width: 1.1; }
  .foothill .trees { stroke: #8f8f8f; }
  .near .s { stroke: #2a2a2a; stroke-width: 1.2; }
  .near .trees { stroke: #2a2a2a; }
  .range .h { stroke: #8a8a8a; }
  .snow { fill: none; stroke: #8a8a8a; stroke-width: .9; opacity: .85; }
  .snowline { fill: none; stroke: #c9c9c9; stroke-width: .9; opacity: .9; }
  .near .s { stroke: #2a2a2a; }
  .trees { fill: none; stroke: #2a2a2a; stroke-width: 1; opacity: .75; }
  .church { fill: #2a2a2a; stroke: none; }
  .meadow .s { stroke: #191919; stroke-width: 1.4; }
  .grass { fill: none; stroke: #191919; stroke-width: 1; opacity: .7; }
  .flowers .stem { fill: none; stroke: #191919; stroke-width: 1; opacity: .6; }
  .flowers circle { fill: #d98aa0; stroke: none; }
  .figure .ink { fill: #191919; stroke: #191919; stroke-width: 1; stroke-linejoin: round; }
  .figure .limb { fill: none; stroke: #191919; stroke-width: 5; stroke-linecap: round; }
  .figure .leg { fill: none; stroke: #191919; stroke-width: 4.5; stroke-linecap: round; }
  @media (max-width: 900px) { .sketch { height: clamp(240px, 70vw, 340px); } }
</style>
<script>
  const root = document.querySelector<HTMLElement>('[data-sketch]');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (root) {
    // Drawing layers drift with the cursor; farther layers move less.
    const layers = [...root.querySelectorAll<SVGGElement>('[data-layer]')].map((g) => ({ g, k: parseFloat(g.dataset.layer ?? '1') }));
    // Stars live on a canvas behind the drawing (the white fills of the ridges hide them).
    const cv = root.querySelector<HTMLCanvasElement>('[data-stars]')!;
    const ctx = cv.getContext('2d')!;
    let W = 0, H = 0, dpr = 1;
    type Star = { x: number; y: number; ox: number; oy: number; vx: number; vy: number; r: number; a: number; ph: number; sp: boolean };
    let stars: Star[] = [];
    const rnd = (a: number, b: number) => a + Math.random() * (b - a);
    // A rough skyline in fractions of the box: stars only above it, and away from the intro text on wide screens.
    // The traced skyline, as fractions of the box height, sampled across the width.
    const SKY = [0.479, 0.458, 0.45, 0.458, 0.456, 0.439, 0.418, 0.441, 0.464, 0.484, 0.497, 0.498, 0.496, 0.496, 0.505, 0.515, 0.521, 0.537, 0.549, 0.551, 0.537, 0.521, 0.492, 0.463, 0.418, 0.377, 0.333, 0.284, 0.26, 0.25, 0.261, 0.285, 0.318, 0.336, 0.372, 0.408, 0.438, 0.436, 0.439, 0.439, 0.461, 0.439, 0.452, 0.446, 0.472, 0.492, 0.514, 0.537];
    const skyline = (fx: number) => { const i = fx * (SKY.length - 1), j = Math.floor(i), t = i - j; return (SKY[j] ?? 1) * (1 - t) + (SKY[Math.min(SKY.length - 1, j + 1)] ?? 1) * t; };
    // Keep stars out of the intro text (with a soft edge), wherever it sits over the drawing.
    let tb = { x0: -1, y0: -1, x1: -1, y1: -1 };
    const measureText = () => {
      const kids = [...document.querySelectorAll<HTMLElement>('.hero .text > *')]; if (!kids.length) return;
      const rr = root.getBoundingClientRect();
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const k of kids) { const r = k.getBoundingClientRect(); if (!r.width) continue; x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); }
      tb = { x0: x0 - rr.left, y0: y0 - rr.top, x1: x1 - rr.left, y1: y1 - rr.top };
    };
    const keep = (fx: number, fy: number, _wide: boolean) => {
      const x = fx * W, y = fy * H;
      const dx = Math.max(tb.x0 - x, 0, x - tb.x1), dy = Math.max(tb.y0 - y, 0, y - tb.y1);
      const d = Math.hypot(dx, dy);
      return d > 24 && Math.random() < Math.min(1, (d - 24) / 120);
    };
    const gauss = () => (Math.random() + Math.random() + Math.random() - 1.5) / 1.5;
    const seed = () => {
      dpr = Math.min(2, window.devicePixelRatio || 1);
      W = root.clientWidth; H = root.clientHeight; measureText();
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      stars = [];
      const wide = window.innerWidth > 900;
      const push = (fx: number, fy: number, r: number, a: number, spark = false) => {
        if (fy < 0 || fy > skyline(fx) - 0.02 || !keep(fx, fy, wide)) return false;
        const x = fx * W, y = fy * H;
        stars.push({ x, y, ox: x, oy: y, vx: 0, vy: 0, r, a, ph: rnd(0, 6.28), sp: spark });
        return true;
      };
      // Scattered field.
      const n = Math.round(W / 9); let guard = 0;
      while (stars.length < n && guard++ < n * 40) push(Math.random(), Math.random() * 0.9, rnd(0.55, 1.15), rnd(0.28, 0.65));
      // The Milky Way: a wide diagonal band of faint dots, a dark dust lane through it,
      // and a brighter core low on the right, above the peaks.
      const band = Math.round(W / 2.4); guard = 0; let made = 0;
      const cxAt = (t: number) => 0.96 - t * 0.42, cyAt = (t: number) => -0.02 + t * 0.56;
      while (made < band && guard++ < band * 40) {
        const t = Math.random();
        const off = gauss() * (0.075 + 0.05 * t);
        const lane = Math.abs(off - 0.02) < 0.012;
        if (lane && Math.random() < 0.8) continue;
        const core = t > 0.6 ? (t - 0.6) / 0.4 : 0;
        const fx = cxAt(t) + off + rnd(-0.01, 0.01), fy = cyAt(t) - off * 0.35 + rnd(-0.01, 0.01);
        if (push(fx, fy, rnd(0.5, 1.0) + core * 0.35, rnd(0.2, 0.45) + core * 0.3)) made++;
      }
      // Bright stars with a small sparkle, and one planet.
      guard = 0; made = 0;
      while (made < 9 && guard++ < 400) if (push(Math.random(), Math.random() * 0.7, rnd(1.7, 2.3), rnd(0.75, 0.95), true)) made++;
      push(0.56, 0.1, 3, 0.95, true);
      for (const [dx, dy] of [[0, 0], [0.9, -0.4], [1.7, 0.3], [0.5, 1.1], [-0.8, 0.9], [1.3, 1.4], [-0.3, -1.1]]) push(0.78 + dx * 0.006, 0.07 + dy * 0.012, 1.1, 0.85);
    };
    seed(); new ResizeObserver(seed).observe(root);
    let px = -9999, py = -9999, tx = 0, ty = 0, cx = 0, cy = 0, burst = 0;
    const local = (e: PointerEvent) => { const r = root.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top, r]; };
    window.addEventListener('pointermove', (e) => {
      const [x, y, r] = local(e) as [number, number, DOMRect];
      px = x; py = y;
      tx = Math.max(-1, Math.min(1, (x / r.width - 0.5) * 2));
      ty = Math.max(-1, Math.min(1, (y / r.height - 0.5) * 2));
    }, { passive: true });
    document.addEventListener('pointerleave', () => { px = py = -9999; tx = ty = 0; });
    root.addEventListener('pointerdown', (e) => { const [x, y] = local(e) as [number, number, DOMRect]; px = x; py = y; burst = 1; });
    const draw = (t: number) => {
      ctx.clearRect(0, 0, W, H);
      const R = 110, R2 = R * R;
      const near: Star[] = [];
      for (const s of stars) {
        if (!reduce) {
          const dx = s.x - px, dy = s.y - py, d2 = dx * dx + dy * dy;
          if (d2 < R2) {
            const d = Math.sqrt(d2) || 1, f = (1 - d / R) ** 2 * 1.6;
            s.vx += (dx / d) * f; s.vy += (dy / d) * f;
          }
          if (burst > 0 && d2 < 360 * 360) {
            const d = Math.sqrt(d2) || 1, f = (1 - d / 360) * 22 * burst;
            s.vx += (dx / d) * f; s.vy += (dy / d) * f;
          }
          s.vx += (s.ox - s.x) * 0.015; s.vy += (s.oy - s.y) * 0.015;
          s.vx *= 0.86; s.vy *= 0.86;
          s.x += s.vx; s.y += s.vy;
          if (d2 < 130 * 130 && near.length < 28) near.push(s);
        }
        const tw = reduce ? 1 : 0.85 + 0.15 * Math.sin(t / 900 + s.ph);
        ctx.globalAlpha = s.a * tw;
        ctx.fillStyle = '#191919';
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
        if (s.sp) { const L = s.r * 3.2; ctx.globalAlpha = s.a * tw * 0.35; ctx.lineWidth = 0.6; ctx.strokeStyle = '#191919'; ctx.beginPath(); ctx.moveTo(s.x - L, s.y); ctx.lineTo(s.x + L, s.y); ctx.moveTo(s.x, s.y - L); ctx.lineTo(s.x, s.y + L); ctx.stroke(); }
      }
      burst = 0;
      // Constellations: faint lines between stars that are close to each other and to the cursor.
      if (near.length > 1) {
        ctx.lineWidth = 0.7; ctx.strokeStyle = '#191919';
        for (let i = 0; i < near.length; i++) for (let j = i + 1; j < near.length; j++) {
          const a = near[i], b = near[j], dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy;
          if (d2 < 70 * 70) { ctx.globalAlpha = 0.22 * (1 - d2 / (70 * 70)); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
        }
      }
      ctx.globalAlpha = 1;
      if (!reduce) {
        const ax = tx + 0.2 * Math.sin(t / 4200), ay = ty + 0.15 * Math.cos(t / 5600);
        cx += (ax - cx) * 0.045; cy += (ay - cy) * 0.045;
        for (const { g, k } of layers) g.style.transform = `translate(${(cx * 14 * k).toFixed(2)}px, ${(cy * 6 * k).toFixed(2)}px)`;
      }
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  }
</script>
'''
open(out, 'w').write(component)
print("Sketch.astro written,", len(component), "bytes")
