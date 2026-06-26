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
    Componente HTML autossuficiente que roda dentro do iframe do Streamlit.
    Usa position:fixed relativo ao iframe — visível dentro do app.
    Notificação nativa do browser funciona pois Streamlit Cloud é https.
    """
    tarefas_json = json.dumps(tarefas, ensure_ascii=False)
    modo = "testar" if testar else "checar"
    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin:0; padding:0; background:transparent; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
  #toast {{
    display:none; position:fixed; bottom:16px; right:16px;
    background:#fff; border:1.5px solid #e08a00; border-left:5px solid #e08a00;
    border-radius:10px; padding:14px 16px; max-width:300px;
    box-shadow:0 8px 32px rgba(0,0,0,.22); z-index:9999;
  }}
  #toast.show {{ display:block; }}
  .t-label {{ font-size:10px; font-weight:700; color:#854f0b; text-transform:uppercase; letter-spacing:.06em; margin-bottom:3px; }}
  .t-title {{ font-size:14px; font-weight:600; color:#18180f; }}
  .t-desc {{ font-size:12px; color:#5a5a50; margin-top:2px; }}
  #t-close {{ float:right; border:none; background:none; cursor:pointer; color:#9a9a8e; font-size:20px; line-height:1; padding:0; margin-left:8px; }}
  #perm-btn {{
    display:none; width:100%; padding:8px; background:#eaf3de; border:1px solid #3b6d11;
    border-radius:6px; color:#27500a; font-size:13px; cursor:pointer; margin-top:4px;
  }}
</style>
</head>
<body>
<button id="perm-btn" onclick="pedirPermissao()">🔔 Clique para ativar notificações do sistema</button>
<div id="toast">
  <button id="t-close" onclick="fechar()">×</button>
  <div class="t-label" id="t-label">Lembrete</div>
  <div class="t-title" id="t-title"></div>
  <div class="t-desc" id="t-desc"></div>
</div>
<script>
var tarefas = {tarefas_json};
var modo = "{modo}";
var hoje = new Date().toISOString().split('T')[0];
var diaSem = ['dom','seg','ter','qua','qui','sex','sab'][new Date().getDay()];

function fechar(){{ document.getElementById('toast').classList.remove('show'); }}

function tocarSom(){{
  try{{
    var ctx = new(window.AudioContext||window.webkitAudioContext)();
    function bip(f,t,d){{
      var o=ctx.createOscillator(), g=ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type='sine'; o.frequency.value=f;
      g.gain.setValueAtTime(0, ctx.currentTime+t);
      g.gain.linearRampToValueAtTime(0.35, ctx.currentTime+t+0.02);
      g.gain.linearRampToValueAtTime(0, ctx.currentTime+t+d);
      o.start(ctx.currentTime+t); o.stop(ctx.currentTime+t+d+0.1);
    }}
    bip(880,0,0.15); bip(880,0.2,0.15); bip(1100,0.4,0.25);
  }}catch(e){{ console.warn('Som falhou',e); }}
}}

function mostrarToast(titulo, desc){{
  var hora = new Date().toLocaleTimeString('pt-BR',{{hour:'2-digit',minute:'2-digit'}});
  document.getElementById('t-label').textContent = 'Lembrete · ' + hora;
  document.getElementById('t-title').textContent = titulo;
  document.getElementById('t-desc').textContent = desc||'';
  document.getElementById('toast').classList.add('show');
  tocarSom();
  // Notificação nativa (funciona em https)
  if(window.Notification && Notification.permission==='granted'){{
    try{{ new Notification('🔔 '+titulo, {{body: desc||titulo}}); }}catch(e){{}}
  }}
}}

function pedirPermissao(){{
  if(!window.Notification) return;
  Notification.requestPermission().then(function(p){{
    document.getElementById('perm-btn').style.display='none';
    if(p==='granted') mostrarToast('Notificações ativadas!','Você receberá alertas mesmo com a aba em segundo plano.');
  }});
}}

function deveAvisarHoje(t){{
  if(t.status==='concluida'||!t.lembrete) return false;
  if(t.tipo==='avulsa'||t.tipo==='reuniao'){{
    if(!t.prazo) return false;
    var d=new Date(t.prazo+'T00:00:00');
    d.setDate(d.getDate()-(t.lembreteAnte||0));
    return d.toISOString().split('T')[0]===hoje;
  }}
  if(t.tipo==='recorrente'){{
    if(t.recorrencia==='diaria') return true;
    if(t.recorrencia==='semanal'&&t.dias) return t.dias.indexOf(diaSem)>=0;
    if(t.recorrencia==='quinzenal'&&t.diaMes){{
      var ref=new Date(t.diaMes+'T00:00:00'), hjd=new Date(hoje+'T00:00:00');
      var diff=Math.round((hjd-ref)/86400000);
      return diff>=0&&diff%14===0;
    }}
    if(t.recorrencia==='mensal'&&t.diaMes){{
      return new Date(t.diaMes+'T00:00:00').getDate()===new Date().getDate();
    }}
  }}
  return false;
}}

function checarNotificacoes(){{
  var agora=new Date(), atual=agora.getHours()*60+agora.getMinutes();
  var fired=JSON.parse(localStorage.getItem('gt_fired')||'{{}}');
  tarefas.forEach(function(t){{
    if(!deveAvisarHoje(t)) return;
    var partes=(t.lembreteHora||'08:00').split(':');
    var alvo=parseInt(partes[0])*60+parseInt(partes[1]);
    if(atual<alvo||atual>alvo+3) return;
    var key=t.id+'_'+hoje+'_'+(t.lembreteHora||'08:00');
    if(fired[key]) return;
    fired[key]=true; localStorage.setItem('gt_fired',JSON.stringify(fired));
    mostrarToast(t.titulo, t.desc||'');
  }});
}}

// Mostrar botão de permissão se ainda não foi dada
if(window.Notification && Notification.permission==='default'){{
  document.getElementById('perm-btn').style.display='block';
}}

if(modo==='testar'){{
  var t = tarefas.find(function(x){{ return x.lembrete; }});
  mostrarToast(t ? t.titulo : 'Teste de aviso', t ? (t.desc||'') : 'Som e aviso funcionando!');
}} else {{
  checarNotificacoes();
  setInterval(checarNotificacoes, 30000);
}}
</script>
</body>
</html>"""
    # altura 80 mostra o toast e o botão de permissão se necessário
    st.components.v1.html(html, height=80, scrolling=False)

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
            pauta_txt = st.text_area("Pauta prévia (uma por linha)", value="\n".join(edit.get("pauta",[]) if edit else []), he
