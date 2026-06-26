import streamlit as st
import json
import os
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Gestão da Equipe", page_icon="✅", layout="wide")

DATA_FILE = "data.json"

# ── DADOS ──────────────────────────────────────────────────────────────────────
def carregar():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d.get("tarefas", []), d.get("pendencias", [])
    return [], []

def salvar(tarefas, pendencias):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"tarefas": tarefas, "pendencias": pendencias}, f, ensure_ascii=False, indent=2)

if "tarefas" not in st.session_state or "pendencias" not in st.session_state:
    t, p = carregar()
    st.session_state.tarefas = t
    st.session_state.pendencias = p

if "pessoa" not in st.session_state:
    st.session_state.pessoa = ""
if "view" not in st.session_state:
    st.session_state.view = "dashboard"
if "form_open" not in st.session_state:
    st.session_state.form_open = None  # None | "tarefa" | "pendencia" | "encaminhamento"
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

def hoje():
    return date.today().isoformat()

def salvar_tudo():
    salvar(st.session_state.tarefas, st.session_state.pendencias)

# ── NOTIFICAÇÕES (JS injetado) ──────────────────────────────────────────────────
def widget_notificacoes(tarefas, testar=False, titulo_teste="", desc_teste=""):
    """
    Componente sempre presente no sidebar.
    Usa Notification API nativa (funciona em https do Streamlit Cloud).
    Salva tarefas no localStorage para o intervalo continuar mesmo após reruns.
    """
    tarefas_json = json.dumps(tarefas, ensure_ascii=False)
    modo = "testar" if testar else "checar"
    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin:0; padding:0; background:transparent; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; overflow:hidden; }}
  #wrap {{ padding:4px 0; }}
  #perm-btn {{ display:none; width:100%; padding:7px 10px; background:#eaf3de; border:1px solid #3b6d11; border-radius:6px; color:#27500a; font-size:12px; cursor:pointer; }}
  #toast {{ display:none; background:#fff; border:1.5px solid #e08a00; border-left:5px solid #e08a00; border-radius:8px; padding:10px 12px; box-shadow:0 4px 16px rgba(0,0,0,.18); }}
  #toast.show {{ display:block; }}
  .tl {{ font-size:10px; font-weight:700; color:#854f0b; text-transform:uppercase; letter-spacing:.05em; margin-bottom:2px; }}
  .tt {{ font-size:13px; font-weight:600; color:#18180f; }}
  .td {{ font-size:11px; color:#5a5a50; margin-top:2px; }}
  #tc {{ float:right; border:none; background:none; cursor:pointer; color:#9a9a8e; font-size:18px; line-height:1; padding:0; margin-left:6px; }}
  #status {{ font-size:10px; color:#9a9a8e; padding:2px 0; }}
</style>
</head>
<body>
<div id="wrap">
  <div id="status">⏱ Monitorando lembretes...</div>
  <button id="perm-btn" onclick="pedirPermissao()">🔔 Ativar notificações do sistema</button>
  <div id="toast">
    <button id="tc" onclick="fechar()">×</button>
    <div class="tl" id="tl">Lembrete</div>
    <div class="tt" id="tt"></div>
    <div class="td" id="td"></div>
  </div>
</div>
<script>
// Salvar tarefas no localStorage para persistir entre reruns
var tarefasNovas = {tarefas_json};
var modo = "{modo}";
localStorage.setItem('gt_tarefas', JSON.stringify(tarefasNovas));

var hoje = new Date().toISOString().split('T')[0];
var diaSem = ['dom','seg','ter','qua','qui','sex','sab'][new Date().getDay()];

function fechar(){{ document.getElementById('toast').classList.remove('show'); }}

function tocarSom(){{
  try{{
    var ctx=new(window.AudioContext||window.webkitAudioContext)();
    function bip(f,t,d){{
      var o=ctx.createOscillator(),g=ctx.createGain();
      o.connect(g);g.connect(ctx.destination);o.type='sine';o.frequency.value=f;
      g.gain.setValueAtTime(0,ctx.currentTime+t);
      g.gain.linearRampToValueAtTime(0.35,ctx.currentTime+t+0.02);
      g.gain.linearRampToValueAtTime(0,ctx.currentTime+t+d);
      o.start(ctx.currentTime+t);o.stop(ctx.currentTime+t+d+0.1);
    }}
    bip(880,0,0.15);bip(880,0.2,0.15);bip(1100,0.4,0.25);
  }}catch(e){{}}
}}

function mostrarToast(titulo,desc){{
  var hora=new Date().toLocaleTimeString('pt-BR',{{hour:'2-digit',minute:'2-digit'}});
  document.getElementById('tl').textContent='Lembrete · '+hora;
  document.getElementById('tt').textContent=titulo;
  document.getElementById('td').textContent=desc||'';
  document.getElementById('toast').classList.add('show');
  tocarSom();
  if(window.Notification&&Notification.permission==='granted'){{
    try{{new Notification('🔔 '+titulo,{{body:desc||titulo}});}}catch(e){{}}
  }}
}}

function pedirPermissao(){{
  if(!window.Notification)return;
  Notification.requestPermission().then(function(p){{
    document.getElementById('perm-btn').style.display='none';
    if(p==='granted')mostrarToast('✅ Notificações ativadas!','Você será avisada mesmo com a aba em segundo plano.');
  }});
}}

function deveAvisar(t){{
  if(t.status==='concluida'||!t.lembrete)return false;
  if(t.tipo==='avulsa'||t.tipo==='reuniao'){{
    if(!t.prazo)return false;
    var d=new Date(t.prazo+'T00:00:00');
    d.setDate(d.getDate()-(t.lembreteAnte||0));
    return d.toISOString().split('T')[0]===hoje;
  }}
  if(t.tipo==='recorrente'){{
    if(t.recorrencia==='diaria')return true;
    if(t.recorrencia==='semanal'&&t.dias)return t.dias.indexOf(diaSem)>=0;
    if(t.recorrencia==='quinzenal'&&t.diaMes){{
      var ref=new Date(t.diaMes+'T00:00:00'),hjd=new Date(hoje+'T00:00:00');
      return Math.round((hjd-ref)/86400000)%14===0;
    }}
    if(t.recorrencia==='mensal'&&t.diaMes){{
      return new Date(t.diaMes+'T00:00:00').getDate()===new Date().getDate();
    }}
  }}
  return false;
}}

function checar(){{
  // Sempre lê do localStorage — persiste entre reruns do Streamlit
  var tarefas=JSON.parse(localStorage.getItem('gt_tarefas')||'[]');
  var fired=JSON.parse(localStorage.getItem('gt_fired')||'{{}}');
  var agora=new Date(), atual=agora.getHours()*60+agora.getMinutes();
  var hora_str=agora.toLocaleTimeString('pt-BR',{{hour:'2-digit',minute:'2-digit'}});
  document.getElementById('status').textContent='⏱ Verificado às '+hora_str;
  tarefas.forEach(function(t){{
    if(!deveAvisar(t))return;
    var partes=(t.lembreteHora||'08:00').split(':');
    var alvo=parseInt(partes[0])*60+parseInt(partes[1]);
    if(atual<alvo||atual>alvo+3)return;
    var key=t.id+'_'+hoje+'_'+(t.lembreteHora||'08:00');
    if(fired[key])return;
    fired[key]=true;localStorage.setItem('gt_fired',JSON.stringify(fired));
    mostrarToast(t.titulo,t.desc||'');
  }});
}}

// Permissão
if(window.Notification&&Notification.permission==='default'){{
  document.getElementById('perm-btn').style.display='block';
}}

if(modo==='testar'){{
  var tarefas=JSON.parse(localStorage.getItem('gt_tarefas')||'[]');
  var t=tarefas.find(function(x){{return x.lembrete;}});
  mostrarToast(t?t.titulo:'Teste de aviso',t?(t.desc||''):'Som e aviso funcionando!');
}}

// Inicia intervalo — persiste enquanto o iframe existir
if(!window._gt_interval){{
  window._gt_interval=setInterval(checar,30000);
  checar();
}}
</script>
</body>
</html>"""
    st.components.v1.html(html, height=90, scrolling=False)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
div[data-testid="stSidebarContent"] { padding-top: 1rem; }
.block-container { padding: 1.5rem 2rem; }
.card { background: white; border: 0.5px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 14px 16px; margin-bottom: 8px; }
.card-overdue { border-left: 3px solid #a32d2d !important; }
.card-urgente { border-left: 3px solid #854f0b !important; }
.card-rec { border-left: 3px solid #185fa5 !important; }
.card-reuniao { border-left: 3px solid #534ab7 !important; }
.card-done { opacity: 0.55; }
.badge { display:inline-block; padding:2px 8px; border-radius:8px; font-size:11px; font-weight:500; margin-right:4px; }
.b-red { background:#fcebeb; color:#791f1f; }
.b-amber { background:#faeeda; color:#633806; }
.b-green { background:#eaf3de; color:#27500a; }
.b-blue { background:#e6f1fb; color:#0c447c; }
.b-purple { background:#eeedfe; color:#3c3489; }
.b-gray { background:#f0efe9; color:#5a5a50; }
.b-teal { background:#e1f5ee; color:#085041; }
.stat-box { background:white; border:0.5px solid rgba(0,0,0,0.1); border-radius:10px; padding:14px 16px; text-align:center; }
.stat-val { font-size:28px; font-weight:700; }
.stat-lbl { font-size:11px; color:#9a9a8e; text-transform:uppercase; letter-spacing:.06em; }
.proc-bar-bg { height:4px; background:#e0e0e0; border-radius:2px; margin:6px 0; }
.pend-dot-aberta { color:#854f0b; font-size:10px; }
.pend-dot-enc { color:#185fa5; font-size:10px; }
.pend-dot-res { color:#3b6d11; font-size:10px; }
.enc-box { background:#e6f1fb; border-left:3px solid #185fa5; border-radius:6px; padding:8px 10px; margin-top:8px; font-size:13px; }
h3 { font-size:15px !important; font-weight:600 !important; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────────────────
def status_prazo(prazo_str):
    if not prazo_str:
        return "ok"
    try:
        d = date.fromisoformat(prazo_str)
        diff = (d - date.today()).days
        if diff < 0: return "vencido"
        if diff <= 2: return "urgente"
        return "ok"
    except:
        return "ok"

def fmt_data(d):
    if not d: return ""
    try:
        return date.fromisoformat(d).strftime("%d/%m/%Y")
    except:
        return d

def dias_text(prazo_str):
    if not prazo_str: return ""
    try:
        diff = (date.fromisoformat(prazo_str) - date.today()).days
        if diff < 0: return f"{abs(diff)}d atraso"
        if diff == 0: return "Hoje"
        if diff == 1: return "Amanhã"
        return f"{diff}d"
    except:
        return ""

def badge(txt, cls):
    return f'<span class="badge {cls}">{txt}</span>'

def prazo_badge(prazo):
    if not prazo: return ""
    st_ = status_prazo(prazo)
    cls = "b-red" if st_=="vencido" else "b-amber" if st_=="urgente" else "b-green"
    return badge(f"📅 {fmt_data(prazo)} · {dias_text(prazo)}", cls)

def rec_label(t):
    nomes = {"seg":"Segunda","ter":"Terça","qua":"Quarta","qui":"Quinta","sex":"Sexta"}
    r = t.get("recorrencia","")
    if r == "semanal" and t.get("dias"):
        return "Toda " + ", ".join(nomes.get(d,d) for d in t["dias"])
    if r == "quinzenal" and t.get("diaMes"):
        try:
            ref = date.fromisoformat(t["diaMes"])
            dn = ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"][ref.weekday()+1 if ref.weekday()<6 else 0]
            return f"Quinzenal ({dn}-feira)"
        except:
            return "Quinzenal"
    if r == "mensal" and t.get("diaMes"):
        try:
            return f"Mensal (dia {date.fromisoformat(t['diaMes']).day})"
        except:
            return "Mensal"
    return r.capitalize() if r else ""

def borda_card(t):
    if t.get("status") == "concluida": return ""
    if t.get("tipo") == "recorrente": return "card-rec"
    if t.get("tipo") == "reuniao": return "card-reuniao"
    st_ = status_prazo(t.get("prazo",""))
    if st_ == "vencido": return "card-overdue"
    if st_ == "urgente": return "card-urgente"
    return ""

# ── RENDER TAREFA CARD ─────────────────────────────────────────────────────────
def render_tarefa(t, key_prefix=""):
    done = t.get("status") == "concluida"
    cls = "card " + borda_card(t) + (" card-done" if done else "")
    tipo = t.get("tipo","")

    tipo_badge = ""
    if tipo == "recorrente": tipo_badge = badge("↻ Recorrente", "b-blue")
    elif tipo == "reuniao": tipo_badge = badge("👥 Reunião", "b-purple")
    elif tipo == "avulsa": tipo_badge = badge("☑ Avulsa", "b-gray")

    rec_b = badge(f"↻ {rec_label(t)}", "b-blue") if tipo=="recorrente" and rec_label(t) else ""
    pb = prazo_badge(t.get("prazo",""))
    resp_b = badge(f"👤 {t.get('resp','')}", "b-gray") if t.get("resp") else ""
    prio_b = badge("Alta prioridade", "b-red") if t.get("prio")=="alta" else ""
    hora_b = badge(f"🕐 {t.get('hora','')}", "b-gray") if t.get("hora") else ""
    local_b = badge(f"📍 {t.get('local','')}", "b-gray") if t.get("local") else ""
    lem_b = badge(f"🔔 {t.get('lembreteHora','')}", "b-amber") if t.get("lembrete") else ""

    passos = t.get("passos", [])
    feitos = sum(1 for p in passos if p.get("feito"))
    passos_b = badge(f"⤵ {feitos}/{len(passos)} passos", "b-teal") if passos else ""
    prog_pct = int(feitos/len(passos)*100) if passos else 0

    titulo_style = "text-decoration:line-through;" if done else ""

    html = f"""<div class="{cls}">
      <div style="font-size:14px;font-weight:600;color:#18180f;margin-bottom:3px;{titulo_style}">{t.get('titulo','')}</div>
      {"<div style='font-size:12px;color:#5a5a50;margin-bottom:4px'>"+t.get('desc','')+"</div>" if t.get('desc') else ""}
      <div style="margin:4px 0">{tipo_badge}{rec_b}{pb}{hora_b}{local_b}{resp_b}{prio_b}{passos_b}{lem_b}</div>"""

    if passos:
        html += f"""<div class="proc-bar-bg"><div style="height:4px;background:#3b6d11;border-radius:2px;width:{prog_pct}%"></div></div>"""

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Passos expandíveis
    if passos:
        with st.expander(f"Passos do processo ({feitos}/{len(passos)})", expanded=False):
            for i, p in enumerate(passos):
                c1, c2 = st.columns([0.05, 0.95])
                with c1:
                    checked = st.checkbox("", value=p.get("feito", False),
                                         key=f"{key_prefix}_step_{t['id']}_{i}",
                                         label_visibility="collapsed")
                with c2:
                    st.markdown(f"{'~~' if p.get('feito') else ''}{p['texto']}{'~~' if p.get('feito') else ''}")
                if checked != p.get("feito", False):
                    if st.session_state.get(f"confirm_step_{t['id']}_{i}"):
                        for tarefa in st.session_state.tarefas:
                            if tarefa["id"] == t["id"]:
                                tarefa["passos"][i]["feito"] = checked
                                todos = all(pp.get("feito") for pp in tarefa["passos"])
                                if todos: tarefa["status"] = "concluida"
                                elif tarefa["status"] == "concluida": tarefa["status"] = "em andamento"
                        salvar_tudo()
                        st.session_state.pop(f"confirm_step_{t['id']}_{i}", None)
                        st.rerun()
                    else:
                        acao = "Confirmar" if checked else "Desmarcar"
                        st.warning(f"{acao} passo: **{p['texto']}**?")
                        c1b, c2b = st.columns(2)
                        with c1b:
                            if st.button("✓ Sim", key=f"cs_ok_{t['id']}_{i}"):
                                st.session_state[f"confirm_step_{t['id']}_{i}"] = True
                                st.rerun()
                        with c2b:
                            if st.button("✗ Não", key=f"cs_no_{t['id']}_{i}"):
                                st.rerun()

    # Pauta reunião
    if tipo == "reuniao" and t.get("pauta"):
        with st.expander("📋 Pauta", expanded=False):
            for item in t["pauta"]:
                st.markdown(f"• {item}")

    # Botões de ação
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    with c1:
        lbl = "↩ Reabrir" if done else "✓ Concluir"
        if st.button(lbl, key=f"conc_{key_prefix}_{t['id']}", use_container_width=True):
            st.session_state[f"confirm_conc_{t['id']}"] = True
    with c2:
        if st.button("✏ Editar", key=f"edit_{key_prefix}_{t['id']}", use_container_width=True):
            st.session_state.edit_id = t["id"]
            st.session_state.form_open = "tarefa"
            st.rerun()
    with c3:
        if st.button("🗑 Excluir", key=f"del_{key_prefix}_{t['id']}", use_container_width=True):
            st.session_state[f"confirm_del_{t['id']}"] = True

    # Confirmações
    if st.session_state.get(f"confirm_conc_{t['id']}"):
        acao = "Reabrir" if done else "Marcar como concluída"
        st.warning(f"{acao}: **{t['titulo']}**?")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✓ Confirmar", key=f"conc_ok_{t['id']}"):
                for tarefa in st.session_state.tarefas:
                    if tarefa["id"] == t["id"]:
                        tarefa["status"] = "pendente" if done else "concluida"
                        tarefa["concluido"] = None if done else hoje()
                salvar_tudo()
                st.session_state.pop(f"confirm_conc_{t['id']}", None)
                st.rerun()
        with cc2:
            if st.button("✗ Cancelar", key=f"conc_no_{t['id']}"):
                st.session_state.pop(f"confirm_conc_{t['id']}", None)
                st.rerun()

    if st.session_state.get(f"confirm_del_{t['id']}"):
        st.error(f"Excluir permanentemente: **{t['titulo']}**?")
        cd1, cd2 = st.columns(2)
        with cd1:
            if st.button("🗑 Excluir", key=f"del_ok_{t['id']}"):
                st.session_state.tarefas = [x for x in st.session_state.tarefas if x["id"] != t["id"]]
                salvar_tudo()
                st.session_state.pop(f"confirm_del_{t['id']}", None)
                st.rerun()
        with cd2:
            if st.button("✗ Cancelar", key=f"del_no_{t['id']}"):
                st.session_state.pop(f"confirm_del_{t['id']}", None)
                st.rerun()

    st.markdown("---")

# ── RENDER PENDÊNCIA ───────────────────────────────────────────────────────────
def render_pendencia(p, key_prefix=""):
    status = p.get("status", "aberta")
    dot = {"aberta":"🔴","encaminhada":"🔵","resolvida":"🟢"}.get(status,"🔴")
    st_badge = {"aberta": badge("Aberta","b-amber"), "encaminhada": badge("Encaminhada","b-blue"), "resolvida": badge("Resolvida","b-green")}.get(status,"")
    pb = prazo_badge(p.get("prazo",""))
    quem_b = badge(f"👤 {p.get('quem','')}", "b-gray") if p.get("quem") else ""

    st.markdown(f"""<div class="card">
      <div style="display:flex;align-items:flex-start;gap:10px">
        <span style="font-size:16px;margin-top:2px">{dot}</span>
        <div style="flex:1">
          <div style="font-size:14px;font-weight:600;color:#18180f;margin-bottom:4px">{p.get('desc','')}</div>
          <div>{st_badge}{quem_b}{pb}</div>
          <div style="font-size:11px;color:#9a9a8e;margin-top:3px">Criado em {fmt_data(p.get('criado',''))}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Histórico de encaminhamentos
    encs = p.get("encaminhamentos", [])
    if encs:
        with st.expander(f"📋 Histórico ({len(encs)} encaminhamento(s))", expanded=False):
            for e in encs:
                st.markdown(f"""<div class="enc-box">
                  <div style="font-size:10px;font-weight:700;color:#0c447c;text-transform:uppercase;margin-bottom:3px">
                    {fmt_data(e.get('data',''))} · {e.get('pessoa','')}
                  </div>
                  <div style="font-size:13px">{e.get('desc','')}</div>
                  {"<div style='font-size:12px;color:#185fa5;margin-top:3px'>Prazo: <strong>"+fmt_data(e.get('prazo',''))+"</strong></div>" if e.get('prazo') else ""}
                </div>""", unsafe_allow_html=True)

    c1, c2, c3, _ = st.columns([1.2, 1, 1, 4])
    with c1:
        if st.button("↪ Encaminhar", key=f"enc_{key_prefix}_{p['id']}", use_container_width=True):
            st.session_state.edit_id = p["id"]
            st.session_state.form_open = "encaminhamento"
            st.rerun()
    with c2:
        if st.button("✏ Editar", key=f"pedit_{key_prefix}_{p['id']}", use_container_width=True):
            st.session_state.edit_id = p["id"]
            st.session_state.form_open = "pendencia"
            st.rerun()
    with c3:
        if st.button("🗑 Excluir", key=f"pdel_{key_prefix}_{p['id']}", use_container_width=True):
            st.session_state[f"confirm_pdel_{p['id']}"] = True

    if st.session_state.get(f"confirm_pdel_{p['id']}"):
        st.error(f"Excluir permanentemente esta pendência?")
        pd1, pd2 = st.columns(2)
        with pd1:
            if st.button("🗑 Excluir", key=f"pdel_ok_{p['id']}"):
                st.session_state.pendencias = [x for x in st.session_state.pendencias if x["id"] != p["id"]]
                salvar_tudo()
                st.session_state.pop(f"confirm_pdel_{p['id']}", None)
                st.rerun()
        with pd2:
            if st.button("✗ Cancelar", key=f"pdel_no_{p['id']}"):
                st.session_state.pop(f"confirm_pdel_{p['id']}", None)
                st.rerun()
    st.markdown("")

# ── FORMULÁRIOS ────────────────────────────────────────────────────────────────
def form_tarefa():
    edit = None
    if st.session_state.edit_id:
        edit = next((t for t in st.session_state.tarefas if t["id"] == st.session_state.edit_id), None)

    titulo_form = "✏️ Editar tarefa" if edit else "➕ Nova tarefa"
    with st.expander(titulo_form, expanded=True):
        tipo = st.selectbox("Tipo", ["recorrente","avulsa","reuniao"],
                           index=["recorrente","avulsa","reuniao"].index(edit.get("tipo","avulsa")) if edit else 0,
                           format_func=lambda x: {"recorrente":"↻ Tarefa recorrente","avulsa":"☑ Tarefa avulsa","reuniao":"👥 Reunião"}[x])

        titulo = st.text_input("Título *", value=edit.get("titulo","") if edit else "")
        desc = st.text_area("Descrição", value=edit.get("desc","") if edit else "", height=80)

        col1, col2 = st.columns(2)
        with col1:
            resp = st.text_input("Responsável", value=edit.get("resp", st.session_state.pessoa) if edit else st.session_state.pessoa)
        with col2:
            prio = st.selectbox("Prioridade", ["normal","alta","baixa"],
                               index=["normal","alta","baixa"].index(edit.get("prio","normal")) if edit else 0,
                               format_func=lambda x: {"normal":"Normal","alta":"Alta","baixa":"Baixa"}[x])

        # Recorrência
        rec = None; dias_sel = []; dia_mes = ""
        if tipo == "recorrente":
            rec = st.selectbox("Frequência", ["semanal","diaria","quinzenal","mensal"],
                              index=["semanal","diaria","quinzenal","mensal"].index(edit.get("recorrencia","semanal")) if edit and edit.get("recorrencia") else 0,
                              format_func=lambda x: {"semanal":"Semanal","diaria":"Diária","quinzenal":"Quinzenal","mensal":"Mensal"}[x])
            if rec == "semanal":
                opcoes = {"seg":"Segunda","ter":"Terça","qua":"Quarta","qui":"Quinta","sex":"Sexta"}
                dias_sel_nomes = st.multiselect("Dia(s) da semana",
                    options=list(opcoes.values()),
                    default=[opcoes[d] for d in (edit.get("dias",[]) if edit else [])])
                inv = {v:k for k,v in opcoes.items()}
                dias_sel = [inv[n] for n in dias_sel_nomes]
            elif rec in ["quinzenal","mensal"]:
                dm_val = None
                if edit and edit.get("diaMes"):
                    try: dm_val = date.fromisoformat(edit["diaMes"])
                    except: dm_val = None
                lbl = "Data de referência (1ª ocorrência)" if rec=="quinzenal" else "Dia de referência (mesmo dia todo mês)"
                dm = st.date_input(lbl, value=dm_val or date.today())
                dia_mes = dm.isoformat()

        # Prazo / hora
        prazo = ""; hora = ""; local = ""; pauta_txt = ""
        if tipo in ["avulsa","reuniao"]:
            col1, col2 = st.columns(2)
            with col1:
                pv = None
                if edit and edit.get("prazo"):
                    try: pv = date.fromisoformat(edit["prazo"])
                    except: pv = None
                prazo_d = st.date_input("Data / prazo", value=pv)
                prazo = prazo_d.isoformat() if prazo_d else ""
            with col2:
                hora = st.text_input("Horário", value=edit.get("hora","") if edit else "", placeholder="Ex: 14h30")
        if tipo == "reuniao":
            local = st.text_input("Local ou link", value=edit.get("local","") if edit else "")
            pauta_val = chr(10).join(edit.get("pauta",[]) if edit else [])
            pauta_txt = st.text_area("Pauta prévia (uma por linha)", value=pauta_val, height=80)

        # Lembrete
        lem = st.checkbox("🔔 Ativar lembrete por notificação", value=edit.get("lembrete",False) if edit else False)
        lem_hora = "08:00"; lem_ante = 0
        if lem:
            col1, col2 = st.columns(2)
            with col1:
                lem_hora = st.text_input("Avisar no horário (HH:MM)", value=edit.get("lembreteHora","08:00") if edit else "08:00")
            with col2:
                lem_ante = st.selectbox("Com antecedência",
                    options=[0,1,2,3],
                    index=edit.get("lembreteAnte",0) if edit else 0,
                    format_func=lambda x: {0:"No dia",1:"1 dia antes",2:"2 dias antes",3:"3 dias antes"}[x])

        # Processo
        tem_proc = st.checkbox("⤵ Esta tarefa tem processo (passo a passo)?",
                               value=bool(edit.get("passos") if edit else False))
        passos = []
        if tem_proc:
            n_passos = st.number_input("Quantos passos?", min_value=1, max_value=20,
                                       value=max(len(edit.get("passos",[])),1) if edit else 3)
            for i in range(int(n_passos)):
                val = edit["passos"][i]["texto"] if edit and edit.get("passos") and i < len(edit["passos"]) else ""
                feito = edit["passos"][i]["feito"] if edit and edit.get("passos") and i < len(edit["passos"]) else False
                txt = st.text_input(f"Passo {i+1}", value=val, key=f"passo_{i}")
                if txt.strip():
                    passos.append({"texto": txt.strip(), "feito": feito})

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("💾 Salvar", type="primary", use_container_width=True):
                if not titulo.strip():
                    st.error("Informe o título.")
                else:
                    obj = {
                        "id": edit["id"] if edit else str(int(datetime.now().timestamp()*1000)),
                        "tipo": tipo, "titulo": titulo.strip(), "desc": desc.strip(),
                        "resp": resp.strip(), "prio": prio,
                        "prazo": prazo, "hora": hora.strip(),
                        "local": local.strip() if tipo=="reuniao" else "",
                        "pauta": [x.strip() for x in pauta_txt.split("\n") if x.strip()] if tipo=="reuniao" else [],
                        "recorrencia": rec if tipo=="recorrente" else None,
                        "dias": dias_sel if rec=="semanal" else None,
                        "diaMes": dia_mes if rec in ["quinzenal","mensal"] else "",
                        "passos": passos,
                        "lembrete": lem, "lembreteHora": lem_hora, "lembreteAnte": lem_ante,
                        "status": edit.get("status","pendente") if edit else "pendente",
                        "criado": edit.get("criado", hoje()) if edit else hoje(),
                        "pessoa": st.session_state.pessoa,
                    }
                    if edit:
                        st.session_state.tarefas = [obj if t["id"]==edit["id"] else t for t in st.session_state.tarefas]
                    else:
                        st.session_state.tarefas.append(obj)
                    salvar_tudo()
                    st.session_state.form_open = None
                    st.session_state.edit_id = None
                    st.rerun()
        with col2:
            if st.button("✗ Cancelar", use_container_width=False):
                st.session_state.form_open = None
                st.session_state.edit_id = None
                st.rerun()

def form_pendencia():
    edit = None
    if st.session_state.edit_id:
        edit = next((p for p in st.session_state.pendencias if p["id"] == st.session_state.edit_id), None)

    with st.expander("✏️ Pendência" if edit else "➕ Nova pendência", expanded=True):
        desc = st.text_area("Descrição da pendência *", value=edit.get("desc","") if edit else "", height=90)
        col1, col2 = st.columns(2)
        with col1:
            quem = st.text_input("Quem está envolvido", value=edit.get("quem","") if edit else "")
        with col2:
            pv = None
            if edit and edit.get("prazo"):
                try: pv = date.fromisoformat(edit["prazo"])
                except: pv = None
            prazo_d = st.date_input("Prazo (se houver)", value=pv)
            prazo = prazo_d.isoformat() if prazo_d else ""
        status = st.radio("Status", ["aberta","encaminhada","resolvida"],
                         index=["aberta","encaminhada","resolvida"].index(edit.get("status","aberta")) if edit else 0,
                         horizontal=True,
                         format_func=lambda x: {"aberta":"🔴 Aberta","encaminhada":"🔵 Encaminhada","resolvida":"🟢 Resolvida"}[x])
        col1, col2 = st.columns([1,5])
        with col1:
            if st.button("💾 Salvar", type="primary", use_container_width=True):
                if not desc.strip():
                    st.error("Descreva a pendência.")
                else:
                    obj = {
                        "id": edit["id"] if edit else str(int(datetime.now().timestamp()*1000)),
                        "desc": desc.strip(), "quem": quem.strip(),
                        "prazo": prazo, "status": status,
                        "encaminhamentos": edit.get("encaminhamentos",[]) if edit else [],
                        "criado": edit.get("criado", hoje()) if edit else hoje(),
                        "pessoa": st.session_state.pessoa,
                    }
                    if edit:
                        st.session_state.pendencias = [obj if p["id"]==edit["id"] else p for p in st.session_state.pendencias]
                    else:
                        st.session_state.pendencias.append(obj)
                    salvar_tudo()
                    st.session_state.form_open = None
                    st.session_state.edit_id = None
                    st.rerun()
        with col2:
            if st.button("✗ Cancelar", key="canc_pend"):
                st.session_state.form_open = None
                st.session_state.edit_id = None
                st.rerun()

def form_encaminhamento():
    pend_id = st.session_state.edit_id
    pend = next((p for p in st.session_state.pendencias if p["id"] == pend_id), None)
    titulo_pend = pend.get("desc","")[:60] if pend else ""

    with st.expander(f"↪ Encaminhar: {titulo_pend}", expanded=True):
        if not pend:
            st.warning("Pendência não encontrada.")
        else:
            desc = st.text_area("O que foi encaminhado / decidido *", height=90)
            col1, col2 = st.columns(2)
            with col1:
                prazo_d = st.date_input("Prazo dado pelo gerente", value=None)
                prazo = prazo_d.isoformat() if prazo_d else ""
            with col2:
                novo_status = st.radio("Novo status", ["encaminhada","resolvida","aberta"],
                                      horizontal=True,
                                      format_func=lambda x: {"aberta":"🔴 Aberta","encaminhada":"🔵 Encaminhada","resolvida":"🟢 Resolvida"}[x])
            col1, col2 = st.columns([1,5])
            with col1:
                if st.button("💾 Salvar", type="primary", use_container_width=True):
                    if not desc.strip():
                        st.error("Descreva o encaminhamento.")
                    else:
                        enc = {"id": str(int(datetime.now().timestamp()*1000)),
                               "desc": desc.strip(), "prazo": prazo,
                               "status": novo_status, "data": hoje(),
                               "pessoa": st.session_state.pessoa}
                        for p in st.session_state.pendencias:
                            if p["id"] == pend_id:
                                p.setdefault("encaminhamentos",[]).append(enc)
                                p["status"] = novo_status
                        salvar_tudo()
                        st.session_state.form_open = None
                        st.session_state.edit_id = None
                        st.rerun()
            with col2:
                if st.button("✗ Cancelar", key="canc_enc"):
                    st.session_state.form_open = None
                    st.session_state.edit_id = None
                    st.rerun()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✅ Gestão da Equipe")

    nome = st.text_input("Seu nome", value=st.session_state.pessoa, placeholder="Ex: Ana, João...")
    if nome != st.session_state.pessoa:
        st.session_state.pessoa = nome

    st.markdown("---")
    st.markdown("**Visão geral**")
    ativas = [t for t in st.session_state.tarefas if t.get("status") != "concluida"]
    pend_ab = [p for p in st.session_state.pendencias if p.get("status") != "resolvida"]
    venc = [t for t in ativas if status_prazo(t.get("prazo","")) in ["vencido","urgente"]]

    views = {
        "dashboard": "📊 Dashboard",
        "todas": f"📋 Todas as tarefas ({len(ativas)})",
        "recorrentes": "↻ Recorrentes",
        "reunioes": "👥 Reuniões",
        "avulsas": "☑ Avulsas",
        "kanban": "⬛ Kanban",
    }
    for k, v in views.items():
        if st.button(v, key=f"nav_{k}", use_container_width=True,
                     type="primary" if st.session_state.view == k else "secondary"):
            st.session_state.view = k
            st.session_state.form_open = None
            st.rerun()

    st.markdown("**Pendências**")
    pend_views = {
        "pendencias": f"⏳ Lista ({len(pend_ab)} abertas)",
        "pauta": "📋 Pauta p/ gerente",
    }
    for k, v in pend_views.items():
        if st.button(v, key=f"nav_{k}", use_container_width=True,
                     type="primary" if st.session_state.view == k else "secondary"):
            st.session_state.view = k
            st.session_state.form_open = None
            st.rerun()

    st.markdown("**Filtros**")
    filter_views = {
        "vencendo": f"🔴 Vencendo ({len(venc)})",
        "concluidas": "✅ Concluídas",
    }
    for k, v in filter_views.items():
        if st.button(v, key=f"nav_{k}", use_container_width=True,
                     type="primary" if st.session_state.view == k else "secondary"):
            st.session_state.view = k
            st.session_state.form_open = None
            st.rerun()

    st.markdown("---")
    if st.button("🔔 Testar aviso", use_container_width=True):
        st.session_state["testar_notif"] = True
        st.rerun()

# ── WIDGET DE NOTIFICAÇÕES ─────────────────────────────────────────────────────
testar = st.session_state.pop("testar_notif", False)
t_teste = next((t for t in st.session_state.tarefas if t.get("lembrete")), None)
widget_notificacoes(
    st.session_state.tarefas,
    testar=testar,
    titulo_teste=t_teste["titulo"] if t_teste else "Teste de aviso",
    desc_teste=t_teste.get("desc","") if t_teste else "Funcionando!"
)

# ── VIEWS ──────────────────────────────────────────────────────────────────────
view = st.session_state.view
tarefas = st.session_state.tarefas
pendencias = st.session_state.pendencias
ativas = [t for t in tarefas if t.get("status") != "concluida"]

# Formulários no topo
if st.session_state.form_open == "tarefa":
    form_tarefa()
elif st.session_state.form_open == "pendencia":
    form_pendencia()
elif st.session_state.form_open == "encaminhamento":
    form_encaminhamento()

# ── DASHBOARD ──────────────────────────────────────────────────────────────────
if view == "dashboard" and not st.session_state.form_open:
    conc = [t for t in tarefas if t.get("status") == "concluida"]
    venc_n = [t for t in ativas if status_prazo(t.get("prazo","")) == "vencido"]
    urg_n = [t for t in ativas if status_prazo(t.get("prazo","")) == "urgente"]
    pend_ab = [p for p in pendencias if p.get("status") != "resolvida"]

    c1,c2,c3,c4,c5 = st.columns(5)
    for col, val, lbl, cor in [
        (c1, len(ativas), "Ativas", "#18180f"),
        (c2, len(venc_n), "Atrasadas", "#a32d2d"),
        (c3, len(urg_n), "Urgentes", "#854f0b"),
        (c4, len(pend_ab), "Pendências abertas", "#993c1d"),
        (c5, len(conc), "Concluídas", "#3b6d11"),
    ]:
        col.markdown(f"""<div class="stat-box">
          <div class="stat-val" style="color:{cor}">{val}</div>
          <div class="stat-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    prox = sorted([t for t in ativas if t.get("prazo")], key=lambda t: t["prazo"])[:5]
    if prox:
        st.markdown("### 🕐 Próximos vencimentos")
        for t in prox:
            render_tarefa(t, "dash")

    if pend_ab:
        st.markdown("### ⏳ Pendências em aberto")
        for p in pend_ab[:3]:
            render_pendencia(p, "dash")
        if len(pend_ab) > 3:
            if st.button(f"Ver todas as {len(pend_ab)} pendências"):
                st.session_state.view = "pendencias"
                st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nova tarefa", type="primary", use_container_width=True):
            st.session_state.form_open = "tarefa"
            st.session_state.edit_id = None
            st.rerun()
    with col2:
        if st.button("➕ Nova pendência", use_container_width=True):
            st.session_state.form_open = "pendencia"
            st.session_state.edit_id = None
            st.rerun()

# ── LISTAS DE TAREFAS ──────────────────────────────────────────────────────────
elif view in ["todas","recorrentes","reunioes","avulsas","vencendo","concluidas"] and not st.session_state.form_open:
    filtros = {
        "todas": (lambda t: t.get("status")!="concluida", "📋 Todas as tarefas"),
        "recorrentes": (lambda t: t.get("tipo")=="recorrente" and t.get("status")!="concluida", "↻ Tarefas recorrentes"),
        "reunioes": (lambda t: t.get("tipo")=="reuniao" and t.get("status")!="concluida", "👥 Reuniões"),
        "avulsas": (lambda t: t.get("tipo")=="avulsa" and t.get("status")!="concluida", "☑ Tarefas avulsas"),
        "vencendo": (lambda t: t.get("status")!="concluida" and status_prazo(t.get("prazo","")) in ["vencido","urgente"], "🔴 Vencendo / Atrasadas"),
        "concluidas": (lambda t: t.get("status")=="concluida", "✅ Concluídas"),
    }
    fn, titulo = filtros[view]
    lista = sorted([t for t in tarefas if fn(t)],
                   key=lambda t: (t.get("status")=="concluida", ["vencido","urgente","ok"].index(status_prazo(t.get("prazo",""))) if status_prazo(t.get("prazo","")) in ["vencido","urgente","ok"] else 3, t.get("prazo","9")))

    col1, col2 = st.columns([4,1])
    with col1:
        st.markdown(f"### {titulo} ({len(lista)})")
    with col2:
        if st.button("➕ Nova tarefa", type="primary", use_container_width=True):
            st.session_state.form_open = "tarefa"
            st.session_state.edit_id = None
            st.rerun()

    if lista:
        for t in lista:
            render_tarefa(t, view)
    else:
        st.info("Nenhuma tarefa aqui.")

# ── KANBAN ─────────────────────────────────────────────────────────────────────
elif view == "kanban" and not st.session_state.form_open:
    st.markdown("### ⬛ Kanban")
    colunas = [("pendente","Pendente"),("em andamento","Em andamento"),("aguardando","Aguardando"),("concluida","Concluída")]
    cols = st.columns(4)
    for col, (status_k, label) in zip(cols, colunas):
        with col:
            cards = [t for t in tarefas if t.get("status") == status_k]
            st.markdown(f"**{label}** ({len(cards)})")
            st.markdown("---")
            for t in cards:
                pb = prazo_badge(t.get("prazo",""))
                st.markdown(f"""<div class="card">
                  <div style="font-size:13px;font-weight:600">{t.get('titulo','')}</div>
                  <div style="margin-top:4px">{pb}</div>
                  <div style="font-size:11px;color:#9a9a8e;margin-top:2px">{t.get('resp','')}</div>
                </div>""", unsafe_allow_html=True)
                if status_k != "concluida":
                    prox_status = {"pendente":"em andamento","em andamento":"aguardando","aguardando":"concluida"}.get(status_k,"")
                    if st.button(f"→ {prox_status.capitalize()}", key=f"kb_{t['id']}"):
                        st.session_state[f"confirm_kb_{t['id']}"] = prox_status
                if st.session_state.get(f"confirm_kb_{t['id']}"):
                    ns = st.session_state[f"confirm_kb_{t['id']}"]
                    st.warning(f"Mover para **{ns}**?")
                    kc1,kc2=st.columns(2)
                    with kc1:
                        if st.button("✓",key=f"kb_ok_{t['id']}"):
                            for tarefa in st.session_state.tarefas:
                                if tarefa["id"]==t["id"]:
                                    tarefa["status"]=ns
                                    if ns=="concluida": tarefa["concluido"]=hoje()
                            salvar_tudo()
                            st.session_state.pop(f"confirm_kb_{t['id']}",None)
                            st.rerun()
                    with kc2:
                        if st.button("✗",key=f"kb_no_{t['id']}"):
                            st.session_state.pop(f"confirm_kb_{t['id']}",None)
                            st.rerun()

# ── PENDÊNCIAS ─────────────────────────────────────────────────────────────────
elif view == "pendencias" and not st.session_state.form_open:
    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        st.markdown(f"### ⏳ Lista de pendências ({len(pendencias)})")
    with col2:
        if st.button("↪ Encaminhar", use_container_width=True):
            pend_ab2 = [p for p in pendencias if p.get("status")!="resolvida"]
            if pend_ab2:
                st.session_state.edit_id = pend_ab2[0]["id"]
            st.session_state.form_open = "encaminhamento"
            st.rerun()
    with col3:
        if st.button("➕ Nova", type="primary", use_container_width=True):
            st.session_state.form_open = "pendencia"
            st.session_state.edit_id = None
            st.rerun()

    ordem = {"aberta":0,"encaminhada":1,"resolvida":2}
    lista_p = sorted(pendencias, key=lambda p: ordem.get(p.get("status","aberta"),3))
    if lista_p:
        for p in lista_p:
            render_pendencia(p, "pend")
    else:
        st.info("Nenhuma pendência cadastrada.")

# ── PAUTA ──────────────────────────────────────────────────────────────────────
elif view == "pauta" and not st.session_state.form_open:
    abertas = [p for p in pendencias if p.get("status") != "resolvida"]
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    st.markdown(f"### 📋 Pauta para o gerente — {hoje_str}")
    st.markdown(f"**{len(abertas)} pendência(s) em aberto**")

    if abertas:
        for i, p in enumerate(abertas):
            with st.expander(f"{i+1}. {p.get('desc','')[:80]}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    if p.get("quem"):
                        st.markdown(f"**Envolvido:** {p['quem']}")
                with col2:
                    if p.get("prazo"):
                        st.markdown(f"**Prazo:** {fmt_data(p['prazo'])}")
                status_label = {"aberta":"🔴 Aberta","encaminhada":"🔵 Encaminhada","resolvida":"🟢 Resolvida"}.get(p.get("status","aberta"),"")
                st.markdown(f"**Status:** {status_label}")
                encs = p.get("encaminhamentos",[])
                if encs:
                    st.markdown("**Histórico:**")
                    for e in encs:
                        st.markdown(f"&nbsp;&nbsp;· {fmt_data(e.get('data',''))} — {e.get('desc','')} {'· prazo: '+fmt_data(e['prazo']) if e.get('prazo') else ''}")
                st.markdown("---")
                st.markdown("**Encaminhamento / instrução do gerente:**")
                st.text_input("", placeholder="Anote aqui a instrução...", key=f"pauta_enc_{p['id']}", label_visibility="collapsed")
    else:
        st.success("🎉 Nenhuma pendência em aberto para a pauta!")
