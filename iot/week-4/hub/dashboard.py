"""Real-time smart-home dashboard (reads the hub's SQLite log; refreshes every 5 s).

    streamlit run hub/dashboard.py
"""
import os
import sqlite3

import pandas as pd
import streamlit as st

DB = os.environ.get("HUB_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "hub.db"))
st.set_page_config(page_title="Smart home", layout="wide")
st.title("Smart home")

if not os.path.exists(DB):
    st.info("No hub database yet: start hub/hub.py, or run `python hub/demo.py` for a recorded week.")
    st.stop()
con = sqlite3.connect(DB)
tel = pd.read_sql("SELECT * FROM telemetry", con)
tel["time"] = pd.to_datetime(tel.ts, unit="s")
last_day = tel[tel.time >= tel.time.max() - pd.Timedelta(hours=24)]

cols = st.columns(4)
for col, (room, g) in zip(cols[:2], tel.groupby("room")):
    r = g.iloc[-1]
    col.metric(f"{room.title()}", f"{r.temp_c:.1f} °C")
    col.caption(f"**{'occupied' if r.occ > 0.5 else 'empty'}** (p = {r.occ:.2f}) · light {'ON' if r.light else 'off'} · fan {'ON' if r.fan else 'off'} · {r.sound_db:.0f} dB · {r.lux:.0f} lux")
days = (tel.time.max() - tel.time.min()).total_seconds() / 86400
kwh = tel.watts.sum() / 60 / 1000
cols[2].metric("Energy, lights + fans", f"{kwh / days * 7:.1f} kWh/week", f"{1 - (kwh / days * 7) / 10.3:.0%} less than manual switching")
n = pd.read_sql("SELECT * FROM notifications ORDER BY ts DESC", con)
cols[3].metric("Notifications", len(n))
cols[3].caption(f"{(n.level == 'alert').sum()} alerts, {(n.level == 'info').sum()} info")

st.subheader("Last 24 hours")
left, right = st.columns(2)
occ = last_day.pivot_table(index="time", columns="room", values="occ")
left.caption("Occupancy probability (on-device int8 model)")
left.line_chart(occ, height=220)
watts = last_day.pivot_table(index="time", columns="room", values="watts")
right.caption("Power drawn by lights and fans (W)")
right.area_chart(watts, height=220)

a, b = st.columns([3, 2])
with a:
    st.subheader("Notifications")
    n["time"] = pd.to_datetime(n.ts, unit="s").dt.strftime("%a %H:%M")
    st.dataframe(n[["time", "level", "title", "body"]], hide_index=True, use_container_width=True, height=300)
with b:
    st.subheader("Requests & security")
    e = pd.read_sql("SELECT ts, room, kind, detail FROM events WHERE kind != 'node_online' ORDER BY ts DESC", con)
    e["time"] = pd.to_datetime(e.ts, unit="s").dt.strftime("%a %H:%M")
    st.dataframe(e[["time", "room", "kind", "detail"]], hide_index=True, use_container_width=True, height=300)
