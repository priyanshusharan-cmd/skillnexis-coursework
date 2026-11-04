"""Home dashboard: doorbell visits (with snapshots) and sensor alerts from the MQTT pipeline.

    streamlit run doorbell/dashboard.py        (reads doorbell/doorbell.db and alerts.db)
"""
import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
VISITS = os.environ.get("DOORBELL_DB", os.path.join(HERE, "doorbell.db"))
if not os.path.exists(VISITS):
    VISITS = os.path.join(HERE, "eval.db")
ALERTS = os.environ.get("ALERTS_DB", "alerts.db")

st.set_page_config(page_title="Home: doorbell & sensors", layout="wide")
st.title("Doorbell & sensor alerts")

left, right = st.columns([3, 2])
with left:
    st.subheader("Visitors")
    if os.path.exists(VISITS):
        con = sqlite3.connect(VISITS)
        total, unknown, sent = con.execute("SELECT COUNT(*), SUM(who = 'unknown'), SUM(notified) FROM visits").fetchone()
        v = pd.read_sql("SELECT ts, who, confidence, faces, notified, snapshot FROM visits ORDER BY ts DESC LIMIT 60", con)
        a, b, c = st.columns(3)
        a.metric("Visits logged", total)
        b.metric("Unknown visitors", unknown or 0)
        c.metric("Notifications sent", sent or 0)
        only_unknown = st.toggle("Only unknown visitors")
        shown = v[v.who == "unknown"] if only_unknown else v
        for row in shown.head(12).itertuples():
            cols = st.columns([1, 2])
            cols[0].image(row.snapshot, width=160)
            when = datetime.fromtimestamp(row.ts).strftime("%d %b %H:%M:%S") if row.ts > 1e9 else f"t+{row.ts:.0f}s"
            cols[1].markdown(f"**{row.who.replace('_', ' ')}**, {row.confidence:.0%} confidence  \n{when} · "
                             f"{row.faces} face(s) · {'notified' if row.notified else 'logged only (cooldown)'}")
    else:
        st.info("No doorbell database yet. Run `python doorbell/doorbell.py --evaluate` or start the doorbell.")
with right:
    st.subheader("Sensor alerts")
    if os.path.exists(ALERTS):
        al = pd.read_sql("SELECT ts, device, kind, state, value, message FROM alerts ORDER BY ts DESC LIMIT 100", sqlite3.connect(ALERTS))
        al["time"] = pd.to_datetime(al.ts, unit="s").dt.strftime("%H:%M:%S")
        st.dataframe(al[["time", "device", "kind", "state", "message"]], hide_index=True, use_container_width=True)
    else:
        st.info("No alerts database yet. Run `python mqtt/pipeline.py alerter`.")
