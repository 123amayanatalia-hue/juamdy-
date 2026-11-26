# -*- coding: utf-8 -*-
"""
Juamdy Cartagena S.A.S. - Núcleo de datos y reglas de negocio.

Aquí vive todo lo que NO es pantalla: catálogo de panes, recetas, procedimientos,
base de datos (SQLite), inventarios PEPS/FEFO, programación según demanda,
calidad, voz del cliente y la evaluación económica del proyecto Lean Service.
"""
import os
import json
import math
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date, timedelta, timezone

import pandas as pd

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Bogota")
except Exception:  # sin tzdata
    TZ = timezone(timedelta(hours=-5))

EMPRESA = "Juamdy Cartagena S.A.S."
LEMA = "Pan fresco, calidad constante, siempre disponible"
CLAVE_ACCESO = "Wandy"
DB_PATH = os.environ.get("JUAMDY_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "juamdy.db"))

FMT_TS = "%Y-%m-%d %H:%M:%S"
FMT_D = "%Y-%m-%d"


def ahora():
    return datetime.now(TZ).replace(tzinfo=None, microsecond=0)


def hoy():
    return ahora().date()


def ts(dt=None):
    return (dt or ahora()).strftime(FMT_TS)


def cop(v):
    """Formato pesos colombianos: $1.474.000"""
    try:
        return "$" + f"{float(v):,.0f}".replace(",", ".")
    except Exception:
        return str(v)


def num(v, dec=1):
    try:
        return f"{float(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


# ════════════════════════════════════════════════════════════════════
#  CATÁLOGO: PANES  (datos del diagnóstico ene-jun: 32.790 panes)
# ════════════════════════════════════════════════════════════════════
VENTA_DIARIA_PROM = 182          # ≈182 panes/día (diagnóstico)
TOLERANCIA_PESO = 0.05           # ±5 % en porcionado
TOLERANCIA_PESAJE = 0.02         # ±2 % en pesaje de ingredientes

PRODUCTOS = [
    dict(nombre="Pan de queso", codigo="QUE", icono="🧀", color="#F5B301", share=0.352, precio=2500,
         peso_masa_g=70, peso_relleno_g=30, relleno="Queso costeño", unid_tanda=40,
         horno_c=180, horno_min=20, vida_h=48, stock_min=24),
    dict(nombre="Pan de bocadillo", codigo="BOC", icono="🍬", color="#E5484D", share=0.201, precio=2000,
         peso_masa_g=70, peso_relleno_g=25, relleno="Bocadillo de guayaba", unid_tanda=40,
         horno_c=180, horno_min=18, vida_h=48, stock_min=14),
    dict(nombre="Pan de arequipe", codigo="ARE", icono="🍯", color="#B7791F", share=0.150, precio=2500,
         peso_masa_g=70, peso_relleno_g=30, relleno="Arequipe", unid_tanda=40,
         horno_c=175, horno_min=18, vida_h=48, stock_min=10),
    dict(nombre="Pan de jamón y queso", codigo="JYQ", icono="🥓", color="#F97316", share=0.149, precio=3500,
         peso_masa_g=70, peso_relleno_g=40, relleno="Jamón (20 g) + queso (20 g)", unid_tanda=40,
         horno_c=180, horno_min=20, vida_h=24, stock_min=10),
    dict(nombre="Pan de mantequilla", codigo="MAN", icono="🧈", color="#EAB308", share=0.149, precio=1500,
         peso_masa_g=70, peso_relleno_g=6, relleno="Cobertura de mantequilla", unid_tanda=40,
         horno_c=175, horno_min=17, vida_h=72, stock_min=10),
]
PROD = {p["nombre"]: p for p in PRODUCTOS}
NOMBRES_PAN = [p["nombre"] for p in PRODUCTOS]
for _p in PRODUCTOS:
    _p["peso_porcion_g"] = _p["peso_masa_g"] + _p["peso_relleno_g"]

# ════════════════════════════════════════════════════════════════════
#  MATERIAS PRIMAS
# ════════════════════════════════════════════════════════════════════
MATERIAS = {
    "Harina de trigo": dict(unidad="kg", icono="🌾", color="#D69E2E", min=25, max=125, vida=180, frio=False, temp_max=None,
                            criterios=["Empaque íntegro, sellado y seco", "Sin grumos, insectos ni olor a rancio",
                                       "Color uniforme (blanco crema)", "Fecha de vencimiento vigente y legible"]),
    "Mantequilla": dict(unidad="kg", icono="🧈", color="#F6E05E", min=4, max=20, vida=90, frio=True, temp_max=8,
                        criterios=["Empaque íntegro, sin fugas", "Color amarillo uniforme, sin manchas ni olor rancio",
                                   "Cadena de frío mantenida durante el transporte", "Fecha de vencimiento vigente y legible"]),
    "Huevos": dict(unidad="und", icono="🥚", color="#FBD38D", min=60, max=300, vida=21, frio=False, temp_max=None,
                   criterios=["Cascarón limpio y sin fisuras", "Sin olor extraño; bandejas limpias",
                              "Calibre homogéneo", "Fecha o lote legible"]),
    "Leche": dict(unidad="L", icono="🥛", color="#63B3ED", min=10, max=30, vida=5, frio=True, temp_max=5,
                  criterios=["Envase íntegro, sin hinchazón", "Olor y aspecto normales",
                             "Cadena de frío mantenida (≤ 5 °C)", "Fecha de vencimiento vigente y legible"]),
    "Azúcar": dict(unidad="kg", icono="🍚", color="#E2E8F0", min=3, max=20, vida=720, frio=False, temp_max=None,
                   criterios=["Empaque íntegro y seco", "Sin humedad ni terrones duros ni impurezas", "Fecha vigente"]),
    "Sal": dict(unidad="kg", icono="🧂", color="#CBD5E0", min=1, max=5, vida=1080, frio=False, temp_max=None,
                criterios=["Empaque íntegro y seco", "Sin impurezas ni humedad", "Fecha vigente"]),
    "Levadura": dict(unidad="kg", icono="🫧", color="#A0AEC0", min=0.5, max=2.5, vida=180, frio=True, temp_max=8,
                     criterios=["Empaque íntegro y al vacío", "Sin olor agrio; textura suelta", "Cadena de frío mantenida",
                                "Fecha de vencimiento vigente"]),
    "Queso": dict(unidad="kg", icono="🧀", color="#F6AD55", min=8, max=30, vida=30, frio=True, temp_max=8,
                  criterios=["Empaque íntegro, sin fugas de suero", "Sin moho, olor ácido ni babosidad",
                             "Cadena de frío mantenida (≤ 8 °C)", "Fecha de vencimiento vigente y legible"]),
    "Bocadillo": dict(unidad="kg", icono="🍬", color="#FC8181", min=3, max=12, vida=180, frio=False, temp_max=None,
                      criterios=["Empaque íntegro", "Color y aroma normales, sin fermentación", "Fecha vigente"]),
    "Arequipe": dict(unidad="kg", icono="🍯", color="#C05621", min=3, max=10, vida=90, frio=False, temp_max=None,
                     criterios=["Envase íntegro y bien cerrado", "Sin cristales, moho ni olor agrio", "Fecha vigente"]),
    "Jamón": dict(unidad="kg", icono="🥓", color="#F687B3", min=2, max=8, vida=30, frio=True, temp_max=5,
                  criterios=["Empaque íntegro al vacío", "Sin baba, olor ácido ni color verdoso",
                             "Cadena de frío mantenida (≤ 5 °C)", "Fecha de vencimiento vigente y legible"]),
}
NOMBRES_MP = list(MATERIAS.keys())

# Receta base: masa para 1 tanda (40 panes). VALORES DE REFERENCIA: validar con el maestro panadero.
_MASA_BASE = {"Harina de trigo": 1.60, "Azúcar": 0.20, "Sal": 0.03, "Levadura": 0.03,
              "Mantequilla": 0.16, "Huevos": 4, "Leche": 0.55}
_RELLENO = {
    "Pan de queso": {"Queso": 1.20},
    "Pan de bocadillo": {"Bocadillo": 1.00},
    "Pan de arequipe": {"Arequipe": 1.20},
    "Pan de jamón y queso": {"Jamón": 0.80, "Queso": 0.80},
    "Pan de mantequilla": {"Mantequilla": 0.24},
}


def receta(producto, tandas=1):
    """Ingredientes (por materia) para N tandas de un pan."""
    r = dict(_MASA_BASE)
    for k, v in _RELLENO[producto].items():
        r[k] = r.get(k, 0) + v
    return {k: round(v * tandas, 3) for k, v in r.items()}


def consumo_diario_estimado():
    cons = {m: 0.0 for m in NOMBRES_MP}
    for p in PRODUCTOS:
        tandas = VENTA_DIARIA_PROM * p["share"] / p["unid_tanda"]
        for m, q_ in receta(p["nombre"]).items():
            cons[m] += q_ * tandas
    return cons


# ════════════════════════════════════════════════════════════════════
#  PROCEDIMIENTOS (paso a paso)  -  15 pasos, ligados al AMFE
# ════════════════════════════════════════════════════════════════════
def pasos_produccion(producto):
    p = PROD[producto]
    masa = p["peso_masa_g"]
    lo, hi = masa * (1 - TOLERANCIA_PESO), masa * (1 + TOLERANCIA_PESO)
    return [
        dict(n=1, titulo="Preparar el área y aplicar 5S", icono="🧼", color="#14B8A6", etapa="Limpieza y 5S", npr=None,
             critico=False, tiempo="10 min",
             hacer=["Lavarse las manos 20 s, usar gorro, tapabocas y delantal limpio.",
                    "Limpiar y desinfectar mesones, amasadora, laminadora y utensilios.",
                    "Verificar que básculas, termómetro y temporizadores estén en su lugar."],
             control="Área ordenada y limpia antes de abrir ningún insumo.",
             error="Empezar con superficies sucias o sin báscula a mano."),
        dict(n=2, titulo="Revisar orden de producción (Kanban)", icono="📅", color="#3B82F6", etapa="Inventario y programación", npr=252,
             critico=True, tiempo="3 min",
             hacer=["Abrir la orden en la app: producto, tandas y unidades a producir.",
                    "Confirmar el stock de producto terminado disponible.",
                    "Producir SOLO lo que pide la orden (producción según demanda)."],
             control="Orden pendiente seleccionada y materias primas disponibles (semáforo verde).",
             error="Producir 'a ojo' y quedarse sin producto o con exceso que se pierde."),
        dict(n=3, titulo="Alistar insumos con PEPS / FEFO", icono="📦", color="#8B5CF6", etapa="Recepción de materias primas", npr=120,
             critico=False, tiempo="10 min",
             hacer=["Tomar primero el lote que vence primero (PEPS/FEFO).",
                    "Revisar aspecto, olor y fecha de cada insumo.",
                    "Separar lo dudoso y avisar al supervisor; no usarlo."],
             control="Solo lotes 'Aceptados' y vigentes. La app descuenta el inventario por lote.",
             error="Usar el lote nuevo y dejar vencer el antiguo."),
        dict(n=4, titulo="Pesar ingredientes con báscula", icono="⚖️", color="#EF4444", etapa="Pesaje de ingredientes", npr=210,
             critico=True, tiempo="15 min",
             hacer=["Tarar el recipiente y pesar cada ingrediente según la ficha técnica.",
                    "Pesar líquidos por masa (o con jarra graduada) y huevos por unidad.",
                    "Registrar en la app el peso real; tolerancia ±2 %."],
             control="Cada ingrediente dentro de ±2 % de lo indicado (semáforo en la app).",
             error="Medir con vasos o 'a ojo'; cambia sabor, textura y tamaño."),
        dict(n=5, titulo="Mezclar y amasar", icono="🌀", color="#F97316", etapa="Mezclado y amasado", npr=96,
             critico=False, tiempo="15 min",
             hacer=["Mezclar secos, agregar líquidos y huevos; 6 min velocidad lenta.",
                    "Agregar la mantequilla y amasar 8 min en velocidad rápida.",
                    "Probar la 'ventana' (la masa se estira sin romperse) y medir temperatura de la masa."],
             control="Masa lisa y elástica, temperatura 24–26 °C. Registrar minutos y temperatura.",
             error="Amasar de menos (masa pegajosa/pan denso) o de más (masa caliente y floja)."),
        dict(n=6, titulo="Primer reposo (fermentación en bloque)", icono="⏳", color="#06B6D4", etapa="Fermentación", npr=None,
             critico=False, tiempo="40 min",
             hacer=["Colocar la masa en recipiente tapado y engrasado.",
                    "Dejar reposar 40 min en lugar templado, sin corrientes de aire.",
                    "Programar el temporizador y registrar la hora."],
             control="La masa aumenta ≈ 50–70 % de volumen.",
             error="Dejar la masa destapada: se reseca la superficie."),
        dict(n=7, titulo="Dividir y porcionar a peso estándar", icono="🔪", color="#EF4444", etapa="División y porcionado", npr=210,
             critico=True, tiempo="20 min",
             hacer=[f"Cortar porciones de {masa} g (rango {lo:.1f}–{hi:.1f} g) con cortador y báscula.",
                    "Pesar 1 de cada 10 porciones; ajustar el cortador si se sale del rango.",
                    "Registrar en la app el peso de 5 porciones de muestra."],
             control=f"Peso de masa {masa} g ±5 % → todas las muestras dentro de {lo:.1f}–{hi:.1f} g.",
             error="Porciones desiguales → panes de tamaños distintos y quejas por tamaño."),
        dict(n=8, titulo="Formar, rellenar y rayar", icono="🥖", color="#EC4899", etapa="División y porcionado", npr=210,
             critico=False, tiempo="25 min",
             hacer=[f"Rellenar con {p['relleno']}: {p['peso_relleno_g']} g por pan (usar porcionador/cuchara dosificadora).",
                    "Cerrar bien el pan para que no se salga el relleno al hornear.",
                    "Rayar la superficie y ubicar en bandejas con espacio entre panes."],
             control=f"Relleno estándar de {p['peso_relleno_g']} g; mismo relleno en todos los panes.",
             error="Rellenar 'a ojo': unos panes con mucho y otros con poco relleno."),
        dict(n=9, titulo="Fermentación final", icono="🫧", color="#06B6D4", etapa="Fermentación", npr=None,
             critico=False, tiempo="45 min",
             hacer=["Dejar las bandejas tapadas, 40–50 min en lugar templado.",
                    "Prueba del dedo: al presionar suave, la masa vuelve lento.",
                    "Precalentar el horno durante este tiempo."],
             control="Panes casi duplicados de volumen, sin colapsar.",
             error="Hornear antes de tiempo (pan duro) o pasarse (pan aplastado)."),
        dict(n=10, titulo="Hornear", icono="🔥", color="#DC2626", etapa="Horneado", npr=96,
             critico=True, tiempo=f"{p['horno_min']} min",
             hacer=[f"Hornear a {p['horno_c']} °C durante {p['horno_min']} min (horno precalentado).",
                    "Rotar bandejas a la mitad del tiempo para cocción pareja.",
                    "Registrar temperatura y tiempo real de la tanda."],
             control=f"{p['horno_c']} °C / {p['horno_min']} min; dorado uniforme, sin partes crudas ni quemadas.",
             error="Abrir el horno muy seguido o hornear sin precalentar."),
        dict(n=11, titulo="Enfriar en rejillas", icono="❄️", color="#0EA5E9", etapa="Almacenamiento", npr=175,
             critico=False, tiempo="20 min",
             hacer=["Pasar los panes a rejillas limpias.",
                    "Dejar enfriar 20 min antes de empacar o guardar.",
                    "Nunca guardar pan caliente en recipiente cerrado."],
             control="Pan tibio-frío al tacto.", error="Empacar caliente: se humedece y pierde frescura."),
        dict(n=12, titulo="Verificar calidad del producto", icono="✅", color="#22C55E", etapa="Control de calidad", npr=None,
             critico=True, tiempo="5 min",
             hacer=["Revisar tamaño, color, textura (miga), relleno y cocción.",
                    "Comparar con el lote anterior; separar panes defectuosos.",
                    "Registrar el resultado en la app (Conforme / No conforme)."],
             control="5 atributos conformes. Si falla alguno el lote queda RETENIDO hasta revisión.",
             error="Saltarse la inspección: la queja llega después con el cliente."),
        dict(n=13, titulo="Almacenar y etiquetar (PEPS)", icono="🏷️", color="#8B5CF6", etapa="Almacenamiento", npr=175,
             critico=False, tiempo="5 min",
             hacer=["Etiquetar con producto, lote, fecha y hora de elaboración y de vencimiento.",
                    "Guardar en recipientes herméticos limpios; delante lo más antiguo (PEPS).",
                    "El pan con jamón y queso va refrigerado."],
             control="Toda caja/bandeja con etiqueta legible y fecha.",
             error="Mezclar lotes de distintos días sin etiqueta."),
        dict(n=14, titulo="Registrar lote en inventario", icono="🗂️", color="#3B82F6", etapa="Inventario y programación", npr=252,
             critico=True, tiempo="2 min",
             hacer=["Finalizar la orden en la app: queda creado el lote de producto terminado.",
                    "Contar unidades reales producidas y anotar mermas.",
                    "Verificar que el stock de la app coincide con lo que hay en vitrina."],
             control="Inventario físico = inventario en la app.",
             error="No registrar: luego 'no hay producto' aunque sí había."),
        dict(n=15, titulo="Limpieza y cierre", icono="🧽", color="#14B8A6", etapa="Limpieza y 5S", npr=None,
             critico=False, tiempo="15 min",
             hacer=["Lavar y desinfectar equipos y utensilios; ordenar el área.",
                    "Anotar observaciones, fallas o ideas de mejora (Kaizen).",
                    "Apagar horno y equipos; dejar básculas limpias."],
             control="Área lista para el siguiente turno.", error="Dejar residuos de masa en equipos."),
    ]


PASOS_RECEPCION = [
    ("📄", "Verificar documentos", "Factura/remisión coincide con el pedido; proveedor conocido."),
    ("👀", "Inspección visual del empaque", "Sin roturas, humedad, golpes ni plagas."),
    ("👃", "Olor, color y textura", "Comparar contra los criterios de cada materia prima."),
    ("🌡️", "Medir temperatura (productos fríos)", "Leche ≤ 5 °C, jamón ≤ 5 °C, queso/mantequilla/levadura ≤ 8 °C."),
    ("📅", "Revisar fecha de vencimiento", "Debe tener vida útil suficiente para usarse antes de vencer."),
    ("⚖️", "Pesar / contar", "Verificar la cantidad recibida contra lo facturado."),
    ("✅", "Aceptar, rechazar o poner en cuarentena", "Registrar el lote en la app. Lo rechazado NO entra al inventario."),
    ("🏷️", "Etiquetar y almacenar con PEPS", "Etiqueta con lote y vencimiento; lo más antiguo adelante; 15 cm sobre el piso."),
]

PROCEDIMIENTOS_GENERALES = {
    "Almacenamiento PEPS y 5S": [
        "Clasificar: dejar en el área solo lo que se usa. Retirar lo vencido.",
        "Ordenar: cada materia prima con su lugar y su etiqueta.",
        "Limpiar: pisos, estantes y vitrinas al cierre de cada turno.",
        "Estandarizar: mismos recipientes, etiquetas y formatos para todos.",
        "Disciplina: revisar el termohigrómetro y registrar al abrir y cerrar.",
        "PEPS: primero en entrar, primero en salir. En producto terminado, vender primero el lote más antiguo.",
        "Producto terminado: vida útil indicada en la app (24–72 h según el pan). Lo vencido se da de baja como merma.",
    ],
    "Atención de quejas (Voz del cliente)": [
        "Escuchar y agradecer; pedir disculpas sin discutir.",
        "Registrar la queja en la app: producto, tipo, gravedad y, si se sabe, el lote.",
        "Ofrecer solución inmediata (cambio o reposición) según política de la panadería.",
        "Revisar el lote en el módulo de Calidad y buscar la causa (¿qué paso falló?).",
        "Definir acción correctiva y cerrar la queja cuando se verifique.",
        "Revisar el Pareto semanal con el equipo (Kaizen).",
    ],
}

# ════════════════════════════════════════════════════════════════════
#  DATOS DEL DIAGNÓSTICO / PROYECTO (de la presentación)
# ════════════════════════════════════════════════════════════════════
HISTORICO = pd.DataFrame({
    "Mes": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
    "Ventas": [5702, 5282, 5614, 5462, 5637, 5093],
    "Inconformidades": [1558, 905, 1088, 2004, 1801, 2666],
})
HISTORICO["Tasa %"] = (HISTORICO["Inconformidades"] / HISTORICO["Ventas"] * 100).round(1)
MOTIVOS_MES = ["Calidad, textura y sabor", "Frescura y disponibilidad", "Tamaño irregular y relleno",
               "Calidad y frescura", "Disponibilidad y diferencias", "Calidad, disponibilidad y esperas"]
HISTORICO["Motivo principal"] = MOTIVOS_MES

AMFE = pd.DataFrame([
    ("Inventario y programación", "Falta de productos → disponibilidad y esperas", 7, 6, 6, "Registrar inventarios y programar según la demanda (Kanban)"),
    ("Pesaje de ingredientes", "Cantidades incorrectas → calidad, sabor y textura", 7, 6, 5, "Estandarizar cantidades, usar básculas y verificar el pesaje"),
    ("División y porcionado", "Porciones desiguales → tamaño y relleno", 6, 7, 5, "Peso estándar, moldes y verificación periódica"),
    ("Almacenamiento", "Pérdida de frescura", 7, 5, 5, "Mejorar almacenamiento, rotación PEPS y control de tiempos"),
    ("Recepción de materias primas", "Ingredientes en mal estado", 8, 3, 5, "Criterios de recepción y registro de lotes"),
    ("Mezclado y amasado", "Mezcla inadecuada → textura", 6, 4, 4, "Definir tiempos y criterios de consistencia"),
    ("Horneado", "Pan quemado o poco cocido", 8, 4, 3, "Estandarizar tiempo y temperatura; registrar por tanda"),
], columns=["Etapa", "Modo de fallo → queja VOC", "S", "O", "D", "Acción recomendada"])
AMFE["NPR"] = AMFE["S"] * AMFE["O"] * AMFE["D"]
AMFE["Módulo de la app"] = ["📅 Programación + 📦 Inventario", "🍞 Producción (pesaje con semáforo)",
                            "🍞 Producción (peso de muestra)", "📦 Inventario PT (PEPS/FEFO)",
                            "📥 Recepción de materias primas", "📖 Procedimientos (tiempos)", "🍞 Producción (horno por tanda)"]

# Tipos de queja VOC  → etapa AMFE responsable
VOC_TIPOS = {
    "Calidad, textura o sabor": "Pesaje de ingredientes",
    "Pérdida de frescura": "Almacenamiento",
    "Tamaño irregular": "División y porcionado",
    "Cantidad de relleno": "División y porcionado",
    "Disponibilidad (agotado)": "Inventario y programación",
    "Tiempo de espera": "Inventario y programación",
    "Pan quemado o crudo": "Horneado",
    "Ingrediente en mal estado": "Recepción de materias primas",
}
VOC_CANALES = ["Mostrador", "WhatsApp", "Código QR", "Redes sociales", "Pedido / domicilio"]
VOC_GRAVEDAD = ["Baja", "Media", "Alta"]

MARKOV = pd.DataFrame({
    "Indicador": ["P(producto conforme)", "P(desecho interno)", "P(inconformidad reportada)",
                  "Visitas esperadas a reproceso", "Unidades evitadas por año"],
    "Actual": ["55,1 %", "14,3 %", "30,6 %", "0,19", "—"],
    "Parcial (−20 %)": ["62,6 %", "11,9 %", "25,5 %", "0,16", "≈4.918"],
    "Rediseño (−40 %)": ["70,8 %", "9,3 %", "19,9 %", "0,12", "≈10.296"],
})

INVERSION = pd.DataFrame([
    ("Calidad, textura y sabor", "Pesaje de ingredientes (210)", "Báscula de precisión 5 kg y báscula de insumos 30 kg", 250000),
    ("Tamaño irregular y relleno", "División y porcionado (210)", "Moldes, cortadores y porcionadores", 150000),
    ("Cocción y textura", "Mezclado y horneado (96)", "Termómetros de sonda (2) y temporizadores (3)", 160000),
    ("Disponibilidad y esperas", "Inventario y programación (252)", "Tablero visual de producción; hoja de cálculo / esta app", 80000),
    ("Pérdida de frescura", "Almacenamiento (175)", "Recipientes herméticos, etiquetas y termohigrómetro", 350000),
    ("Insumos fuera de estándar", "Recepción de materias primas (120)", "Formatos impresos y carpetas", 60000),
    ("Todo el proceso", "Seguimiento", "Capacitación (3 sesiones), QR y carteles, imprevistos (10 %)", 424000),
], columns=["Problema (queja)", "Etapa AMFE (NPR)", "Compra de artículos", "COP"])
INVERSION_TOTAL = int(INVERSION["COP"].sum())  # 1.474.000

PLAN_LEAN_SEED = [
    ("1–2", "Línea base y registro de inconformidades", "Línea base verificable"),
    ("2–5", "Estandarización de pesaje y porcionado (fichas técnicas, básculas, moldes)", "Calidad, textura, sabor y tamaño uniformes"),
    ("4–8", "Programación de producción e inventario (demanda, Kanban, tablero visual)", "Mayor disponibilidad"),
    ("3–6", "5S y almacenamiento (PEPS, etiquetas por fecha)", "Pan más fresco"),
    ("5–8", "Control de calidad en la fuente (listas de verificación)", "Menos producto no conforme"),
    ("6–12", "Voz del cliente, capacitación, Kaizen y software de apoyo", "Mejora continua"),
]

TMAR = 0.15
UNIDADES_EVITADAS = {"Actual": 0, "Parcial (−20 %)": 4918, "Rediseño (−40 %)": 10296}


def vpn(tasa, inversion, flujos):
    return -inversion + sum(f / (1 + tasa) ** (i + 1) for i, f in enumerate(flujos))


def tir(inversion, flujos):
    if not flujos or sum(flujos) <= inversion:
        return None
    lo, hi = 0.0, 1.0
    while vpn(hi, inversion, flujos) > 0 and hi < 1e6:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if vpn(mid, inversion, flujos) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def evaluacion_economica(unidades_anuales, costo_unit, inversion=INVERSION_TOTAL, tasa=TMAR, anios=5):
    b = unidades_anuales * costo_unit
    flujos = [b] * anios
    v = vpn(tasa, inversion, flujos)
    t = tir(inversion, flujos)
    simple = (inversion / b * 12) if b > 0 else None
    pv1 = b / (1 + tasa)
    desc = (inversion / pv1 * 12) if b > 0 and pv1 >= inversion else None
    return dict(beneficio=b, acumulado=b * anios, vpn=v, tir=t, rec_simple=simple, rec_desc=desc,
                viable=(v > 0 and (t or 0) > tasa))


# ════════════════════════════════════════════════════════════════════
#  BASE DE DATOS
# ════════════════════════════════════════════════════════════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS operadores(id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, rol TEXT, activo INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS lotes_mp(id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, materia TEXT, proveedor TEXT, lote_prov TEXT,
  fecha_recep TEXT, fecha_venc TEXT, cantidad_inicial REAL, cantidad_actual REAL, unidad TEXT, temp_c REAL, estado TEXT,
  costo_total REAL, checklist TEXT, observaciones TEXT, operador TEXT);
