# ============================================================
# EPSS Vehicle System - Logistics Page (User 3)
# ============================================================

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from config import DRIVERS, DRIVER_VEHICLE_TYPE
from auth import current_user, is_logged_in
from persistence import save_requests, append_audit

if not is_logged_in():
    st.warning("Please log in first.")
    st.stop()

user = current_user()

if user["role"] != "Assigner":
    st.error("Access denied. This page is for Assigners only.")
    st.stop()

st.title("Assigner Dashboard")
st.caption(f"Logged in as {user['name']} ({user['role']})")
st.divider()

if "requests" not in st.session_state:
    st.session_state.requests = []


def get_on_duty_drivers():
    on_duty = {}
    for r in st.session_state.requests:
        for a in r.get("assignments", []):
            if a.get("status") == "On Duty":
                on_duty[a["driver"]] = {
                    "hub": a.get("hub", r.get("hub", "?")),
                    "days_out": 0,
                    "plate": a.get("plate", ""),
                    "request_id": r["request_id"],
                    "assigned_at": a.get("assigned_at", ""),
                }
    return on_duty


on_duty = get_on_duty_drivers()

tab1, tab2, tab3, tab4 = st.tabs(["Assign Drivers", "Mark Returned", "On Duty Overview", "Returned History"])

# ============================================================
# TAB 1 — Assign Drivers
# ============================================================
with tab1:
    st.subheader("Assign Drivers to Approved Requests")

    active = [r for r in st.session_state.requests if r["status"] in ["Approved", "Partially Assigned"]]

    if not active:
        st.info("No approved requests waiting for assignment.")
    else:
        for r in active:
            with st.container(border=True):
                st.markdown(f"### {r['request_id']} - From: {r['requester_name']}")
                st.write(f"**Warehouse:** {r['warehouse']}  |  **Hub:** {r['hub']}")
                st.write(f"**Status:** {r['status']}")
                st.divider()

                existing_assignments = r.get("assignments", [])

                vehicle_slots = []
                slot_index = 0
                for v in r["vehicles"]:
                    for j in range(v["qty"]):
                        assigned = None
                        if slot_index < len(existing_assignments):
                            assigned = existing_assignments[slot_index]
                        vehicle_slots.append({
                            "index": slot_index,
                            "label": f"{v['type']} #{j+1}",
                            "existing": assigned,
                        })
                        slot_index += 1

                available_drivers = [d for d in DRIVERS if d not in on_duty]

                name_to_plate = {}
                for d in available_drivers:
                    parts = d.split(" - ")
                    if len(parts) >= 2:
                        name_to_plate[parts[0].strip()] = parts[-1].strip()

                for slot in vehicle_slots:
                    label = slot["label"]
                    idx = slot["index"]
                    existing = slot["existing"]

                    st.markdown(f"**{label}**")

                    if existing and existing.get("status") in ["On Duty", "Returned"]:
                        status_icon = "On Duty" if existing["status"] == "On Duty" else "Returned"
                        st.success(f"Assigned: {existing['driver']} - Plate: {existing.get('plate','')} ({status_icon})")
                        continue

                    if not available_drivers:
                        st.warning("No drivers available right now. Leave this vehicle pending.")
                        continue

                    col1, col2, col3 = st.columns([3, 3, 1])
                    with col1:
                        chosen_name = st.selectbox(
                            "Driver Name",
                            options=["-- Select Driver --"] + list(name_to_plate.keys()),
                            key=f"name_{r['request_id']}_{idx}",
                        )
                    with col2:
                        if chosen_name != "-- Select Driver --":
                            plate_options = [name_to_plate[chosen_name]]
                        else:
                            plate_options = ["-- Plate auto-fills --"]
                        chosen_plate = st.selectbox(
                            "Plate Number",
                            options=plate_options,
                            key=f"plate_{r['request_id']}_{idx}",
                            disabled=(chosen_name == "-- Select Driver --"),
                        )
                    with col3:
                        st.write("")
                        st.write("")
                        assign_clicked = st.button(
                            "Assign",
                            key=f"assign_{r['request_id']}_{idx}",
                            use_container_width=True,
                        )

                    if assign_clicked:
                        if chosen_name == "-- Select Driver --":
                            st.error("Please select a driver first.")
                        else:
                            final_plate = name_to_plate[chosen_name]
                            r.setdefault("assignments", []).append({
                                "vehicle": slot["label"],
                                "driver": chosen_name,
                                "plate": final_plate,
                                "hub": r["hub"],
                                "assigned_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "returned_at": None,
                                "status": "On Duty",
                            })
                            total_slots = sum(v["qty"] for v in r["vehicles"])
                            assigned_now = len([a for a in r["assignments"] if a.get("status") in ["On Duty", "Returned"]])
                            if assigned_now >= total_slots:
                                r["status"] = "On Duty"
                            else:
                                r["status"] = "Partially Assigned"
                            save_requests(st.session_state.requests)
                            append_audit("Driver Assigned", user["email"], r["request_id"])
                            st.success(f"{slot['label']} assigned to {chosen_name} (Plate: {final_plate}).")
                            st.rerun()

