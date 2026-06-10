"""Embedded Jinja2 template for the calendar browse page.

Kept as a Python string rather than a templates/ folder so the build has no
external file dependency and can never fail with TemplateNotFound.
"""

INDEX_TEMPLATE = r"""{% macro event_card(r, idx) -%}
<article class="event"
         style="--i:{{ idx if idx < 40 else 40 }}"
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
{%- endmacro -%}
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Conference Calendar</title>
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
  header{padding:26px 0 16px; border-bottom:2px solid var(--ink)}
  .kicker{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.2em;
    text-transform:uppercase; color:var(--accent); margin:0 0 8px}
  h1{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(26px,4vw,40px);
    line-height:1.05; letter-spacing:-.01em; margin:0 0 8px}
  .lede{font-size:clamp(15px,1.8vw,18px); color:var(--muted); font-style:italic;
    max-width:52ch; margin:0 0 8px}
  .header-grid{display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:18px 36px}
  .header-main{flex:1 1 440px; min-width:0}
  .built{font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--muted); margin:0}
  .built a{color:var(--accent); border-bottom:1px solid rgba(198,58,22,.4)}
  .built a:hover{border-color:var(--accent)}
  .actions{flex:0 0 auto; display:flex; flex-direction:column; align-items:flex-start; gap:10px; max-width:300px}
  .subscribe{display:inline-flex; align-items:center; gap:9px; background:var(--ink);
    color:var(--paper); padding:11px 18px; border-radius:999px; font-family:"IBM Plex Mono",monospace;
    font-size:13px; letter-spacing:.04em; transition:transform .15s ease, background .15s ease}
  .subscribe:hover{transform:translateY(-1px); background:var(--accent)}
  .subscribe svg{width:15px;height:15px}
  .ics-url{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--muted); word-break:break-all}
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
  .past-events{margin-top:4px; padding-bottom:60px}
  .past-events>summary{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(18px,3vw,24px);
    color:var(--muted); cursor:pointer; list-style:none; padding:16px 0; border-top:1px solid var(--line)}
  .past-events>summary::-webkit-details-marker{display:none}
  .past-events>summary::before{content:"\25B8\00a0"; color:var(--accent); font-size:.8em}
  .past-events[open]>summary::before{content:"\25BE\00a0"}
  .past-events>summary:hover{color:var(--ink)}
  .past-events .event{animation:none; opacity:.82; transform:none}
  .past-events .list{padding-bottom:10px}
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
  .tag.precon{border-color:#463c91; color:#463c91}
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
    .wrap{padding:0 16px}                    /* reclaim width on phones */
    .controls{position:static}               /* not sticky — frees the viewport */
    .search{font-size:16px}                  /* >=16px stops iOS zoom-on-focus */
    .chips{gap:7px}
    .chip{padding:9px 14px; font-size:13px}  /* larger tap targets */
    .actions{max-width:none}
    .subscribe{padding:13px 18px}
    .built{font-size:12px}
    .event{grid-template-columns:1fr; gap:10px; padding:20px 0}
    .when{display:flex; flex-wrap:wrap; gap:10px; align-items:center}
    .cfs{margin-bottom:0}
    .soon{padding:13px 15px}
  }

  /* Section label between calendar and list */
  .section-label{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(20px,3.4vw,26px);
    margin:0 0 6px; padding-top:30px; border-top:1px solid var(--line)}

  /* Closing-soon callout */
  .soon{border:1px solid var(--accent); background:var(--accent-soft); border-radius:12px; padding:15px 18px; margin:0 0 26px}
  .soon-title{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(17px,3vw,21px); margin:0 0 3px; color:#9a2f12}
  .soon-sub{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.03em; color:#a35334; margin:0 0 8px}
  .soon-item{display:flex; gap:12px; align-items:baseline; padding:7px 0; border-top:1px solid rgba(198,58,22,.16)}
  .soon-when{font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:600; color:var(--accent); white-space:nowrap; min-width:7ch}
  .soon-name{font-family:"Fraunces",serif; font-size:16px}
  .soon-name a{color:var(--ink); text-decoration:none; border-bottom:1px solid rgba(23,21,15,.25)}
  .soon-name a:hover{border-color:var(--ink)}
  .soon-where{font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--muted)}

  /* Calendar */
  #calendar-view{padding-bottom:30px}
  .cal-head{display:flex; align-items:center; flex-wrap:wrap; gap:8px 18px; padding:14px 0 12px}
  .cal-head h2{font-family:"Fraunces",serif; font-weight:600; font-size:clamp(22px,4vw,30px); margin:0; min-width:8.5ch}
  .cal-head-meta{margin-left:auto; display:flex; flex-direction:column; align-items:flex-end; gap:3px; min-width:0}
  .cal-hint{font-family:"Newsreader",Georgia,serif; font-style:italic; font-size:12.5px; color:var(--muted); margin:0}
  .cal-nav{display:flex; gap:6px}
  .cal-nav button, .cal-today{font-family:"IBM Plex Mono",monospace; font-size:13px; cursor:pointer;
    border:1px solid var(--line); background:transparent; color:var(--ink); border-radius:8px; padding:6px 11px}
  .cal-nav button:hover, .cal-today:hover{border-color:var(--ink)}
  .cal-today{font-size:12px}
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
  .cal-chip.precon{background:#e7e6f5; color:#463c91}
  .cal-chip.conf{background:#ece7dd; color:#46402f}
  .cal-more{font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--muted)}

  /* multi-day conference span bars */
  .cal-band{display:block; height:15px; line-height:15px; font-size:10px; font-weight:600;
    padding:0 6px; margin:0 -6px 2px; background:#e4ddcc; color:#46402f;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
  .cal-band.l{border-top-left-radius:4px; border-bottom-left-radius:4px}
  .cal-band.r{border-top-right-radius:4px; border-bottom-right-radius:4px}
  .cal-band-sp{display:block; height:15px; margin-bottom:2px}

  /* legend */
  .cal-legend{display:flex; flex-wrap:wrap; justify-content:flex-end; gap:6px 15px; padding:0;
    font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--muted)}
  .cal-legend .lg{display:inline-flex; align-items:center; gap:6px}
  .cal-legend .sw{width:13px; height:13px; border-radius:3px; flex:none}
  .cal-legend .sw.cfs{background:var(--accent)}
  .cal-legend .sw.precon{background:#e7e6f5; box-shadow:inset 0 0 0 1.5px #463c91}
  .cal-legend .sw.conf{background:#e4ddcc; box-shadow:inset 0 0 0 1.5px #8a7d5f}

  .cal-detail{margin:2px 0 16px; border-bottom:1px solid var(--line); padding-bottom:16px}
  .cal-detail:empty{display:none}
  .cal-detail h3{font-family:"Fraunces",serif; font-weight:600; font-size:20px; margin:0 0 12px}
  .cal-detail .di{display:flex; gap:12px; padding:11px 0; border-bottom:1px solid var(--line); align-items:baseline}
  .cal-detail .di-kind{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.06em; text-transform:uppercase;
    border-radius:4px; padding:2px 7px; white-space:nowrap}
  .di-kind.cfs{background:var(--accent); color:#fff}
  .di-kind.precon{background:#e7e6f5; color:#463c91}
  .di-kind.conf{background:#ece7dd; color:#46402f}
  .cal-detail .di-name{font-family:"Fraunces",serif; font-size:17px}
  .cal-detail .di-sub{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--muted); margin-top:2px}
  .cal-detail .placeholder{color:var(--muted); font-style:italic}

  @media (max-width:620px){
    .cal-nav{order:0}
    .cal-head h2{order:1}
    .cal-today{order:2; margin-left:auto}            /* title + Today share line 1 */
    .cal-head-meta{order:3; width:100%; margin-left:0; align-items:flex-start; gap:4px}  /* legend + hint drop to line 2, left-aligned */
    .cal-legend{justify-content:flex-start}
    .cal-nav button, .cal-today{padding:9px 13px}    /* larger tap targets */
    .cal-grid{gap:2px}
    .cal-cell{min-height:66px; padding:3px 3px; border-radius:6px}
    .cal-daynum{font-size:11px}
    .cal-chip{font-size:0; padding:0; height:6px; border-radius:3px}  /* chips become colour bars */
    .cal-band{font-size:0; height:6px; padding:0; margin:0 -3px 2px}
    .cal-band-sp{height:6px}
    .cal-more{font-size:9px}
  }
</style>
</head>
<body>
<header>
  <div class="wrap header-grid">
    <div class="header-main">
      <p class="kicker">Call for Data Speakers &middot; community calendar</p>
      <h1>Data Conference Calendar</h1>
      <p class="lede">Conference &amp; precon dates and Call-for-Speakers deadlines.</p>
      <p class="built">Built upon data from <a href="https://callfordataspeakers.com/" target="_blank" rel="noopener">callfordataspeakers.com</a> (more info: <a href="https://github.com/dataplat/DataSpeakers/" target="_blank" rel="noopener">GitHub</a>)</p>
    </div>
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
<section id="cfs-soon" class="soon" hidden>
  <h2 class="soon-title">Call for Speakers closing soon</h2>
  <p class="soon-sub" id="soon-sub"></p>
  <div id="soon-list"></div>
</section>
<section id="calendar-view">
  <div class="cal-head">
    <div class="cal-nav">
      <button id="cal-prev" aria-label="Previous month">&#8249;</button>
      <button id="cal-next" aria-label="Next month">&#8250;</button>
    </div>
    <h2 id="cal-title">&nbsp;</h2>
    <div class="cal-head-meta">
      <div class="cal-legend" aria-label="Legend">
        <span class="lg"><span class="sw cfs"></span>CfS deadline</span>
        <span class="lg"><span class="sw precon"></span>Precon</span>
        <span class="lg"><span class="sw conf"></span>Conference</span>
      </div>
      <p class="cal-hint" id="cal-hint">Select a day to see its events.</p>
    </div>
    <button class="cal-today" id="cal-today">Today</button>
  </div>
  <div class="cal-detail" id="cal-detail"></div>
  <div class="cal-grid" id="cal-dow"></div>
  <div class="cal-grid" id="cal-grid"></div>
</section>

<h2 class="section-label">All events</h2>
<div id="list-view" class="list">
  <p class="count" id="count">{{ open_count }} of {{ total }} with an open Call for Speakers</p>
  {% for r in rows if not r.is_past %}{{ event_card(r, loop.index0) }}{% endfor %}
  <p class="empty" id="empty">Nothing matches those filters.</p>
</div><!-- /#list-view -->
{% set past_rows = rows | selectattr('is_past') | list %}
{% if past_rows %}
<details class="past-events">
  <summary>Past events ({{ past_rows | length }})</summary>
  <div class="list">
    {% for r in past_rows %}{{ event_card(r, loop.index0) }}{% endfor %}
  </div>
</details>
{% endif %}
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
  var listEvents = Array.prototype.slice.call(document.querySelectorAll('#list-view .event'));
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
  var DAY = 86400000;
  function dayDiff(a, b){ var a0 = new Date(a.getFullYear(), a.getMonth(), a.getDate()); var b0 = new Date(b.getFullYear(), b.getMonth(), b.getDate()); return Math.round((b0 - a0) / DAY); }

  function fOf(ev){
    return { open: !!ev.cfs_open, precon: !!ev.is_precon, online: !!ev.is_online, inperson: !!ev.is_in_person,
             continents: ev.continents || [], text: ((ev.name || '') + ' ' + (ev.venue || '')).toLowerCase() };
  }

  function buildModel(){
    var single = {}, spans = [], detail = {};
    function push(map, k, it){ (map[k] = map[k] || []).push(it); }
    DATA.forEach(function(ev){
      if (!passes(fOf(ev))) return;
      if (ev.cfs_iso){ var cd = new Date(ev.cfs_iso); if (!isNaN(cd)){ var k = ymd(new Date(cd.getFullYear(), cd.getMonth(), cd.getDate())); push(single, k, {kind:'cfs', ev:ev}); push(detail, k, {kind:'cfs', ev:ev}); } }
      if (ev.precon_iso){ push(single, ev.precon_iso, {kind:'precon', ev:ev}); push(detail, ev.precon_iso, {kind:'precon', ev:ev}); }
      if (ev.conf_iso){
        var s = parseYMD(ev.conf_iso), e = ev.main_end_iso ? parseYMD(ev.main_end_iso) : s;
        for (var dt = new Date(s); dt <= e; dt.setDate(dt.getDate()+1)) push(detail, ymd(dt), {kind:'conf', ev:ev});
        if (e > s) spans.push({ev:ev, start:s, end:e}); else push(single, ymd(s), {kind:'conf', ev:ev});
      }
    });
    return {single:single, spans:spans, detail:detail};
  }

  function renderDOW(){
    var c = document.getElementById('cal-dow');
    if (c.childElementCount) return;
    DOW.forEach(function(d){ var s = document.createElement('div'); s.className = 'cal-dow'; s.textContent = d; c.appendChild(s); });
  }

  function renderCalendar(){
    renderDOW();
    document.getElementById('cal-title').textContent = MONTHS[calMonth.getMonth()] + ' ' + calMonth.getFullYear();
    var grid = document.getElementById('cal-grid'); grid.innerHTML = '';
    var model = buildModel();
    var first = new Date(calMonth.getFullYear(), calMonth.getMonth(), 1);
    var startDow = (first.getDay() + 6) % 7;                 // Monday-start
    var start = new Date(first); start.setDate(1 - startDow);
    var todayKey = ymd(new Date());

    for (var w = 0; w < 6; w++){
      var weekStart = new Date(start); weekStart.setDate(start.getDate() + w*7);
      var weekEnd = new Date(weekStart); weekEnd.setDate(weekStart.getDate() + 6);
      // multi-day conferences overlapping this week, packed into lanes (week-local)
      var wspans = model.spans.filter(function(sp){ return sp.start <= weekEnd && sp.end >= weekStart; })
                              .sort(function(a, b){ return (a.start - b.start) || (b.end - a.end); });
      var laneEnd = [];
      wspans.forEach(function(sp){
        var cs = sp.start > weekStart ? sp.start : weekStart;
        var ce = sp.end   < weekEnd   ? sp.end   : weekEnd;
        var L = 0; for (; L < laneEnd.length; L++){ if (cs > laneEnd[L]) break; }
        sp._lane = L; laneEnd[L] = ce;
      });
      var laneCount = laneEnd.length;

      for (var col = 0; col < 7; col++){
        var d = new Date(weekStart); d.setDate(weekStart.getDate() + col);
        var key = ymd(d);
        var cls = 'cal-cell';
        if (d.getMonth() !== calMonth.getMonth()) cls += ' out';
        if (d.getDay() === 0 || d.getDay() === 6) cls += ' weekend';
        if (key === todayKey) cls += ' today';
        if (key === selected) cls += ' sel';
        var has = false;
        var html = '<span class="cal-daynum">' + d.getDate() + '</span>';
        // spanning-conference lanes (bars line up across the row; spacers keep alignment)
        for (var L = 0; L < laneCount; L++){
          var sp = null;
          for (var si = 0; si < wspans.length; si++){ var cand = wspans[si]; if (cand._lane === L && cand.start <= d && cand.end >= d){ sp = cand; break; } }
          if (sp){
            has = true;
            var head = (dayDiff(sp.start, d) === 0) || (col === 0);   // span start OR week start
            var tail = (dayDiff(sp.end, d) === 0) || (col === 6);     // span end OR week end
            var bcls = 'cal-band' + (head ? ' l' : '') + (tail ? ' r' : '');
            html += '<span class="' + bcls + '" title="' + esc(sp.ev.name) + '">' + (head ? esc(sp.ev.name) : '&nbsp;') + '</span>';
          } else {
            html += '<span class="cal-band-sp"></span>';
          }
        }
        // single-day items (CfS, precon, single-day conferences)
        var items = (model.single[key] || []).slice().sort(function(a, b){ return ORDER[a.kind] - ORDER[b.kind]; });
        if (items.length) has = true;
        for (var j = 0; j < Math.min(items.length, 3); j++){
          html += '<span class="cal-chip ' + items[j].kind + '" title="' + esc(items[j].ev.name) + '">' + esc(items[j].ev.name) + '</span>';
        }
        if (items.length > 3) html += '<span class="cal-more">+' + (items.length - 3) + ' more</span>';
        if (!has) cls += ' cal-empty';
        var cell = document.createElement('div'); cell.className = cls; cell.innerHTML = html;
        if (has){ cell.addEventListener('click', (function(k){ return function(){ selected = k; renderCalendar(); }; })(key)); }
        grid.appendChild(cell);
      }
    }
    renderDetail(model.detail);
  }

  function renderDetail(byDay){
    var box = document.getElementById('cal-detail');
    var hint = document.getElementById('cal-hint');
    if (!selected){ box.innerHTML = ''; if (hint) hint.style.display = ''; return; }
    var items = (byDay[selected] || []).slice().sort(function(a, b){ return ORDER[a.kind] - ORDER[b.kind]; });
    if (!items.length){ box.innerHTML = ''; if (hint) hint.style.display = ''; return; }
    if (hint) hint.style.display = 'none';
    var head = '<h3>' + parseYMD(selected).toLocaleDateString(undefined, {weekday:'long', year:'numeric', month:'long', day:'numeric'}) + '</h3>';
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

  function renderSoon(){
    var box = document.getElementById('cfs-soon'); if (!box) return;
    var now = new Date(), rows = [];
    DATA.forEach(function(ev){
      if (!ev.cfs_iso) return;
      var d = new Date(ev.cfs_iso); if (isNaN(d) || d <= now) return;   // missing or already closed
      var days = dayDiff(now, d);
      if (days < 0 || days > 7) return;                                  // within 7 calendar days
      rows.push({ev:ev, d:d, days:days});
    });
    if (!rows.length){ box.hidden = true; return; }
    rows.sort(function(a, b){ return a.d - b.d; });
    var sub = document.getElementById('soon-sub');
    if (sub) sub.textContent = (rows.length === 1 ? '1 deadline' : rows.length + ' deadlines') + ' in the next 7 days';
    document.getElementById('soon-list').innerHTML = rows.map(function(r){
      var ev = r.ev, when = r.days === 0 ? 'today' : 'in ' + r.days + 'd';
      var nm = ev.url ? '<a href="' + esc(ev.url) + '" target="_blank" rel="noopener">' + esc(ev.name) + '</a>' : esc(ev.name);
      var where = ev.venue ? ' <span class="soon-where">' + esc(ev.venue) + '</span>' : '';
      return '<div class="soon-item"><span class="soon-when">' + when + '</span>'
           + '<span class="soon-name">' + nm + where + '</span></div>';
    }).join('');
    box.hidden = false;
  }

  document.getElementById('cal-prev').addEventListener('click', function(){ calMonth.setMonth(calMonth.getMonth() - 1); renderCalendar(); });
  document.getElementById('cal-next').addEventListener('click', function(){ calMonth.setMonth(calMonth.getMonth() + 1); renderCalendar(); });
  document.getElementById('cal-today').addEventListener('click', function(){ calMonth = new Date(); calMonth.setDate(1); renderCalendar(); });

  renderSoon();
  renderCalendar();   // calendar + list are both visible on load
})();
</script>
</body>
</html>
"""