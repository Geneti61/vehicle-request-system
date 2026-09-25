# ============================================================
# EPSS Vehicle System - Director Dashboard
# Only visible to the Director role
# ============================================================

import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from auth import current_user, is_logged_in

if not is_logged_in():
    st.warning("🔒 Please log in first.")
    st.stop()

user = current_user()

if user["role"] != "Director":
    st.error("🚫 Access denied. This page is for the **Director** only.")
    st.stop()

# ============================================================
# HEADER
# ============================================================
st.title("👔 EPSS — Director's Dashboard")
st.caption(f"Welcome, **{user['name']}**  •  {datetime.now().strftime('%A, %d %B %Y — %H:%M')}")

if "requests" not in st.session_state:
    st.session_state.requests = []

reqs = st.session_state.requests
now = datetime.now()
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

# ============================================================
# HELPER: check if a datetime string falls in a range
# ============================================================
def in_range(dt_str, start, end):
    if not dt_str:
        return False
    try:
        d = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return start <= d <= end
    except Exception:
        return False

# ============================================================
# SECTION 1 — TODAY'S SNAPSHOT
# ============================================================
st.divider()
st.subheader("📆 Today's Snapshot")

today_requests = [r for r in reqs if in_range(r.get("created_at"), today_start, now)]
today_approved = [r for r in reqs if in_range(r.get("approved_at"), today_start, now) and r.get("status") in ["Approved", "On Duty", "Completed"]]
today_rejected = [r for r in reqs if in_range(r.get("approved_at"), today_start, now) and r.get("status") == "Rejected"]

today_assigned = 0
today_returned = 0
on_duty_now = 0

for r in reqs:
    for a in r.get("assignments", []):
        if in_range(a.get("assigned_at"), today_start, now):
            today_assigned += 1
        if a.get("returned_at") and in_range(a.get("returned_at"), today_start, now):
            today_returned += 1
        if a.get("status") == "On Duty":
            on_duty_now += 1

c1, c2, c3 = st.columns(3)
c1.metric("📝 Requests Today", len(today_requests))
c2.metric("✅ Approved Today", len(today_approved))
c3.metric("❌ Rejected Today", len(today_rejected))

c4, c5, c6 = st.columns(3)
c4.metric("🚚 Assigned Today", today_assigned)
c5.metric("✅ Returned Today", today_returned)
c6.metric("🚛 On Duty Now", on_duty_now)

# ============================================================
# SECTION 2 — ATTENTION NEEDED
# ============================================================
st.divider()
st.subheader("⚠️ Attention Needed")

# 1) Pending requests older than 24h
old_pending = []
for r in reqs:
    if r.get("status") == "Pending" and r.get("created_at"):
        try:
            d = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M")
            if (now - d).total_seconds() > 24 * 3600:
                old_pending.append(r)
        except Exception:
            pass

# 2) Approved but no driver assigned
waiting_assign = [r for r in reqs if r.get("status") == "Approved"]

# 3) Overdue (>7 days on duty)
overdue = []
for r in reqs:
    for a in r.get("assignments", []):
        if a.get("status") == "On Duty" and a.get("assigned_at"):
            try:
                d = datetime.strptime(a["assigned_at"], "%Y-%m-%d %H:%M")
                days = (now - d).days
                if days > 7:
                    overdue.append({
                        "driver": a.get("driver", "?"),
                        "hub": a.get("hub", "?"),
                        "days": days,
                        "plate": a.get("plate", "?"),
                    })
            except Exception:
                pass

alerts_shown = False
if old_pending:
    st.warning(f"⏳ **{len(old_pending)}** requests waiting >24h for approval")
    alerts_shown = True
if waiting_assign:
    st.warning(f"🕐 **{len(waiting_assign)}** requests approved but awaiting driver assignment")
    alerts_shown = True
if overdue:
    st.error(f"🚨 **{len(overdue)}** vehicle(s) overdue (>7 days on duty):")
    for o in overdue:
        st.write(f"• **{o['driver']}** — {o['hub']} — {o['days']} days (Plate: {o['plate']})")
    alerts_shown = True

if not alerts_shown:
    st.success("✅ No pending alerts. Operations running smoothly.")

# ============================================================
# SECTION 3 — VEHICLES CURRENTLY ON DUTY
# ============================================================
st.divider()
st.subheader("🚚 Vehicles Currently On Duty")

on_duty_rows = []
for r in reqs:
    for a in r.get("assignments", []):
        if a.get("status") == "On Duty" and a.get("assigned_at"):
            try:
                d = datetime.strptime(a["assigned_at"], "%Y-%m-%d %H:%M")
                days = (now - d).days
            except Exception:
                days = 0
            on_duty_rows.append({
                "Driver": a.get("driver", ""),
                "Plate": a.get("plate", ""),
                "Hub": a.get("hub", ""),
                "Days Out": days,
                "Request ID": r["request_id"],
            })

