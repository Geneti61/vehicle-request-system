# ============================================================
# EPSS Vehicle System - Requester Page (User 1)
# ============================================================

import streamlit as st
from datetime import datetime, date
from config import VEHICLES, WAREHOUSES, HUBS
from auth import current_user, is_logged_in

# Require login
if not is_logged_in():
    st.warning("🔒 Please log in first.")
    st.stop()

user = current_user()

# Only Requester can see this page
if user["role"] != "Requester":
    st.error("🚫 Access denied. This page is for **Requesters** only.")
    st.stop()

st.title("📝 New Vehicle Request")
st.caption(f"Logged in as **{user['name']}** ({user['role']})")
st.divider()

# Initialize requests list in session
if "requests" not in st.session_state:
    st.session_state.requests = []

with st.form("request_form"):
    st.subheader("Request Details")

    requester_name = st.text_input("Requester Name", value=user["name"], disabled=True)
    warehouse = st.selectbox("Warehouse Requested For", WAREHOUSES)
    hub = st.selectbox("Hub Requested For", HUBS)
    purpose = st.text_area("Purpose / Reason", placeholder="e.g., Distribution to Adama Hub")
    required_date = st.date_input("Required Date", value=date.today())

    st.divider()
    st.subheader("🚛 Vehicles Requested")

    num_vehicles = st.number_input("How many vehicles?", min_value=1, max_value=20, value=1)

    vehicle_entries = []
    for i in range(int(num_vehicles)):
        col1, col2 = st.columns([3, 1])
        with col1:
            vtype = st.selectbox(f"Vehicle Type #{i+1}", VEHICLES, key=f"vtype_{i}")
        with col2:
            qty = st.number_input(f"Qty", min_value=1, value=1, key=f"vqty_{i}")
        vehicle_entries.append({"type": vtype, "qty": qty})

    submitted = st.form_submit_button("📤 Submit Request", type="primary", use_container_width=True)

    if submitted:
        req_id = f"VR-{datetime.now().strftime('%Y')}-{len(st.session_state.requests)+1:04d}"
        new_request = {
            "request_id": req_id,
            "requester_name": requester_name,
            "requester_email": user["email"],
            "warehouse": warehouse,
            "hub": hub,
            "purpose": purpose,
            "required_date": str(required_date),
            "vehicles": vehicle_entries,
            "status": "Pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "approved_by": "",
            "approved_at": "",
            "rejection_reason": "",
            "assignments": [],
        }
        st.session_state.requests.append(new_request)
        st.success(f"✅ Request **{req_id}** submitted successfully!")
        st.balloons()

st.divider()
st.subheader("📋 My Requests")

my_requests = [r for r in st.session_state.requests if r["requester_email"] == user["email"]]

if not my_requests:
    st.info("No requests yet. Submit your first one above.")
else:
    for r in reversed(my_requests):
        with st.expander(f"**{r['request_id']}** — {r['status']} — {r['created_at']}"):
            st.write(f"**Warehouse:** {r['warehouse']}")
            st.write(f"**Hub:** {r['hub']}")
            st.write(f"**Purpose:** {r['purpose']}")
            st.write(f"**Required Date:** {r['required_date']}")
            st.write("**Vehicles:**")
            for v in r["vehicles"]:
                st.write(f"• {v['type']} (x{v['qty']})")
            st.write(f"**Status:** {r['status']}")

            if r["status"] == "Rejected" and r["rejection_reason"]:
                st.error(f"❌ Rejected: {r['rejection_reason']}")

            if r["status"] == "Completed" and r["assignments"]:
                st.success("✅ Driver Assignments:")
                for a in r["assignments"]:
                    st.write(f"• {a['vehicle']} — Driver: {a['driver']} — Plate: {a['plate']}")
