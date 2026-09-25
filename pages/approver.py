# ============================================================
# EPSS Vehicle System - Approver Page (User 2)
# ============================================================

import streamlit as st
from datetime import datetime, date
from config import VEHICLES, WAREHOUSES, HUBS
from auth import current_user, is_logged_in

if not is_logged_in():
    st.warning("🔒 Please log in first.")
    st.stop()

user = current_user()

if user["role"] != "Approver":
    st.error("🚫 Access denied. This page is for **Approvers** only.")
    st.stop()

st.title("✅ Approver Dashboard")
st.caption(f"Logged in as **{user['name']}** ({user['role']})")
st.divider()

# Initialize requests list if missing
if "requests" not in st.session_state:
    st.session_state.requests = []

# Two tabs
tab1, tab2 = st.tabs(["📥 Pending Requests", "🆕 New Direct Request"])

# ============================================================
# TAB 1 — Pending Requests (Approve / Reject)
# ============================================================
with tab1:
    st.subheader("📥 Pending Requests")
    st.caption("Review requests submitted by Requesters.")

    pending = [r for r in st.session_state.requests if r["status"] == "Pending"]

    if not pending:
        st.info("🎉 No pending requests at the moment.")
    else:
        for r in pending:
            with st.container(border=True):
                st.markdown(f"### {r['request_id']}")
                st.write(f"**Requester:** {r['requester_name']}")
                st.write(f"**Warehouse:** {r['warehouse']}  |  **Hub:** {r['hub']}")
                st.write(f"**Purpose:** {r['purpose']}")
                st.write(f"**Required Date:** {r['required_date']}")
                st.write("**Vehicles:**")
                for v in r["vehicles"]:
                    st.write(f"• {v['type']} (x{v['qty']})")
                st.write(f"**Submitted:** {r['created_at']}")

                st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve {r['request_id']}", key=f"ap_{r['request_id']}", use_container_width=True):
                        r["status"] = "Approved"
                        r["approved_by"] = user["name"]
                        r["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.rerun()
                with col2:
                    if st.button(f"❌ Reject {r['request_id']}", key=f"rj_{r['request_id']}", use_container_width=True):
                        r["status"] = "Rejected"
                        r["rejection_reason"] = "Rejected by approver"
                        st.rerun()

# ============================================================
# TAB 2 — New Direct Request (Approver creates & auto-approves)
# ============================================================
with tab2:
    st.subheader("🆕 New Direct Request")
    st.caption("Create a request directly. It will be auto-approved and sent to the Assigner.")

    with st.form("direct_request_form"):
        st.write("**Request Details**")
        warehouse = st.selectbox("Warehouse Requested For", WAREHOUSES, key="dir_wh")
        hub = st.selectbox("Hub Requested For", HUBS, key="dir_hub")
        purpose = st.text_area("Purpose / Reason", placeholder="e.g., Urgent distribution to Adama Hub", key="dir_purpose")
        required_date = st.date_input("Required Date", value=date.today(), key="dir_reqdate")

        st.divider()
        st.subheader("🚛 Vehicles Requested")

        num_vehicles = st.number_input("How many vehicles?", min_value=1, max_value=20, value=1, key="dir_num")

        vehicle_entries = []
        for i in range(int(num_vehicles)):
            col1, col2 = st.columns([3, 1])
            with col1:
                vtype = st.selectbox(f"Vehicle Type #{i+1}", VEHICLES, key=f"dir_vtype_{i}")
            with col2:
                qty = st.number_input(f"Qty", min_value=1, value=1, key=f"dir_vqty_{i}")
            vehicle_entries.append({"type": vtype, "qty": qty})

        submitted = st.form_submit_button("📤 Submit Direct Request", type="primary", use_container_width=True)

        if submitted:
            req_id = f"VR-{datetime.now().strftime('%Y')}-{len(st.session_state.requests)+1:04d}"
            new_request = {
                "request_id": req_id,
                "requester_name": f"{user['name']} (Approver - Direct)",
                "requester_email": user["email"],
                "warehouse": warehouse,
                "hub": hub,
                "purpose": purpose,
                "required_date": str(required_date),
                "vehicles": vehicle_entries,
                "status": "Approved",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "approved_by": user["name"],
                "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "rejection_reason": "",
                "assignments": [],
                "source": "Approver-Direct",
            }
            st.session_state.requests.append(new_request)
            st.success(f"✅ Direct Request **{req_id}** submitted and auto-approved!")
            st.balloons()
