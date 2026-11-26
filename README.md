# 🥐 Juamdy Cartagena S.A.S. — Sistema integrado (Streamlit)

## Cómo ejecutarlo
```bash
pip install -r requirements.txt
streamlit run app.py
```
- **Palabra de acceso:** `Wandy` (cámbiala con `APP_PASSWORD` en `.streamlit/secrets.toml`).
- Luego se elige el **operador** y el turno; todo queda registrado a su nombre (bitácora).
- Los datos se guardan en `juamdy.db` (SQLite). La primera vez carga datos de demostración;
  en ⚙️ Administración → "Vaciar datos" para empezar en limpio.

## Flujo
📥 Recepción MP → 📦 Inventario (PEPS/FEFO) → 📅 Programación según demanda → 🍞 Producción guiada (15 pasos)
→ ✅ Calidad (lote liberado o retenido) → 🛒 Mostrador → 🗣️ Voz del cliente → 📈 Proyecto Lean (AMFE, plan, VPN/TIR).

## Supuestos a validar con la panadería
Recetas por tanda (40 panes), pesos, tiempos y temperaturas de horno, vida útil del pan, precios, stock mínimo/máximo
y factores de demanda por día están en `juamdy_core.py` (PRODUCTOS, MATERIAS, _MASA_BASE, FACTORES_DIA).
Son valores de referencia, no datos medidos de la panadería.