if on_duty_rows:
    df_on_duty = pd.DataFrame(on_duty_rows).sort_values("Days Out", ascending=False)
    df_on_duty["Days Out"] = df_on_duty["Days Out"].apply(lambda x: f"{x} ⚠️" if x > 7 else str(x))
    st.dataframe(df_on_duty, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    col1.metric("Total On Duty", len(on_duty_rows))
    longest = max(on_duty_rows, key=lambda x: x["Days Out"])
    col2.metric("Longest Out", f"{longest['Driver']} ({longest['Days Out']} days)")
else:
    st.info("✅ No vehicles currently on duty.")

# ============================================================
# SECTION 4 — WEEKLY TREND
# ============================================================
st.divider()
st.subheader("📈 Weekly Trend — Requests per Day")

week_start = today_start - timedelta(days=today_start.weekday())
day_counts = {}
for r in reqs:
    if r.get("created_at"):
        try:
            d = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M")
            if week_start <= d <= now:
                day = d.strftime("%a")
                day_counts[day] = day_counts.get(day, 0) + 1
        except Exception:
            pass

if day_counts:
    days_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ordered = {d: day_counts.get(d, 0) for d in days_order}
    df_week = pd.DataFrame({"Day": list(ordered.keys()), "Requests": list(ordered.values())})
    st.bar_chart(df_week.set_index("Day"))
else:
    st.info("No data this week.")

# ============================================================
# SECTION 5 — TOP WAREHOUSES (This Month)
# ============================================================
st.divider()
st.subheader("🏢 Top Warehouses (This Month)")

month_start = today_start.replace(day=1)
wh_counts = {}
for r in reqs:
    if r.get("created_at"):
        try:
            d = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M")
            if month_start <= d <= now:
                wh = r.get("warehouse", "?")
                wh_counts[wh] = wh_counts.get(wh, 0) + 1
        except Exception:
            pass

if wh_counts:
    df_wh = pd.DataFrame({
        "Warehouse": list(wh_counts.keys()),
        "Requests": list(wh_counts.values())
    }).sort_values("Requests", ascending=False).head(10)
    st.bar_chart(df_wh.set_index("Warehouse"))
else:
    st.info("No data this month.")

# ============================================================
# SECTION 6 — TOP DRIVERS (This Month)
# ============================================================
st.divider()
st.subheader("🚗 Top Drivers (This Month)")

driver_counts = {}
for r in reqs:
    for a in r.get("assignments", []):
        if a.get("assigned_at"):
            try:
                d = datetime.strptime(a["assigned_at"], "%Y-%m-%d %H:%M")
                if month_start <= d <= now:
                    drv = a.get("driver", "?")
                    driver_counts[drv] = driver_counts.get(drv, 0) + 1
            except Exception:
                pass

if driver_counts:
    df_dr = pd.DataFrame({
        "Driver": list(driver_counts.keys()),
        "Trips": list(driver_counts.values())
    }).sort_values("Trips", ascending=False).head(10)
    st.bar_chart(df_dr.set_index("Driver"))
else:
    st.info("No driver activity this month.")

# ============================================================
# SECTION 7 — FULL REQUEST LIST
# ============================================================
st.divider()
st.subheader("📋 Full Request List")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search = st.text_input("🔍 Search (Request ID, Driver, Warehouse)", "")
with col2:
    status_f = st.selectbox("Status", ["All", "Pending", "Approved", "Rejected", "On Duty", "Completed"])
with col3:
    wh_f = st.selectbox("Warehouse", ["All"] + sorted(list({r.get("warehouse", "?") for r in reqs})))

# Build rows
all_rows = []
for r in reqs:
    base = {
        "Request ID": r.get("request_id", ""),
        "Requester": r.get("requester_name", ""),
        "Warehouse": r.get("warehouse", ""),
        "Hub": r.get("hub", ""),
        "Vehicles": ", ".join([f"{v['type']}(x{v['qty']})" for v in r.get("vehicles", [])]),
        "Status": r.get("status", ""),
        "Created": r.get("created_at", ""),
        "Approved By": r.get("approved_by", ""),
        "Drivers": ", ".join([a.get("driver", "") for a in r.get("assignments", [])]) or "—",
    }
    all_rows.append(base)

# Apply filters
filtered = all_rows
if search:
    s = search.lower()
    filtered = [r for r in filtered if s in r["Request ID"].lower() or s in r["Drivers"].lower() or s in r["Warehouse"].lower()]
if status_f != "All":
    filtered = [r for r in filtered if r["Status"] == status_f]
if wh_f != "All":
    filtered = [r for r in filtered if r["Warehouse"] == wh_f]

if filtered:
    df_all = pd.DataFrame(filtered)
    st.dataframe(df_all, use_container_width=True, hide_index=True)

    # Excel download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_all.to_excel(writer, index=False, sheet_name='Requests')
    st.download_button(
        label="📥 Download Full Report (Excel .xlsx)",
        data=output.getvalue(),
        file_name=f"EPSS_Director_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
else:
    st.info("No matching requests.")
