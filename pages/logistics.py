# ============================================================
# EPSS Vehicle System - Logistics Page (User 3)
# Assign drivers, mark returned, view on-duty
# ============================================================

import streamlit as st
from datetime import datetime
from config import DRIVERS
from auth import current_user, is_logged_in

if not is_logged_in():
    st.warning("🔒 Please log in first.")
    st.stop()

user = current_user()

if user["role"] != "Assigner":
    st.error("🚫 Access denied. This page is for **Assigners** only.")
    st.stop()

st.title("🚗 Assigner Dashboard")
st.caption(f"Logged in as **{user['name']}** ({user['role']})")
st.divider()

if "requests" not in st.session_state:
    st.session_state.requests = []

# ============================================================
# HELPER: Get all "On Duty" drivers across all requests
# ============================================================
def get_on_duty_drivers():
    on_duty = {}
    for r in st.session_state.requests:
        for a in r.get("assignments", []):
            if a.get("status") == "On Duty":
                driver = a["driver"]
                hub = a.get("hub", r.get("hub", "?"))
                assigned_at = a.get("assigned_at", "")
                days_out = 0
                if assigned_at:
                    try:
                        d = datetime.strptime(assigned_at, "%Y-%m-%d %H:%M")
                        days_out = (datetime.now() - d).days
                    except Exception:
                        days_out = 0
                on_duty[driver] = {
                    "hub": hub,
                    "days_out": days_out,
                    "plate": a.get("plate", ""),
                    "request_id": r["request_id"],
                    "assigned_at": assigned_at,
                }
    return on_duty

on_duty = get_on_duty_drivers()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs(["📋 Assign Drivers", "✅ Mark Returned", "🚚 On Duty Overview"])

# ============================================================
# TAB 1 — Assign Drivers
# ============================================================
with tab1:
    st.subheader("📋 Assign Drivers to Approved Requests")

    approved = [r for r in st.session_state.requests if r["status"] == "Approved"]

    if not approved:
        st.info("📭 No approved requests waiting for assignment.")
    else:
        for r in approved:
            with st.container(border=True):
                st.markdown(f"### {r['request_id']} — From: {r['requester_name']}")
                st.write(f"**Warehouse:** {r['warehouse']}  |  **Hub:** {r['hub']}")
                st.write("**Vehicles:**")
                for v in r["vehicles"]:
                    st.write(f"• {v['type']} (x{v['qty']})")
                st.divider()

                # Build the list of drivers with status
                driver_options = []
                for d in DRIVERS:
                    if d in on_duty:
                        info = on_duty[d]
                        label = f"🚫 {d} — ON DUTY ({info['hub']}, {info['days_out']} days)"
                        driver_options.append(label)
                    else:
                        driver_options.append(f"✅ {d} — Available")

                # Available drivers only for selection
                available_drivers = [d for d in DRIVERS if d not in on_duty]

                if not available_drivers:
                    st.error("⚠️ No drivers available. All are currently On Duty. Mark some as returned first.")
                    continue

                # Build assignments per vehicle
                assignments = []
                v_index = 0
                for v in r["vehicles"]:
                    for j in range(v["qty"]):
                        st.markdown(f"**{v['type']} #{j+1}**")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            chosen = st.selectbox(
                                "Driver",
                                options=available_drivers,
                                key=f"drv_{r['request_id']}_{v_index}",
                            )
                        with col2:
                            plate = st.text_input(
                                "Plate",
                                value=chosen.split(" - ")[-1] if " - " in chosen else "",
                                key=f"plate_{r['request_id']}_{v_index}",
                                disabled=True,
                            )
                        assignments.append({
                            "vehicle": v["type"],
                            "driver": chosen,
                            "plate": plate,
                            "hub": r["hub"],
                            "assigned_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "returned_at": None,
                            "status": "On Duty",
                        })
                        v_index += 1

                if st.button(f"💾 Assign & Send On Duty", key=f"assign_{r['request_id']}", type="primary", use_container_width=True):
                    r["assignments"] = assignments
                    r["status"] = "On Duty"
                    st.success(f"✅ {r['request_id']} assigned. Drivers are now On Duty.")
                    st.rerun()

# ============================================================
# TAB 2 — Mark Returned
# ============================================================
with tab2:
    st.subheader("✅ Mark Returned")

    if not on_duty:
        st.info("🎉 No vehicles currently On Duty. All drivers are available.")
    else:
        # Gather all on-duty assignment entries
        for r in st.session_state.requests:
            for idx, a in enumerate(r.get("assignments", [])):
                if a.get("status") == "On Duty":
                    days_out = 0
                    try:
                        d = datetime.strptime(a.get("assigned_at", ""), "%Y-%m-%d %H:%M")
                        days_out = (datetime.now() - d).days
                    except Exception:
                        days_out = 0

                    warning = " ⚠️" if days_out > 7 else ""

                    with st.container(border=True):
                        st.markdown(f"### 🚚 {a['driver']}")
                        st.write(f"**Plate:** {a.get('plate', '?')}")
                        st.write(f"**Hub:** {a.get('hub', '?')}")
                        st.write(f"**Assigned:** {a.get('assigned_at', '?')}  ({days_out} days ago){warning}")
                        st.write(f"**Request:** {r['request_id']}")

                        if st.button(f"✅ Mark Returned", key=f"ret_{r['request_id']}_{idx}", use_container_width=True):
                            a["returned_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            a["status"] = "Returned"

                            # If ALL assignments in this request are returned → mark Completed
                            if all(x.get("status") == "Returned" for x in r["assignments"]):
                                r["status"] = "Completed"

                            st.success(f"✅ {a['driver']} marked as Returned.")
                            st.rerun()

# ============================================================
# TAB 3 — On Duty Overview
# ============================================================
with tab3:
    st.subheader("🚚 Vehicles Currently On Duty")

    if not on_duty:
        st.info("No vehicles on duty right now.")
    else:
        rows = []
        for driver, info in on_duty.items():
            warn = " ⚠️" if info["days_out"] > 7 else ""
            rows.append({
                "Driver": driver,
                "Plate": info["plate"],
                "Hub": info["hub"],
                "Days Out": f"{info['days_out']}{warn}",
                "Request ID": info["request_id"],
                "Assigned At": info["assigned_at"],
            })
        st.dataframe(rows, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total On Duty", len(on_duty))
        longest = max(on_duty.items(), key=lambda x: x[1]["days_out"])
        col2.metric("Longest Out", f"{longest[1]['days_out']} days")
        col3.metric("Longest Driver", longest[0].split(" - ")[0])
