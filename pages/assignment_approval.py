# ============================================================
# EPSS Vehicle System - Assignment Approval Page (New Role)
# ============================================================

import streamlit as st
from datetime import datetime
from auth import current_user, is_logged_in
from persistence import save_requests, append_audit

if not is_logged_in():
    st.warning("Please log in first.")
    st.stop()

user = current_user()

if user["role"] != "Assignment Approver":
    st.error("Access denied. This page is for Assignment Approvers only.")
    st.stop()

st.title("✅ Assignment Approval")
st.caption(f"Logged in as {user['name']} ({user['role']})")
st.caption("Review driver assignments made by the Fleet Manager before vehicles go On Duty.")
st.divider()

if "requests" not in st.session_state:
    st.session_state.requests = []

# Find requests with assignments pending approval
assigned = [r for r in st.session_state.requests if r["status"] in ["Assigned", "Partially Assigned"]]

if not assigned:
    st.info("🎉 No assignments waiting for your approval.")
else:
    for r in assigned:
        with st.container(border=True):
            st.markdown(f"### {r['request_id']} — From: {r['requester_name']}")
            st.write(f"**Warehouse:** {r['warehouse']}  |  **Hub:** {r['hub']}")
            st.write(f"**Purpose:** {r['purpose']}")
            st.write(f"**Required Date:** {r['required_date']}")
            st.write(f"**Status:** {r['status']}")
            st.divider()

            st.write("**Assigned Vehicles:**")
            pending_count = 0
            for a in r.get("assignments", []):
                if a.get("status") in ["Assigned", "On Duty"]:
                    st.write(f"• **{a.get('vehicle', '?')}** — Driver: **{a.get('driver', '?')}** — Plate: **{a.get('plate', '?')}**")
                    st.caption(f"   Assigned at: {a.get('assigned_at', '?')}  |  Status: {a.get('status')}")
                    if a.get("status") == "Assigned":
                        pending_count += 1

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Approve Assignment {r['request_id']}", key=f"aap_{r['request_id']}", use_container_width=True):
                    for a in r.get("assignments", []):
                        if a.get("status") == "Assigned":
                            a["status"] = "On Duty"
                    if all(a.get("status") in ["On Duty", "Returned"] for a in r.get("assignments", [])):
                        r["status"] = "On Duty"
                    else:
                        r["status"] = "Partially Assigned"
                    r["assignment_approved_by"] = user["name"]
                    r["assignment_approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_requests(st.session_state.requests)
                    append_audit("Assignment Approved", user["email"], r["request_id"])
                    st.success(f"Assignment for {r['request_id']} approved. Vehicle is now On Duty.")
                    st.rerun()
            with col2:
                if st.button(f"❌ Send Back {r['request_id']}", key=f"asb_{r['request_id']}", use_container_width=True):
                    r["assignments"] = [a for a in r.get("assignments", []) if a.get("status") != "Assigned"]
                    r["status"] = "Approved"
                    save_requests(st.session_state.requests)
                    append_audit("Assignment Sent Back", user["email"], r["request_id"])
                    st.warning(f"Assignment for {r['request_id']} sent back to Fleet Manager.")
                    st.rerun()
