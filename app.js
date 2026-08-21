/* ==========================================================
   DIMA VISION
   Povestea rulează ca un film de 20 de secunde, legat de scroll.
   Trecutul e sepia și granulat; prezentul e curat și rece.
   La final, muchia de sticlă din logo taie ecranul și te lasă
   pe pagina Coming Soon.
   Three.js r128 (atmosferă) + GSAP ScrollTrigger (progres)
   ========================================================== */

(function () {
  'use strict';

  /* ---------- utilitare ---------- */
  var clamp = function (v, a, b) { return v < a ? a : v > b ? b : v; };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var range = function (p, a, b) { return clamp((p - a) / (b - a), 0, 1); };
  var smooth = function (t) { return t * t * (3 - 2 * t); };
  var easeOut = function (t) { return 1 - Math.pow(1 - t, 3); };

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var isTouch = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;

  /* ==========================================================
     GRAFICA CADRELOR
     Desen de linie, monocrom, colorat prin currentColor.
     Se poate înlocui oricând cu fotografii reale (vezi `photo`).
     ========================================================== */
  var svg = function (inner, vb) {
    return '<svg viewBox="' + (vb || '0 0 600 300') + '" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>';
  };

  var ART = {
    /* satul din care a plecat meseria */
    village: function () {
      var s = '<circle class="faint" cx="452" cy="84" r="52"/>';
      s += '<path class="faint" d="M0 198C78 168 132 184 206 170 288 154 338 176 408 162 476 148 542 166 600 154"/>';
      s += '<path d="M0 236C88 200 148 218 218 204 300 188 350 212 430 198 500 186 552 204 600 194"/>';
      /* biserica */
      s += '<path d="M292 236v-48h30v48"/><path d="M292 188l15-36 15 36"/><path d="M307 152v-16"/><path d="M300 143h14"/>';
      /* case */
      s += '<path d="M150 236v-22l20-16 20 16v22"/><path d="M196 236v-16l16-13 16 13v16"/>';
      s += '<path class="faint" d="M366 236v-18l17-14 17 14v18"/><path class="faint" d="M414 236v-13l13-11 13 11v13"/>';
      s += '<path class="faint" d="M96 236v-14l14-11 14 11v14"/>';
      s += '<path class="faint" d="M0 236h600"/>';
      return svg(s);
    },

    /* foaia de sticlă și tăietura trasă cu mâna */
    pane: function () {
      var s = '<path d="M176 54l252-18 20 214-252 20z"/>';
      s += '<path class="faint" d="M212 74l58-4 16 178-58 5z"/>';
      s += '<path class="dash" d="M198 96l232 108"/>';
      s += '<path d="M186 84l16 20"/><circle class="fill" cx="196" cy="92" r="4"/>';
      s += '<path class="faint" d="M150 292h300"/>';
      return svg(s);
    },

    /* roata căruței */
    wheel: function () {
      var s = '<circle cx="300" cy="150" r="102"/><circle class="faint" cx="300" cy="150" r="88"/>';
      for (var i = 0; i < 12; i++) {
        var a = (i / 12) * Math.PI * 2;
        s += '<path d="M' + (300 + Math.cos(a) * 16).toFixed(1) + ' ' + (150 + Math.sin(a) * 16).toFixed(1) +
             'L' + (300 + Math.cos(a) * 88).toFixed(1) + ' ' + (150 + Math.sin(a) * 88).toFixed(1) + '"/>';
      }
      s += '<circle cx="300" cy="150" r="16"/><circle class="fill" cx="300" cy="150" r="4"/>';
      s += '<path class="faint" d="M120 268h360"/>';
      s += '<path class="faint" d="M300 150h180l24 44"/>';
      return svg(s);
    },

    /* drumul lung, cu stâlpi care se pierd în zare */
    road: function () {
      var s = '<path class="faint" d="M0 138h600"/>';
      s += '<path d="M86 288L286 142"/><path d="M514 288L314 142"/>';
      for (var i = 0; i < 7; i++) {
        var t = i / 7, y = lerp(286, 150, t), w = lerp(26, 3, t);
        s += '<path d="M' + (300 - w / 2) + ' ' + y.toFixed(1) + 'h' + w.toFixed(1) + '"/>';
      }
      for (var j = 0; j < 6; j++) {
        var u = j / 6, yy = lerp(280, 152, u), h = lerp(52, 6, u);
        var xl = lerp(52, 282, u), xr = lerp(548, 318, u);
        s += '<path class="faint" d="M' + xl.toFixed(1) + ' ' + yy.toFixed(1) + 'v-' + h.toFixed(1) + '"/>';
        s += '<path class="faint" d="M' + xr.toFixed(1) + ' ' + yy.toFixed(1) + 'v-' + h.toFixed(1) + '"/>';
      }
      s += '<path class="faint" d="M180 138c40-22 78-14 120-24 44-10 82 2 120-10"/>';
      return svg(s);
    },

    /* anii, ca muchii de sticlă stivuite */
    stack: function () {
      var s = '';
      for (var i = 0; i < 16; i++) {
        var y = 60 + i * 12;
        var x1 = 150 + i * 4, x2 = 452 - i * 3;
        s += '<path class="' + (i % 3 ? 'faint' : '') + '" d="M' + x1 + ' ' + y + 'H' + x2 + '"/>';
      }
      s += '<path d="M150 60L214 252"/><path class="faint" d="M452 60L407 252"/>';
      s += '<circle class="fill" cx="300" cy="150" r="3"/>';
      return svg(s);
    },

    /* două generații, două foi */
    diptych: function () {
      var s = '<path class="dash" d="M92 78h190v170H92z"/>';
      s += '<path d="M318 62h190v186H318z"/>';
      s += '<path class="faint" d="M118 100h60v128h-60z"/><path class="faint" d="M344 84h64v142h-64z"/>';
      s += '<path class="faint" d="M282 160h36"/>';
      s += '<circle class="fill" cx="300" cy="160" r="3"/>';
      return svg(s);
    },

    /* timpul schimbă uneltele: mâna într-o parte, mașina în cealaltă */
    split: function () {
      /* stânga: diamantul de tăiat, ținut în mână */
      var s = '<path d="M62 212h176"/><path class="faint" d="M62 230h176"/>';
      s += '<path d="M96 86l34-22 68 104-34 22z"/>';
      s += '<path class="faint" d="M112 96l24-16"/>';
      s += '<path class="fill" d="M196 188l14 24-24-6z"/>';
      s += '<path class="dash" d="M72 198h134"/>';
      /* dreapta: capul CNC */
      s += '<path d="M362 212h176"/><path class="faint" d="M362 230h176"/>';
      s += '<path d="M406 70h94v58h-94z"/><path d="M440 128h26v40h-26z"/>';
      s += '<path class="fill" d="M447 168h12l-4 26h-4z"/>';
      s += '<path class="faint" d="M382 92h24M500 92h24"/><path class="faint" d="M406 70h94"/>';
      s += '<path class="dash" d="M394 198h134"/>';
      /* muchia de sticlă din logo, exact pe mijloc */
      s += '<path class="fill" d="M300 16c3 62 4 166 0 268-4-102-3-206 0-268z"/>';
      return svg(s);
    },

    /* linia de prelucrare */
    cnc: function () {
      var s = '<path d="M60 210h480"/><path class="faint" d="M60 232h480"/>';
      for (var i = 0; i < 11; i++) s += '<circle cx="' + (86 + i * 43) + '" cy="196" r="13"/>';
      s += '<path class="faint" d="M96 178h408"/>';
      s += '<path d="M120 68h360v20H120z"/><path d="M140 88v-20M460 88v-20"/>';
      s += '<path d="M282 88h48v42h-48z"/><path d="M300 130h12v26h-12z"/><path d="M303 156l3 22-9 0 6-22z"/>';
      s += '<path class="dash" d="M96 168h408"/>';
      return svg(s);
    },

    /* viziunea: proiectul, înainte de piesă */
    screen: function () {
      var s = '<path d="M148 66h304v176H148z"/><path d="M104 262h392l-24-20H128z"/><path class="faint" d="M258 252h84"/>';
      /* cabina desenată în perspectivă, pe ecran */
      s += '<path d="M212 118h116v96H212z"/><path class="faint" d="M328 118l44-24v96l-44 24"/>';
      s += '<path class="faint" d="M212 118l44-24h116"/><path class="dash" d="M270 118v96"/>';
      s += '<path class="faint" d="M196 226h208"/>';
      return svg(s);
    },

    /* standardul nou: oglinda cu lumină */
    mirror: function () {
      var s = '<ellipse cx="300" cy="132" rx="92" ry="106"/>';
      s += '<ellipse class="faint" cx="300" cy="132" rx="104" ry="118"/>';
      s += '<ellipse class="faint" cx="300" cy="132" rx="116" ry="130"/>';
      s += '<path class="faint" d="M246 84c14-16 34-24 54-24"/>';
      s += '<path d="M150 262h300"/><path class="faint" d="M270 262v-14h60v14"/>';
      s += '<path class="faint" d="M300 248v-10"/>';
      return svg(s);
    }
  };

  /* ==========================================================
     CADRELE
     `photo` e opțional: pune calea unei fotografii (ex. 'media/01.jpg')
     și apare în locul desenului. Dacă fișierul lipsește, rămâne desenul.
     ========================================================== */
  var SCENES = [
    { art: 'village', place: 'Bociu, Huedin', sub: 'Cluj, România', lines: ['Totul a început aici.'], photo: '01-sat.png' },
    { art: 'pane', lines: ['O meserie veche,', 'dusă din generație în generație.'], photo: '02-atelier-vechi.png' },
    { art: 'wheel', lines: ['Cu căruța și calul,', 'în căutarea oamenilor care aveau nevoie.'], photo: '03-caruta.png' },
    { art: 'road', lines: ['Drumuri lungi.', 'Încredere câștigată pas cu pas.'], photo: '04-drum.png' },
    { art: 'stack', lines: ['Anii au trecut.', 'Pasiunea a rămas.'], photo: '05-ani.png' },
    { art: 'diptych', lines: ['A doua generație a continuat.'], photo: '06-generatii.png' },
    { art: 'pane', lines: ['Experiență. Răbdare. Calitate.'], photo: '07-maiestrie.png' },
    { art: 'split', lines: ['Timpul schimbă uneltele.'], photo: '08-unelte.png' },
    { art: 'cnc', lines: ['Tehnologia duce mai departe.'], photo: '09-cnc.png' },
    { art: 'screen', lines: ['Viziunea noastră.'], photo: '10-proiect.png' },
    { art: 'mirror', lines: ['Aceleași valori.', 'Un nou standard.'], photo: '11-oglinda.png' },
    { claim: true, lines: ['Următorul capitol', '<em>începe acum.</em>'], words: 'Tradiție. Experiență. Evoluție.', photo: null },
    { logo: true, words: 'Clar, se vede.', photo: null }
  ];

  var SPLIT_INDEX = 7;   /* cadrul în care trecutul și prezentul stau față în față */

  /* ---------- încadrarea fotografiilor, după raportul lor real (fără decupaj) ---------- */
  function artBudget() {
    var vw = window.innerWidth, vh = window.innerHeight;
    var maxW = vw <= 640 ? Math.min(520, vw * 0.92) : Math.min(860, vw * 0.88);
    var maxH = vh <= 620 ? Math.min(400, vh * 0.46) : Math.min(640, vh * 0.60);
    return { maxW: maxW, maxH: maxH };
  }
  function sizeArt(el, ratio) {
    var b = artBudget();
    var w = b.maxW, h = w / ratio;
    if (h > b.maxH) { h = b.maxH; w = h * ratio; }
    el.style.width = w.toFixed(1) + 'px';
    el.style.height = h.toFixed(1) + 'px';
  }

  /* ---------- construirea cadrelor ---------- */
  var film = document.getElementById('film');
  var nodes = [];

  SCENES.forEach(function (sc, i) {
    var el = document.createElement('section');
    el.className = 'scene' + (sc.claim ? ' scene--claim' : '');
    el.setAttribute('aria-label', 'Cadrul ' + (i + 1) + ' din ' + SCENES.length);

    var html = '';
    if (sc.logo) {
      html += '<img class="scene__logo" src="logo-light.png" alt="DIMA VISION" />';
    } else if (ART[sc.art]) {
      html += '<div class="scene__art" data-art>' + ART[sc.art]() + '</div>';
    }
    if (sc.place) html += '<p class="scene__place">' + sc.place + '</p>';
    if (sc.sub) html += '<p class="scene__sub">' + sc.sub + '</p>';
    if (sc.lines) sc.lines.forEach(function (l) { html += '<p class="scene__line">' + l + '</p>'; });
    if (sc.words) html += '<p class="scene__words">' + sc.words + '</p>';
    el.innerHTML = html;

    film.appendChild(el);

    var node = { el: el, art: el.querySelector('[data-art], .scene__logo'), load: null };

    /* fotografia se cere abia când cadrul se apropie; desenul ține locul până atunci */
    if (sc.photo) {
      node.load = function () {
        node.load = null;
        var img = new Image();
        img.className = 'scene__photo';
        img.alt = '';
        img.decoding = 'async';
        img.onload = function () {
          var holder = el.querySelector('[data-art]');
          if (holder) {
            node.ratio = img.naturalWidth / img.naturalHeight;
            sizeArt(holder, node.ratio);
            holder.innerHTML = ''; holder.appendChild(img);
          }
        };
        img.src = sc.photo;
      };
    }

    nodes.push(node);
  });

  /* ---------- lucruri care merg oricum ---------- */
  window.addEventListener('resize', function () {
    nodes.forEach(function (n) {
      if (n.ratio && n.art) sizeArt(n.art, n.ratio);
    });
  });

  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  var replay = document.getElementById('replay');
  if (replay) replay.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
  });

  (function revealOnScroll() {
    var items = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) {
      [].forEach.call(items, function (el) { el.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.14 });
    [].forEach.call(items, function (el, i) {
      el.style.transitionDelay = Math.min(i % 4, 3) * 80 + 'ms';
      io.observe(el);
    });
  })();

  /* ---------- fallback: fără WebGL sau cu mișcare redusă ---------- */
  function webglOk() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (e) { return false; }
  }

  if (!window.THREE || !webglOk() || reduced) {
    document.body.classList.add('plain');
    return;
  }

  /* ==========================================================
     ATMOSFERA (Three.js)
     Un singur quad pe tot ecranul: granulație de film, vignetă,
     lumină care se plimbă, plus praf în aer. Toate se calmează
     pe măsură ce povestea ajunge în prezent.
     ========================================================== */
  var atmo = document.getElementById('atmo');
  var renderer, scene3, cam3, quad, dust;
  var era = 0, time = 0, lastT = performance.now();

  var FRAG = [
    'precision mediump float;',
    'varying vec2 vUv;',
    'uniform float uTime, uEra, uAspect;',
    'uniform vec2 uRes;',
    'float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }',
    'float noise(vec2 p){',
    '  vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);',
    '  return mix(mix(hash(i),hash(i+vec2(1.0,0.0)),f.x), mix(hash(i+vec2(0.0,1.0)),hash(i+vec2(1.0,1.0)),f.x), f.y);',
    '}',
    'void main(){',
    '  vec2 uv = vUv;',
    '  vec2 c = uv - 0.5; c.x *= uAspect;',
    '  float r = length(c);',
    '  vec3 A = mix(vec3(0.075,0.055,0.030), vec3(0.030,0.035,0.044), uEra);',
    '  vec3 B = mix(vec3(0.290,0.205,0.100), vec3(0.082,0.130,0.168), uEra);',
    '  vec3 col = mix(A, B, smoothstep(0.95, 0.0, r));',
    '  vec2 lp = vec2(sin(uTime*0.06)*0.26, 0.20 + cos(uTime*0.045)*0.12);',
    '  float leak = smoothstep(0.72, 0.0, length(c - lp));',
    '  col += mix(vec3(0.58,0.40,0.15), vec3(0.20,0.34,0.46), uEra) * leak * (0.17 - uEra*0.07);',
    '  float n = noise(uv*3.2 + vec2(uTime*0.02, uTime*0.014));',
    '  col += (n - 0.5) * (0.040 - uEra*0.022);',
    '  col *= 1.0 - smoothstep(0.34, 1.08, r) * mix(0.88, 0.58, uEra);',
    '  float gr = hash(uv*uRes + fract(uTime)*vec2(31.7,17.3));',
    '  col += (gr - 0.5) * mix(0.085, 0.020, uEra);',
    '  float sc = step(0.9988, hash(vec2(floor(uv.x*420.0), floor(uTime*9.0))));',
    '  col += sc * (1.0 - uEra) * 0.055;',
    '  gl_FragColor = vec4(col, 1.0);',
    '}'
  ].join('\n');

  var VERT = [
    'varying vec2 vUv;',
    'void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }'
  ].join('\n');

  var DUST_VERT = [
    'attribute float aSeed;',
    'attribute float aSize;',
    'uniform float uTime, uEra, uPx;',
    'varying float vA;',
    'void main(){',
    '  float sp = 0.02 + aSeed * 0.05;',
    '  float y = mod(position.y + uTime * sp + aSeed, 2.2) - 1.1;',
    '  float x = position.x + sin(uTime * (0.15 + aSeed*0.3) + aSeed*6.28) * 0.06;',
    '  gl_Position = vec4(x, y, 0.0, 1.0);',
    '  gl_PointSize = aSize * uPx * (1.0 - uEra*0.35);',
    '  vA = (0.30 + aSeed*0.45) * (1.0 - uEra*0.62);',
    '}'
  ].join('\n');

  var DUST_FRAG = [
    'precision mediump float;',
    'uniform float uEra;',
    'varying float vA;',
    'void main(){',
    '  float d = length(gl_PointCoord - 0.5);',
    '  float a = smoothstep(0.5, 0.0, d) * vA;',
    '  vec3 col = mix(vec3(0.86,0.70,0.40), vec3(0.62,0.78,0.90), uEra);',
    '  gl_FragColor = vec4(col, a);',
    '}'
  ].join('\n');

  function initAtmo() {
    scene3 = new THREE.Scene();
    cam3 = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isTouch ? 1.5 : 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    atmo.appendChild(renderer.domElement);

    quad = new THREE.Mesh(
      new THREE.PlaneGeometry(2, 2),
      new THREE.ShaderMaterial({
        vertexShader: VERT, fragmentShader: FRAG, depthTest: false, depthWrite: false,
        uniforms: {
          uTime: { value: 0 }, uEra: { value: 0 },
          uAspect: { value: 1 }, uRes: { value: new THREE.Vector2(1, 1) }
        }
      })
    );
    quad.frustumCulled = false;
    scene3.add(quad);

    /* praful din atelier */
    var N = isTouch ? 130 : 260;
    var pos = new Float32Array(N * 3), seed = new Float32Array(N), size = new Float32Array(N);
    for (var i = 0; i < N; i++) {
      pos[i * 3] = Math.random() * 2 - 1;
      pos[i * 3 + 1] = Math.random() * 2 - 1;
      pos[i * 3 + 2] = 0;
      seed[i] = Math.random();
      size[i] = 0.8 + Math.random() * 2.6;
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 1));
    g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));

    dust = new THREE.Points(g, new THREE.ShaderMaterial({
      vertexShader: DUST_VERT, fragmentShader: DUST_FRAG,
      transparent: true, depthTest: false, depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uEra: { value: 0 }, uPx: { value: 1 } }
    }));
    dust.frustumCulled = false;
    dust.renderOrder = 2;
    scene3.add(dust);

    resize();
    window.addEventListener('resize', resize);
    requestAnimationFrame(loop);
  }

  function resize() {
    var w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h);
    var pr = renderer.getPixelRatio();
    quad.material.uniforms.uAspect.value = w / h;
    quad.material.uniforms.uRes.value.set(w * pr * 0.5, h * pr * 0.5);
    dust.material.uniforms.uPx.value = pr;
  }

  function loop(now) {
    var dt = Math.min((now - lastT) / 1000, 0.05);
    lastT = now;
    time += dt;

    smoothed += (target - smoothed) * (1 - Math.exp(-dt * 10));
    if (Math.abs(target - smoothed) < 0.0004) smoothed = target;
    paint(smoothed);

    quad.material.uniforms.uTime.value = time;
    quad.material.uniforms.uEra.value = era;
    dust.material.uniforms.uTime.value = time;
    dust.material.uniforms.uEra.value = era;
    renderer.render(scene3, cam3);

    requestAnimationFrame(loop);
  }

  /* ==========================================================
     PROGRESUL POVEȘTII
     ========================================================== */
  var reel = document.getElementById('reel');
  var spine = document.getElementById('spine');
  var tc = document.getElementById('tc');
  var tcVal = document.getElementById('tcVal');
  var hint = document.getElementById('hint');
  var fade = document.getElementById('atmoFade');
  var flash = document.getElementById('flash');
  var topBar = document.getElementById('top');
  var root = document.documentElement;

  var target = 0, smoothed = 0;
  var N = SCENES.length;
  var STORY_END = 0.90;                 /* după asta se face trecerea */
  var step = STORY_END / N;
  var overlap = step * 0.34;

  var GOLD = [201, 162, 39], STEEL = [146, 196, 226];

  function paint(p) {
    /* trecerea de la sepia la modern, exact în jurul cadrului cu uneltele */
    var eraStart = (SPLIT_INDEX - 0.35) * step;
    var eraEnd = (SPLIT_INDEX + 1.6) * step;
    era = smooth(range(p, eraStart, eraEnd));

    var ac = [
      Math.round(lerp(GOLD[0], STEEL[0], era)),
      Math.round(lerp(GOLD[1], STEEL[1], era)),
      Math.round(lerp(GOLD[2], STEEL[2], era))
    ];
    root.style.setProperty('--accent', 'rgb(' + ac[0] + ',' + ac[1] + ',' + ac[2] + ')');
    root.style.setProperty('--era', era.toFixed(3));

    /* cadrele */
    var near = Math.round(p / step);
    for (var k = Math.max(0, near - 1); k < Math.min(N, near + 3); k++) {
      if (nodes[k].load) nodes[k].load();
    }

    for (var i = 0; i < N; i++) {
      var a = i * step, b = (i + 1) * step;
      var inn = i === 0 ? 1 : range(p, a - overlap * 0.15, a + overlap);
      var out = i === N - 1 ? range(p, 0.905, 0.948) : range(p, b - overlap * 0.15, b + overlap * 0.85);
      var o = Math.min(inn, 1 - out);
      var n = nodes[i];

      if (o <= 0.002) {
        if (n.el.style.visibility !== 'hidden') {
          n.el.style.visibility = 'hidden';
          n.el.style.opacity = '0';
        }
        continue;
      }
      n.el.style.visibility = 'visible';
      n.el.style.opacity = o.toFixed(3);

      /* mișcare mică, cât să nu pară un slideshow */
      var local = clamp((p - a) / (b - a), 0, 1);
      var y = lerp(26, -26, local);
      var sc = lerp(1.02, 0.985, local);
      n.el.style.transform = 'translate3d(0,' + y.toFixed(1) + 'px,0)';
      if (n.art) n.art.style.transform = 'translate3d(0,' + (y * -0.55).toFixed(1) + 'px,0) scale(' + sc.toFixed(3) + ')';
    }

    /* muchia de sticlă: crește odată cu povestea, se aprinde la „Timpul schimbă uneltele" */
    var sIn = range(p, 0.03, 0.10);
    var splitGlow = Math.min(range(p, (SPLIT_INDEX - 0.1) * step, (SPLIT_INDEX + 0.25) * step),
                             1 - range(p, (SPLIT_INDEX + 0.7) * step, (SPLIT_INDEX + 1.05) * step));
    var cut = range(p, 0.905, 0.968);            /* taie ecranul la final */
    var sy = lerp(0.10, 1.0, easeOut(range(p, 0.03, STORY_END)));
    var sx = 1 + Math.pow(cut, 2.2) * 900 + splitGlow * 1.6;

    spine.style.opacity = (Math.max(sIn * (0.45 + splitGlow * 0.55), cut)).toFixed(3);
    spine.style.transform = 'translateX(-50%) scaleY(' + sy.toFixed(3) + ') scaleX(' + sx.toFixed(2) + ')';
    spine.style.filter = 'brightness(' + (1 + splitGlow * 0.5 + cut * 1.6).toFixed(2) + ')';

    /* cortina finală: muchia taie ecranul, albul se stinge în fundalul paginii */
    var flashOn = Math.min(range(p, 0.902, 0.945), 1 - range(p, 0.972, 0.998));
    flash.style.opacity = flashOn.toFixed(3);
    fade.style.opacity = range(p, 0.950, 0.996).toFixed(3);
    topBar.style.opacity = (1 - Math.min(range(p, 0.90, 0.94), 1 - range(p, 0.985, 1))).toFixed(3);

    /* riglă de timp și indiciu */
    var secs = Math.min(20, Math.round(p / STORY_END * 20));
    tcVal.textContent = '0:' + (secs < 10 ? '0' : '') + secs;
    tc.style.opacity = Math.min(range(p, 0.02, 0.07), 1 - range(p, 0.88, 0.94)).toFixed(3);
    hint.style.opacity = (1 - range(p, 0.01, 0.05)).toFixed(3);
  }

  /* legarea de scroll */
  function bind() {
    if (window.gsap && window.ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
      ScrollTrigger.create({
        trigger: reel, start: 'top top', end: 'bottom bottom',
        onUpdate: function (self) { target = self.progress; }
      });
      window.addEventListener('orientationchange', function () {
        setTimeout(function () { ScrollTrigger.refresh(); }, 250);
      });
    } else {
      var manual = function () {
        var r = reel.getBoundingClientRect();
        var total = r.height - window.innerHeight;
        target = total > 0 ? clamp(-r.top / total, 0, 1) : 0;
      };
      window.addEventListener('scroll', manual, { passive: true });
      window.addEventListener('resize', manual);
      manual();
    }
  }

  try {
    initAtmo();
  } catch (e) {
    document.body.classList.add('plain');
    return;
  }

  bind();

  /* dacă pagina se încarcă deja derulată, pornim din locul corect */
  (function sync() {
    var r = reel.getBoundingClientRect();
    var total = r.height - window.innerHeight;
    target = smoothed = total > 0 ? clamp(-r.top / total, 0, 1) : 0;
    paint(smoothed);
  })();
})();
