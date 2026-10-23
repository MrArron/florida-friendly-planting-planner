/* Map-style pan/zoom for [data-zoom] sheets. CSS transform on a wrapper around svg.plan. */
(function(){
  var MAXZ = 8, reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ICON = {
    plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
    minus: '<svg viewBox="0 0 24 24"><path d="M5 12h14"/></svg>',
    fit: '<svg viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>',
    full: '<svg viewBox="0 0 24 24"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/></svg>',
    exit: '<svg viewBox="0 0 24 24"><path d="M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5"/></svg>'
  };
  function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }

  function init(fig){
    var scroll = fig.querySelector('.scroll'), svg = scroll && scroll.querySelector('svg.plan');
    if (!svg) return;
    var vb = (svg.getAttribute('viewBox') || '0 0 4 3').split(/[\s,]+/).map(Number);
    var aspect = (vb[3] / vb[2]) || 0.75;
    var frame = document.createElement('div'); frame.className = 'zframe';
    scroll.parentNode.insertBefore(frame, scroll); frame.appendChild(scroll);
    var pan = document.createElement('div'); pan.className = 'zpan';
    scroll.insertBefore(pan, svg); pan.appendChild(svg);
    scroll.tabIndex = 0; scroll.setAttribute('role', 'group');
    scroll.setAttribute('aria-label', (fig.querySelector('.sheet-bar b') || {textContent: 'Plan'}).textContent + ' - use plus, minus, 0 and arrow keys to zoom and move');

    var ctl = document.createElement('div'); ctl.className = 'zctl'; ctl.setAttribute('role', 'group'); ctl.setAttribute('aria-label', 'Map controls');
    function mk(cls, label, icon, txt){
      var b = document.createElement('button'); b.type = 'button'; b.className = cls; b.setAttribute('aria-label', label); b.title = label;
      b.innerHTML = icon; return b;
    }
    var bIn = mk('zin', 'Zoom in', ICON.plus), bOut = mk('zout', 'Zoom out', ICON.minus),
        bFit = mk('zfit', 'Reset view (fit)', ICON.fit), bFs = mk('zfull', 'Full screen', ICON.full);
    var gap = document.createElement('div'); gap.className = 'zgap';
    [bIn, bOut, bFit, gap, bFs].forEach(function(n){ ctl.appendChild(n); });
    frame.appendChild(ctl);

    var hint = document.createElement('div'); hint.className = 'zhint';
    hint.textContent = (window.matchMedia && matchMedia('(pointer: coarse)').matches) ? 'Pinch to zoom · drag to move' : 'Scroll to zoom · drag to move';
    frame.appendChild(hint);
    var hintGone = false;
    function dismissHint(){ if (hintGone) return; hintGone = true; hint.classList.add('gone'); setTimeout(function(){ hint.remove(); }, 700); }

    var vw = 0, vh = 0, bw = 0, bh = 0;
    var cur = {z: 1, x: 0, y: 0}, tgt = {z: 1, x: 0, y: 0}, raf = 0, fs = false;

    function limits(z){ // returns clamp fn results
      return {cw: bw * z, ch: bh * z};
    }
    function clampView(v){
      var z = clamp(v.z, 1, MAXZ), cw = bw * z, ch = bh * z, x = v.x, y = v.y;
      x = cw <= vw ? (vw - cw) / 2 : clamp(x, vw - cw, 0);
      y = ch <= vh ? (vh - ch) / 2 : clamp(y, vh - ch, 0);
      return {z: z, x: x, y: y};
    }
    function paint(){
      raf = 0;
      if (!reduce) {
        var dz = tgt.z - cur.z, dx = tgt.x - cur.x, dy = tgt.y - cur.y;
        if (Math.abs(dz) < 0.002 && Math.abs(dx) < 0.3 && Math.abs(dy) < 0.3) { cur.z = tgt.z; cur.x = tgt.x; cur.y = tgt.y; }
        else {
          // ease in log-scale for z so zoom feels multiplicative
          cur.z = cur.z * Math.pow(tgt.z / cur.z, 0.3); cur.x += dx * 0.3; cur.y += dy * 0.3;
          raf = requestAnimationFrame(paint);
        }
      } else { cur.z = tgt.z; cur.x = tgt.x; cur.y = tgt.y; }
      pan.style.transform = 'translate3d(' + cur.x + 'px,' + cur.y + 'px,0) scale(' + cur.z + ')';
      scroll.dataset.zoomScale = cur.z.toFixed(3);
    }
    function sched(){ if (!raf) raf = requestAnimationFrame(paint); }
    function setTarget(v, instant){
      tgt = clampView(v);
      if (instant || reduce) { cur = {z: tgt.z, x: tgt.x, y: tgt.y}; }
      sched();
    }
    // zoom target by factor about viewport point (px,py), based on the *target* view
    function zoomAt(f, px, py, instant){
      var z1 = clamp(tgt.z * f, 1, MAXZ), k = z1 / tgt.z;
      setTarget({z: z1, x: px - (px - tgt.x) * k, y: py - (py - tgt.y) * k}, instant);
    }
    function reset(instant){ setTarget({z: 1, x: 0, y: 0}, instant); }

    function layout(keep){
      var w = scroll.parentNode.clientWidth || frame.clientWidth;
      if (fs) {
        vw = frame.clientWidth; vh = frame.clientHeight;
        bw = Math.min(vw, vh / aspect); bh = bw * aspect;
        scroll.style.height = '';
      } else {
        vw = w;
        var cap = window.innerWidth <= 720 ? 0.75 * window.innerHeight : 0.85 * window.innerHeight;
        vh = Math.round(Math.min(vw * aspect, cap));
        bw = Math.min(vw, vh / aspect); bh = bw * aspect;
        scroll.style.height = vh + 'px';
      }
      if (fs) { vw = scroll.clientWidth || vw; vh = scroll.clientHeight || vh; bw = Math.min(vw, vh / aspect); bh = bw * aspect; }
      pan.style.width = bw + 'px';
      if (keep) setTarget(tgt, true); else reset(true);
    }

    // ---------- pointer handling ----------
    var ptrs = new Map(), moved = false, pinched = false, suppress = false;
    var lastType = 'mouse', drag = null, pinch = null, lastTap = {t: 0, x: 0, y: 0};
    function local(e){ var r = scroll.getBoundingClientRect(); return {x: e.clientX - r.left, y: e.clientY - r.top}; }
    function beginPan(){
      var p = ptrs.values().next().value; drag = {x: p.x, y: p.y, vx: tgt.x, vy: tgt.y};
    }
    function beginPinch(){
      var a = Array.from(ptrs.values()), dx = a[0].x - a[1].x, dy = a[0].y - a[1].y;
      pinch = {d: Math.hypot(dx, dy) || 1, mx: (a[0].x + a[1].x) / 2, my: (a[0].y + a[1].y) / 2, z: tgt.z, vx: tgt.x, vy: tgt.y};
      drag = null; pinched = true; suppress = true;
    }
    scroll.addEventListener('pointerdown', function(e){
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      dismissHint(); lastType = e.pointerType;
      if (ptrs.size === 0) { moved = false; pinched = false; suppress = false; }
      var l = local(e); ptrs.set(e.pointerId, {x: l.x, y: l.y, sx: l.x, sy: l.y, type: e.pointerType});
      if (ptrs.size === 1) beginPan(); else if (ptrs.size === 2) beginPinch();
    });
    scroll.addEventListener('pointermove', function(e){
      var p = ptrs.get(e.pointerId); if (!p) return;
      var l = local(e); p.x = l.x; p.y = l.y;
      if (pinch && ptrs.size >= 2) {
        var a = Array.from(ptrs.values()), d = Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y) || 1,
            mx = (a[0].x + a[1].x) / 2, my = (a[0].y + a[1].y) / 2;
        var z1 = clamp(pinch.z * d / pinch.d, 1, MAXZ);
        var cx = (pinch.mx - pinch.vx) / pinch.z, cy = (pinch.my - pinch.vy) / pinch.z;
        setTarget({z: z1, x: mx - cx * z1, y: my - cy * z1}, true);
        return;
      }
      if (!drag) return;
      var dx = p.x - drag.x, dy = p.y - drag.y;
      if (!moved && Math.hypot(p.x - p.sx, p.y - p.sy) > 5) {
        moved = true; suppress = true; scroll.classList.add('zdrag');
        try { scroll.setPointerCapture(e.pointerId); } catch (_) {}
      }
      if (moved) setTarget({z: tgt.z, x: drag.vx + dx, y: drag.vy + dy}, true);
    });
    function end(e){
      var p = ptrs.get(e.pointerId); if (!p) return;
      ptrs.delete(e.pointerId);
      if (ptrs.size === 0) {
        scroll.classList.remove('zdrag'); pinch = null; drag = null;
        // touch double-tap
        if (e.type === 'pointerup' && p.type !== 'mouse' && !moved && !pinched) {
          var now = e.timeStamp, l = local(e);
          if (now - lastTap.t < 320 && Math.hypot(l.x - lastTap.x, l.y - lastTap.y) < 30) {
            zoomAt(2, l.x, l.y); suppress = true; lastTap.t = 0;
          } else lastTap = {t: now, x: l.x, y: l.y};
        }
      } else if (ptrs.size === 1) { pinch = null; beginPan(); var q = ptrs.values().next().value; q.sx = q.x; q.sy = q.y; }
      else if (ptrs.size >= 2) beginPinch();
    }
    scroll.addEventListener('pointerup', end);
    scroll.addEventListener('pointercancel', end);
    scroll.addEventListener('lostpointercapture', function(e){ if (ptrs.has(e.pointerId) && e.pointerType === 'mouse') end(e); });
    // a drag/pinch must not become a click (capture phase, before the plan's click-to-inspect handler)
    scroll.addEventListener('click', function(e){
      if (suppress) { e.stopPropagation(); e.preventDefault(); suppress = false; }
    }, true);
    scroll.addEventListener('dblclick', function(e){
      if (lastType !== 'mouse') return;
      var l = local(e); zoomAt(2, l.x, l.y); e.preventDefault();
    });
    scroll.addEventListener('wheel', function(e){
      e.preventDefault(); dismissHint();
      var d = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1);
      var l = local(e), f = Math.exp(-d * (e.ctrlKey ? 0.01 : 0.0018));
      zoomAt(f, l.x, l.y);
    }, {passive: false});

    // ---------- controls & keys ----------
    function center(f){ zoomAt(f, vw / 2, vh / 2); }
    bIn.addEventListener('click', function(){ dismissHint(); center(1.6); });
    bOut.addEventListener('click', function(){ dismissHint(); center(1 / 1.6); });
    bFit.addEventListener('click', function(){ dismissHint(); reset(); });
    scroll.addEventListener('keydown', function(e){
      var k = e.key, s = 80, h = true;
      if (k === '+' || k === '=') center(1.4);
      else if (k === '-' || k === '_') center(1 / 1.4);
      else if (k === '0') reset();
      else if (k === 'ArrowLeft') setTarget({z: tgt.z, x: tgt.x + s, y: tgt.y});
      else if (k === 'ArrowRight') setTarget({z: tgt.z, x: tgt.x - s, y: tgt.y});
      else if (k === 'ArrowUp') setTarget({z: tgt.z, x: tgt.x, y: tgt.y + s});
      else if (k === 'ArrowDown') setTarget({z: tgt.z, x: tgt.x, y: tgt.y - s});
      else h = false;
      if (h) { e.preventDefault(); dismissHint(); }
    });

    // ---------- full screen ----------
    function setFs(on){
      if (on === fs) return;
      if (!on && document.fullscreenElement === fig && document.exitFullscreen) { try { document.exitFullscreen(); } catch (_) {} }
      fs = on; fig.classList.toggle('zfs', on); document.body.classList.toggle('zfs-lock', on);
      bFs.innerHTML = on ? ICON.exit : ICON.full;
      var t = on ? 'Exit full screen' : 'Full screen'; bFs.title = t; bFs.setAttribute('aria-label', t);
      bFs.setAttribute('aria-pressed', on ? 'true' : 'false');
      layout(false);
      if (!on) { try { fig.scrollIntoView({block: 'start'}); } catch (_) {} }
    }
    bFs.addEventListener('click', function(){
      dismissHint();
      if (!fs) {
        setFs(true);
        if (fig.requestFullscreen) { try { var pr = fig.requestFullscreen(); if (pr && pr.catch) pr.catch(function(){}); } catch (_) {} }
      } else {
        setFs(false);
      }
    });
    document.addEventListener('fullscreenchange', function(){
      if (fs && document.fullscreenElement !== fig && !fig._zEntering) setFs(false);
      else if (fs) layout(false);
    });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && fs) setFs(false); });

    layout(false);
    if (window.ResizeObserver) new ResizeObserver(function(){
      var w = fs ? frame.clientWidth : (scroll.parentNode.clientWidth);
      if (fs ? (frame.clientWidth !== vw || frame.clientHeight !== vh) : (w !== vw)) layout(true);
    }).observe(frame);
    window.addEventListener('resize', function(){ layout(true); });
    fig._zoom = {get: function(){ return cur; }, setFs: setFs};
  }
  document.querySelectorAll('[data-zoom]').forEach(init);
})();