# ============================================================
# TAB 2 — Mark Returned
# ============================================================
with tab2:
    st.subheader("Mark Returned")
    if not on_duty:
        st.info("No vehicles currently On Duty.")
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
                    warning = " WARNING" if days_out > 7 else ""
                    with st.container(border=True):
                        st.markdown(f"### {a['driver']}")
                        st.write(f"**Vehicle:** {a.get('vehicle', '?')}")
                        st.write(f"**Plate:** {a.get('plate', '?')}")
                        st.write(f"**Hub:** {a.get('hub', '?')}")
                        st.write(f"**Assigned:** {a.get('assigned_at', '?')}  ({days_out} days ago){warning}")
                        st.write(f"**Request:** {r['request_id']}")
                        if st.button("Mark Returned", key=f"ret_{r['request_id']}_{idx}", use_container_width=True):
                            a["returned_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            a["status"] = "Returned"
                            if all(x.get("status") == "Returned" for x in r["assignments"]):
                                r["status"] = "Completed"
                            save_requests(st.session_state.requests)
                            append_audit("Vehicle Returned", user["email"], r["request_id"])
                            st.success(f"{a['driver']} marked as Returned.")
                            st.rerun()

# ============================================================
# TAB 3 — On Duty Overview
# ============================================================
with tab3:
    st.subheader("Vehicles Currently On Duty")
    if not on_duty:
        st.info("No vehicles on duty right now.")
    else:
        rows = []
        for driver, info in on_duty.items():
            warn = " WARNING" if info["days_out"] > 7 else ""
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
        col3.metric("Longest Driver", longest[0])

# ============================================================
# TAB 4 — Returned History
# ============================================================
with tab4:
    st.subheader("📜 Returned Vehicles History")
    st.caption("All vehicles that have been marked as Returned.")

    returned_rows = []
    for r in st.session_state.requests:
        for a in r.get("assignments", []):
            if a.get("status") == "Returned" and a.get("returned_at"):
                days_out = "—"
                try:
                    d1 = datetime.strptime(a.get("assigned_at", ""), "%Y-%m-%d %H:%M")
                    d2 = datetime.strptime(a.get("returned_at", ""), "%Y-%m-%d %H:%M")
                    days_out = (d2 - d1).days
                except Exception:
                    pass

                vtype = DRIVER_VEHICLE_TYPE.get(a.get("driver", ""), "—")

                returned_rows.append({
                    "Driver": a.get("driver", ""),
                    "Plate": a.get("plate", ""),
                    "Vehicle Type": vtype,
                    "Hub": a.get("hub", r.get("hub", "")),
                    "Request ID": r.get("request_id", ""),
                    "Assigned": a.get("assigned_at", ""),
                    "Returned": a.get("returned_at", ""),
                    "Days Out": days_out,
                })

    if not returned_rows:
        st.info("📭 No returned vehicles yet.")
    else:
        returned_rows.sort(key=lambda x: x["Returned"], reverse=True)

        search = st.text_input("🔍 Search (Driver, Plate, Hub)", "")
        if search:
            s = search.lower()
            returned_rows = [r for r in returned_rows
                            if s in r["Driver"].lower()
                            or s in r["Plate"].lower()
                            or s in r["Hub"].lower()]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Returned", len(returned_rows))
        c2.metric("Showing", len(returned_rows))
        try:
            avg_days = round(sum(int(r["Days Out"]) for r in returned_rows if isinstance(r["Days Out"], int)) / len(returned_rows), 1)
            c3.metric("Avg Days Out", avg_days)
        except Exception:
            c3.metric("Avg Days Out", "—")

        st.divider()

        df = pd.DataFrame(returned_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Returned Vehicles')
        st.download_button(
            label="📥 Download as Excel (.xlsx)",
            data=output.getvalue(),
            file_name=f"EPSS_Returned_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
