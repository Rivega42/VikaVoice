"""
Минимальный веб-кабинет (E7.2, скелет): список встреч, стенограмма, протокол, поиск.
Одна самодостаточная страница поверх существующего JSON-API — без сборки фронтенда,
без внешних CDN (работает офлайн в Edge-редакции). Полноценный кабинет — EPIC-7.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VikaVoice — кабинет</title>
<style>
  :root { color-scheme: light dark;
    --bg:#fff; --fg:#1a1a1a; --muted:#667; --card:#f4f5f7; --acc:#2456d6; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14161a; --fg:#e8e8ea; --muted:#99a; --card:#1e2127; --acc:#7aa2ff; } }
  body { margin:0; font:15px/1.5 system-ui,sans-serif; background:var(--bg); color:var(--fg);
         display:grid; grid-template-columns:320px 1fr; min-height:100vh; }
  aside { border-right:1px solid var(--card); padding:16px; overflow-y:auto; }
  main { padding:16px 24px; overflow-y:auto; }
  h1 { font-size:18px; margin:0 0 12px; }
  input[type=search] { width:100%; box-sizing:border-box; padding:8px 10px; margin-bottom:12px;
    border:1px solid var(--card); border-radius:8px; background:var(--card); color:var(--fg); }
  .sess { padding:10px 12px; border-radius:8px; cursor:pointer; margin-bottom:6px;
          background:var(--card); }
  .sess:hover { outline:2px solid var(--acc); }
  .sess .meta { color:var(--muted); font-size:12px; }
  .badge { font-size:11px; padding:1px 8px; border-radius:10px; background:var(--acc);
           color:#fff; }
  .seg { margin:6px 0; }
  .spk { color:var(--acc); font-weight:600; margin-right:6px; }
  .t { color:var(--muted); font-size:12px; margin-right:6px; }
  button { padding:6px 14px; border-radius:8px; border:1px solid var(--acc);
           background:transparent; color:var(--acc); cursor:pointer; margin-right:8px; }
  pre { background:var(--card); padding:12px; border-radius:8px; overflow-x:auto;
        white-space:pre-wrap; }
  .muted { color:var(--muted); }
</style>
</head>
<body>
<aside>
  <h1>VikaVoice</h1>
  <input type="search" id="q" placeholder="Поиск по стенограммам…">
  <div id="list" class="muted">загрузка…</div>
</aside>
<main id="view"><p class="muted">Выберите встречу слева.</p></main>
<script>
const $=s=>document.querySelector(s);
const esc=t=>t.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
const fmt=s=>{const m=Math.floor(s/60),ss=String(Math.floor(s%60)).padStart(2,"0");return m+":"+ss};

async function loadList(){
  const r=await fetch("/sessions"); const items=await r.json();
  $("#list").innerHTML = items.length ? items.map(s=>
    `<div class="sess" onclick="openSession('${s.id}')">
       <div>${esc(s.created_at||"")} <span class="badge">${esc(s.status)}</span></div>
       <div class="meta">${esc(s.source||"—")} · ${s.rate} Гц · ${s.id.slice(0,8)}</div>
     </div>`).join("") : "<p class='muted'>Сессий пока нет.</p>";
}

async function openSession(id){
  const t=await (await fetch(`/sessions/${id}/transcript`)).json();
  let html=`<h1>Встреча ${id.slice(0,8)} <span class="badge">${esc(t.status)}</span></h1>
    <p><button onclick="act('${id}','transcribe')">Транскрибировать</button>
       <button onclick="act('${id}','summarize')">Построить протокол</button>
       <button onclick="showProtocol('${id}')">Показать протокол</button></p>`;
  if(t.error) html+=`<p class="muted">Ошибка: ${esc(t.error)}</p>`;
  html += t.transcript ? t.transcript.map(s=>
      `<div class="seg"><span class="t">${fmt(s.start)}</span>` +
      `<span class="spk">${esc(s.speaker||"?")}</span>${esc(s.text)}</div>`).join("")
    : "<p class='muted'>Стенограммы ещё нет.</p>";
  $("#view").innerHTML=html;
}

async function act(id, action){
  const r=await fetch(`/sessions/${id}/${action}`,{method:"POST"});
  if(!r.ok){alert((await r.json()).detail||r.status)}
  openSession(id); loadList();
}

async function showProtocol(id){
  const r=await fetch(`/sessions/${id}/protocol`);
  if(!r.ok){alert("Протокол ещё не построен");return}
  const p=await r.json();
  $("#view").innerHTML=`<h1>Протокол ${id.slice(0,8)}</h1><pre>${esc(p.markdown)}</pre>
    <p><button onclick="openSession('${id}')">← к стенограмме</button></p>`;
}

let deb;
$("#q").addEventListener("input", e=>{
  clearTimeout(deb);
  const q=e.target.value.trim();
  if(!q){loadList();return}
  deb=setTimeout(async()=>{
    const r=await (await fetch(`/search?q=${encodeURIComponent(q)}`)).json();
    $("#list").innerHTML = r.results.length ? r.results.map(h=>
      `<div class="sess" onclick="openSession('${h.id}')">
         <div>${esc(h.created_at||"")} · ${h.id.slice(0,8)}</div>
         ${h.matches.map(m=>`<div class="meta">${fmt(m.start)} ${esc(m.text)}</div>`).join("")}
       </div>`).join("") : "<p class='muted'>Ничего не найдено.</p>";
  },250);
});

loadList();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def cabinet() -> str:
    return _PAGE
