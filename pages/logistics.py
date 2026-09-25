# ============================================================
# EPSS Vehicle System - Logistics Page (User 3)
# Independent vehicle assignment + Mark Returned
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
# HELPER: Get all "On Duty" drivers
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
# TAB 1 — Assign Drivers (independent per vehicle)
# ============================================================
with tab1:
    st.subheader("📋 Assign Drivers to Approved Requests")

    # Show requests that are Approved OR Partially Assigned
    active = [r for r in st.session_state.requests if r["status"] in ["Approved", "Partially Assigned"]]

    if not active:
        st.info("📭 No approved requests waiting for assignment.")
    else:
        for r in active:
            with st.container(border=True):
                st.markdown(f"### {r['request_id']} — From: {r['requester_name']}")
                st.write(f"**Warehouse:** {r['warehouse']}  |  **Hub:** {r['hub']}")
                st.write(f"**Status:** {r['status']}")
                st.divider()

                # Build a flat list of vehicles with a unique index
                # Each vehicle has: type, index, assigned or not
                existing_assignments = r.get("assignments", [])
                assigned_count = len([a for a in existing_assignments if a.get("status") in ["On Duty", "Returned"]])

                # Build list of vehicle slots
                vehicle_slots = []
                slot_index = 0
                for v in r["vehicles"]:
                    for j in range(v["qty"]):
                        # Check if this slot already has an assignment
                        assigned = None
                        if slot_index < len(existing_assignments):
                            assigned = existing_assignments[slot_index]
                        vehicle_slots.append({
                            "index": slot_index,
                            "label": f"{v['type']} #{j+1}",
                            "existing": assigned,
                        })
                        slot_index += 1

                # Track drivers chosen during THIS session (for unassigned vehicles)
                drivers_picked_this_session = []

                # Available drivers = those not currently On Duty
                available_drivers = [d for d in DRIVERS if d not in on_duty]

                # Render each vehicle independently
                for slot in vehicle_slots:
                    label = slot["label"]
                    idx = slot["index"]
                    existing = slot["existing"]

                    st.markdown(f"**{label}**")

                    # If already assigned → show as read-only
                    if existing and existing.get("status") in ["On Duty", "Returned"]:
                        status_icon = "🚚 On Duty" if existing["status"] == "On Duty" else "✅ Returned"
                        st.success(f"✔️ Assigned: **{existing['driver']}** — Plate: **{existing.get('plate','')}** ({status_icon})")
                        continue

                    # If not assigned → show driver picker
                    # Remove drivers already picked in this session
                    selectable = [d for d in available_drivers if d not in drivers_picked_this_session]

                    if not selectable:
                        st.warning("⚠️ No drivers available right now. Leave this vehicle pending.")
                        continue

                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        chosen = st.selectbox(
                            "Driver",
                            options=["— Select driver —"] + selectable,
                            key=f"drv_{r['request_id']}_{idx}",
                        )
                    with col2:
                        plate_val = ""
                        if chosen != "— Select driver —" and " - " in chosen:
                            plate_val = chosen.split(" - ")[-1]
                        st.text_input(
                            "Plate",
                            value=plate_val,
                            key=f"plate_{r['request_id']}_{idx}",
                            disabled=True,
                        )
                    with col3:
                        st.write("")
                        st.write("")
                        assign_clicked = st.button(
                            "✅ Assign",
                            key=f"assign_{r['request_id']}_{idx}",
                            use_container_width=True,
                        )

                    if assign_clicked:
                        if chosen == "— Select driver —":
                            st.error("Please select a driver first.")
                        else:
                            # Add the assignment
                            r.setdefault("assignments", []).append({
                                "vehicle": slot["label"],
                                "driver": chosen,
                                "plate": plate_val,
                                "hub": r["hub"],
                                "assigned_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "returned_at": None,
                                "status": "On Duty",
                            })

                            # Update request status
                            total_slots = sum(v["qty"] for v in r["vehicles"])
                            assigned_now = len([a for a in r["assignments"] if a.get("status") in ["On Duty", "Returned"]])
                            if assigned_now >= total_slots:
                                r["status"] = "On Duty"
                            else:
                                r["status"] = "Partially Assigned"

                            st.success(f"✅ {slot['label']} assigned to {chosen}.")
                            st.rerun()

                    drivers_picked_this_session.append(chosen) if chosen != "— Select driver —" else None

# ============================================================
# TAB 2 — Mark Returned
# ============================================================
with tab2:
    st.subheader("✅ Mark Returned")

    if not on_duty:
        st.info("🎉 No vehicles currently On Duty. All drivers are available.")
    else:
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
                        st.write(f"**Vehicle:** {a.get('vehicle', '?')}")
                        st.write(f"**Plate:** {a.get('plate', '?')}")
                        st.write(f"**Hub:** {a.get('hub', '?')}")
                        st.write(f"**Assigned:** {a.get('assigned_at', '?')}  ({days_out} days ago){warning}")
                        st.write(f"**Request:** {r['request_id']}")

                        if st.button("✅ Mark Returned", key=f"ret_{r['request_id']}_{idx}", use_container_width=True):
                            a["returned_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            a["status"] = "Returned"

                            # If all assignments are returned → Completed
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
        st.dataframe(rows, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total On Duty", len(on_duty))
        longest = max(on_duty.items(), key=lambda x: x[1]["days_out"])
        col2.metric("Longest Out", f"{longest[1]['days_out']} days")
        col3.metric("Longest Driver", longest[0].split(" - ")[0])