CREATE TABLE IF NOT EXISTS pt_lotes(id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, producto TEXT, fecha_elab TEXT, fecha_venc TEXT,
  cantidad_inicial INTEGER, cantidad_actual INTEGER, estado TEXT, orden_id INTEGER, operador TEXT);
CREATE TABLE IF NOT EXISTS ordenes(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, producto TEXT, tandas INTEGER, unidades_plan INTEGER,
  unidades_real INTEGER, estado TEXT, operador TEXT, creado TEXT, inicio TEXT, fin TEXT, nota TEXT, lote_pt TEXT);
CREATE TABLE IF NOT EXISTS ejecuciones(id INTEGER PRIMARY KEY AUTOINCREMENT, orden_id INTEGER, lote_pt TEXT, datos TEXT, ts TEXT, operador TEXT);
CREATE TABLE IF NOT EXISTS calidad(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, lote_pt TEXT, producto TEXT, peso_prom REAL, peso_std REAL,
  desv_pct REAL, fuera_rango INTEGER, c_tamano INTEGER, c_color INTEGER, c_textura INTEGER, c_relleno INTEGER, c_coccion INTEGER,
  resultado TEXT, accion TEXT, operador TEXT);
CREATE TABLE IF NOT EXISTS voc(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, producto TEXT, tipo TEXT, etapa_amfe TEXT, canal TEXT, gravedad TEXT,
  calificacion INTEGER, descripcion TEXT, lote TEXT, estado TEXT, accion TEXT, operador TEXT);
