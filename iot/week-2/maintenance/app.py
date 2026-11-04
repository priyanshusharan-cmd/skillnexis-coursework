"""Predictive maintenance dashboard.   streamlit run maintenance/app.py

Replays the motor log: drag the time slider (or press Play) to watch the health index climb, the alert
status change, and the remaining-life estimate appear as the bearing wears."""
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from engine import Engine, windows

DATA = HERE.parent / "data" / "machine_raw.csv"
st.set_page_config(page_title="Motor health", page_icon="⚙️", layout="wide")


@st.cache_data
def load():
    raw = pd.read_csv(DATA, parse_dates=["timestamp"])
    w = windows(raw)
    eng = Engine().fit(w)
    return raw, eng.score(w), eng


raw, scored, eng = load()
st.title("Motor M-07: predictive maintenance")
st.caption("Synthetic 30-day log. Health model learned from the first 7 days; alerts need 2 hours above threshold.")

times = list(scored.index)
if "i" not in st.session_state:
    st.session_state.i = len(times) - 1
c1, c2 = st.columns([5, 1])
idx = c1.slider("Replay time", 0, len(times) - 1, key="i", format="%d")
play = c2.toggle("Play", value=False)
now = times[idx]
view = scored.loc[:now]
row = view.iloc[-1]
status = row["status"]
rul = eng.rul_hours(scored, now)

colour = {"OK": "green", "WARNING": "orange", "CRITICAL": "red"}[status]
st.markdown(f"### {now:%a %d %b %Y, %H:%M} · status: :{colour}[**{status}**]")
k = st.columns(4)
k[0].metric("Vibration (30-min median)", f"{row['vib_mean']:.2f} mm/s", f"{row['vib_mean'] - view['vib_mean'].iloc[max(0, len(view) - 49)]:+.2f} vs 24 h ago")
k[1].metric("Bearing temperature", f"{row['temp_mean']:.1f} °C")
k[2].metric("Health index", f"{row['hi']:.1f}", f"warning at {eng.warn:.1f}", delta_color="off")
k[3].metric("Remaining useful life", "—" if rul is None else f"{rul:.0f} h", "no wear trend" if rul is None else f"≈ {rul / 24:.1f} days", delta_color="off")

if status == "CRITICAL":
    st.error(f"CRITICAL: plan bearing replacement now. Estimated {('?' if rul is None else f'{rul:.0f} h')} to the vibration damage zone.")
elif status == "WARNING":
    st.warning("WARNING: health index has stayed above the warning level for 2 hours. Schedule an inspection.")
else:
    st.success("Normal operation")

chart = view[["hi"]].rename(columns={"hi": "health index"})
chart["warning"] = eng.warn
chart["critical"] = eng.critical
st.line_chart(chart, height=260)
st.line_chart(raw.set_index("timestamp").loc[:now, ["vibration_rms_mm_s"]].resample("10min").median(), height=200)

events = view[(view["status"] != view["status"].shift()) | view["transient"]].copy()
events["event"] = events.apply(lambda r: "transient spike (ignored)" if r["transient"] and r["status"] == "OK" else f"status → {r['status']}", axis=1)
st.subheader("Event log")
st.dataframe(events[["event", "hi", "vib_mean", "temp_mean"]].iloc[::-1].head(15).round(2), use_container_width=True)

if play and idx < len(times) - 1:
    time.sleep(0.15)
    st.session_state.i = min(idx + 6, len(times) - 1)   # 3 hours per frame
    st.rerun()
