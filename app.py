# -*- coding: utf-8 -*-
"""
🥐 Juamdy Cartagena S.A.S. — Sistema integrado de panadería (Lean Service)
Ejecutar:  streamlit run app.py
"""
import re
from datetime import date, timedelta
from html import escape as esc

import pandas as pd
import streamlit as st

import juamdy_core as k

st.set_page_config(page_title="Juamdy Cartagena S.A.S.", page_icon="🥐", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def _boot():
    k.init_db()
    return True


_boot()

# ════════════════════════════════════════════════════════════════════
#  ESTILO
# ════════════════════════════════════════════════════════════════════
CSS = """
<style>
.block-container{padding-top:1.2rem;max-width:1450px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#FFF1D6 0%,#FFD9A0 100%)}
.stTabs [data-baseweb="tab"]{font-weight:700;font-size:1rem;padding:10px 16px}
.stButton>button,.stDownloadButton>button{border-radius:12px;font-weight:700}
div[data-testid="stExpander"]{background:#fff;border-radius:14px;border:1px solid #F3D9B1}
.banner{background:linear-gradient(120deg,#7C2D12 0%,#EA580C 55%,#F59E0B 100%);color:#fff;border-radius:22px;padding:20px 28px;margin-bottom:16px;box-shadow:0 8px 24px rgba(124,45,18,.25)}
.banner .t{font-size:1.9rem;font-weight:800;line-height:1.15}
.banner .s{opacity:.95;font-size:1rem;margin-top:4px}
.hero{background:linear-gradient(135deg,#7C2D12 0%,#C2410C 40%,#F59E0B 100%);color:#fff;border-radius:28px;padding:34px 30px;text-align:center;box-shadow:0 14px 40px rgba(124,45,18,.35)}
.hero .big{font-size:3.2rem}.hero .t{font-size:2.2rem;font-weight:800}.hero .s{font-size:1.05rem;opacity:.95}
.kpi{background:#fff;border-radius:18px;padding:14px 16px;border-left:8px solid #EA580C;box-shadow:0 3px 12px rgba(91,42,18,.10);height:100%}
.kpi .l{font-size:.74rem;color:#7A5C48;font-weight:800;text-transform:uppercase;letter-spacing:.05em}
.kpi .v{font-size:1.9rem;font-weight:800;line-height:1.2}
.kpi .s{font-size:.8rem;color:#7A5C48}
.card{background:#fff;border-radius:18px;padding:14px 16px;box-shadow:0 3px 12px rgba(91,42,18,.10);border-top:7px solid #EA580C;margin-bottom:12px;color:#3B1D0E}
.card .h{font-weight:800;font-size:1.05rem}
.card .m{font-size:.85rem;color:#6B4A36}
.chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.72rem;font-weight:800;color:#fff;margin:1px 2px 1px 0}
.alert{border-radius:12px;padding:9px 12px;margin-bottom:7px;font-size:.9rem;border-left:7px solid #999;color:#3B1D0E}
.step{display:flex;gap:14px;background:#fff;border-radius:16px;padding:14px 16px;margin-bottom:10px;border-left:9px solid #EA580C;box-shadow:0 3px 10px rgba(91,42,18,.10);color:#3B1D0E}
.step .n{width:44px;height:44px;border-radius:50%;color:#fff;font-weight:800;font-size:1.1rem;display:flex;align-items:center;justify-content:center;flex:none}
.step ul{margin:6px 0 6px 18px;padding:0}
.step .ctl{background:#F0FDF4;border-radius:8px;padding:5px 9px;font-size:.85rem;margin-top:4px}
.step .err{background:#FEF2F2;border-radius:8px;padding:5px 9px;font-size:.85rem;margin-top:4px}
.bar{height:11px;background:#F1E4D3;border-radius:99px;overflow:hidden}
.bar>div{height:100%;border-radius:99px}
.kan{background:#fff;border-radius:14px;padding:9px 12px;margin-bottom:8px;border-left:7px solid #EA580C;box-shadow:0 2px 8px rgba(91,42,18,.10);color:#3B1D0E;font-size:.9rem}
.kcol{border-radius:14px;padding:6px 10px;font-weight:800;color:#fff;margin-bottom:8px;text-align:center}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:14px}
.flow .arrow{color:#B45309;font-weight:800}
.gantt{display:flex;align-items:center;margin-bottom:6px}
.gantt .gl{width:40%;font-size:.85rem;padding-right:10px;color:#3B1D0E}
.gantt .gg{width:60%;display:grid;grid-template-columns:repeat(12,1fr);gap:2px}
.gantt .cell{height:24px;border-radius:6px;background:#F1E4D3}
.pareto{display:flex;align-items:center;gap:8px;margin-bottom:7px;font-size:.88rem;color:#3B1D0E}
.pareto .nm{width:34%}.pareto .bb{width:50%}.pareto .vv{width:16%;font-weight:800}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  AYUDAS DE INTERFAZ
# ════════════════════════════════════════════════════════════════════
def H(s):
    """Markdown/HTML en una sola línea (evita que Markdown lo tome como código) y protege el signo $."""
    s = re.sub(r"\n\s*", "", s).replace("$", "&#36;")
    if not s.startswith("<div"):
        s = f"<div>{s}</div>"
    st.markdown(s, unsafe_allow_html=True)


def chip(txt, color):
    return f"<span class='chip' style='background:{color}'>{esc(str(txt))}</span>"


def kpi(label, value, sub="", color="#EA580C", icon=""):
    return (f"<div class='kpi' style='border-left-color:{color}'><div class='l'>{icon} {label}</div>"
            f"<div class='v' style='color:{color}'>{value}</div><div class='s'>{sub}</div></div>")


def kpi_row(items):
    cols = st.columns(len(items))
    for c, it in zip(cols, items):
        with c:
            H(kpi(*it))


def bar(pct, color, h=11):
    pct = max(0, min(100, pct))
    return f"<div class='bar' style='height:{h}px'><div style='width:{pct:.0f}%;background:{color}'></div></div>"


def titulo(icono, texto, sub, c1="#7C2D12", c2="#EA580C"):
    H(f"<div class='banner' style='background:linear-gradient(120deg,{c1} 0%,{c2} 100%)'>"
      f"<div class='t'>{icono} {texto}</div><div class='s'>{sub}</div></div>")


DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
ESTADO_COLOR = {"Crítico": ("#DC2626", "#FEE2E2"), "Bajo": ("#D97706", "#FEF3C7"),
                "Óptimo": ("#16A34A", "#DCFCE7"), "Exceso": ("#2563EB", "#DBEAFE")}
NIVEL = {"rojo": ("#DC2626", "#FEE2E2", "🔴"), "amarillo": ("#D97706", "#FEF3C7", "🟡"),
         "verde": ("#16A34A", "#DCFCE7", "🟢"), "azul": ("#2563EB", "#DBEAFE", "🔵")}


def alerta_html(nivel, texto):
    c, bg, ic = NIVEL[nivel]
    return f"<div class='alert' style='border-left-color:{c};background:{bg}'>{ic} {texto}</div>"


def flash(msg, kind="success"):
    st.session_state.setdefault("_flash", []).append((kind, msg))


def show_flash():
    for kind, msg in st.session_state.pop("_flash", []):
        {"success": st.success, "error": st.error, "warning": st.warning, "info": st.info}.get(kind, st.info)(msg)


def csv_btn(df, nombre, key):
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8-sig"), f"{nombre}.csv", "text/csv", key=key)


def op():
    return st.session_state.get("operador", "Operador")


def sel(label, options, key, **kw):
    """selectbox que no se rompe si la opción guardada ya no existe (p. ej. orden finalizada)."""
    options = list(options)
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
    return st.selectbox(label, options, key=key, **kw)


def step_html(s, mostrar_npr=True):
    badges = ""
    if s["critico"]:
        badges += chip("PUNTO CRÍTICO", "#DC2626")
    if s["npr"] and mostrar_npr:
        badges += chip(f"AMFE · NPR {s['npr']}", "#7C3AED")
    badges += chip(f"⏱ {s['tiempo']}", "#0EA5E9")
    bullets = "".join(f"<li>{esc(h)}</li>" for h in s["hacer"])
    return (f"<div class='step' style='border-left-color:{s['color']}'>"
            f"<div class='n' style='background:{s['color']}'>{s['n']}</div>"
            f"<div style='flex:1'><div style='font-weight:800;font-size:1.05rem'>{s['icono']} {esc(s['titulo'])}</div>"
            f"<div>{badges}</div><ul>{bullets}</ul>"
            f"<div class='ctl'>✅ <b>Control:</b> {esc(s['control'])}</div>"
            f"<div class='err'>⚠️ <b>Error común:</b> {esc(s['error'])}</div></div></div>")


# ════════════════════════════════════════════════════════════════════
#  ALERTAS (usadas en panel y barra lateral)
# ════════════════════════════════════════════════════════════════════
def calcular_alertas():
    out = []
    for _, r in k.stock_mp().iterrows():
        if r["Estado"] == "Crítico":
            out.append(("rojo", f"{r['Icono']} <b>{r['Materia']}</b>: stock crítico ({k.num(r['Stock'], 2)} {r['Unidad']}, mínimo {r['Mínimo']}). "
                                f"Comprar ≈ {k.num(r['A_pedir'], 1)} {r['Unidad']}."))
        elif r["Estado"] == "Bajo":
            out.append(("amarillo", f"{r['Icono']} <b>{r['Materia']}</b>: stock bajo ({k.num(r['Stock'], 2)} {r['Unidad']}); alcanza ≈ {r['Cobertura_dias']} días."))
    lm = k.lotes_mp_df(True)
    if len(lm):
        for _, r in lm[(lm["estado"] == "Aceptado")].iterrows():
            if r["dias_vence"] < 0:
                out.append(("rojo", f"⛔ Lote vencido {r['codigo']} ({r['materia']}): retirar del inventario."))
            elif r["dias_vence"] <= 3:
                out.append(("amarillo", f"⏳ Lote {r['codigo']} ({r['materia']}) vence en {int(r['dias_vence'])} día(s): usar primero (PEPS)."))
        for _, r in lm[(lm["estado"] == "Cuarentena")].iterrows():
            out.append(("amarillo", f"🧪 Lote {r['codigo']} ({r['materia']}) en cuarentena: pendiente de decisión del supervisor."))
    pt = k.pt_lotes_df()
    if len(pt):
        for _, r in pt.iterrows():
            if r["estado"] == "Retenido":
                out.append(("amarillo", f"🔒 Lote {r['codigo']} RETENIDO por calidad ({int(r['cantidad_actual'])} und)."))
            elif r["horas_rest"] <= 0:
                out.append(("rojo", f"🗑️ Lote {r['codigo']} vencido ({int(r['cantidad_actual'])} und): dar de baja."))
            elif r["horas_rest"] <= 6 and r["estado"] == "Disponible":
                out.append(("amarillo", f"🕒 {r['producto']} · lote {r['codigo']} vence en {r['horas_rest']:.0f} h: vender primero."))
    disp = k.pt_disponible()
    for p in k.PRODUCTOS:
        if disp[p["nombre"]] == 0:
            out.append(("rojo", f"{p['icono']} <b>{p['nombre']}</b>: AGOTADO. Programar producción."))
        elif disp[p["nombre"]] < p["stock_min"]:
            out.append(("amarillo", f"{p['icono']} <b>{p['nombre']}</b>: {disp[p['nombre']]} und (mínimo {p['stock_min']})."))
    v = k.voc_df()
    if len(v):
        n = len(v[(v["estado"] == "Abierta") & (v["gravedad"] == "Alta")])
        if n:
            out.append(("rojo", f"🗣️ {n} queja(s) de gravedad ALTA sin cerrar."))
    return out


# ════════════════════════════════════════════════════════════════════
#  LOGIN
# ════════════════════════════════════════════════════════════════════
def pantalla_login():
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        H(f"<div class='hero'><div class='big'>🥐🍞🥖</div><div class='t'>{k.EMPRESA}</div>"
          f"<div class='s'>{k.LEMA}</div><div class='s' style='margin-top:10px'>Sistema integrado de producción, inventario y calidad</div></div>")
        st.write("")
        if not st.session_state.get("auth"):
            H("<div class='card' style='border-top-color:#EA580C'><div class='h'>🔑 Paso 1 · Palabra de acceso</div>"
              "<div class='m'>Escribe la palabra clave de la panadería para entrar.</div></div>")
            with st.form("login"):
                pw = st.text_input("Palabra de acceso", type="password", placeholder="••••••")
                ok = st.form_submit_button("Entrar", type="primary")
            if ok:
                clave = k.CLAVE_ACCESO
                try:
                    clave = st.secrets.get("APP_PASSWORD", clave)
                except Exception:
                    pass
                if pw.strip().lower() == str(clave).strip().lower():
                    st.session_state["auth"] = True
                    st.rerun()
                else:
                    st.error("Palabra incorrecta. Intenta de nuevo.")
        else:
            H("<div class='card' style='border-top-color:#16A34A'><div class='h'>👷 Paso 2 · ¿Quién opera hoy?</div>"
              "<div class='m'>Todo lo que se registre quedará a nombre del operador (trazabilidad).</div></div>")
            ops = k.operadores_activos()
            nombre = st.selectbox("Operador", list(ops["nombre"]), key="login_op")
            turno = st.radio("Turno", ["🌅 Mañana", "🌇 Tarde", "🌙 Noche"], horizontal=True, key="login_turno")
            with st.expander("➕ Mi nombre no está en la lista"):
                nuevo = st.text_input("Nombre del nuevo operador", key="login_nuevo")
                if st.button("Agregar operador", key="login_add"):
                    if k.crear_operador(nuevo):
                        st.success("Operador agregado. Selecciónalo arriba.")
                        st.rerun()
                    else:
                        st.warning("Escribe un nombre.")
            c1, c2 = st.columns([2, 1])
            if c1.button("▶️ Iniciar turno", type="primary", key="login_go"):
                st.session_state["operador"] = nombre
                st.session_state["turno"] = turno
                k.log(nombre, "Acceso", "Inicio de turno", turno)
                st.rerun()
            if c2.button("← Cambiar clave", key="login_back"):
                st.session_state["auth"] = False
                st.rerun()


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: PANEL DE CONTROL
# ════════════════════════════════════════════════════════════════════
def pg_panel():
    hoy_ = k.hoy()
    titulo("🏠", "Panel de control", f"{DIAS_ES[hoy_.weekday()]} {hoy_.day} de {MESES_ES[hoy_.month - 1]} de {hoy_.year}" + f" · Turno {st.session_state.get('turno', '')} · Operador: {op()}")
    flujo = [("📥 Recepción", "#8B5CF6"), ("📦 Inventario", "#3B82F6"), ("📅 Programación", "#0EA5E9"), ("🍞 Producción", "#EA580C"),
             ("✅ Calidad", "#16A34A"), ("🛒 Venta", "#F59E0B"), ("🗣️ Voz del cliente", "#EC4899")]
    H("<div class='flow'>" + "<span class='arrow'>➜</span>".join(chip(t, c) for t, c in flujo) + "</div>")

    vt = k.ventas_df(0)
    vend = vt[vt["tipo"] == "Venta"] if len(vt) else vt
    und = int(vend["cantidad"].sum()) if len(vend) else 0
    val = float(vend["valor"].sum()) if len(vend) else 0.0
    disp = k.pt_disponible()
    ords = k.ordenes_df(fecha=k.hoy())
    pend = int((ords["estado"] == "Pendiente").sum()) if len(ords) else 0
    proc = int((ords["estado"] == "En proceso").sum()) if len(ords) else 0
    smp = k.stock_mp()
    alerta_mp = int(smp["Estado"].isin(["Crítico", "Bajo"]).sum())
    cal = k.calidad_df()
    conf = "—"
    if len(cal):
        c30 = cal[cal["ts"] >= k.ts(k.ahora() - timedelta(days=30))]
        if len(c30):
            conf = f"{(c30['resultado'] == 'Conforme').mean() * 100:.0f} %"
    v = k.voc_df()
    abiertas = int((v["estado"] == "Abierta").sum()) if len(v) else 0
    kpi_row([("Ventas de hoy", f"{und}", k.cop(val), "#F59E0B", "🛒"),
             ("Pan disponible", f"{sum(disp.values())}", "unidades vendibles", "#EA580C", "🥐"),
             ("Órdenes hoy", f"{pend + proc}", f"{pend} pendientes · {proc} en proceso", "#3B82F6", "📅"),
             ("Materias en alerta", f"{alerta_mp}", "de 11 insumos", "#DC2626" if alerta_mp else "#16A34A", "📦"),
             ("Conformidad 30 d", conf, "calidad de lotes", "#16A34A", "✅"),
             ("Quejas abiertas", f"{abiertas}", "voz del cliente", "#EC4899", "🗣️")])
    st.write("")
    a, b = st.columns([1.2, 1])
    with a:
        st.markdown("#### 🚨 Alertas y pendientes")
        al = calcular_alertas()
        if not al:
            H(alerta_html("verde", "Todo en orden. Sin alertas por ahora."))
        else:
            orden = {"rojo": 0, "amarillo": 1, "azul": 2, "verde": 3}
            H("".join(alerta_html(n, t) for n, t in sorted(al, key=lambda x: orden[x[0]])[:12]))
            if len(al) > 12:
                st.caption(f"… y {len(al) - 12} alertas más en Inventarios.")
        if len(ords) == 0:
            H(alerta_html("azul", "Aún no hay programación para hoy. Ve a <b>📅 Programación</b> para generar las órdenes según la demanda."))
    with b:
        st.markdown("#### 🥐 Pan disponible vs. mínimo")
        for p in k.PRODUCTOS:
            d = disp[p["nombre"]]
            pct = d / max(p["stock_min"] * 2, 1) * 100
            col = "#DC2626" if d == 0 else ("#D97706" if d < p["stock_min"] else "#16A34A")
            H(f"<div style='margin-bottom:9px;color:#3B1D0E'><div style='display:flex;justify-content:space-between'><b>{p['icono']} {p['nombre']}</b>"
              f"<span>{d} und <span style='opacity:.6'>(mín. {p['stock_min']})</span></span></div>{bar(pct, col, 12)}</div>")
    st.markdown("#### 📋 Tablero Kanban de hoy")
    kanban(k.hoy(), key="dash")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📈 Ventas de los últimos 14 días")
        vd = k.ventas_df(14)
        vd = vd[vd["tipo"] == "Venta"] if len(vd) else vd
        if len(vd):
            pv = vd.pivot_table(index="fecha", columns="producto", values="cantidad", aggfunc="sum").fillna(0)
            pv = pv[[p["nombre"] for p in k.PRODUCTOS if p["nombre"] in pv.columns]]
            st.bar_chart(pv, color=[k.PROD[c]["color"] for c in pv.columns])
        else:
            st.info("Aún no hay ventas registradas.")
    with c2:
        st.markdown("#### 🎯 Punto de partida (ene–jun): tasa de inconformidad")
        st.line_chart(k.HISTORICO.set_index("Mes")[["Tasa %"]], color="#DC2626")
        st.caption("Promedio 30,6 % · pico de 52,3 % en junio. Meta del proyecto: bajar a ≈ 19,9 % (escenario Rediseño).")


# ════════════════════════════════════════════════════════════════════
#  KANBAN
# ════════════════════════════════════════════════════════════════════
def kanban(fecha, key, permitir_cancelar=False):
    ords = k.ordenes_df(fecha=fecha)
    if len(ords):
        ords = ords[ords["estado"] != "Cancelada"]
    cols = st.columns(3)
    defs = [("Pendiente", "⏳ Por hacer", "#F59E0B"), ("En proceso", "🔥 En proceso", "#EA580C"), ("Terminada", "✅ Terminadas", "#16A34A")]
    for c, (est, tit, col) in zip(cols, defs):
        with c:
            sub = ords[ords["estado"] == est] if len(ords) else ords
            H(f"<div class='kcol' style='background:{col}'>{tit} · {len(sub)}</div>")
            if not len(sub):
                st.caption("—")
            for _, o in sub.iterrows():
                p = k.PROD[o["producto"]]
                extra = ""
                if est == "Terminada":
                    extra = f" · {int(o['unidades_real'] or 0)} und · lote {esc(str(o['lote_pt']))}"
                H(f"<div class='kan' style='border-left-color:{p['color']}'><b>{p['icono']} #{o['id']} {o['producto']}</b><br>"
                  f"{int(o['tandas'])} tandas · {int(o['unidades_plan'])} und{extra}</div>")
                if permitir_cancelar and est == "Pendiente":
                    if st.button(f"Cancelar #{o['id']}", key=f"{key}_cx_{o['id']}"):
                        k.cancelar_orden(int(o["id"]), op())
                        st.rerun()


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: RECEPCIÓN DE MATERIAS PRIMAS
# ════════════════════════════════════════════════════════════════════
def pg_recepcion():
    titulo("📥", "Recepción de materias primas", "Harina, mantequilla, huevos, leche y más: inspecciona, decide y registra el lote.", "#5B21B6", "#8B5CF6")
    show_flash()
    izq, der = st.columns([1.15, 1])
    with izq:
        materia = st.selectbox("¿Qué llegó?", k.NOMBRES_MP, format_func=lambda m: f"{k.MATERIAS[m]['icono']} {m}", key="rc_mat")
        info = k.MATERIAS[materia]
        H(f"<div class='card' style='border-top-color:{info['color']}'><div class='h'>{info['icono']} {materia}</div>"
          f"<div class='m'>Unidad: {info['unidad']} · Vida útil típica: {info['vida']} días · "
          f"{'❄️ Requiere frío (máx. ' + str(info['temp_max']) + ' °C)' if info['frio'] else '🌡️ Almacenar en lugar seco y fresco'}</div></div>")
        c1, c2 = st.columns(2)
        prov = c1.text_input("Proveedor", key="rc_prov")
        lote_prov = c2.text_input("Lote del proveedor / factura", key="rc_lote")
        c3, c4, c5 = st.columns(3)
        cant = c3.number_input(f"Cantidad ({info['unidad']})", min_value=0.0, value=0.0, step=1.0 if info["unidad"] == "und" else 0.5, key=f"rc_cant_{materia}")
        costo = c4.number_input("Costo total (COP)", min_value=0.0, value=0.0, step=1000.0, key=f"rc_costo_{materia}")
        venc = c5.date_input("Fecha de vencimiento", value=k.hoy() + timedelta(days=int(info["vida"] * 0.9)), key=f"rc_venc_{materia}")
        temp = None
        if info["frio"]:
            temp = st.number_input("🌡️ Temperatura al recibir (°C)", min_value=-30.0, max_value=40.0, value=4.0, step=0.5, key=f"rc_temp_{materia}")
        st.markdown("**Lista de inspección**")
        crit = [st.checkbox(c, key=f"rc_c_{materia}_{i}") for i, c in enumerate(info["criterios"])]
        aprobado, fallas = k.evaluar_recepcion(materia, crit, temp, venc)
        if aprobado:
            H(alerta_html("verde", "<b>Cumple todos los criterios.</b> Puede aceptarse el lote."))
            decision = "Aceptar"
        else:
            H(alerta_html("rojo", "<b>No cumple:</b><br>" + "<br>".join("• " + esc(f) for f in fallas)))
            decision = st.radio("Decisión", ["Rechazar", "Cuarentena"], horizontal=True, key=f"rc_dec_{materia}",
                                help="Cuarentena: queda bloqueado hasta que el supervisor lo libere o rechace.")
        obs = st.text_input("Observaciones", key=f"rc_obs_{materia}")
        if st.button("💾 Registrar recepción", type="primary", key="rc_go"):
            if cant <= 0 or not prov.strip():
                st.error("Indica el proveedor y una cantidad mayor que 0.")
            else:
                if not aprobado and not obs.strip():
                    obs = "; ".join(fallas)
                cod, est = k.recibir_mp(materia, prov.strip(), lote_prov.strip(), cant, venc, temp, crit, decision, costo, obs, op())
                flash(f"Lote {cod} registrado como {est.upper()} · {info['icono']} {materia} · {cant} {info['unidad']}", "success" if est == "Aceptado" else "warning")
                st.rerun()
    with der:
        t1, t2 = st.tabs(["📋 Últimas recepciones", "📖 Procedimiento"])
        with t1:
            lm = k.lotes_mp_df()
            if len(lm):
                v = lm.sort_values("id", ascending=False).head(12)[["codigo", "materia", "proveedor", "cantidad_inicial", "unidad", "fecha_venc", "estado"]]
                v.columns = ["Lote", "Materia", "Proveedor", "Cant.", "Und", "Vence", "Estado"]
                st.dataframe(v, hide_index=True)
            else:
                st.info("Aún no hay recepciones.")
        with t2:
            for i, (ic, t, d) in enumerate(k.PASOS_RECEPCION, 1):
                cols = ["#8B5CF6", "#6366F1", "#3B82F6", "#06B6D4", "#14B8A6", "#22C55E", "#F59E0B", "#EA580C"]
                H(f"<div class='step' style='border-left-color:{cols[i - 1]};padding:9px 12px'><div class='n' style='background:{cols[i - 1]};width:34px;height:34px'>{i}</div>"
                  f"<div><b>{ic} {t}</b><br><span style='font-size:.85rem'>{d}</span></div></div>")


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: INVENTARIOS
# ════════════════════════════════════════════════════════════════════
def pg_inventarios():
    titulo("📦", "Inventarios", "Materias primas y producto terminado con semáforos, PEPS/FEFO y kardex.", "#1E3A8A", "#3B82F6")
    show_flash()
    t1, t2, t3 = st.tabs(["🧂 Materias primas", "🥐 Producto terminado", "📒 Kardex"])
    with t1:
        s = k.stock_mp()
        leyenda = "".join(chip(e, c[0]) for e, c in ESTADO_COLOR.items())
        H(f"<div>{leyenda}</div>")
        for fila in range(0, len(s), 4):
            cols = st.columns(4)
            for c, (_, r) in zip(cols, s.iloc[fila:fila + 4].iterrows()):
                col, bg = ESTADO_COLOR[r["Estado"]]
                pct = r["Stock"] / r["Máximo"] * 100
                cob = f"{r['Cobertura_dias']} días" if r["Cobertura_dias"] is not None else "—"
                prox = r["Próx_vence"] if r["Próx_vence"] else "—"
                with c:
                    H(f"<div class='card' style='border-top-color:{col};background:{bg}'><div class='h'>{r['Icono']} {r['Materia']} {chip(r['Estado'], col)}</div>"
                      f"<div style='font-size:1.6rem;font-weight:800;color:{col}'>{k.num(r['Stock'], 2)} <span style='font-size:.9rem'>{r['Unidad']}</span></div>"
                      f"{bar(pct, col)}<div class='m'>Mín. {r['Mínimo']} · Máx. {r['Máximo']}<br>Cobertura ≈ {cob}<br>Próx. vence: {prox}</div></div>")
        comp = s[s["A_pedir"] > 0][["Materia", "Unidad", "Stock", "Mínimo", "A_pedir"]]
        if len(comp):
            st.markdown("##### 🛒 Lista de compras sugerida")
            comp.columns = ["Materia", "Unidad", "Stock", "Mínimo", "Comprar (hasta máx.)"]
            st.dataframe(comp, hide_index=True)
            csv_btn(comp, "lista_compras", "dl_compras")
        st.markdown("##### 📑 Lotes de materias primas")
        lm = k.lotes_mp_df()
        if len(lm):
            vista = lm[["id", "codigo", "materia", "proveedor", "fecha_recep", "fecha_venc", "dias_vence", "cantidad_actual", "unidad", "estado"]].copy()
            vista.columns = ["ID", "Lote", "Materia", "Proveedor", "Recibido", "Vence", "Días p/vencer", "Disponible", "Und", "Estado"]
            st.dataframe(vista, hide_index=True)
            with st.expander("🛠️ Supervisor: cambiar estado de un lote (liberar cuarentena, retirar vencido…)"):
                a, b, c = st.columns([2, 1, 1])
                lid = sel("Lote", lm["id"], "inv_lote", format_func=lambda i: f"{lm[lm['id'] == i]['codigo'].iloc[0]} · {lm[lm['id'] == i]['materia'].iloc[0]} · {lm[lm['id'] == i]['estado'].iloc[0]}")
                nuevo = b.selectbox("Nuevo estado", ["Aceptado", "Cuarentena", "Rechazado", "Vencido"], key="inv_estado")
                c.write("")
                if c.button("Aplicar", key="inv_apply"):
                    k.cambiar_estado_lote_mp(int(lid), nuevo, op())
                    flash("Estado actualizado.")
                    st.rerun()
    with t2:
        pt = k.pt_lotes_df()
        disp = k.pt_disponible()
        cols = st.columns(5)
        for c, p in zip(cols, k.PRODUCTOS):
            d = disp[p["nombre"]]
            col = "#DC2626" if d == 0 else ("#D97706" if d < p["stock_min"] else "#16A34A")
            with c:
                H(f"<div class='card' style='border-top-color:{p['color']}'><div class='h'>{p['icono']} {p['nombre']}</div>"
                  f"<div style='font-size:2rem;font-weight:800;color:{col}'>{d}</div>{bar(d / max(p['stock_min'] * 2, 1) * 100, col)}"
                  f"<div class='m'>Mínimo {p['stock_min']} · Vida útil {p['vida_h']} h</div></div>")
        if len(pt):
            v = pt[["id", "codigo", "producto", "fecha_elab", "fecha_venc", "horas_rest", "cantidad_actual", "estado"]].copy()
            v["Semáforo"] = v.apply(lambda r: "🔒 Retenido" if r["estado"] == "Retenido" else ("🔴 Vencido" if r["horas_rest"] <= 0 else ("🟡 Vende primero" if r["horas_rest"] <= 6 else "🟢 Fresco")), axis=1)
            v = v.sort_values("fecha_venc")
            v.columns = ["ID", "Lote", "Producto", "Elaborado", "Vence", "Horas rest.", "Unidades", "Estado", "Semáforo"]
            st.markdown("##### 🏷️ Lotes en inventario (orden PEPS: el primero se vende primero)")
            st.dataframe(v, hide_index=True)
            venc = pt[pt["horas_rest"] <= 0]
            if len(venc):
                H(alerta_html("rojo", f"Hay {len(venc)} lote(s) vencido(s) con {int(venc['cantidad_actual'].sum())} unidades."))
                if st.button("🗑️ Dar de baja lotes vencidos (merma)", key="pt_baja"):
                    tot = sum(k.dar_baja_pt(int(i), "Vencido", op()) for i in venc["id"])
                    flash(f"Se dieron de baja {tot} unidades vencidas.", "warning")
                    st.rerun()
        else:
            st.info("No hay producto terminado en inventario.")
    with t3:
        kd = k.kardex_df()
        if len(kd):
            tipos = st.multiselect("Filtrar por tipo de movimiento", sorted(kd["tipo"].unique()), key="kd_f")
            if tipos:
                kd = kd[kd["tipo"].isin(tipos)]
            kd.columns = ["Fecha/hora", "Tipo", "Ítem", "Cantidad", "Und", "Referencia (lote)", "Operador"]
            st.dataframe(kd, hide_index=True)
            csv_btn(kd, "kardex", "dl_kardex")
        else:
            st.info("Aún no hay movimientos.")


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: PROGRAMACIÓN
# ════════════════════════════════════════════════════════════════════
def pg_programacion():
    titulo("📅", "Programación según demanda", "Pronóstico + stock + colchón = qué panes hornear y cuántas tandas (sistema Kanban de arrastre).", "#075985", "#0EA5E9")
    show_flash()
    c1, c2, c3 = st.columns([1, 1, 2])
    fecha = c1.date_input("Fecha a programar", value=k.hoy(), key="prog_fecha")
    colchon = c2.slider("Colchón de seguridad (%)", 0, 30, 10, key="prog_col") / 100
    with c3:
        H("<div class='card' style='border-top-color:#0EA5E9'><div class='m'><b>Cómo se calcula:</b> demanda promedio de los últimos 14 días × factor del día × (1 + colchón) "
          "− pan disponible − lo ya programado → se redondea a <b>tandas de 40 panes</b>. También cuenta la demanda NO atendida (clientes que no encontraron pan).</div></div>")
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    with st.expander("⚙️ Factores de demanda por día de la semana (supuestos ajustables)"):
        cs = st.columns(7)
        factores = {i: cs[i].slider(dias[i], 0.5, 1.6, float(k.FACTORES_DIA[i]), 0.05, key=f"fd_{i}") for i in range(7)}
    plan = k.plan_demanda(fecha, colchon, factores)
    st.markdown(f"#### 🧮 Plan sugerido para {dias[fecha.weekday()]} {fecha:%d/%m/%Y}")
    cols = st.columns(5)
    tandas = {}
    pcol = {"Urgente": "#DC2626", "Normal": "#D97706", "Cubierto": "#16A34A"}
    for c, (_, r) in zip(cols, plan.iterrows()):
        p = k.PROD[r["Producto"]]
        with c:
            H(f"<div class='card' style='border-top-color:{p['color']}'><div class='h'>{p['icono']} {p['nombre']}</div>{chip(r['Prioridad'], pcol[r['Prioridad']])}"
              f"<div class='m' style='margin-top:6px'>Pronóstico: <b>{r['Pronóstico']}</b><br>Objetivo (+colchón): <b>{r['Objetivo']}</b><br>"
              f"Disponible: <b>{r['Stock']}</b> · Ya programado: <b>{r['Ya_programado']}</b><br>Faltante: <b>{r['Faltante']}</b></div></div>")
            tandas[r["Producto"]] = st.number_input("Tandas", min_value=0, max_value=40, value=min(40, int(r["Tandas"])), step=1,
                                                    key=f"pt_{p['codigo']}_{fecha}_{int(r['Tandas'])}",
                                                    help=f"1 tanda = {p['unid_tanda']} panes")
            st.caption(f"= {tandas[r['Producto']] * p['unid_tanda']} panes")
    st.caption("Fuente de demanda: " + " · ".join(f"{r['Producto'].replace('Pan de ', '')}: {r['Fuente']}" for _, r in plan.head(1).iterrows()))
    st.markdown("#### 🧂 ¿Alcanzan las materias primas?")
    req = k.requerimiento_mp(tandas)
    if len(req):
        req["Estado"] = req.apply(lambda r: "✅ Suficiente" if r["OK"] else f"❌ Falta {k.num(r['Falta'], 2)} {r['Unidad']}", axis=1)
        st.dataframe(req[["Icono", "Materia", "Unidad", "Requerido", "Disponible", "Estado"]], hide_index=True)
        if not req["OK"].all():
            H(alerta_html("rojo", "Faltan insumos para producir todo el plan. Registra la compra en <b>📥 Recepción</b> o reduce las tandas."))
    else:
        st.info("No hay tandas para producir con esta configuración.")
    total_t = sum(tandas.values())
    if st.button(f"✅ Crear órdenes de producción ({total_t} tandas)", type="primary", disabled=total_t == 0, key="prog_crear"):
        n = 0
        for prod, t in tandas.items():
            if t > 0:
                k.crear_orden(fecha, prod, t, op())
                n += 1
        flash(f"Se crearon {n} órdenes de producción para {fecha:%d/%m/%Y}. Ve a 🍞 Producción guiada.")
        st.rerun()
    st.markdown("#### 📋 Tablero Kanban")
    kanban(fecha, key="prog", permitir_cancelar=True)


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: PRODUCCIÓN GUIADA
# ════════════════════════════════════════════════════════════════════
def pg_produccion():
    titulo("🍞", "Producción guiada", "Paso a paso con controles: pesaje, porcionado, horneado y calidad. Todo queda registrado por lote.", "#7C2D12", "#EA580C")
    show_flash()
    r = st.session_state.pop("ult_prod", None)
    if r:
        if r["resultado"] == "Conforme":
            st.success(f"🎉 Lote {r['codigo']} registrado y DISPONIBLE para la venta. Calidad: CONFORME.")
            st.balloons()
        else:
            st.warning(f"🔒 Lote {r['codigo']} registrado pero RETENIDO por calidad (no se vende hasta que el supervisor lo libere).")
        if r["faltantes"]:
            st.warning("Materias primas sin stock suficiente al descontar: " + ", ".join(f"{m}: {v}" for m, v in r["faltantes"].items()))
    ords = k.ordenes_df(["Pendiente", "En proceso"])
    if ords.empty:
        H(alerta_html("azul", "No hay órdenes pendientes. Crea la programación en <b>📅 Programación</b>."))
        return
    opciones = {int(x["id"]): f"#{x['id']} · {x['producto']} · {x['tandas']} tandas · {x['estado']}" for _, x in ords.iterrows()}
    oid = sel("Selecciona la orden de producción", opciones, "prod_orden", format_func=lambda i: opciones[i])
    o = ords[ords["id"] == oid].iloc[0]
    prod, tn = o["producto"], int(o["tandas"])
    p = k.PROD[prod]
    H(f"<div class='card' style='border-top-color:{p['color']}'><div class='h' style='font-size:1.3rem'>{p['icono']} {prod} — Orden #{oid}</div>"
      f"{chip(o['estado'], '#EA580C' if o['estado'] == 'En proceso' else '#F59E0B')}"
      f"<div class='m' style='margin-top:6px'>{tn} tandas · {int(o['unidades_plan'])} panes · Peso de masa estándar {p['peso_masa_g']} g · "
      f"Horno {p['horno_c']} °C / {p['horno_min']} min · Relleno: {p['relleno']}</div></div>")
    rec = k.receta(prod, tn)
    if o["estado"] == "Pendiente":
        req = k.requerimiento_mp({prod: tn})
        req["Estado"] = req.apply(lambda x: "✅ Suficiente" if x["OK"] else f"❌ Falta {k.num(x['Falta'], 2)} {x['Unidad']}", axis=1)
        st.markdown("##### 🧂 Verificación de materias primas")
        st.dataframe(req[["Icono", "Materia", "Unidad", "Requerido", "Disponible", "Estado"]], hide_index=True)
        if st.button("▶️ Iniciar producción", type="primary", key=f"ini_{oid}"):
            ok, _ = k.iniciar_orden(int(oid), op())
            if ok:
                flash("Producción iniciada. ¡Sigue los pasos!")
                st.rerun()
            else:
                st.error("No hay materias primas suficientes. Registra la recepción o reduce las tandas.")
        with st.expander("👀 Vista previa del procedimiento (15 pasos)"):
            for s in k.pasos_produccion(prod):
                H(step_html(s))
        return

    pasos = k.pasos_produccion(prod)
    izq, der = st.columns([2.2, 1])
    done_flags, pesos, muestras, checks = [], {}, [], {}
    datos = {}
    unidades = tn * p["unid_tanda"]
    with izq:
        for s in pasos:
            n = s["n"]
            etq = f"Paso {n} · {s['icono']} {s['titulo']}" + ("  🔴 CRÍTICO" if s["critico"] else "") + f"  ·  ⏱ {s['tiempo']}"
            with st.expander(etq, expanded=(n == 1)):
                H(step_html(s))
                if n == 4:
                    st.markdown("**⚖️ Registra el peso real** (por defecto aparece lo indicado; corrígelo si pesaste distinto)")
                    cs = st.columns(3)
                    for i, (m, cant) in enumerate(rec.items()):
                        info = k.MATERIAS[m]
                        und = info["unidad"] == "und"
                        with cs[i % 3]:
                            v = st.number_input(f"{info['icono']} {m} ({info['unidad']})", min_value=0.0, value=float(cant), step=1.0 if und else 0.01,
                                                format="%.0f" if und else "%.3f", key=f"w_{oid}_{m}")
                            pesos[m] = v
                            dev = abs(v - cant) / cant if cant else 0
                            st.caption("✅ dentro de ±2 %" if dev <= k.TOLERANCIA_PESAJE else f"⚠️ desvío de {dev * 100:.1f} %")
                if n == 5:
                    a, b = st.columns(2)
                    datos["amasado_min"] = a.number_input("Minutos de amasado total", min_value=0.0, value=14.0, step=1.0, key=f"mix_{oid}")
                    datos["temp_masa_c"] = b.number_input("Temperatura de la masa (°C)", min_value=0.0, value=25.0, step=0.5, key=f"tm_{oid}")
                    if not (24 <= datos["temp_masa_c"] <= 26):
                        st.caption("⚠️ Fuera del rango objetivo 24–26 °C")
                if n == 7:
                    st.markdown(f"**🔪 Pesa 5 porciones de masa** (estándar {p['peso_masa_g']} g, aceptable {p['peso_masa_g'] * 0.95:.1f}–{p['peso_masa_g'] * 1.05:.1f} g)")
                    cs = st.columns(5)
                    for i in range(5):
                        muestras.append(cs[i].number_input(f"Muestra {i + 1} (g)", min_value=0.0, value=0.0, step=0.5, key=f"ms_{oid}_{i}"))
                    ev = k.evaluar_muestras(prod, muestras)
                    if ev["n"]:
                        col = "verde" if ev["fuera"] == 0 else "rojo"
                        H(alerta_html(col, f"Promedio <b>{ev['prom']} g</b> ({ev['desv']:+.1f} %) · {ev['fuera']} de {ev['n']} fuera de rango"
                                           + ("" if ev["fuera"] == 0 else " → <b>ajusta el cortador</b> y vuelve a pesar")))
                if n == 10:
                    a, b = st.columns(2)
                    datos["horno_c"] = a.number_input("Temperatura real del horno (°C)", min_value=0.0, value=float(p["horno_c"]), step=5.0, key=f"hc_{oid}")
                    datos["horno_min"] = b.number_input("Minutos reales de horneado", min_value=0.0, value=float(p["horno_min"]), step=1.0, key=f"hm_{oid}")
                if n == 12:
                    st.markdown("**✅ Marca lo que está CONFORME**")
                    cs = st.columns(3)
                    for i, (kk, lab) in enumerate(k.CHECKS_CALIDAD):
                        checks[kk] = cs[i % 3].checkbox(lab, key=f"q_{oid}_{kk}")
                if n == 14:
                    unidades = st.number_input("Unidades reales obtenidas (aptas para la venta)", min_value=0, value=int(tn * p["unid_tanda"]), step=1, key=f"ur_{oid}")
                done_flags.append(st.checkbox("✔ Paso completado", key=f"ck_{oid}_{n}"))
        obs = st.text_area("Observaciones o acción correctiva (obligatoria si hay desvíos o no conformidades)", key=f"obs_{oid}")
        if st.button("🏁 Finalizar y registrar lote", type="primary", key=f"fin_{oid}"):
            ev = k.evaluar_muestras(prod, muestras)
            errores = []
            if not all(done_flags):
                errores.append(f"Faltan {done_flags.count(False)} paso(s) por marcar como completados.")
            if ev["n"] < 3:
                errores.append("Registra al menos 3 pesos de muestra en el paso 7.")
            if unidades <= 0:
                errores.append("Indica las unidades obtenidas en el paso 14.")
            if (not all(checks.values()) or ev["fuera"] > 0) and not obs.strip():
                errores.append("Hay desvíos de calidad: escribe la acción correctiva / observación.")
            if errores:
                for e in errores:
                    st.error(e)
            else:
                res = k.finalizar_orden(int(oid), op(), pesos, datos, muestras, checks, int(unidades), obs.strip())
                st.session_state["ult_prod"] = res
                st.rerun()
    with der:
        hechos = sum(done_flags)
        H("<div class='card' style='border-top-color:#16A34A'><div class='h'>📊 Avance de la orden</div></div>")
        st.progress(hechos / len(pasos), text=f"{hechos} de {len(pasos)} pasos completados")
        fuera = [m for m, c_ in rec.items() if c_ and abs(pesos.get(m, c_) - c_) / c_ > k.TOLERANCIA_PESAJE]
        if fuera:
            H(alerta_html("amarillo", "Pesaje fuera de ±2 %: " + ", ".join(fuera)))
        st.markdown("##### 📦 Lotes a usar (PEPS/FEFO)")
        lm = k.lotes_mp_df(True)
        filas = []
        if len(lm):
            lm = lm[(lm["estado"] == "Aceptado") & (lm["dias_vence"] >= 0)]
            for m in rec:
                sub = lm[lm["materia"] == m].sort_values(["fecha_venc", "id"])
                if len(sub):
                    filas.append({"Materia": m, "Lote": sub.iloc[0]["codigo"], "Vence": sub.iloc[0]["fecha_venc"]})
        if filas:
            st.dataframe(pd.DataFrame(filas), hide_index=True)
        st.markdown("##### 🧾 Receta de la orden")
        st.dataframe(pd.DataFrame([{"Ingrediente": f"{k.MATERIAS[m]['icono']} {m}", "Cantidad": f"{k.num(c_, 2)} {k.MATERIAS[m]['unidad']}"} for m, c_ in rec.items()]), hide_index=True)


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: PROCEDIMIENTOS
# ════════════════════════════════════════════════════════════════════
def ficha_md(prod):
    p = k.PROD[prod]
    rec = k.receta(prod)
    lines = [f"# Ficha técnica — {prod}", f"**{k.EMPRESA}**", "",
             f"- Unidades por tanda: {p['unid_tanda']}", f"- Peso de masa: {p['peso_masa_g']} g (±5 %)", f"- Relleno: {p['relleno']} ({p['peso_relleno_g']} g)",
             f"- Horno: {p['horno_c']} °C / {p['horno_min']} min", f"- Vida útil: {p['vida_h']} h", "", "## Ingredientes por tanda"]
    lines += [f"- {m}: {k.num(c, 2)} {k.MATERIAS[m]['unidad']}" for m, c in rec.items()]
    lines += ["", "## Pasos"]
    for s in k.pasos_produccion(prod):
        lines.append(f"{s['n']}. **{s['titulo']}** ({s['tiempo']}){' — CRÍTICO' if s['critico'] else ''}")
        lines += [f"   - {h}" for h in s["hacer"]]
        lines.append(f"   - Control: {s['control']}")
    lines += ["", "*Valores de referencia: validar con el maestro panadero.*"]
    return "\n".join(lines)


def pg_procedimientos():
    titulo("📖", "Procedimientos y fichas técnicas", "Cómo se hace cada pan, paso a paso, con puntos críticos y controles.", "#14532D", "#16A34A")
    prod = st.radio("Elige el pan", k.NOMBRES_PAN, horizontal=True, format_func=lambda n: f"{k.PROD[n]['icono']} {n.replace('Pan de ', '')}", key="proc_pan")
    p = k.PROD[prod]
    t1, t2, t3, t4 = st.tabs(["🍞 Ficha técnica", "📋 Paso a paso (15 pasos)", "📥 Recepción de MP", "🧹 5S, PEPS y quejas"])
    with t1:
        H(f"<div class='banner' style='background:linear-gradient(120deg,{p['color']},#7C2D12)'><div class='t'>{p['icono']} {prod}</div>"
          f"<div class='s'>Relleno: {p['relleno']}</div></div>")
        kpi_row([("Panes por tanda", p["unid_tanda"], "unidades", p["color"], "🔢"), ("Masa por pan", f"{p['peso_masa_g']} g", f"±5 %: {p['peso_masa_g'] * .95:.1f}–{p['peso_masa_g'] * 1.05:.1f} g", "#EF4444", "⚖️"),
                 ("Relleno", f"{p['peso_relleno_g']} g", p["relleno"], "#EC4899", "🥄"), ("Horno", f"{p['horno_c']} °C", f"{p['horno_min']} minutos", "#DC2626", "🔥"),
                 ("Vida útil", f"{p['vida_h']} h", "vender antes de vencer", "#0EA5E9", "🕒")])
        st.write("")
        rec = k.receta(prod)
        df = pd.DataFrame([{"Ingrediente": f"{k.MATERIAS[m]['icono']} {m}", "Por tanda (40 panes)": f"{k.num(c, 2)} {k.MATERIAS[m]['unidad']}",
                            "Por pan": (f"{c / p['unid_tanda'] * 1000:.1f} g" if k.MATERIAS[m]["unidad"] != "und" and k.MATERIAS[m]["unidad"] != "L" else
                                        (f"{c / p['unid_tanda'] * 1000:.1f} ml" if k.MATERIAS[m]["unidad"] == "L" else f"{c / p['unid_tanda']:.2f} und")),
                            "Tolerancia de pesaje": "±2 %"} for m, c in rec.items()])
        st.dataframe(df, hide_index=True)
        H(alerta_html("amarillo", "Las cantidades son una <b>receta base de referencia</b> para empezar a estandarizar. Valídalas con el maestro panadero y ajústalas en <code>juamdy_core.py</code>."))
        crit = [s for s in k.pasos_produccion(prod) if s["critico"]]
        st.markdown("##### 🔴 Puntos críticos de este pan")
        for s in crit:
            H(alerta_html("rojo", f"<b>Paso {s['n']} · {esc(s['titulo'])}</b> — {esc(s['control'])}"))
        st.download_button("⬇️ Descargar ficha (Markdown)", ficha_md(prod).encode("utf-8"), f"ficha_{p['codigo']}.md", "text/markdown", key="dl_ficha")
    with t2:
        pasos = k.pasos_produccion(prod)
        H("<div class='flow'>" + "".join(chip(f"{s['n']}. {s['icono']}", s["color"]) for s in pasos) + "</div>")
        for s in pasos:
            H(step_html(s))
    with t3:
        st.markdown("##### Pasos de la recepción")
        for i, (ic, t, d) in enumerate(k.PASOS_RECEPCION, 1):
            H(f"<div class='step' style='border-left-color:#8B5CF6;padding:9px 12px'><div class='n' style='background:#8B5CF6;width:34px;height:34px'>{i}</div><div><b>{ic} {t}</b><br><span style='font-size:.85rem'>{d}</span></div></div>")
        st.markdown("##### Criterios por materia prima")
        df = pd.DataFrame([{"Materia": f"{m_['icono']} {m}", "Frío": f"≤ {m_['temp_max']} °C" if m_["frio"] else "No",
                            "Vida útil típica": f"{m_['vida']} días", "Criterios": " · ".join(m_["criterios"])} for m, m_ in k.MATERIAS.items()])
        st.dataframe(df, hide_index=True)
    with t4:
        for nombre, items in k.PROCEDIMIENTOS_GENERALES.items():
            with st.expander(f"📌 {nombre}", expanded=True):
                for i, it in enumerate(items, 1):
                    st.markdown(f"**{i}.** {it}")


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: CALIDAD
# ════════════════════════════════════════════════════════════════════
def pg_calidad():
    titulo("✅", "Control de calidad", "Inspección por lote, lotes retenidos y tendencia de conformidad.", "#065F46", "#10B981")
    show_flash()
    t1, t2, t3 = st.tabs(["📊 Tablero", "📝 Nueva inspección", "🔒 Lotes retenidos"])
    cal = k.calidad_df()
    with t1:
        if not len(cal):
            st.info("Aún no hay inspecciones. Se crean automáticamente al finalizar una producción.")
        else:
            conf = (cal["resultado"] == "Conforme").mean() * 100
            kpi_row([("Conformidad global", f"{conf:.0f} %", f"{len(cal)} inspecciones", "#16A34A" if conf >= 85 else "#D97706", "✅"),
                     ("No conformes", f"{int((cal['resultado'] != 'Conforme').sum())}", "lotes con desvío", "#DC2626", "⚠️"),
                     ("Peso medio vs estándar", f"{cal['desv_pct'].mean():+.1f} %", "porcionado", "#3B82F6", "⚖️"),
                     ("Panes fuera de rango", f"{int(cal['fuera_rango'].sum())}", "muestras pesadas", "#F59E0B", "📏")])
            st.write("")
            a, b = st.columns(2)
            with a:
                st.markdown("##### Conformidad por pan")
                for p in k.PRODUCTOS:
                    sub = cal[cal["producto"] == p["nombre"]]
                    if len(sub):
                        pc = (sub["resultado"] == "Conforme").mean() * 100
                        H(f"<div style='margin-bottom:8px;color:#3B1D0E'><b>{p['icono']} {p['nombre']}</b> — {pc:.0f} % ({len(sub)} lotes){bar(pc, '#16A34A' if pc >= 85 else '#D97706', 12)}</div>")
            with b:
                st.markdown("##### Atributos que más fallan")
                for kk, lab in k.CHECKS_CALIDAD:
                    nf = int((cal[kk] == 0).sum())
                    H(f"<div style='margin-bottom:8px;color:#3B1D0E'><b>{lab}</b> — {nf} fallas{bar(nf / max(len(cal), 1) * 100 * 3, '#EF4444', 10)}</div>")
            st.markdown("##### Historial de inspecciones")
            v = cal[["ts", "lote_pt", "producto", "peso_prom", "peso_std", "desv_pct", "resultado", "accion", "operador"]].copy()
            v.columns = ["Fecha", "Lote", "Producto", "Peso prom. (g)", "Estándar (g)", "Desv. %", "Resultado", "Acción correctiva", "Inspector"]
            st.dataframe(v, hide_index=True)
            csv_btn(v, "calidad", "dl_cal")
    with t2:
        pt = k.pt_lotes_df()
        if not len(pt):
            st.info("No hay lotes en inventario para inspeccionar.")
        else:
            lote = sel("Lote a inspeccionar", pt["codigo"], "qa_lote")
            prod = pt[pt["codigo"] == lote]["producto"].iloc[0]
            pp = k.PROD[prod]
            st.caption(f"{pp['icono']} {prod} · masa estándar {pp['peso_masa_g']} g ±5 %")
            cs = st.columns(5)
            ms = [cs[i].number_input(f"Muestra {i + 1} (g)", min_value=0.0, value=0.0, step=0.5, key=f"qa_m{i}") for i in range(5)]
            cs = st.columns(3)
            ck = {kk: cs[i % 3].checkbox(lab, key=f"qa_{kk}") for i, (kk, lab) in enumerate(k.CHECKS_CALIDAD)}
            acc = st.text_input("Acción correctiva (si aplica)", key="qa_acc")
            if st.button("💾 Registrar inspección", type="primary", key="qa_go"):
                ev = k.evaluar_muestras(prod, ms)
                if ev["n"] < 3:
                    st.error("Pesa al menos 3 muestras.")
                else:
                    res, _ = k.registrar_calidad(lote, prod, ms, ck, acc)
                    flash(f"Inspección registrada: {res.upper()}", "success" if res == "Conforme" else "warning")
                    st.rerun()
    with t3:
        pt = k.pt_lotes_df()
        ret = pt[pt["estado"] == "Retenido"] if len(pt) else pt
        if not len(ret):
            H(alerta_html("verde", "No hay lotes retenidos."))
        for _, r in ret.iterrows():
            H(alerta_html("amarillo", f"🔒 <b>{r['codigo']}</b> · {r['producto']} · {int(r['cantidad_actual'])} und"))
            a, b, _c = st.columns([1, 1, 3])
            if a.button("Liberar para venta", key=f"lib_{r['id']}"):
                k.liberar_pt(int(r["id"]), op())
                flash("Lote liberado.")
                st.rerun()
            if b.button("Dar de baja", key=f"bj_{r['id']}"):
                k.dar_baja_pt(int(r["id"]), "No conforme", op())
                flash("Lote dado de baja.", "warning")
                st.rerun()


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: VOZ DEL CLIENTE
# ════════════════════════════════════════════════════════════════════
def pg_voc():
    titulo("🗣️", "Voz del cliente (VOC)", "Cada queja se conecta con la etapa del proceso que la origina (AMFE).", "#9D174D", "#EC4899")
    show_flash()
    t1, t2, t3 = st.tabs(["➕ Registrar queja o sugerencia", "📋 Seguimiento", "📊 Pareto y causas"])
    with t1:
        with st.form("voc_form", clear_on_submit=True):
            a, b = st.columns(2)
            prod = a.selectbox("Producto", k.NOMBRES_PAN, key="voc_p")
            tipo = b.selectbox("¿Qué pasó?", list(k.VOC_TIPOS), key="voc_t")
            c, d, e = st.columns(3)
            canal = c.selectbox("Canal", k.VOC_CANALES, key="voc_c")
            grav = d.selectbox("Gravedad", k.VOC_GRAVEDAD, index=1, key="voc_g")
            cal = e.select_slider("Calificación del cliente", options=[1, 2, 3, 4, 5], value=3, format_func=lambda n: "⭐" * n, key="voc_cal")
            lotes = [""] + list(k.pt_lotes_df(False).sort_values("id", ascending=False)["codigo"].head(15))
            lote = st.selectbox("Lote del pan (si se conoce)", lotes, key="voc_l")
            desc = st.text_area("Lo que dijo el cliente", key="voc_d")
            ok = st.form_submit_button("💾 Registrar", type="primary")
        if ok:
            if not desc.strip():
                st.error("Escribe lo que dijo el cliente.")
            else:
                vid = k.registrar_voc(prod, tipo, canal, grav, cal, desc.strip(), lote, op())
                flash(f"Queja #{vid} registrada → etapa responsable: {k.VOC_TIPOS[tipo]}.")
                st.rerun()
        st.markdown("##### 🔗 ¿Qué etapa del proceso responde a cada tipo de queja?")
        st.dataframe(pd.DataFrame([{"Tipo de queja": t, "Etapa AMFE": e, "NPR": int(k.AMFE[k.AMFE["Etapa"] == e]["NPR"].iloc[0]) if (k.AMFE["Etapa"] == e).any() else None} for t, e in k.VOC_TIPOS.items()]), hide_index=True)
    with t2:
        v = k.voc_df()
        if not len(v):
            st.info("Aún no hay quejas.")
        else:
            ab = v[v["estado"] == "Abierta"]
            kpi_row([("Abiertas", len(ab), "por resolver", "#DC2626", "📂"), ("Cerradas", int((v["estado"] == "Cerrada").sum()), "resueltas", "#16A34A", "✅"),
                     ("Calificación media", f"{v['calificacion'].mean():.1f} ⭐", "de 5", "#F59E0B", "⭐")])
            st.write("")
            gc = {"Alta": "#DC2626", "Media": "#D97706", "Baja": "#16A34A"}
            for _, r in ab.iterrows():
                H(f"<div class='card' style='border-top-color:{gc[r['gravedad']]}'><div class='h'>#{r['id']} · {k.PROD[r['producto']]['icono']} {r['producto']} {chip(r['gravedad'], gc[r['gravedad']])} {chip(r['tipo'], '#7C3AED')}</div>"
                  f"<div class='m'>“{esc(r['descripcion'])}” — {r['canal']} · {'⭐' * int(r['calificacion'])} · {r['ts']}<br>Etapa responsable: <b>{r['etapa_amfe']}</b>{' · Lote ' + esc(r['lote']) if r['lote'] else ''}</div></div>")
            if len(ab):
                with st.expander("✅ Cerrar una queja"):
                    qid = sel("Queja", ab["id"], "voc_cerrar", format_func=lambda i: f"#{i} · {ab[ab['id'] == i]['producto'].iloc[0]} · {ab[ab['id'] == i]['tipo'].iloc[0]}")
                    accion = st.text_input("Acción tomada / causa raíz", key="voc_accion")
                    if st.button("Cerrar queja", key="voc_close"):
                        if accion.strip():
                            k.cerrar_voc(int(qid), accion.strip(), op())
                            flash("Queja cerrada.")
                            st.rerun()
                        else:
                            st.error("Describe la acción tomada.")
            st.markdown("##### Historial")
            h = v[["id", "ts", "producto", "tipo", "gravedad", "canal", "estado", "accion"]].copy()
            h.columns = ["#", "Fecha", "Producto", "Tipo", "Gravedad", "Canal", "Estado", "Acción"]
            st.dataframe(h, hide_index=True)
            csv_btn(h, "voz_cliente", "dl_voc")
    with t3:
        v = k.voc_df()
        if not len(v):
            st.info("Sin datos.")
        else:
            cnt = v["tipo"].value_counts()
            tot = cnt.sum()
            acum = 0
            st.markdown("##### Pareto de quejas")
            palette = ["#DC2626", "#EA580C", "#F59E0B", "#84CC16", "#10B981", "#06B6D4", "#6366F1", "#EC4899"]
            for i, (t, n) in enumerate(cnt.items()):
                acum += n
                H(f"<div class='pareto'><div class='nm'>{esc(t)}</div><div class='bb'>{bar(n / cnt.max() * 100, palette[i % 8], 14)}</div>"
                  f"<div class='vv'>{n} <span style='opacity:.6;font-weight:400'>({acum / tot * 100:.0f} % acum.)</span></div></div>")
            a, b = st.columns(2)
            with a:
                st.markdown("##### Quejas por etapa del proceso")
                et = v["etapa_amfe"].value_counts().rename_axis("Etapa").reset_index(name="Quejas")
                et["NPR AMFE"] = et["Etapa"].map(dict(zip(k.AMFE["Etapa"], k.AMFE["NPR"])))
                st.dataframe(et, hide_index=True)
            with b:
                st.markdown("##### Quejas por producto")
                pp = v["producto"].value_counts()
                st.bar_chart(pp, color="#EC4899")


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: VENTAS / MOSTRADOR
# ════════════════════════════════════════════════════════════════════
def pg_ventas():
    titulo("🛒", "Mostrador y ventas", "Cada venta descuenta del lote más antiguo (PEPS). Lo que el cliente no encontró también se anota: es demanda real.", "#92400E", "#F59E0B")
    show_flash()
    disp = k.pt_disponible()
    cols = st.columns(5)
    for c, p in zip(cols, k.PRODUCTOS):
        d = disp[p["nombre"]]
        with c:
            col = "#DC2626" if d == 0 else ("#D97706" if d < p["stock_min"] else "#16A34A")
            H(f"<div class='card' style='border-top-color:{p['color']}'><div class='h'>{p['icono']} {p['nombre']}</div>"
              f"<div style='font-size:2rem;font-weight:800;color:{col}'>{d}</div><div class='m'>disponibles · {k.cop(p['precio'])} c/u</div></div>")
            qty = st.number_input("Cantidad", min_value=1, max_value=300, value=1, step=1, key=f"vq_{p['codigo']}")
            b1, b2 = st.columns(2)
            if b1.button("🛒 Vender", key=f"vb_{p['codigo']}", type="primary"):
                vend, falt = k.registrar_venta(p["nombre"], int(qty), op())
                if falt:
                    flash(f"{p['nombre']}: se vendieron {vend}; {falt} no se atendieron (sin stock) y quedaron como demanda perdida.", "warning")
                else:
                    flash(f"Venta registrada: {vend} × {p['nombre']} = {k.cop(vend * p['precio'])}")
                st.rerun()
            if b2.button("🚫 Agotado", key=f"vn_{p['codigo']}", help="El cliente pidió y no había"):
                k.registrar_no_atendida(p["nombre"], int(qty), op())
                flash("Demanda no atendida registrada.", "warning")
                st.rerun()
    vd = k.ventas_df(14)
    if len(vd):
        a, b = st.columns([1.2, 1])
        with a:
            st.markdown("##### 📈 Ventas por día (14 días)")
            vv = vd[vd["tipo"] == "Venta"]
            if len(vv):
                pv = vv.pivot_table(index="fecha", columns="producto", values="cantidad", aggfunc="sum").fillna(0)
                st.bar_chart(pv, color=[k.PROD[x]["color"] for x in pv.columns])
        with b:
            st.markdown("##### 🚫 Demanda no atendida (14 días)")
            na = vd[vd["tipo"] == "No atendida"]
            if len(na):
                st.bar_chart(na.groupby("producto")["cantidad"].sum(), color="#DC2626")
                st.caption("Esta demanda perdida se suma al pronóstico para programar más producción.")
            else:
                st.caption("Sin demanda perdida registrada.")
        hoyv = vd[vd["fecha"] == k.hoy().strftime(k.FMT_D)]
        if len(hoyv):
            st.markdown("##### 🧾 Movimientos de hoy")
            h = hoyv[["ts", "producto", "cantidad", "tipo", "valor", "lote", "operador"]].copy()
            h.columns = ["Hora", "Producto", "Cant.", "Tipo", "Valor", "Lote", "Operador"]
            st.dataframe(h, hide_index=True)


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: PROYECTO LEAN
# ════════════════════════════════════════════════════════════════════
def pg_lean():
    titulo("📈", "Proyecto Lean Service", "Diagnóstico, AMFE, plan de 12 semanas y evaluación económica del proyecto de mejora.", "#4C1D95", "#8B5CF6")
    show_flash()
    t1, t2, t3, t4 = st.tabs(["📍 Diagnóstico", "⚠️ AMFE", "🛠️ Plan 12 semanas", "💰 Evaluación económica"])
    with t1:
        kpi_row([("Panes vendidos ene–jun", "32.790", "≈ 5.465 al mes", "#3B82F6", "🍞"), ("Inconformidades", "10.022", "30,6 % de las ventas", "#DC2626", "⚠️"),
                 ("Venta diaria", "≈ 182", "panes por día", "#F59E0B", "📅"), ("Pico en junio", "52,3 %", "tasa de inconformidad", "#EA580C", "📈")])
        st.write("")
        a, b = st.columns([1, 1.2])
        with a:
            st.bar_chart(k.HISTORICO.set_index("Mes")[["Tasa %"]], color="#EA580C")
        with b:
            st.dataframe(k.HISTORICO, hide_index=True)
        st.caption("Son estimaciones del registro de la empresa, no devoluciones comprobadas.")
        st.markdown("##### 🎲 Modelo de Markov: efecto esperado de la mejora")
        st.dataframe(k.MARKOV, hide_index=True)
    with t2:
        st.markdown("##### Priorización por NPR (Severidad × Ocurrencia × Detección)")
        mx = k.AMFE["NPR"].max()
        for _, r in k.AMFE.iterrows():
            col = "#DC2626" if r["NPR"] >= 200 else ("#F59E0B" if r["NPR"] >= 120 else "#16A34A")
            H(f"<div class='card' style='border-top-color:{col};padding:10px 14px'><div style='display:flex;justify-content:space-between;gap:10px'>"
              f"<div class='h'>{esc(r['Etapa'])}</div><div style='font-weight:800;color:{col};font-size:1.2rem'>NPR {r['NPR']}</div></div>"
              f"{bar(r['NPR'] / mx * 100, col, 10)}<div class='m'>{esc(r['Modo de fallo → queja VOC'])} · S·O·D = {r['S']}·{r['O']}·{r['D']}<br>"
              f"➡️ {esc(r['Acción recomendada'])}<br>🧩 En esta app: <b>{esc(r['Módulo de la app'])}</b></div></div>")
    with t3:
        pl = k.plan_lean_df()
        cab = "".join(f"<div style='text-align:center;font-size:.7rem;font-weight:800;color:#6B4A36'>S{i}</div>" for i in range(1, 13))
        H(f"<div class='gantt'><div class='gl'><b>Actividad</b></div><div class='gg'>{cab}</div></div>")
        palette = ["#14B8A6", "#EF4444", "#3B82F6", "#8B5CF6", "#22C55E", "#EC4899"]
        for i, r in pl.iterrows():
            a, b = [int(x) for x in re.split(r"[–-]", r["semanas"])]
            col = palette[i % 6]
            cells = ""
            for w in range(1, 13):
                if a <= w <= b:
                    cells += f"<div class='cell' style='background:{col}'></div>"
                else:
                    cells += "<div class='cell'></div>"
            H(f"<div class='gantt'><div class='gl'><b>S{r['semanas']}</b> · {esc(r['actividad'])}<br>{bar(r['avance'], col, 7)}</div><div class='gg'>{cells}</div></div>")
        with st.expander("✏️ Actualizar avance de una actividad"):
            a, b, c = st.columns([3, 2, 1])
            pid = a.selectbox("Actividad", list(pl["id"]), format_func=lambda i: f"S{pl[pl['id'] == i]['semanas'].iloc[0]} · {pl[pl['id'] == i]['actividad'].iloc[0][:55]}", key="pl_sel")
            av = b.slider("Avance %", 0, 100, int(pl[pl["id"] == pid]["avance"].iloc[0]), 5, key=f"pl_av_{pid}")
            c.write("")
            if c.button("Guardar", key="pl_save"):
                k.set_avance(int(pid), av)
                st.rerun()
        st.metric("Avance global del plan", f"{pl['avance'].mean():.0f} %")
    with t4:
        st.markdown("##### 🧾 Inversión: del problema a la compra de artículos")
        inv = k.INVERSION.copy()
        inv["COP"] = inv["COP"].map(k.cop)
        st.dataframe(inv, hide_index=True)
        H(f"<div class='card' style='border-top-color:#16A34A'><div class='h'>INVERSIÓN TOTAL: {k.cop(k.INVERSION_TOTAL)}</div></div>")
        st.markdown("##### 🎛️ Simulador (TMAR 15 %, 5 años)")
        a, b = st.columns(2)
        esc_ = a.selectbox("Escenario de mejora", list(k.UNIDADES_EVITADAS)[1:], index=1, key="eco_esc")
        costo = b.slider("Costo evitable por unidad (COP)", 300, 2000, 1000, 50, key="eco_costo")
        e = k.evaluacion_economica(k.UNIDADES_EVITADAS[esc_], costo)
        kpi_row([("Beneficio anual", k.cop(e["beneficio"]), f"{k.UNIDADES_EVITADAS[esc_]:,} und evitadas".replace(",", "."), "#3B82F6", "💵"),
                 ("VPN", k.cop(e["vpn"]), "valor presente neto", "#16A34A" if e["vpn"] > 0 else "#DC2626", "📊"),
                 ("TIR", f"{(e['tir'] or 0) * 100:,.0f} %".replace(",", "."), "vs. TMAR 15 %", "#8B5CF6", "📈"),
                 ("Recuperación", f"{e['rec_simple']:.1f} meses" if e["rec_simple"] else "—", f"descontada: {e['rec_desc']:.1f} m" if e["rec_desc"] else "", "#F59E0B", "⏱️"),
                 ("Decisión", "VIABLE" if e["viable"] else "NO VIABLE", "VPN > 0 y TIR > TMAR", "#16A34A" if e["viable"] else "#DC2626", "✅")])
        st.write("")
        flujo = [-k.INVERSION_TOTAL] + [e["beneficio"]] * 5
        acum, s_ = [], 0
        for f in flujo:
            s_ += f
            acum.append(s_)
        st.bar_chart(pd.DataFrame({"Flujo acumulado (COP)": acum}, index=[f"Año {i}" for i in range(6)]), color="#10B981")
        st.markdown("##### Escenarios del proyecto (Rediseño, −40 %)")
        filas = []
        for nm, cu in [("Pesimista ($500/u)", 500), ("Base ($1.000/u)", 1000), ("Optimista ($1.500/u)", 1500)]:
            x = k.evaluacion_economica(k.UNIDADES_EVITADAS["Rediseño (−40 %)"], cu)
            filas.append({"Escenario": nm, "Beneficio anual": k.cop(x["beneficio"]), "VPN": k.cop(x["vpn"]), "TIR": f"≈{x['tir'] * 100:,.0f} %".replace(",", "."),
                          "Recup. simple/desc. (meses)": f"{x['rec_simple']:.1f} / {x['rec_desc']:.1f}", "Decisión": "Viable" if x["viable"] else "No viable"})
        st.dataframe(pd.DataFrame(filas), hide_index=True)
        st.caption("Beneficios brutos (sin costos recurrentes). El costo por unidad es ilustrativo: valídalo con costos reales de la panadería.")


# ════════════════════════════════════════════════════════════════════
#  PÁGINA: ADMINISTRACIÓN
# ════════════════════════════════════════════════════════════════════
def pg_admin():
    titulo("⚙️", "Administración", "Operadores, bitácora de auditoría, exportación y datos de demostración.", "#1F2937", "#6B7280")
    show_flash()
    t1, t2, t3 = st.tabs(["👷 Operadores", "🕵️ Bitácora", "🧰 Datos"])
    with t1:
        st.dataframe(k.operadores_activos().rename(columns={"nombre": "Operador", "rol": "Rol"}), hide_index=True)
        a, b, c = st.columns([2, 1, 1])
        nom = a.text_input("Nuevo operador", key="ad_nom")
        rol = b.selectbox("Rol", ["Operador", "Supervisor"], key="ad_rol")
        c.write("")
        if c.button("➕ Agregar", key="ad_add"):
            if k.crear_operador(nom, rol):
                flash("Operador agregado.")
                st.rerun()
    with t2:
        b = k.bitacora_df()
        if len(b):
            b.columns = ["Fecha/hora", "Operador", "Módulo", "Acción", "Detalle"]
            st.dataframe(b, hide_index=True)
            csv_btn(b, "bitacora", "dl_bit")
        else:
            st.info("Sin registros.")
    with t3:
        st.caption(f"Base de datos: {k.DB_PATH}")
        for nombre, tabla in [("Lotes de materias primas", "lotes_mp"), ("Lotes de producto terminado", "pt_lotes"), ("Órdenes de producción", "ordenes"),
                              ("Calidad", "calidad"), ("Voz del cliente", "voc"), ("Ventas", "ventas")]:
            df = k.q(f"SELECT * FROM {tabla}")
            csv_btn(df, tabla, f"dl_{tabla}") if len(df) else None
        st.divider()
        st.markdown("##### Datos de demostración")
        H(alerta_html("amarillo", "Esto <b>borra</b> los registros actuales. Para empezar a operar de verdad, usa <b>Vaciar datos</b>."))
        ok = st.checkbox("Entiendo que se borrarán los registros", key="ad_ok")
        a, b = st.columns(2)
        if a.button("🎭 Cargar datos de demostración", disabled=not ok, key="ad_demo"):
            k.cargar_demo()
            flash("Datos de demostración cargados.")
            st.rerun()
        if b.button("🧹 Vaciar datos (empezar en limpio)", disabled=not ok, key="ad_clean"):
            k.limpiar_datos()
            flash("Datos vaciados. Empieza registrando una recepción de materias primas.", "info")
            st.rerun()


# ════════════════════════════════════════════════════════════════════
#  NAVEGACIÓN
# ════════════════════════════════════════════════════════════════════
PAGINAS = {
    "🏠 Panel de control": pg_panel,
    "📥 Recepción de materias primas": pg_recepcion,
    "📦 Inventarios": pg_inventarios,
    "📅 Programación": pg_programacion,
    "🍞 Producción guiada": pg_produccion,
    "🛒 Mostrador y ventas": pg_ventas,
    "✅ Calidad": pg_calidad,
    "🗣️ Voz del cliente": pg_voc,
    "📖 Procedimientos": pg_procedimientos,
    "📈 Proyecto Lean": pg_lean,
    "⚙️ Administración": pg_admin,
}


def main():
    if not st.session_state.get("auth") or not st.session_state.get("operador"):
        pantalla_login()
        return
    with st.sidebar:
        H(f"<div style='text-align:center'><div style='font-size:2.4rem'>🥐</div><div style='font-weight:800;font-size:1.15rem;color:#7C2D12'>{k.EMPRESA}</div>"
          f"<div style='font-size:.8rem;color:#92400E'>{k.LEMA}</div></div>")
        H(f"<div class='card' style='border-top-color:#16A34A;margin-top:10px;padding:8px 12px'><div class='m'>👷 Operador</div><div class='h'>{esc(op())}</div>"
          f"<div class='m'>{esc(st.session_state.get('turno', ''))} · {k.ahora():%H:%M}</div></div>")
        pagina = st.radio("Menú", list(PAGINAS), key="nav", label_visibility="collapsed")
        n_al = sum(1 for n, _ in calcular_alertas() if n == "rojo")
        if n_al:
            H(alerta_html("rojo", f"<b>{n_al}</b> alerta(s) crítica(s). Revisa el panel."))
        if st.button("🚪 Cerrar turno", key="logout"):
            k.log(op(), "Acceso", "Cierre de turno")
            for key in ["auth", "operador", "turno"]:
                st.session_state.pop(key, None)
            st.rerun()
    PAGINAS[pagina]()


main()