CREATE TABLE IF NOT EXISTS ventas(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, ts TEXT, producto TEXT, cantidad INTEGER, tipo TEXT,
  valor REAL, lote TEXT, operador TEXT);
CREATE TABLE IF NOT EXISTS movimientos(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, tipo TEXT, item TEXT, cantidad REAL, unidad TEXT, ref TEXT, operador TEXT);
CREATE TABLE IF NOT EXISTS bitacora(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, operador TEXT, modulo TEXT, accion TEXT, detalle TEXT);
CREATE TABLE IF NOT EXISTS plan_lean(id INTEGER PRIMARY KEY AUTOINCREMENT, semanas TEXT, actividad TEXT, resultado TEXT, avance INTEGER DEFAULT 0);
"""


def conn():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    return c


@contextmanager
def tx():
    c = conn()
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def q(sql, params=()):
    c = conn()
    try:
        return pd.read_sql_query(sql, c, params=params)
    finally:
        c.close()


def ex(sql, params=()):
    with tx() as c:
        return c.execute(sql, params).lastrowid


def log(operador, modulo, accion, detalle="", c=None):
    sql = "INSERT INTO bitacora(ts,operador,modulo,accion,detalle) VALUES(?,?,?,?,?)"
    args = (ts(), operador, modulo, accion, detalle)
    if c is not None:
        c.execute(sql, args)
    else:
        ex(sql, args)


def init_db():
    with tx() as c:
        c.executescript(SCHEMA)
    if q("SELECT COUNT(*) n FROM operadores")["n"][0] == 0:
        for n, r in [("Operador 1", "Operador"), ("Operador 2", "Operador"), ("Supervisor de calidad", "Supervisor")]:
            ex("INSERT INTO operadores(nombre,rol) VALUES(?,?)", (n, r))
    if q("SELECT COUNT(*) n FROM plan_lean")["n"][0] == 0:
        for s, a, r in PLAN_LEAN_SEED:
            ex("INSERT INTO plan_lean(semanas,actividad,resultado,avance) VALUES(?,?,?,0)", (s, a, r))
    if q("SELECT COUNT(*) n FROM meta WHERE clave='demo_cargado'")["n"][0] == 0:
        cargar_demo()


def operadores_activos():
    return q("SELECT nombre, rol FROM operadores WHERE activo=1 ORDER BY id")


def crear_operador(nombre, rol="Operador"):
    nombre = (nombre or "").strip()
    if not nombre:
        return False
    try:
        ex("INSERT INTO operadores(nombre,rol) VALUES(?,?)", (nombre, rol))
    except sqlite3.IntegrityError:
        ex("UPDATE operadores SET activo=1 WHERE nombre=?", (nombre,))
    return True


# ─────────────────────────  DEMO / LIMPIEZA  ─────────────────────────
TABLAS_TRANS = ["lotes_mp", "pt_lotes", "ordenes", "ejecuciones", "calidad", "voc", "ventas", "movimientos", "bitacora"]


def limpiar_datos():
    with tx() as c:
        for t in TABLAS_TRANS:
            c.execute(f"DELETE FROM {t}")
            c.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
        c.execute("UPDATE plan_lean SET avance=0")
        c.execute("INSERT OR REPLACE INTO meta VALUES('demo_cargado','0')")


FACTORES_DIA = [0.90, 0.90, 0.95, 1.00, 1.10, 1.25, 0.90]   # Lun..Dom (supuesto ajustable en la app)


def factor_dia(d):
    return FACTORES_DIA[d.weekday()]


def cargar_demo():
    limpiar_datos()
    rnd = random.Random(2026)
    now = ahora()
    hoy_ = now.date()
    op = "Operador 1"
    # Materias primas (algunas en alerta a propósito para mostrar semáforos)
    stock_demo = {"Harina de trigo": 82, "Mantequilla": 9.5, "Huevos": 150, "Leche": 8, "Azúcar": 12, "Sal": 3.5,
                  "Levadura": 0.4, "Queso": 18, "Bocadillo": 7, "Arequipe": 5, "Jamón": 4.2}
    provs = {"Harina de trigo": "Distribuidora La Cosecha", "Mantequilla": "Lácteos del Caribe", "Huevos": "Avícola Bolívar",
             "Leche": "Lácteos del Caribe", "Azúcar": "Distribuidora La Cosecha", "Sal": "Distribuidora La Cosecha",
             "Levadura": "Insumos Panaderos", "Queso": "Lácteos del Caribe", "Bocadillo": "Dulces Vélez",
             "Arequipe": "Dulces Vélez", "Jamón": "Cárnicos Cartagena"}
    with tx() as c:
        for i, (m, cant) in enumerate(stock_demo.items(), 1):
            info = MATERIAS[m]
            rec = hoy_ - timedelta(days=rnd.randint(1, 6))
            venc = rec + timedelta(days=info["vida"] - 3)
            if m == "Leche":
                venc = hoy_ + timedelta(days=2)
            c.execute("""INSERT INTO lotes_mp(codigo,materia,proveedor,lote_prov,fecha_recep,fecha_venc,cantidad_inicial,cantidad_actual,
                         unidad,temp_c,estado,costo_total,checklist,observaciones,operador) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (f"MP-{rec:%Y%m%d}-{i:03d}", m, provs[m], f"L{rnd.randint(1000, 9999)}", rec.strftime(FMT_D), venc.strftime(FMT_D),
                       cant * 1.2, cant, info["unidad"], (4.0 if info["frio"] else None), "Aceptado", None,
                       json.dumps(info["criterios"], ensure_ascii=False), "Datos de demostración", op))
        c.execute("""INSERT INTO lotes_mp(codigo,materia,proveedor,lote_prov,fecha_recep,fecha_venc,cantidad_inicial,cantidad_actual,unidad,
                     temp_c,estado,observaciones,operador) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (f"MP-{hoy_:%Y%m%d}-099", "Leche", "Lácteos del Caribe", "L5521", hoy_.strftime(FMT_D),
                   (hoy_ + timedelta(days=4)).strftime(FMT_D), 20, 0, "L", 9.5, "Rechazado",
                   "Rechazado: llegó a 9,5 °C (máx. 5 °C). Demo.", op))
    # Ventas de los últimos 14 días
    with tx() as c:
        for k in range(14, 0, -1):
            d = hoy_ - timedelta(days=k)
            for p in PRODUCTOS:
                base = VENTA_DIARIA_PROM * p["share"] * factor_dia(d)
                n = max(5, int(round(base * rnd.uniform(0.9, 1.1))))
                c.execute("INSERT INTO ventas(fecha,ts,producto,cantidad,tipo,valor,operador) VALUES(?,?,?,?,?,?,?)",
                          (d.strftime(FMT_D), f"{d:%Y-%m-%d} 17:00:00", p["nombre"], n, "Venta", n * p["precio"], op))
                if p["codigo"] in ("ARE", "QUE") and rnd.random() < 0.45:
                    nn = rnd.randint(2, 8)
                    c.execute("INSERT INTO ventas(fecha,ts,producto,cantidad,tipo,valor,operador) VALUES(?,?,?,?,?,?,?)",
                              (d.strftime(FMT_D), f"{d:%Y-%m-%d} 18:00:00", p["nombre"], nn, "No atendida", 0, op))
    # Producto terminado en stock
    pt = [("Pan de queso", 24, 5), ("Pan de bocadillo", 6, 6), ("Pan de jamón y queso", 12, 4), ("Pan de mantequilla", 18, 8)]
    with tx() as c:
        for i, (prod, cant, horas) in enumerate(pt, 1):
            p = PROD[prod]
            fe = now - timedelta(hours=horas)
            fv = fe + timedelta(hours=p["vida_h"])
            c.execute("""INSERT INTO pt_lotes(codigo,producto,fecha_elab,fecha_venc,cantidad_inicial,cantidad_actual,estado,operador)
                         VALUES(?,?,?,?,?,?,?,?)""",
                      (f"PT-{p['codigo']}-{fe:%Y%m%d}-{i:02d}", prod, ts(fe), ts(fv), cant + 10, cant, "Disponible", op))
        p = PROD["Pan de jamón y queso"]
        fe = now - timedelta(hours=p["vida_h"] - 3)
        c.execute("""INSERT INTO pt_lotes(codigo,producto,fecha_elab,fecha_venc,cantidad_inicial,cantidad_actual,estado,operador)
                     VALUES(?,?,?,?,?,?,?,?)""",
                  (f"PT-JYQ-{fe:%Y%m%d}-90", "Pan de jamón y queso", ts(fe), ts(fe + timedelta(hours=p["vida_h"])), 20, 5, "Disponible", op))
    # Calidad histórica
    with tx() as c:
        for k in range(10, 0, -1):
            d = now - timedelta(days=k)
            for p in rnd.sample(PRODUCTOS, 2):
                ok = rnd.random() < 0.82
                std = p["peso_masa_g"]
                prom = std * rnd.uniform(0.97, 1.03) if ok else std * rnd.uniform(1.06, 1.10)
                checks = [1, 1, 1, 1, 1] if ok else [1, 1, rnd.choice([0, 1]), 0, 1]
                c.execute("""INSERT INTO calidad(ts,lote_pt,producto,peso_prom,peso_std,desv_pct,fuera_rango,c_tamano,c_color,c_textura,
                             c_relleno,c_coccion,resultado,accion,operador) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (ts(d), f"PT-{p['codigo']}-{d:%Y%m%d}-01", p["nombre"], round(prom, 1), std, round((prom - std) / std * 100, 1),
                           0 if ok else 2, *checks, "Conforme" if ok else "No conforme",
                           "" if ok else "Recalibrar cortador y capacitar en porcionado", "Supervisor de calidad"))
    # Voz del cliente
    quejas = [("Pan de queso", "Calidad, textura o sabor", "Mostrador", "Media", 2, "El pan salió algo seco y duro."),
              ("Pan de arequipe", "Disponibilidad (agotado)", "Mostrador", "Alta", 1, "Llegué a las 4 pm y ya no había."),
              ("Pan de bocadillo", "Tamaño irregular", "WhatsApp", "Baja", 3, "Los panes del pedido eran de distinto tamaño."),
              ("Pan de jamón y queso", "Cantidad de relleno", "Código QR", "Media", 2, "Casi no tenía jamón."),
              ("Pan de queso", "Pérdida de frescura", "Mostrador", "Media", 2, "Se sentía del día anterior."),
              ("Pan de mantequilla", "Pan quemado o crudo", "Redes sociales", "Media", 2, "La base estaba muy oscura."),
              ("Pan de arequipe", "Tiempo de espera", "Mostrador", "Baja", 3, "Esperé mucho a que sacaran más."),
              ("Pan de queso", "Disponibilidad (agotado)", "Pedido / domicilio", "Alta", 1, "Pedido incompleto, faltaron panes de queso.")]
    with tx() as c:
        for i, (pr, ti, ca, gr, cal, de) in enumerate(quejas):
            d = now - timedelta(days=len(quejas) - i, hours=rnd.randint(0, 6))
            est = "Cerrada" if i < 3 else "Abierta"
            c.execute("""INSERT INTO voc(ts,producto,tipo,etapa_amfe,canal,gravedad,calificacion,descripcion,lote,estado,accion,operador)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (ts(d), pr, ti, VOC_TIPOS[ti], ca, gr, cal, de, "", est,
                       "Cambio del producto y revisión del lote" if est == "Cerrada" else "", "Operador 2"))
    # Avance del plan Lean de ejemplo
    for i, av in enumerate([100, 60, 35, 50, 20, 10], 1):
        ex("UPDATE plan_lean SET avance=? WHERE id=?", (av, i))
    ex("INSERT OR REPLACE INTO meta VALUES('demo_cargado','1')")
    log("Sistema", "Admin", "Datos de demostración cargados")


# ════════════════════════════════════════════════════════════════════
#  MATERIAS PRIMAS: recepción, inventario, consumo FEFO
# ════════════════════════════════════════════════════════════════════
def evaluar_recepcion(materia, criterios_ok, temp_c, fecha_venc, fecha_recep=None):
    """Devuelve (aprobado, [motivos de falla])."""
    info = MATERIAS[materia]
    fallas = []
    for crit, ok in zip(info["criterios"], criterios_ok):
        if not ok:
            fallas.append(f"No cumple: {crit}")
    if info["frio"] and info["temp_max"] is not None:
        if temp_c is None or temp_c > info["temp_max"]:
            fallas.append(f"Temperatura {num(temp_c) if temp_c is not None else 'sin medir'} °C (máx. {info['temp_max']} °C)")
    fr = fecha_recep or hoy()
    dias = (fecha_venc - fr).days
    min_dias = max(2, int(info["vida"] * 0.3)) if info["vida"] > 10 else max(2, int(info["vida"] * 0.4))
    if dias < min_dias:
        fallas.append(f"Vida útil restante de {dias} días (mínimo {min_dias})")
    return (len(fallas) == 0), fallas


def recibir_mp(materia, proveedor, lote_prov, cantidad, fecha_venc, temp_c, criterios_ok, decision, costo, obs, operador):
    info = MATERIAS[materia]
    fr = hoy()
    estado = {"Aceptar": "Aceptado", "Cuarentena": "Cuarentena", "Rechazar": "Rechazado"}[decision]
    n = q("SELECT COUNT(*) n FROM lotes_mp WHERE fecha_recep=?", (fr.strftime(FMT_D),))["n"][0] + 1
    codigo = f"MP-{fr:%Y%m%d}-{n:03d}"
    actual = cantidad if estado in ("Aceptado", "Cuarentena") else 0
    with tx() as c:
        c.execute("""INSERT INTO lotes_mp(codigo,materia,proveedor,lote_prov,fecha_recep,fecha_venc,cantidad_inicial,cantidad_actual,unidad,
                     temp_c,estado,costo_total,checklist,observaciones,operador) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (codigo, materia, proveedor, lote_prov, fr.strftime(FMT_D), fecha_venc.strftime(FMT_D), cantidad, actual, info["unidad"],
                   temp_c, estado, costo, json.dumps(dict(zip(info["criterios"], criterios_ok)), ensure_ascii=False), obs, operador))
        if actual:
            c.execute("INSERT INTO movimientos(ts,tipo,item,cantidad,unidad,ref,operador) VALUES(?,?,?,?,?,?,?)",
                      (ts(), "Entrada MP", materia, cantidad, info["unidad"], codigo, operador))
        log(operador, "Recepción", f"Lote {estado}", f"{codigo} · {materia} · {cantidad} {info['unidad']}", c)
    return codigo, estado


