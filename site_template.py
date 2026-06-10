"""Embedded Jinja2 template for the calendar browse page.

Kept as a Python string rather than a templates/ folder so the build has no
external file dependency and can never fail with TemplateNotFound.
"""

INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Platform Conference Calendar</title>
<meta name="description" content="Conference & precon dates and Call-for-Speakers deadlines for the data platform community.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..900;1,9..144,400..700&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#faf5ec; --ink:#17150f; --muted:#6f675b; --line:rgba(23,21,15,.16);
    --accent:#c63a16; --accent-soft:#f6e6da; --ok:#2c6149; --ok-soft:#e4ede7;
  }
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:"Newsreader",Georgia,serif; font-size:18px; line-height:1.5;
    background-image:radial-gradient(140% 90% at 12% -10%, #fffdf8 0%, transparent 55%);
  }
  a{color:inherit; text-decoration:none}
  .wrap{max-width:920px; margin:0 auto; padding:0 22px}
  .mono{font-family:"IBM Plex Mono",ui-monospace,monospace}

  /* Header */
  header{padding:46px 0 18px; border-bottom:2px solid var(--ink)}
  .kicker{font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.22em;
    text-transform:uppercase; color:var(--accent); margin:0 0 10px}
  h1{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(34px,6vw,60px);
    line-height:1.02; letter-spacing:-.01em; margin:0 0 12px}
  .lede{font-size:clamp(17px,2.4vw,21px); color:var(--muted); font-style:italic;
    max-width:46ch; margin:0 0 26px}
  .actions{display:flex; flex-wrap:wrap; gap:14px; align-items:center; margin-bottom:8px}
  .subscribe{display:inline-flex; align-items:center; gap:9px; background:var(--ink);
    color:var(--paper); padding:11px 18px; border-radius:999px; font-family:"IBM Plex Mono",monospace;
    font-size:13px; letter-spacing:.04em; transition:transform .15s ease, background .15s ease}
  .subscribe:hover{transform:translateY(-1px); background:var(--accent)}
  .subscribe svg{width:15px;height:15px}
  .ics-url{font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--muted);
    word-break:break-all}
  .ics-url b{color:var(--ink); font-weight:600}

  /* Controls */
  .controls{position:sticky; top:0; z-index:5; background:var(--paper);
    padding:16px 0 14px; border-bottom:1px solid var(--line)}
  .search{width:100%; border:1px solid var(--line); background:#fffdf8; color:var(--ink);
    font-family:"IBM Plex Mono",monospace; font-size:14px; padding:11px 14px; border-radius:10px;
    margin-bottom:12px}
  .search:focus{outline:none; border-color:var(--ink)}
  .chips{display:flex; flex-wrap:wrap; gap:8px}
  .chip{font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.03em;
    border:1px solid var(--line); background:transparent; color:var(--muted);
    padding:6px 12px; border-radius:999px; cursor:pointer; transition:all .12s ease}
  .chip:hover{border-color:var(--ink); color:var(--ink)}
  .chip.on{background:var(--ink); color:var(--paper); border-color:var(--ink)}
  .count{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--muted);
    padding:14px 0 4px}

  /* Event list */
  .list{padding-bottom:60px}
  .event{display:grid; grid-template-columns:168px 1fr; gap:22px; padding:22px 0;
    border-bottom:1px solid var(--line);
    opacity:0; transform:translateY(8px); animation:rise .5s ease forwards;
    animation-delay:calc(var(--i,0) * 28ms)}
  @keyframes rise{to{opacity:1; transform:none}}
  @media (prefers-reduced-motion:reduce){.event{animation:none; opacity:1; transform:none}}
  .event:hover{background:linear-gradient(90deg, rgba(198,58,22,.04), transparent 70%)}

  .when{font-family:"IBM Plex Mono",monospace}
  .cfs{display:inline-block; font-size:12px; line-height:1.3; padding:6px 9px; border-radius:8px;
    border:1px solid var(--line); color:var(--muted); margin-bottom:10px}
  .cfs .lbl{display:block; font-size:10px; letter-spacing:.16em; text-transform:uppercase; opacity:.8}
  .cfs.urgent{background:var(--accent); color:#fff; border-color:var(--accent)}
  .cfs.soon{background:var(--accent-soft); color:var(--accent); border-color:var(--accent)}
  .cfs.open{background:var(--ok-soft); color:var(--ok); border-color:transparent}
  .cfs.closed{opacity:.55; text-decoration:line-through}
  .cfs.none{font-style:normal}
  .confdate{font-size:13.5px; color:var(--ink); margin-top:2px}
  .precondate{font-size:12px; color:var(--accent); margin-top:5px}
  .precondate.tbd{color:var(--muted)}

  .meta h2{font-family:"Fraunces",serif; font-weight:600; font-size:22px; line-height:1.15;
    margin:0 0 6px; letter-spacing:-.005em}
  .meta h2 a{background-image:linear-gradient(var(--accent),var(--accent));
    background-size:0 1.5px; background-repeat:no-repeat; background-position:0 100%;
    transition:background-size .2s ease}
  .meta h2 a:hover{background-size:100% 1.5px}
  .venue{font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--muted); margin:0 0 9px}
  .tags{display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px}
  .tag{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.06em;
    text-transform:uppercase; border:1px solid var(--line); border-radius:5px; padding:2px 7px; color:var(--muted)}
  .tag.precon{border-color:var(--accent); color:var(--accent)}
  .tag.online{border-color:#2f6f8f; color:#2f6f8f}
  .tag.hybrid{border-color:#7a5a9e; color:#7a5a9e}
  .chip-sep{flex-basis:100%; height:0; margin:2px 0}
  @media (min-width:560px){.chip-sep{flex-basis:auto; width:1px; height:18px; background:var(--line); margin:2px 6px; align-self:center}}
  .info{font-size:15px; color:#3a352c; margin:0; max-width:62ch}
  .note{font-size:12px; font-style:italic; color:var(--muted); margin-top:6px}

  footer{border-top:2px solid var(--ink); padding:26px 0 60px; font-size:14px; color:var(--muted)}
  footer a{text-decoration:underline; text-underline-offset:2px}
  .empty{padding:50px 0; text-align:center; color:var(--muted); font-style:italic; display:none}

  @media (max-width:620px){
    body{font-size:17px}
    .event{grid-template-columns:1fr; gap:10px; padding:20px 0}
    .when{display:flex; flex-wrap:wrap; gap:10px; align-items:center}
    .cfs{margin-bottom:0}
  }

  /* View toggle */
  .viewtoggle{display:inline-flex; border:1px solid var(--ink); border-radius:999px; overflow:hidden; margin-bottom:12px}
  .viewtoggle button{font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.04em;
    border:0; background:transparent; color:var(--ink); padding:7px 16px; cursor:pointer}
  .viewtoggle button.on{background:var(--ink); color:var(--paper)}

  /* Calendar */
  #calendar-view{padding-bottom:60px}
  .cal-head{display:flex; align-items:center; gap:14px; padding:18px 0 14px}
  .cal-head h2{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(22px,4vw,30px); margin:0; min-width:8.5ch}
  .cal-nav{display:flex; gap:6px}
  .cal-nav button, .cal-today{font-family:"IBM Plex Mono",monospace; font-size:13px; cursor:pointer;
    border:1px solid var(--line); background:transparent; color:var(--ink); border-radius:8px; padding:6px 11px}
  .cal-nav button:hover, .cal-today:hover{border-color:var(--ink)}
  .cal-today{margin-left:auto; font-size:12px}
  .cal-grid{display:grid; grid-template-columns:repeat(7,1fr); gap:5px}
  .cal-dow{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.1em; text-transform:uppercase;
    color:var(--muted); text-align:center; padding:4px 0}
  .cal-cell{min-height:104px; border:1px solid rgba(23,21,15,.20); border-radius:7px; padding:5px 6px;
    background:#fffdf8; cursor:pointer; overflow:hidden; transition:border-color .12s ease, background .12s ease}
  .cal-cell:hover{border-color:var(--ink)}
  .cal-cell.weekend{background:#f4eee1}
  .cal-cell.out{background:#f7f2e8}
  .cal-cell.out .cal-daynum{color:#b3aa98}
  .cal-cell.today{border-color:var(--accent); box-shadow:inset 0 0 0 1px var(--accent)}
  .cal-cell.sel{border-color:var(--ink); box-shadow:inset 0 0 0 1px var(--ink)}
  .cal-cell.cal-empty{cursor:default}
  .cal-cell.cal-empty:hover{border-color:rgba(23,21,15,.20)}
  .cal-daynum{font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:#5b5346; font-weight:500; display:block; margin-bottom:3px}
  .cal-cell.today .cal-daynum{color:var(--accent); font-weight:600}
  .cal-chip{display:block; font-size:10.5px; line-height:1.35; border-radius:4px; padding:1px 5px; margin-bottom:2px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
  .cal-chip.cfs{background:var(--accent); color:#fff}
  .cal-chip.precon{background:#efe6f5; color:#6a4d8c}
  .cal-chip.conf{background:#ece7dd; color:#46402f}
  .cal-more{font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--muted)}

  .cal-detail{margin-top:22px; border-top:1px solid var(--line); padding-top:18px}
  .cal-detail h3{font-family:"Fraunces",serif; font-weight:600; font-size:20px; margin:0 0 12px}
  .cal-detail .di{display:flex; gap:12px; padding:11px 0; border-bottom:1px solid var(--line); align-items:baseline}
  .cal-detail .di-kind{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.06em; text-transform:uppercase;
    border-radius:4px; padding:2px 7px; white-space:nowrap}
  .di-kind.cfs{background:var(--accent); color:#fff}
  .di-kind.precon{background:#efe6f5; color:#6a4d8c}
  .di-kind.conf{background:#ece7dd; color:#46402f}
  .cal-detail .di-name{font-family:"Fraunces",serif; font-size:17px}
  .cal-detail .di-sub{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--muted); margin-top:2px}
  .cal-detail .placeholder{color:var(--muted); font-style:italic}

  @media (max-width:620px){
    .cal-grid{gap:2px}
    .cal-cell{min-height:62px; padding:3px 3px; border-radius:6px}
    .cal-daynum{font-size:11px}
    .cal-chip{font-size:0; padding:0; height:5px; border-radius:3px}  /* chips become colour bars */
    .cal-more{font-size:9px}
  }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <p class="kicker">Call for Data Speakers &middot; community calendar</p>
    <h1>Data Platform<br>Conference Calendar</h1>
    <p class="lede">Conference &amp; precon dates and Call-for-Speakers deadlines, all in one feed you can subscribe to.</p>
    <div class="actions">
      <a class="subscribe" href="calendar.ics">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 2v4M16 2v4M3 9h18M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/></svg>
        Subscribe to calendar (.ics)
      </a>
      {% if calendar_url %}<span class="ics-url">or add by URL: <b>{{ calendar_url }}</b></span>{% endif %}
    </div>
  </div>
</header>

<div class="controls">
  <div class="wrap">
    <div class="viewtoggle" id="viewtoggle">
      <button data-view="list" class="on">List</button>
      <button data-view="calendar">Calendar</button>
    </div>
    <input id="search" class="search" type="search" placeholder="Search by name or location…" aria-label="Search">
    <div class="chips" id="chips">
      <button class="chip on" data-filter="all">All</button>
      <button class="chip" data-filter="open">CfS open</button>
      <button class="chip" data-filter="precon">Has precon</button>
      <span class="chip-sep"></span>
      <button class="chip" data-modality="online">Online</button>
      <button class="chip" data-modality="in_person">In person</button>
      {% if continents %}<span class="chip-sep"></span>{% endif %}
      {% for c in continents %}
      <button class="chip" data-continent="{{ c }}">{{ c }}</button>
      {% endfor %}
    </div>
  </div>
</div>

<main class="wrap">
<div id="list-view" class="list">
  <p class="count" id="count">{{ open_count }} of {{ total }} with an open Call for Speakers</p>
  {% for r in rows %}
  <article class="event"
           style="--i:{{ loop.index0 if loop.index0 < 40 else 40 }}"
           data-name="{{ r.name|lower }} {{ r.venue|lower }}"
           data-continents="{{ r.continents|join(',') }}"
           data-online="{{ '1' if r.is_online else '0' }}"
           data-inperson="{{ '1' if r.is_in_person else '0' }}"
           data-open="{{ '1' if r.cfs_open else '0' }}"
           data-precon="{{ '1' if r.is_precon else '0' }}">
    <div class="when">
      {% if r.cfs_iso %}
        <span class="cfs" data-cfs="{{ r.cfs_iso }}"><span class="lbl">CfS</span><span class="cfs-text">{{ r.cfs_display }}</span></span>
      {% else %}
        <span class="cfs none"><span class="lbl">CfS</span>no date listed</span>
      {% endif %}
      <div class="confdate">{{ r.conf_display }}</div>
      {% if r.precon_known %}
        <div class="precondate">Precon: {{ r.precon_display }}</div>
      {% elif r.is_precon %}
        <div class="precondate tbd">Precon: date TBD</div>
      {% endif %}
    </div>
    <div class="meta">
      <h2>{% if r.url %}<a href="{{ r.url }}" target="_blank" rel="noopener">{{ r.name }}</a>{% else %}{{ r.name }}{% endif %}</h2>
      {% if r.venue %}<p class="venue">{{ r.venue }}</p>{% endif %}
      <div class="tags">
        {% if r.is_precon %}<span class="tag precon">Precon</span>{% endif %}
        {% if r.modality_label %}<span class="tag mod {{ r.modality }}">{{ r.modality_label }}</span>{% endif %}
        {% for c in r.continents %}<span class="tag">{{ c }}</span>{% endfor %}
      </div>
      {% if r.info %}<p class="info">{{ r.info }}</p>{% endif %}
      {% if r.precon_known and r.confidence in ['medium','low'] %}<p class="note">Precon date inferred — verify on the event page.</p>{% endif %}
    </div>
  </article>
  {% endfor %}
  <p class="empty" id="empty">Nothing matches those filters.</p>
</div><!-- /#list-view -->

<section id="calendar-view" hidden>
  <div class="cal-head">
    <div class="cal-nav">
      <button id="cal-prev" aria-label="Previous month">&#8249;</button>
      <button id="cal-next" aria-label="Next month">&#8250;</button>
    </div>
    <h2 id="cal-title">&nbsp;</h2>
    <button class="cal-today" id="cal-today">Today</button>
  </div>
  <div class="cal-grid" id="cal-dow"></div>
  <div class="cal-grid" id="cal-grid"></div>
  <div class="cal-detail" id="cal-detail"></div>
</section>
</main>

<script type="application/json" id="cal-data">{{ rows | tojson }}</script>

<footer>
  <div class="wrap">
    <p>Data from <a href="https://callfordataspeakers.com" target="_blank" rel="noopener">callfordataspeakers.com</a>, rebuilt daily. To add or correct a conference, submit it upstream there.</p>
    <p>Last updated {{ generated_at }} &middot; not affiliated with Call for Data Speakers — a community-built view of their open data.</p>
  </div>
</footer>

<script>
(function(){
  var DAY = 86400000;

  // Live CfS countdown + status colouring. data-cfs is a full UTC timestamp;
  // the browser localizes it, and the day count is in the viewer's local days
  // (so a deadline stored as 04:59Z shows on the correct local date).
  document.querySelectorAll('.cfs[data-cfs]').forEach(function(el){
    var d = new Date(el.getAttribute('data-cfs'));      // exact instant, local TZ
    var txt = el.querySelector('.cfs-text');
    if (isNaN(d)) return;
    var now = new Date();
    el.title = 'Closes ' + d.toLocaleString(undefined,
      { weekday:'short', year:'numeric', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' });
    if (d - now < 0) { el.classList.add('closed'); txt.textContent = 'closed'; return; }
    // whole-calendar-day difference in the viewer's local time
    var d0 = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var t0 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var days = Math.round((d0 - t0) / DAY);
    if (days === 0)      { el.classList.add('urgent'); txt.textContent = 'closes today'; }
    else if (days <= 7)  { el.classList.add('urgent'); txt.textContent = 'closes in ' + days + 'd'; }
    else if (days <= 21) { el.classList.add('soon');   txt.textContent = 'in ' + days + ' days'; }
    else                 { el.classList.add('open');   txt.textContent = 'in ' + days + ' days'; }
  });

  // ---------- shared filter state ----------
  var search = document.getElementById('search');
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var listEvents = Array.prototype.slice.call(document.querySelectorAll('.event'));
  var statusMode = 'all', modality = null, continent = null, q = '';

  function passes(f){
    if (statusMode === 'open'   && !f.open)     return false;
    if (statusMode === 'precon' && !f.precon)   return false;
    if (modality === 'online'    && !f.online)   return false;
    if (modality === 'in_person' && !f.inperson) return false;
    if (continent && f.continents.indexOf(continent) === -1) return false;
    if (q && f.text.indexOf(q) === -1) return false;
    return true;
  }

  function apply(){
    q = search.value.trim().toLowerCase();
    var shown = 0;
    listEvents.forEach(function(ev){
      var ok = passes({
        open: ev.dataset.open === '1',
        precon: ev.dataset.precon === '1',
        online: ev.dataset.online === '1',
        inperson: ev.dataset.inperson === '1',
        continents: ev.dataset.continents ? ev.dataset.continents.split(',') : [],
        text: ev.dataset.name
      });
      ev.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    count.textContent = shown + (shown === 1 ? ' event' : ' events') + ' shown';
    empty.style.display = shown ? 'none' : 'block';
    renderCalendar();
  }

  function radio(selector, btn){
    document.querySelectorAll(selector).forEach(function(c){ c.classList.remove('on'); });
    btn.classList.add('on');
  }
  function toggleChip(selector, btn){
    var was = btn.classList.contains('on');
    document.querySelectorAll(selector).forEach(function(c){ c.classList.remove('on'); });
    if (!was){ btn.classList.add('on'); return true; }
    return false;
  }

  document.getElementById('chips').addEventListener('click', function(e){
    var btn = e.target.closest('.chip'); if (!btn) return;
    if (btn.dataset.filter){
      radio('.chip[data-filter]', btn); statusMode = btn.dataset.filter;
    } else if (btn.dataset.modality){
      modality = toggleChip('.chip[data-modality]', btn) ? btn.dataset.modality : null;
    } else if (btn.dataset.continent){
      continent = toggleChip('.chip[data-continent]', btn) ? btn.dataset.continent : null;
    }
    apply();
  });
  search.addEventListener('input', apply);

  // ---------- view toggle ----------
  var listView = document.getElementById('list-view');
  var calView = document.getElementById('calendar-view');
  document.getElementById('viewtoggle').addEventListener('click', function(e){
    var btn = e.target.closest('button'); if (!btn) return;
    radio('#viewtoggle button', btn);
    var showCal = btn.dataset.view === 'calendar';
    calView.hidden = !showCal;
    listView.hidden = showCal;
    if (showCal) renderCalendar();
  });

  // ---------- calendar ----------
  var DATA = [];
  try { DATA = JSON.parse((document.getElementById('cal-data') || {}).textContent || '[]'); } catch(err){ DATA = []; }
  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var DOW = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  var KIND_LABEL = {cfs:'CfS deadline', precon:'Precon', conf:'Conference'};
  var ORDER = {cfs:0, precon:1, conf:2};
  var calMonth = new Date(); calMonth.setDate(1);
  var selected = null;

  function pad(n){ return (n < 10 ? '0' : '') + n; }
  function ymd(d){ return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()); }
  function parseYMD(s){ var p = String(s).split('-'); return new Date(+p[0], (+p[1]) - 1, +p[2]); }
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

  function fOf(ev){
    return { open: !!ev.cfs_open, precon: !!ev.is_precon, online: !!ev.is_online, inperson: !!ev.is_in_person,
             continents: ev.continents || [], text: ((ev.name || '') + ' ' + (ev.venue || '')).toLowerCase() };
  }

  function itemsByDay(){
    var map = {};
    function push(k, it){ (map[k] = map[k] || []).push(it); }
    DATA.forEach(function(ev){
      if (!passes(fOf(ev))) return;
      if (ev.cfs_iso){ var cd = new Date(ev.cfs_iso); if (!isNaN(cd)) push(ymd(new Date(cd.getFullYear(), cd.getMonth(), cd.getDate())), {kind:'cfs', ev:ev}); }
      if (ev.precon_iso) push(ev.precon_iso, {kind:'precon', ev:ev});
      if (ev.conf_iso){ var s = parseYMD(ev.conf_iso), e = ev.main_end_iso ? parseYMD(ev.main_end_iso) : s;
        for (var dt = new Date(s); dt <= e; dt.setDate(dt.getDate()+1)) push(ymd(dt), {kind:'conf', ev:ev}); }
    });
    return map;
  }

  function renderDOW(){
    var c = document.getElementById('cal-dow');
    if (c.childElementCount) return;
    DOW.forEach(function(d){ var s = document.createElement('div'); s.className = 'cal-dow'; s.textContent = d; c.appendChild(s); });
  }

  function renderCalendar(){
    if (calView.hidden) return;
    renderDOW();
    document.getElementById('cal-title').textContent = MONTHS[calMonth.getMonth()] + ' ' + calMonth.getFullYear();
    var grid = document.getElementById('cal-grid'); grid.innerHTML = '';
    var byDay = itemsByDay();
    var first = new Date(calMonth.getFullYear(), calMonth.getMonth(), 1);
    var startDow = (first.getDay() + 6) % 7;                 // Monday-start
    var start = new Date(first); start.setDate(1 - startDow);
    var todayKey = ymd(new Date());
    for (var i = 0; i < 42; i++){
      var d = new Date(start); d.setDate(start.getDate() + i);
      var key = ymd(d);
      var items = (byDay[key] || []).slice().sort(function(a, b){ return ORDER[a.kind] - ORDER[b.kind]; });
      var cls = 'cal-cell';
      if (d.getMonth() !== calMonth.getMonth()) cls += ' out';
      if (d.getDay() === 0 || d.getDay() === 6) cls += ' weekend';
      if (key === todayKey) cls += ' today';
      if (key === selected) cls += ' sel';
      if (!items.length) cls += ' cal-empty';
      var cell = document.createElement('div');
      cell.className = cls;
      var html = '<span class="cal-daynum">' + d.getDate() + '</span>';
      for (var j = 0; j < Math.min(items.length, 3); j++){
        html += '<span class="cal-chip ' + items[j].kind + '" title="' + esc(items[j].ev.name) + '">' + esc(items[j].ev.name) + '</span>';
      }
      if (items.length > 3) html += '<span class="cal-more">+' + (items.length - 3) + ' more</span>';
      cell.innerHTML = html;
      if (items.length){ cell.addEventListener('click', (function(k){ return function(){ selected = k; renderCalendar(); }; })(key)); }
      grid.appendChild(cell);
    }
    renderDetail(byDay);
  }

  function renderDetail(byDay){
    var box = document.getElementById('cal-detail');
    if (!selected){ box.innerHTML = '<p class="placeholder">Select a day to see its events.</p>'; return; }
    var items = (byDay[selected] || []).slice().sort(function(a, b){ return ORDER[a.kind] - ORDER[b.kind]; });
    var head = '<h3>' + parseYMD(selected).toLocaleDateString(undefined, {weekday:'long', year:'numeric', month:'long', day:'numeric'}) + '</h3>';
    if (!items.length){ box.innerHTML = head + '<p class="placeholder">No events.</p>'; return; }
    box.innerHTML = head + items.map(function(it){
      var ev = it.ev, sub = [];
      if (ev.venue) sub.push(esc(ev.venue));
      if (it.kind === 'cfs' && ev.cfs_iso) sub.push('closes ' + new Date(ev.cfs_iso).toLocaleString(undefined, {hour:'2-digit', minute:'2-digit'}));
      var nm = ev.url ? '<a href="' + esc(ev.url) + '" target="_blank" rel="noopener">' + esc(ev.name) + '</a>' : esc(ev.name);
      return '<div class="di"><span class="di-kind ' + it.kind + '">' + KIND_LABEL[it.kind] + '</span>'
           + '<div><div class="di-name">' + nm + '</div>'
           + (sub.length ? '<div class="di-sub">' + sub.join(' &middot; ') + '</div>' : '') + '</div></div>';
    }).join('');
  }

  document.getElementById('cal-prev').addEventListener('click', function(){ calMonth.setMonth(calMonth.getMonth() - 1); renderCalendar(); });
  document.getElementById('cal-next').addEventListener('click', function(){ calMonth.setMonth(calMonth.getMonth() + 1); renderCalendar(); });
  document.getElementById('cal-today').addEventListener('click', function(){ calMonth = new Date(); calMonth.setDate(1); renderCalendar(); });
})();
</script>
</body>
</html>
"""