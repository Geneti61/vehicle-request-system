# ============================================================
# EPSS Vehicle System - Reports Page
# Visible to all logged-in users
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

st.title("📊 Reports & Analytics")
st.caption(f"Logged in as **{user['name']}** ({user['role']})")

if "requests" not in st.session_state:
    st.session_state.requests = []

reqs = st.session_state.requests

# ============================================================
# HELPER: Check if a datetime string is within a range
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
# TIME RANGE SELECTOR
# ============================================================
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    range_choice = st.selectbox(
        "📅 Time Range",
        ["Today", "This Week", "This Month", "This Quarter", "This Year", "All Time"]
    )

now = datetime.now()
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

if range_choice == "Today":
    start, end = today_start, now
elif range_choice == "This Week":
    start = today_start - timedelta(days=today_start.weekday())
    end = now
elif range_choice == "This Month":
    start = today_start.replace(day=1)
    end = now
elif range_choice == "This Quarter":
    q_month = ((today_start.month - 1) // 3) * 3 + 1
    start = today_start.replace(month=q_month, day=1)
    end = now
elif range_choice == "This Year":
    start = today_start.replace(month=1, day=1)
    end = now
else:
    start, end = datetime(2000, 1, 1), now

st.caption(f"Showing data from **{start.strftime('%d %b %Y')}** to **{end.strftime('%d %b %Y')}**")

# ============================================================
# TODAY'S SNAPSHOT (Live numbers)
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
# SUMMARY METRICS (filtered by range)
# ============================================================
st.divider()
st.subheader(f"📈 Summary — {range_choice}")

# Filter requests within range (by created_at)
filtered = [r for r in reqs if in_range(r.get("created_at"), start, end)]

total = len(filtered)
pending = len([r for r in filtered if r.get("status") == "Pending"])
approved = len([r for r in filtered if r.get("status") == "Approved"])
rejected = len([r for r in filtered if r.get("status") == "Rejected"])
on_duty = len([r for r in filtered if r.get("status") == "On Duty"])
completed = len([r for r in filtered if r.get("status") == "Completed"])

total_vehicles = 0
for r in filtered:
    for a in r.get("assignments", []):
        total_vehicles += 1

c1, c2, c3 = st.columns(3)
c1.metric("📋 Total Requests", total)
c2.metric("⏳ Pending", pending)
c3.metric("✅ Approved", approved)

c4, c5, c6 = st.columns(3)
c4.metric("❌ Rejected", rejected)
c5.metric("🚚 On Duty", on_duty)
c6.metric("✅ Completed", completed)

# ============================================================
# CHARTS
# ============================================================
st.divider()
st.subheader("📊 Charts")

# ---- Chart 1: Requests per Day ----
st.markdown("**Requests per Day**")
day_counts = {}
for r in filtered:
    if r.get("created_at"):
        try:
            day = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M").strftime("%Y-%m-%d")
            day_counts[day] = day_counts.get(day, 0) + 1
        except Exception:
            pass

if day_counts:
    df_days = pd.DataFrame({
        "Date": list(day_counts.keys()),
        "Requests": list(day_counts.values())
    }).sort_values("Date")
    st.bar_chart(df_days.set_index("Date"))
else:
    st.info("No data to chart.")

# ---- Chart 2: Status Breakdown ----
st.markdown("**Status Breakdown**")
status_data = {
    "Pending": pending,
    "Approved": approved,
    "Rejected": rejected,
    "On Duty": on_duty,
    "Completed": completed,
}
df_status = pd.DataFrame({
    "Status": list(status_data.keys()),
    "Count": list(status_data.values())
})
if df_status["Count"].sum() > 0:
    st.bar_chart(df_status.set_index("Status"))
else:
    st.info("No status data.")

# ---- Chart 3: Requests per Warehouse ----
st.markdown("**Requests per Warehouse**")
wh_counts = {}
for r in filtered:
    wh = r.get("warehouse", "?")
    wh_counts[wh] = wh_counts.get(wh, 0) + 1

if wh_counts:
    df_wh = pd.DataFrame({
        "Warehouse": list(wh_counts.keys()),
        "Count": list(wh_counts.values())
    }).sort_values("Count", ascending=False)
    st.bar_chart(df_wh.set_index("Warehouse"))
else:
    st.info("No warehouse data.")

# ---- Chart 4: Top Drivers ----
st.markdown("**Top Drivers by Assignments**")
driver_counts = {}
for r in filtered:
    for a in r.get("assignments", []):
        d = a.get("driver", "?")
        driver_counts[d] = driver_counts.get(d, 0) + 1

if driver_counts:
    df_dr = pd.DataFrame({
        "Driver": list(driver_counts.keys()),
        "Trips": list(driver_counts.values())
    }).sort_values("Trips", ascending=False).head(10)
    st.bar_chart(df_dr.set_index("Driver"))
else:
    st.info("No driver data.")

# ============================================================
# MASTER TABLE
# ============================================================
st.divider()
st.subheader("📋 Master Table")

rows = []
for r in filtered:
    if r.get("assignments"):
        for a in r["assignments"]:
            rows.append({
                "Request ID": r["request_id"],
                "Requester": r.get("requester_name", ""),
                "Warehouse": r.get("warehouse", ""),
                "Hub": r.get("hub", ""),
                "Vehicle": a.get("vehicle", ""),
                "Driver": a.get("driver", ""),
                "Plate": a.get("plate", ""),
                "Status": r.get("status", ""),
                "Created": r.get("created_at", ""),
                "Approved By": r.get("approved_by", ""),
            })
    else:
        for v in r.get("vehicles", []):
            rows.append({
                "Request ID": r["request_id"],
                "Requester": r.get("requester_name", ""),
                "Warehouse": r.get("warehouse", ""),
                "Hub": r.get("hub", ""),
                "Vehicle": v.get("type", ""),
                "Driver": "—",
                "Plate": "—",
                "Status": r.get("status", ""),
                "Created": r.get("created_at", ""),
                "Approved By": r.get("approved_by", ""),
            })

if rows:
    df_master = pd.DataFrame(rows)
    st.dataframe(df_master, use_container_width=True, hide_index=True)

    # Download Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_master.to_excel(writer, index=False, sheet_name='EPSS_Report')
    st.download_button(
        label="📥 Download as Excel (.xlsx)",
        data=output.getvalue(),
        file_name=f"EPSS_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
else:
    st.info("No data to show for this time range.")