def stock_mp():
    h = hoy().strftime(FMT_D)
    lotes = q("SELECT materia, cantidad_actual, fecha_venc FROM lotes_mp WHERE estado='Aceptado' AND cantidad_actual>0 AND fecha_venc>=?", (h,))
    cons = consumo_diario_estimado()
    filas = []
    for m, info in MATERIAS.items():
        sub = lotes[lotes["materia"] == m]
        s = float(sub["cantidad_actual"].sum()) if len(sub) else 0.0
        prox = sub["fecha_venc"].min() if len(sub) else None
        if s <= info["min"]:
            est = "Crítico"
        elif s <= info["min"] * 1.5:
            est = "Bajo"
        elif s > info["max"]:
            est = "Exceso"
        else:
            est = "Óptimo"
        dias = s / cons[m] if cons[m] > 0 else None
        filas.append(dict(Materia=m, Icono=info["icono"], Unidad=info["unidad"], Stock=round(s, 2), Mínimo=info["min"], Máximo=info["max"],
                          Estado=est, Cobertura_dias=round(dias, 1) if dias is not None else None,
                          Lotes=len(sub), Próx_vence=prox, A_pedir=max(0.0, round(info["max"] - s, 2)) if s <= info["min"] * 1.5 else 0.0))
    return pd.DataFrame(filas)


