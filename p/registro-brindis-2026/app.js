(function () {
  'use strict';
  var EV = window.EVENTO;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var el = function (tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

  // ---------- datos del evento ----------
  $$('[data-ev]').forEach(function (e) { e.textContent = EV[e.dataset.ev]; });
  $$('[data-ev-href]').forEach(function (e) { e.href = EV[e.dataset.evHref]; });

  // ---------- API ----------
  function api(accion, data) {
    var body = Object.assign({ accion: accion }, data || {});
    if (window.MOCK_API) return window.MOCK_API(body);
    if (!window.API_URL) return Promise.resolve({ ok: false, error: 'El registro abre muy pronto.' });
    return fetch(window.API_URL, { method: 'POST', body: JSON.stringify(body) })
      .then(function (r) { return r.json(); })
      .catch(function () { return { ok: false, error: 'No hay conexión. Intenta de nuevo.' }; });
  }

  function toast(msg) {
    var t = $('#toast'); t.textContent = msg; t.classList.add('on');
    clearTimeout(toast.t); toast.t = setTimeout(function () { t.classList.remove('on'); }, 2600);
  }
  function soloDigitos(v) { return String(v || '').replace(/\D/g, ''); }
  function wa10(v) { var d = soloDigitos(v); if (d.length === 12 && d.indexOf('52') === 0) d = d.slice(2); return d.length === 10 ? d : ''; }
  function ocupado(b, on, txt) { b.disabled = on; if (txt) { if (on) { b.dataset.t = b.textContent; b.textContent = txt; } else if (b.dataset.t) b.textContent = b.dataset.t; } }
  var ss = {
    get: function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} },
    del: function (k) { try { sessionStorage.removeItem(k); } catch (e) {} }
  };

  // ---------- techo LED (estilo Salón Camarena) ----------
  var PALETA = ['#1B3F8B', '#2F6BD8', '#0E2350', '#7FB6FF', '#C9D3E0', '#3D2FA8', '#00A3E0', '#6A4CFF', '#E6EBF2', '#D9467F'];
  function pintarLED(cv, w, h, t, semilla) {
    var c = cv.getContext('2d');
    var s = Math.max(48, Math.round(w / 14));
    var cols = Math.ceil(w / s) + 1, rows = Math.ceil(h / s) + 1;
    var rnd = function (i) { var x = Math.sin(i * 12.9898 + semilla) * 43758.5453; return x - Math.floor(x); };
    c.fillStyle = '#070F24'; c.fillRect(0, 0, w, h);
    for (var y = 0; y < rows; y++) for (var x = 0; x < cols; x++) for (var k = 0; k < 2; k++) {
      var i = (y * cols + x) * 2 + k;
      var r = rnd(i);
      var idx = r < .08 ? 9 : Math.floor(rnd(i + 7) * 9);
      var pulso = .55 + .45 * Math.sin(t / 1400 + r * 6.28);
      c.globalAlpha = (.35 + .65 * rnd(i + 3)) * pulso;
      c.fillStyle = PALETA[idx];
      c.beginPath();
      var X = x * s, Y = y * s;
      if (k === 0) { c.moveTo(X, Y); c.lineTo(X + s, Y); c.lineTo(X, Y + s); }
      else { c.moveTo(X + s, Y); c.lineTo(X + s, Y + s); c.lineTo(X, Y + s); }
      c.closePath(); c.fill();
    }
    c.globalAlpha = 1;
    c.strokeStyle = 'rgba(7,15,36,.9)'; c.lineWidth = Math.max(2, s / 26);
    for (var a = 0; a < rows; a++) { c.beginPath(); c.moveTo(0, a * s); c.lineTo(cols * s, a * s); c.stroke(); }
    for (var b = 0; b < cols; b++) { c.beginPath(); c.moveTo(b * s, 0); c.lineTo(b * s, rows * s); c.stroke(); }
    for (var d = -rows; d < cols; d++) { c.beginPath(); c.moveTo((d + rows) * s, 0); c.lineTo(d * s, rows * s); c.stroke(); }
  }
  (function ledHero() {
    var cv = $('.hero .led'); if (!cv) return;
    var quieto = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    function tam() { var r = cv.getBoundingClientRect(); var p = Math.min(2, window.devicePixelRatio || 1); cv.width = r.width * p; cv.height = r.height * p; }
    tam(); window.addEventListener('resize', tam);
    function cuadro(t) { if (!document.hidden && !$('#v-registro').hidden) pintarLED(cv, cv.width, cv.height, quieto ? 0 : t, 3); if (!quieto) requestAnimationFrame(cuadro); }
    requestAnimationFrame(cuadro);
  })();

  // ---------- navegacion ----------
  function ruta() {
    var h = location.hash.replace(/^#/, '') || 'registro';
    var inv = /^invitacion=([A-Za-z0-9]+)/.exec(h);
    var v = inv ? 'invitacion' : (['registro', 'mi-registro', 'panel'].indexOf(h) >= 0 ? h : 'registro');
    $$('.vista').forEach(function (s) { s.hidden = s.id !== 'v-' + v; });
    $$('.tabs a').forEach(function (a) { a.classList.toggle('on', a.dataset.tab === v); });
    if (inv) mostrarInvitacion(inv[1]);
    if (v === 'panel') iniciarPanel();
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', ruta);

  // ---------- registro ----------
  var actual = null;
  var fNum = $('#num');
  function buscar() {
    var n = soloDigitos(fNum.value);
    $('#e-num').textContent = '';
    if (!n) { $('#e-num').textContent = 'Escribe tu número de distribuidor.'; fNum.focus(); return; }
    var b = $('#b-buscar'); ocupado(b, true, 'Buscando…');
    api('buscar', { num: n }).then(function (r) {
      ocupado(b, false);
      if (!r.ok) { $('#e-num').textContent = r.error; return; }
      if (!r.abierto) { $('#e-num').textContent = 'El registro ya está cerrado.'; return; }
      if (r.registrado) {
        $('#e-num').textContent = '';
        var p = $('#e-num'); p.textContent = 'Este número ya tiene un registro. ';
        var a = el('a', null, 'Consúltalo en Mi registro'); a.href = '#mi-registro'; p.appendChild(a);
        return;
      }
      actual = r;
      $('#d-nombre').textContent = r.nombre;
      $('#d-tipo').textContent = r.tipo;
      $('#d-sub').textContent = r.subterritorio;
      $('#d-pre').textContent = r.premier;
      var g = $('#o-pareja'); g.textContent = '';
      $('#g-pareja').hidden = !r.pareja.length;
      if (r.pareja.length) {
        [['ambos', 'Asistimos los dos: ' + r.pareja[0] + ' y ' + r.pareja[1]], ['0', 'Solo ' + r.pareja[0]], ['1', 'Solo ' + r.pareja[1]]]
          .forEach(function (o) {
            var l = el('label', 'opcion'); var i = el('input'); i.type = 'radio'; i.name = 'asisten'; i.value = o[0];
            l.appendChild(i); l.appendChild(document.createTextNode(o[1])); g.appendChild(l);
          });
      }
      $('#l-emps').textContent = ''; actualizarEmps();
      $('#paso1').hidden = true; $('#paso2').hidden = false;
      $('#wa').focus();
    });
  }
  $('#b-buscar').addEventListener('click', buscar);
  $('#b-ir').addEventListener('click', function (e) { e.preventDefault(); $('#f-reg').scrollIntoView({ behavior: 'smooth', block: 'start' }); setTimeout(function () { if (!$('#paso1').hidden) fNum.focus({ preventScroll: true }); }, 400); });
  $('#f-reg').addEventListener('input', function () { $('#e-reg').textContent = ''; });
  $('#f-reg').addEventListener('change', function () { $('#e-reg').textContent = ''; });
  fNum.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); buscar(); } });
  $('#b-cambiar').addEventListener('click', function () { actual = null; $('#paso2').hidden = true; $('#paso1').hidden = false; $('#e-reg').textContent = ''; fNum.select(); });

  function actualizarEmps() {
    var cajas = $$('#l-emps .emp');
    cajas.forEach(function (c, i) { $('h3', c).textContent = 'Emprendedor ' + (i + 1); });
    var max = actual ? actual.maxEmprendedores : 2;
    $('#b-emp').hidden = cajas.length >= max;
    $('#c-emps').hidden = !cajas.length;
    if (!cajas.length) $('#ok-emps').checked = false;
  }
  $('#b-emp').addEventListener('click', function () {
    var n = $$('#l-emps .emp').length + 1;
    var c = el('div', 'emp');
    c.appendChild(el('h3'));
    var q = el('button', 'link quitar', 'Quitar'); q.type = 'button';
    q.addEventListener('click', function () { c.remove(); actualizarEmps(); });
    c.appendChild(q);
    var l1 = el('label', null, 'Nombre completo'); var i1 = el('input'); i1.className = 'e-nom'; i1.autocomplete = 'off'; i1.id = 'emp-n-' + Date.now(); l1.htmlFor = i1.id;
    var l2 = el('label', null, 'WhatsApp del emprendedor'); var w = el('div', 'tel'); w.appendChild(el('span', null, '+52'));
    var i2 = el('input'); i2.className = 'e-wa'; i2.inputMode = 'tel'; i2.placeholder = '10 dígitos'; i2.maxLength = 14; i2.id = 'emp-w-' + Date.now(); l2.htmlFor = i2.id; w.appendChild(i2);
    [l1, i1, l2, w].forEach(function (x) { c.appendChild(x); });
    $('#l-emps').appendChild(c); actualizarEmps(); i1.focus();
  });

  $('#f-reg').addEventListener('submit', function (e) {
    e.preventDefault();
    if (!actual) return;
    var err = $('#e-reg'); err.textContent = '';
    var wa = wa10($('#wa').value);
    var asisten = ($('input[name=asisten]:checked') || {}).value;
    if (actual.pareja.length && !asisten) { err.textContent = 'Indica quién asiste.'; return; }
    if (!wa) { err.textContent = 'Escribe tu WhatsApp a 10 dígitos.'; $('#wa').focus(); return; }
    var emps = $$('#l-emps .emp').map(function (c) { return { nombre: $('.e-nom', c).value.trim(), whatsapp: wa10($('.e-wa', c).value) }; });
    for (var i = 0; i < emps.length; i++) {
      if (emps[i].nombre.split(/\s+/).length < 2) { err.textContent = 'Escribe nombre y apellido del emprendedor ' + (i + 1) + '.'; return; }
      if (!emps[i].whatsapp) { err.textContent = 'El WhatsApp del emprendedor ' + (i + 1) + ' debe tener 10 dígitos.'; return; }
    }
    if (emps.length && !$('#ok-emps').checked) { err.textContent = 'Confirma que tus emprendedores están próximos a firmar.'; return; }
    var b = $('#b-enviar'); ocupado(b, true, 'Enviando…');
    api('registrar', { num: actual.num, whatsapp: wa, asisten: asisten || '', emprendedores: emps }).then(function (r) {
      ocupado(b, false);
      if (!r.ok) { err.textContent = r.error; return; }
      $('#r-folio').textContent = r.folio;
      pintarPersonas($('#r-personas'), r.personas);
      $('#paso2').hidden = true; $('#paso3').hidden = false;
      $('#f-reg').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  function claseEstado(e) { return 'estado e-' + String(e).split(' ')[0]; }
  function pintarPersonas(ul, ps) {
    ul.textContent = '';
    ps.forEach(function (p) {
      var li = el('li'); var d = el('div');
      d.appendChild(el('span', null, p.nombre)); d.appendChild(el('small', null, p.tipo));
      li.appendChild(d);
      var der = el('div');
      der.appendChild(el('span', claseEstado(p.estado), p.estado));
      if (p.invitacion) { var a = el('a', 'link', 'Ver invitación'); a.href = '#invitacion=' + p.invitacion; der.appendChild(document.createElement('br')); der.appendChild(a); }
      li.appendChild(der); ul.appendChild(li);
    });
  }

  // ---------- mi registro ----------
  $('#f-con').addEventListener('submit', function (e) {
    e.preventDefault();
    var err = $('#e-con'); err.textContent = '';
    var n = soloDigitos($('#c-num').value), wa = wa10($('#c-wa').value);
    if (!n || !wa) { err.textContent = 'Escribe tu número de distribuidor y tu WhatsApp a 10 dígitos.'; return; }
    var b = $('button[type=submit]', this); ocupado(b, true, 'Consultando…');
    api('consultar', { num: n, whatsapp: wa }).then(function (r) {
      ocupado(b, false);
      if (!r.ok) { err.textContent = r.error; $('#r-con').hidden = true; return; }
      $('#rc-folio').textContent = r.folio;
      var vistos = {}, ps = r.personas.map(function (p) { if (p.invitacion && vistos[p.invitacion]) { p = Object.assign({}, p, { invitacion: '' }); } else if (p.invitacion) vistos[p.invitacion] = 1; return p; });
      pintarPersonas($('#rc-personas'), ps);
      $('#r-con').hidden = false;
    });
  });

  // ---------- invitacion (flyer) ----------
  function cargarImg(src) { return new Promise(function (ok) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = function () { ok(null); }; i.src = src; }); }
  function fuentes() {
    if (!document.fonts || !document.fonts.load) return Promise.resolve();
    return Promise.all(['400 40px Limelight', '400 40px Poiret', '500 40px Bodoni', '700 40px Bodoni', '400 20px Figtree', '500 20px Figtree', '600 20px Figtree', '700 20px Figtree'].map(function (f) { return document.fonts.load(f); })).catch(function () {});
  }
  function ajustar(c, texto, maxW, tam, peso, fam) {
    var t = tam; c.font = peso + ' ' + t + 'px ' + fam;
    while (c.measureText(texto).width > maxW && t > 30) { t -= 2; c.font = peso + ' ' + t + 'px ' + fam; }
    return t;
  }
  function envolver(c, texto, maxW) {
    var ps = texto.split(' '), lineas = [], l = '';
    ps.forEach(function (p) { var prueba = l ? l + ' ' + p : p; if (c.measureText(prueba).width > maxW && l) { lineas.push(l); l = p; } else l = prueba; });
    if (l) lineas.push(l); return lineas;
  }
  window.dibujarInvitacion = function (datos) {
    var W = 1080, H = 1350, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    var c = cv.getContext('2d');
    return Promise.all([fuentes(), cargarImg('img/w-chasep.png'), cargarImg('img/w-healthy.png'), cargarImg('img/w-mejab.png'), cargarImg('img/cam-hero.jpg')]).then(function (res) {
      var logos = res.slice(1, 4), foto = res[4];
      var led = document.createElement('canvas'); led.width = W; led.height = 560; pintarLED(led, W, 560, 900, 3);
      c.fillStyle = '#070F24'; c.fillRect(0, 0, W, H);
      // foto real del Salon Camarena arriba
      if (foto) { var fh = 640, fw = fh * foto.width / foto.height; c.drawImage(foto, (W - fw) * .3, 0, fw, fh); }
      var g = c.createLinearGradient(0, 0, 0, 640);
      g.addColorStop(0, 'rgba(7,15,36,0.55)'); g.addColorStop(.25, 'rgba(7,15,36,0.15)'); g.addColorStop(.7, 'rgba(7,15,36,0.8)'); g.addColorStop(1, 'rgba(7,15,36,1)');
      c.fillStyle = g; c.fillRect(0, 0, W, 640);
      // logos blancos, discretos
      var alts = [62, 62, 42], gap = 46, ls = logos.map(function (l, k) { return l ? { img: l, h: alts[k], w: alts[k] * l.width / l.height } : null; }).filter(Boolean);
      var tw = ls.reduce(function (s, b) { return s + b.w; }, 0) + gap * (ls.length - 1), lx = (W - tw) / 2;
      c.globalAlpha = .92; ls.forEach(function (b) { c.drawImage(b.img, lx, 82 + (62 - b.h) / 2, b.w, b.h); lx += b.w + gap; }); c.globalAlpha = 1;
      c.textAlign = 'center'; c.fillStyle = '#E6EBF2';
      c.font = '600 26px Figtree'; c.fillText('I N V I T A C I Ó N   P E R S O N A L', W / 2, 300);
      c.save(); c.shadowColor = 'rgba(127,182,255,.65)'; c.shadowBlur = 26;
      c.fillStyle = '#fff'; c.font = '400 150px Limelight'; c.fillText('BRINDIS', W / 2, 440); c.restore();
      c.fillStyle = '#E6EBF2'; c.font = '400 44px Poiret'; c.fillText('C H A S E P   G L O B A L', W / 2 - 70, 512);
      c.fillStyle = '#7FB6FF'; c.font = '400 58px Limelight'; c.fillText('2026', W / 2 + 330, 514);
      // banda LED inferior
      c.save(); c.translate(0, H); c.scale(1, -1); c.globalAlpha = .55; c.drawImage(led, 0, 0, W, 170); c.restore();
      var g2 = c.createLinearGradient(0, H - 170, 0, H); g2.addColorStop(0, 'rgba(7,15,36,1)'); g2.addColorStop(1, 'rgba(7,15,36,0.35)');
      c.fillStyle = g2; c.fillRect(0, H - 170, W, 170);
      c.strokeStyle = 'rgba(201,211,224,.55)'; c.lineWidth = 3; c.strokeRect(36, 36, W - 72, H - 72);
      // nombres, centrados entre el titulo y el bloque de datos
      var arriba = 560, abajo = 860, bloques = [];
      c.font = '600 30px Figtree';
      bloques.push({ t: datos.nombres.length > 1 ? 'Los esperamos' : 'Te esperamos', f: '600 30px Figtree', col: '#7FB6FF', h: 54 });
      datos.nombres.forEach(function (n, k) {
        if (k === 1) bloques.push({ t: '&', f: '500 48px Bodoni', col: '#C9D3E0', h: 64 });
        var t = ajustar(c, n, W - 180, datos.nombres.length > 1 ? 72 : 88, 500, 'Bodoni');
        bloques.push({ t: n, f: '500 ' + t + 'px Bodoni', col: '#fff', h: t + 16 });
      });
      if (datos.invitadoPor) bloques.push({ t: 'Invitado por ' + datos.invitadoPor, f: '400 30px Figtree', col: '#C9D3E0', h: 56 });
      var alto = bloques.reduce(function (s, b) { return s + b.h; }, 0);
      var y = arriba + (abajo - arriba - alto) / 2;
      bloques.forEach(function (b) { c.font = b.f; c.fillStyle = b.col; c.fillText(b.t, W / 2, y + b.h * .72); y += b.h; });
      // datos del evento
      y = 900;
      c.fillStyle = 'rgba(201,211,224,.45)'; c.fillRect(W / 2 - 170, y, 340, 2);
      c.fillStyle = '#fff'; c.font = '700 44px Figtree'; c.fillText(EV.fecha, W / 2, y + 70);
      c.fillStyle = '#C9D3E0'; c.font = '500 34px Figtree'; c.fillText('Acceso ' + EV.acceso + '  ·  Inicio ' + EV.inicio + '  ·  Cierre ' + EV.fin, W / 2, y + 122);
      c.save(); c.shadowColor = 'rgba(127,182,255,.6)'; c.shadowBlur = 18; c.fillStyle = '#fff'; c.font = '400 60px Limelight'; c.fillText(EV.lugar.toUpperCase(), W / 2, y + 204); c.restore();
      c.fillStyle = '#C9D3E0'; c.font = '400 28px Figtree';
      envolver(c, EV.direccion, W - 220).forEach(function (l, k) { c.fillText(l, W / 2, y + 246 + k * 36); });
      c.fillStyle = '#7FB6FF'; c.font = '600 30px Figtree'; c.fillText('Vestimenta: ' + EV.vestimenta, W / 2, H - 112);
      c.fillStyle = '#C9D3E0'; c.font = '400 22px Figtree'; c.fillText('Después de las 12:00 am, el consumo y uso del lugar corre por cuenta de cada asistente.', W / 2, H - 70);
      return cv;
    });
  };
  function mostrarInvitacion(tok) {
    var box = $('#inv-img'); box.textContent = ''; $('#e-inv').textContent = ''; $('#inv-acc').hidden = true;
    box.appendChild(el('p', 'ayuda', 'Cargando tu invitación…'));
    api('invitacion', { invitacion: tok }).then(function (r) {
      box.textContent = '';
      if (!r.ok) { $('#e-inv').textContent = r.error; return; }
      window.dibujarInvitacion(r).then(function (cv) {
        var url = cv.toDataURL('image/png');
        var img = el('img'); img.alt = 'Invitación para ' + r.nombres.join(' y '); img.src = url; box.appendChild(img);
        $('#inv-desc').href = url; $('#inv-acc').hidden = false;
        document.body.dataset.invitacionLista = '1';
      });
    });
  }

  // ---------- panel ----------
  var sesion = null, datos = [], filtro = 'Pendiente';
  function iniciarPanel() {
    if (!sesion) { var s = ss.get('brindis-sesion'); if (s) try { sesion = JSON.parse(s); } catch (e) {} }
    if (sesion) { $('#p-login').hidden = true; $('#p-app').hidden = false; $('#p-yo').textContent = sesion.por; cargarPanel(); }
    else { $('#p-login').hidden = false; $('#p-app').hidden = true; }
  }
  $('#f-login').addEventListener('submit', function (e) {
    e.preventDefault();
    var por = $('#l-por').value, clave = $('#l-clave').value, err = $('#e-login');
    err.textContent = '';
    if (!por) { err.textContent = 'Elige tu nombre.'; return; }
    var b = $('button[type=submit]', this); ocupado(b, true, 'Entrando…');
    api('admin_login', { por: por, clave: clave }).then(function (r) {
      ocupado(b, false);
      if (!r.ok) { err.textContent = r.error; return; }
      sesion = { por: por, clave: clave }; ss.set('brindis-sesion', JSON.stringify(sesion));
      $('#l-clave').value = ''; iniciarPanel();
    });
  });
  $('#b-salir').addEventListener('click', function () { sesion = null; ss.del('brindis-sesion'); iniciarPanel(); });
  $('#b-recargar').addEventListener('click', function () { cargarPanel(true); });

  function cargarPanel(aviso) {
    var b = $('#b-recargar'); ocupado(b, true, 'Actualizando…');
    api('admin_lista', sesion).then(function (r) {
      ocupado(b, false);
      if (!r.ok) { sesion = null; ss.del('brindis-sesion'); iniciarPanel(); $('#e-login').textContent = r.error; return; }
      datos = r.registros;
      var pres = {}; datos.forEach(function (d) { pres[d.premier] = 1; });
      var sel = $('#p-premier'), v = sel.value; sel.length = 1;
      Object.keys(pres).sort().forEach(function (p) { var o = el('option', null, p); o.value = p; sel.appendChild(o); });
      sel.value = v;
      pintarPanel();
      if (aviso) toast('Lista actualizada');
    });
  }

  var ESTADOS = [['Pendiente', 'Pendientes'], ['Aprobado', 'Aprobados'], ['No aprobado', 'No aprobados'], ['', 'Todos']];
  function pintarPanel() {
    var cuenta = function (f) { return datos.filter(f).length; };
    var folios = {}; datos.forEach(function (d) { folios[d.folio] = 1; });
    var st = $('#p-stats'); st.textContent = '';
    [[datos.length, 'Personas'], [Object.keys(folios).length, 'Registros'], [cuenta(function (d) { return d.estado === 'Pendiente'; }), 'Pendientes'],
     [cuenta(function (d) { return d.estado === 'Aprobado'; }), 'Aprobados'], [cuenta(function (d) { return d.estado === 'No aprobado'; }), 'No aprobados']]
      .forEach(function (s) { var x = el('div', 'stat'); x.appendChild(el('b', null, String(s[0]))); x.appendChild(el('span', null, s[1])); st.appendChild(x); });

    var ch = $('#p-chips'); ch.textContent = '';
    ESTADOS.forEach(function (e) {
      var n = e[0] ? cuenta(function (d) { return d.estado === e[0]; }) : datos.length;
      var b = el('button', 'chip' + (filtro === e[0] ? ' on' : ''), e[1] + ' (' + n + ')'); b.type = 'button';
      b.addEventListener('click', function () { filtro = e[0]; pintarPanel(); }); ch.appendChild(b);
    });

    var q = $('#p-buscar').value.trim().toLowerCase(), pre = $('#p-premier').value;
    var grupos = {};
    datos.forEach(function (d) { (grupos[d.folio] = grupos[d.folio] || []).push(d); });
    var visibles = Object.keys(grupos).map(function (f) { return grupos[f]; }).filter(function (g) {
      if (pre && g[0].premier !== pre) return false;
      if (filtro && !g.some(function (d) { return d.estado === filtro; })) return false;
      if (q && !g.some(function (d) { return (d.nombre + ' ' + d.num + ' ' + d.registradoPor).toLowerCase().indexOf(q) >= 0; })) return false;
      return true;
    });
    var lista = $('#p-lista'); lista.textContent = '';
    if (!visibles.length) { lista.appendChild(el('div', 'vacio', datos.length ? 'No hay registros con este filtro.' : 'Todavía no hay registros.')); return; }

    var arbol = {};
    visibles.forEach(function (g) { var p = g[0].premier, s = g[0].subterritorio; ((arbol[p] = arbol[p] || {})[s] = arbol[p][s] || []).push(g); });
    Object.keys(arbol).sort().forEach(function (p) {
      var personasP = 0; Object.keys(arbol[p]).forEach(function (s) { arbol[p][s].forEach(function (g) { personasP += g.length; }); });
      var hp = el('div', 'premier'); hp.appendChild(el('h3', null, 'Premier ' + p)); hp.appendChild(el('span', null, personasP + ' personas')); lista.appendChild(hp);
      Object.keys(arbol[p]).sort().forEach(function (s) {
        var gs = arbol[p][s], n = 0; gs.forEach(function (g) { n += g.length; });
        var hs = el('div', 'subt'); hs.appendChild(el('h4', null, s)); hs.appendChild(el('span', null, n + ' personas · ' + gs.length + (gs.length === 1 ? ' registro' : ' registros'))); lista.appendChild(hs);
        gs.sort(function (a, b) { return a[0].fecha < b[0].fecha ? 1 : -1; }).forEach(function (g) { lista.appendChild(tarjeta(g)); });
      });
    });
  }
  $('#p-buscar').addEventListener('input', function () { pintarPanel(); });
  $('#p-premier').addEventListener('change', function () { pintarPanel(); });

  function tarjeta(g) {
    var c = el('div', 'folio');
    var h = el('div', 'folio-h');
    var izq = el('span'); izq.appendChild(el('b', null, g[0].registradoPor)); izq.appendChild(document.createTextNode(' · #' + g[0].num + ' · ' + (g[0].nivel || '')));
    h.appendChild(izq); h.appendChild(el('span', null, g[0].folio + ' · ' + g[0].fecha)); c.appendChild(h);
    g.forEach(function (d) {
      var r = el('div', 'per');
      var n = el('div', 'n');
      n.appendChild(el('span', 'badge b-' + d.tipo.split(' ')[0], d.tipo));
      n.appendChild(document.createTextNode(d.nombre));
      n.appendChild(el('small', null, 'WhatsApp ' + d.whatsapp));
      r.appendChild(n);
      var acc = el('div', 'acc');
      acc.appendChild(el('span', claseEstado(d.estado), d.estado));
      if (d.enviado) acc.appendChild(el('span', 'dec', 'WhatsApp enviado'));
      else if (d.estado === 'Pendiente') {
        acc.appendChild(boton('a-ok', 'Aprobar', d, 'aprobar'));
        acc.appendChild(boton('a-no', 'No aprobar', d, 'rechazar'));
      } else acc.appendChild(boton('a-rev', 'Deshacer', d, 'pendiente'));
      r.appendChild(acc);
      if (d.decididoPor) { var dd = el('div', 'dec', (d.estado === 'Aprobado' ? 'Aprobó ' : 'Decidió ') + d.decididoPor + ' · ' + d.fechaDecision); dd.style.gridColumn = '1 / -1'; r.appendChild(dd); }
      c.appendChild(r);
    });
    return c;
  }
  function boton(cls, txt, d, cambio) {
    var b = el('button', cls, txt); b.type = 'button';
    b.addEventListener('click', function () {
      ocupado(b, true, '…');
      api('admin_estado', Object.assign({ id: d.id, cambio: cambio }, sesion)).then(function (r) {
        if (!r.ok) { ocupado(b, false); toast(r.error); return; }
        d.estado = r.estado; d.decididoPor = r.estado === 'Pendiente' ? '' : sesion.por;
        d.fechaDecision = r.estado === 'Pendiente' ? '' : 'ahora';
        toast(d.nombre + ': ' + r.estado);
        pintarPanel();
      });
    });
    return b;
  }

  $('#b-csv').addEventListener('click', function () {
    var cols = [['folio', 'Folio'], ['premier', 'Premier'], ['subterritorio', 'Subterritorio'], ['registradoPor', 'Registrado por'], ['num', 'Num distribuidor'],
      ['nombre', 'Nombre'], ['tipo', 'Tipo'], ['whatsapp', 'WhatsApp'], ['estado', 'Estado'], ['decididoPor', 'Decidido por'], ['fecha', 'Fecha registro']];
    var esc = function (v) { v = String(v == null ? '' : v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var orden = datos.slice().sort(function (a, b) { return (a.premier + a.subterritorio + a.folio).localeCompare(b.premier + b.subterritorio + b.folio); });
    var csv = '﻿' + cols.map(function (c) { return c[1]; }).join(',') + '\n' + orden.map(function (d) { return cols.map(function (c) { return esc(d[c[0]]); }).join(','); }).join('\n');
    var a = el('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'registro-brindis-chasep.csv'; document.body.appendChild(a); a.click(); a.remove();
  });

  ruta();
})();
