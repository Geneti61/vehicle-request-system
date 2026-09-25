# ============================================================
# EPSS Vehicle System - Assigned Vehicles Log
# Visible to ALL logged-in users
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from auth import current_user, is_logged_in

if not is_logged_in():
    st.warning("🔒 Please log in first.")
    st.stop()

user = current_user()

st.title("📋 Assigned Vehicles Log")
st.caption(f"Logged in as **{user['name']}** ({user['role']})")
st.divider()

if "requests" not in st.session_state:
    st.session_state.requests = []

# ============================================================
# BUILD FLAT ROWS FROM ALL ASSIGNMENTS
# ============================================================
rows = []
on_duty_list = []

for r in st.session_state.requests:
    for a in r.get("assignments", []):
        assigned_at = a.get("assigned_at", "")
        returned_at = a.get("returned_at") or "—"
        days = 0
        if assigned_at:
            try:
                d = datetime.strptime(assigned_at, "%Y-%m-%d %H:%M")
                end = datetime.now() if not a.get("returned_at") else datetime.strptime(a["returned_at"], "%Y-%m-%d %H:%M")
                days = (end - d).days
            except Exception:
                days = 0

        status = a.get("status", "On Duty")
        status_display = "🚚 On Duty" if status == "On Duty" else "✅ Returned"
        if status == "On Duty" and days > 7:
            status_display = "🚚 On Duty ⚠️"

        rows.append({
            "Request ID": r["request_id"],
            "Vehicle": a.get("vehicle", ""),
            "Driver": a.get("driver", ""),
            "Plate": a.get("plate", ""),
            "Warehouse": r.get("warehouse", ""),
            "Hub": a.get("hub", r.get("hub", "")),
            "Assigned": assigned_at,
            "Returned": returned_at,
            "Days": days,
            "Status": status_display,
        })

        if status == "On Duty":
            on_duty_list.append({
                "driver": a.get("driver", ""),
                "hub": a.get("hub", ""),
                "days": days,
                "plate": a.get("plate", ""),
            })

# ============================================================
# TOP METRICS
# ============================================================
total = len(rows)
on_duty = len(on_duty_list)
returned = total - on_duty

c1, c2, c3 = st.columns(3)
c1.metric("🚛 Total Assigned", total)
c2.metric("🚚 Currently On Duty", on_duty)
c3.metric("✅ Returned", returned)

# ============================================================
# ON DUTY HIGHLIGHT (if any)
# ============================================================
if on_duty_list:
    overdue = [d for d in on_duty_list if d["days"] > 7]
    if overdue:
        st.error(f"⚠️ {len(overdue)} vehicle(s) overdue (>7 days). Review below.")

    with st.expander(f"🚚 Currently On Duty ({on_duty})", expanded=False):
        for d in on_duty_list:
            warn = " ⚠️" if d["days"] > 7 else ""
            st.write(f"• **{d['driver']}** — {d['hub']} — {d['days']} days{warn}  (Plate: {d['plate']})")

st.divider()

# ============================================================
# EMPTY STATE
# ============================================================
if not rows:
    st.info("📭 No assigned vehicles yet. Once an Assigner assigns a driver, entries will appear here.")
    st.stop()

# ============================================================
# FILTERS
# ============================================================
st.subheader("🔍 Search & Filter")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search = st.text_input("Search (Request ID, Driver, Plate)", "")
with col2:
    status_filter = st.selectbox("Status", ["All", "On Duty", "Returned"])
with col3:
    hub_filter = st.selectbox("Hub", ["All"] + sorted(list({r["Hub"] for r in rows})))

# Apply filters
filtered = rows
if search:
    s = search.lower()
    filtered = [r for r in filtered
                if s in r["Request ID"].lower()
                or s in r["Driver"].lower()
                or s in r["Plate"].lower()]
if status_filter == "On Duty":
    filtered = [r for r in filtered if "On Duty" in r["Status"]]
elif status_filter == "Returned":
    filtered = [r for r in filtered if "Returned" in r["Status"]]
if hub_filter != "All":
    filtered = [r for r in filtered if r["Hub"] == hub_filter]

# ============================================================
# MAIN TABLE
# ============================================================
st.subheader(f"📊 Results ({len(filtered)} records)")

df = pd.DataFrame(filtered)
st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================
# EXCEL DOWNLOAD
# ============================================================
if not df.empty:
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Assigned Vehicles')
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Download as Excel (.xlsx)",
        data=excel_data,
        file_name=f"EPSS_Assigned_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