def lotes_mp_df(solo_activos=False):
    df = q("SELECT * FROM lotes_mp ORDER BY fecha_venc, id")
    if solo_activos:
        df = df[(df["cantidad_actual"] > 0)]
    if len(df):
        df["dias_vence"] = (pd.to_datetime(df["fecha_venc"]) - pd.Timestamp(hoy())).dt.days
    return df


def consumir_mp(c, materia, cantidad, ref, operador):
    """Descuenta por FEFO. Devuelve (consumido, [lotes usados])."""
    h = hoy().strftime(FMT_D)
    rows = c.execute("""SELECT id,codigo,cantidad_actual FROM lotes_mp WHERE materia=? AND estado='Aceptado' AND cantidad_actual>0
                        AND fecha_venc>=? ORDER BY fecha_venc, id""", (materia, h)).fetchall()
    resto = float(cantidad)
    usados = []
    for r in rows:
        if resto <= 1e-9:
            break
        t = min(r["cantidad_actual"], resto)
        c.execute("UPDATE lotes_mp SET cantidad_actual=cantidad_actual-? WHERE id=?", (t, r["id"]))
        usados.append(r["codigo"])
        resto -= t
    consumido = float(cantidad) - max(resto, 0)
    if consumido > 0:
        c.execute("INSERT INTO movimientos(ts,tipo,item,cantidad,unidad,ref,operador) VALUES(?,?,?,?,?,?,?)",
                  (ts(), "Consumo MP", materia, -round(consumido, 3), MATERIAS[materia]["unidad"], ref, operador))
    return consumido, usados


def cambiar_estado_lote_mp(lote_id, estado, operador):
    ex("UPDATE lotes_mp SET estado=? WHERE id=?", (estado, lote_id))
    log(operador, "Inventario MP", f"Lote pasa a {estado}", f"id {lote_id}")


# ════════════════════════════════════════════════════════════════════
#  PRODUCTO TERMINADO
# ════════════════════════════════════════════════════════════════════
def pt_lotes_df(activos=True):
    df = q("SELECT * FROM pt_lotes ORDER BY fecha_elab")
    if activos:
        df = df[df["cantidad_actual"] > 0]
    if len(df):
        df["horas_rest"] = ((pd.to_datetime(df["fecha_venc"]) - pd.Timestamp(ahora())).dt.total_seconds() / 3600).round(1)
    return df.reset_index(drop=True)


def pt_disponible():
    """Unidades vendibles por producto (disponibles y no vencidas)."""
    df = pt_lotes_df()
    out = {p: 0 for p in NOMBRES_PAN}
    if len(df):
        v = df[(df["estado"] == "Disponible") & (df["horas_rest"] > 0)]
        for p, n in v.groupby("producto")["cantidad_actual"].sum().items():
            out[p] = int(n)
    return out


def registrar_venta(producto, cantidad, operador):
    """Vende por PEPS (lote más antiguo). Devuelve (vendidas, faltantes)."""
    df = pt_lotes_df()
    df = df[(df["producto"] == producto) & (df["estado"] == "Disponible") & (df["horas_rest"] > 0)].sort_values("fecha_venc")
    resto = int(cantidad)
    p = PROD[producto]
    with tx() as c:
        for _, r in df.iterrows():
            if resto <= 0:
                break
            t = min(int(r["cantidad_actual"]), resto)
            c.execute("UPDATE pt_lotes SET cantidad_actual=cantidad_actual-? WHERE id=?", (t, int(r["id"])))
            c.execute("INSERT INTO ventas(fecha,ts,producto,cantidad,tipo,valor,lote,operador) VALUES(?,?,?,?,?,?,?,?)",
                      (hoy().strftime(FMT_D), ts(), producto, t, "Venta", t * p["precio"], r["codigo"], operador))
            c.execute("INSERT INTO movimientos(ts,tipo,item,cantidad,unidad,ref,operador) VALUES(?,?,?,?,?,?,?)",
                      (ts(), "Venta PT", producto, -t, "und", r["codigo"], operador))
            resto -= t
        vendidas = int(cantidad) - resto
        if resto > 0:
            c.execute("INSERT INTO ventas(fecha,ts,producto,cantidad,tipo,valor,operador) VALUES(?,?,?,?,?,?,?)",
                      (hoy().strftime(FMT_D), ts(), producto, resto, "No atendida", 0, operador))
        log(operador, "Ventas", "Venta registrada", f"{producto}: {vendidas} vendidas, {resto} no atendidas", c)
    return vendidas, resto


def registrar_no_atendida(producto, cantidad, operador):
    ex("INSERT INTO ventas(fecha,ts,producto,cantidad,tipo,valor,operador) VALUES(?,?,?,?,?,?,?)",
       (hoy().strftime(FMT_D), ts(), producto, int(cantidad), "No atendida", 0, operador))
    log(operador, "Ventas", "Demanda no atendida", f"{producto}: {cantidad}")


def dar_baja_pt(lote_id, motivo, operador):
    r = q("SELECT * FROM pt_lotes WHERE id=?", (lote_id,))
    if not len(r):
        return 0
    n = int(r["cantidad_actual"][0])
    with tx() as c:
        c.execute("UPDATE pt_lotes SET cantidad_actual=0, estado='Baja' WHERE id=?", (lote_id,))
        c.execute("INSERT INTO movimientos(ts,tipo,item,cantidad,unidad,ref,operador) VALUES(?,?,?,?,?,?,?)",
                  (ts(), "Merma PT", r["producto"][0], -n, "und", f"{r['codigo'][0]} · {motivo}", operador))
        log(operador, "Inventario PT", "Baja de lote", f"{r['codigo'][0]} · {n} und · {motivo}", c)
    return n


def liberar_pt(lote_id, operador):
    ex("UPDATE pt_lotes SET estado='Disponible' WHERE id=?", (lote_id,))
    log(operador, "Calidad", "Lote liberado", f"id {lote_id}")


# ════════════════════════════════════════════════════════════════════
#  PROGRAMACIÓN SEGÚN DEMANDA
# ════════════════════════════════════════════════════════════════════
def demanda_base(producto, dias=14):
    d0 = (hoy() - timedelta(days=dias)).strftime(FMT_D)
    df = q("SELECT fecha, SUM(cantidad) n FROM ventas WHERE producto=? AND fecha>=? AND fecha<? GROUP BY fecha",
           (producto, d0, hoy().strftime(FMT_D)))
    if len(df) >= 3:
        return float(df["n"].mean()), f"promedio de {len(df)} días registrados"
    return VENTA_DIARIA_PROM * PROD[producto]["share"], "promedio histórico ene–jun"


def plan_demanda(fecha, colchon=0.10, factores=None):
    """Tabla con pronóstico, stock, órdenes ya creadas y tandas sugeridas por pan."""
    pt = pt_disponible()
    f = (factores or {}).get(fecha.weekday(), factor_dia(fecha))
    ord_ = q("SELECT producto, SUM(unidades_plan) n FROM ordenes WHERE fecha=? AND estado IN ('Pendiente','En proceso') GROUP BY producto",
             (fecha.strftime(FMT_D),))
    plan_prev = dict(zip(ord_["producto"], ord_["n"])) if len(ord_) else {}
    filas = []
    for p in PRODUCTOS:
        base, fuente = demanda_base(p["nombre"])
        pron = base * f
        objetivo = pron * (1 + colchon)
        disp = pt[p["nombre"]] if fecha == hoy() else 0
        ya = int(plan_prev.get(p["nombre"], 0))
        falta = max(0.0, objetivo - disp - ya)
        tandas = int(math.ceil(falta / p["unid_tanda"] - 1e-9)) if falta > 0 else 0
        cobertura = (disp + ya) / objetivo if objetivo > 0 else 1
        prioridad = "Urgente" if cobertura < 0.25 else ("Normal" if cobertura < 0.8 else "Cubierto")
        filas.append(dict(Producto=p["nombre"], Pronóstico=round(pron), Objetivo=round(objetivo), Stock=disp, Ya_programado=ya,
                          Faltante=round(falta), Tandas=tandas, Unidades=tandas * p["unid_tanda"], Prioridad=prioridad, Fuente=fuente))
    return pd.DataFrame(filas)


def requerimiento_mp(tandas_por_producto):
    """{producto: tandas} -> DataFrame de requeridos vs disponibles."""
    req = {m: 0.0 for m in NOMBRES_MP}
    for prod, t in tandas_por_producto.items():
        if t:
            for m, v in receta(prod, t).items():
                req[m] += v
    st = stock_mp().set_index("Materia")
    filas = []
    for m in NOMBRES_MP:
        if req[m] > 0:
            disp = float(st.loc[m, "Stock"])
            filas.append(dict(Materia=m, Icono=MATERIAS[m]["icono"], Unidad=MATERIAS[m]["unidad"], Requerido=round(req[m], 2),
                              Disponible=round(disp, 2), Falta=round(max(0, req[m] - disp), 2), OK=disp + 1e-9 >= req[m]))
    return pd.DataFrame(filas)


def crear_orden(fecha, producto, tandas, operador, nota=""):
    p = PROD[producto]
    oid = ex("""INSERT INTO ordenes(fecha,producto,tandas,unidades_plan,estado,operador,creado,nota) VALUES(?,?,?,?,?,?,?,?)""",
             (fecha.strftime(FMT_D), producto, int(tandas), int(tandas) * p["unid_tanda"], "Pendiente", operador, ts(), nota))
    log(operador, "Programación", "Orden creada", f"#{oid} {producto} × {tandas} tandas")
    return oid


def ordenes_df(estados=None, fecha=None):
    sql, par = "SELECT * FROM ordenes WHERE 1=1", []
    if estados:
        sql += f" AND estado IN ({','.join('?' * len(estados))})"
        par += list(estados)
    if fecha:
        sql += " AND fecha=?"
        par.append(fecha.strftime(FMT_D))
    return q(sql + " ORDER BY id DESC", par)


def cancelar_orden(oid, operador):
    ex("UPDATE ordenes SET estado='Cancelada' WHERE id=? AND estado='Pendiente'", (oid,))
    log(operador, "Programación", "Orden cancelada", f"#{oid}")


def iniciar_orden(oid, operador):
    o = q("SELECT * FROM ordenes WHERE id=?", (oid,)).iloc[0]
    req = requerimiento_mp({o["producto"]: int(o["tandas"])})
    if len(req) and not req["OK"].all():
        return False, req
    ex("UPDATE ordenes SET estado='En proceso', inicio=?, operador=? WHERE id=?", (ts(), operador, oid))
    log(operador, "Producción", "Orden iniciada", f"#{oid} {o['producto']}")
    return True, req


# ════════════════════════════════════════════════════════════════════
#  CALIDAD
# ════════════════════════════════════════════════════════════════════
CHECKS_CALIDAD = [("c_tamano", "📏 Tamaño uniforme"), ("c_color", "🎨 Color dorado parejo"), ("c_textura", "🥖 Textura / miga suave"),
                  ("c_relleno", "🧀 Relleno suficiente y centrado"), ("c_coccion", "🔥 Cocción correcta (ni crudo ni quemado)")]


def evaluar_muestras(producto, muestras):
    std = PROD[producto]["peso_masa_g"]
    muestras = [float(m) for m in muestras if m and m > 0]
    if not muestras:
        return dict(prom=0, desv=0, fuera=0, n=0, std=std)
    lo, hi = std * (1 - TOLERANCIA_PESO), std * (1 + TOLERANCIA_PESO)
    prom = sum(muestras) / len(muestras)
    return dict(prom=round(prom, 1), desv=round((prom - std) / std * 100, 1), n=len(muestras), std=std,
                fuera=sum(1 for m in muestras if m < lo or m > hi), lo=round(lo, 1), hi=round(hi, 1))


def registrar_calidad(lote_pt, producto, muestras, checks, accion, operador, c=None):
    ev = evaluar_muestras(producto, muestras)
    ok = all(checks.values()) and ev["fuera"] == 0 and ev["n"] > 0
    res = "Conforme" if ok else "No conforme"
    sql = """INSERT INTO calidad(ts,lote_pt,producto,peso_prom,peso_std,desv_pct,fuera_rango,c_tamano,c_color,c_textura,c_relleno,c_coccion,
             resultado,accion,operador) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    args = (ts(), lote_pt, producto, ev["prom"], ev["std"], ev["desv"], ev["fuera"], *[int(checks[k]) for k, _ in CHECKS_CALIDAD],
            res, accion, operador)
    if c is not None:
        c.execute(sql, args)
    else:
        ex(sql, args)
        log(operador, "Calidad", f"Inspección {res}", f"{lote_pt}")
    return res, ev


def calidad_df():
    return q("SELECT * FROM calidad ORDER BY ts DESC")


# ════════════════════════════════════════════════════════════════════
#  EJECUCIÓN DE PRODUCCIÓN
# ════════════════════════════════════════════════════════════════════
def finalizar_orden(oid, operador, pesos_reales, datos, muestras, checks, unidades_reales, accion=""):
    """Cierra la orden: consume MP (FEFO), crea lote PT, registra calidad y trazabilidad."""
    o = q("SELECT * FROM ordenes WHERE id=?", (oid,)).iloc[0]
    prod = o["producto"]
    p = PROD[prod]
    now = ahora()
    n = q("SELECT COUNT(*) n FROM pt_lotes WHERE substr(fecha_elab,1,10)=?", (now.strftime(FMT_D),))["n"][0] + 1
    codigo = f"PT-{p['codigo']}-{now:%Y%m%d}-{n:02d}"
    with tx() as c:
        usados, faltantes = {}, {}
        for m, cant in pesos_reales.items():
            cons, lotes = consumir_mp(c, m, cant, codigo, operador)
            usados[m] = lotes
            if cons + 1e-9 < cant:
                faltantes[m] = round(cant - cons, 3)
        res, ev = registrar_calidad(codigo, prod, muestras, checks, accion, operador, c)
        estado = "Disponible" if res == "Conforme" else "Retenido"
        c.execute("""INSERT INTO pt_lotes(codigo,producto,fecha_elab,fecha_venc,cantidad_inicial,cantidad_actual,estado,orden_id,operador)
                     VALUES(?,?,?,?,?,?,?,?,?)""",
                  (codigo, prod, ts(now), ts(now + timedelta(hours=p["vida_h"])), int(unidades_reales), int(unidades_reales), estado, oid, operador))
        c.execute("INSERT INTO movimientos(ts,tipo,item,cantidad,unidad,ref,operador) VALUES(?,?,?,?,?,?,?)",
                  (ts(), "Entrada PT", prod, int(unidades_reales), "und", codigo, operador))
        datos = dict(datos, pesos_reales=pesos_reales, lotes_mp=usados, faltantes_mp=faltantes, resultado=res, muestras=muestras)
        c.execute("INSERT INTO ejecuciones(orden_id,lote_pt,datos,ts,operador) VALUES(?,?,?,?,?)",
                  (oid, codigo, json.dumps(datos, ensure_ascii=False, default=str), ts(), operador))
        c.execute("UPDATE ordenes SET estado='Terminada', fin=?, unidades_real=?, lote_pt=?, operador=? WHERE id=?",
                  (ts(now), int(unidades_reales), codigo, operador, oid))
        log(operador, "Producción", "Orden terminada", f"#{oid} → {codigo} ({res})", c)
    return dict(codigo=codigo, resultado=res, estado=estado, ev=ev, faltantes=faltantes)


# ════════════════════════════════════════════════════════════════════
#  VOZ DEL CLIENTE
# ════════════════════════════════════════════════════════════════════
def registrar_voc(producto, tipo, canal, gravedad, calificacion, descripcion, lote, operador):
    vid = ex("""INSERT INTO voc(ts,producto,tipo,etapa_amfe,canal,gravedad,calificacion,descripcion,lote,estado,accion,operador)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
             (ts(), producto, tipo, VOC_TIPOS[tipo], canal, gravedad, int(calificacion), descripcion, lote, "Abierta", "", operador))
    log(operador, "Voz del cliente", "Queja registrada", f"#{vid} {producto} · {tipo}")
    return vid


def cerrar_voc(vid, accion, operador):
    ex("UPDATE voc SET estado='Cerrada', accion=? WHERE id=?", (accion, vid))
    log(operador, "Voz del cliente", "Queja cerrada", f"#{vid}")


def voc_df():
    return q("SELECT * FROM voc ORDER BY id DESC")


def kardex_df(limit=300):
    return q("SELECT ts, tipo, item, cantidad, unidad, ref, operador FROM movimientos ORDER BY id DESC LIMIT ?", (limit,))


def bitacora_df(limit=300):
    return q("SELECT ts, operador, modulo, accion, detalle FROM bitacora ORDER BY id DESC LIMIT ?", (limit,))


def ventas_df(dias=14):
    d0 = (hoy() - timedelta(days=dias)).strftime(FMT_D)
    return q("SELECT * FROM ventas WHERE fecha>=? ORDER BY id DESC", (d0,))


def plan_lean_df():
    return q("SELECT * FROM plan_lean ORDER BY id")


def set_avance(pid, avance):
    ex("UPDATE plan_lean SET avance=? WHERE id=?", (int(avance), pid))
