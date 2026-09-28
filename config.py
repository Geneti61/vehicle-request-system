# ============================================================
# EPSS Vehicle System - Configuration
# Reads from EPSS_Vehicle_System.xlsx
# ============================================================

import pandas as pd
import os

EXCEL_FILE = "EPSS_Vehicle_System.xlsx"

# Check the file exists
if not os.path.exists(EXCEL_FILE):
    raise FileNotFoundError(f"Missing {EXCEL_FILE} — please upload it to the repo root.")

# ============================================================
# HUBS
# ============================================================
_hubs_df = pd.read_excel(EXCEL_FILE, sheet_name="Hubs")
HUBS = _hubs_df["HubName"].dropna().astype(str).tolist()

# ============================================================
# WAREHOUSES
# ============================================================
_wh_df = pd.read_excel(EXCEL_FILE, sheet_name="Warehouses")
WAREHOUSES = _wh_df["WarehouseName"].dropna().astype(str).tolist()

# ============================================================
# VEHICLES
# ============================================================
_veh_df = pd.read_excel(EXCEL_FILE, sheet_name="Vehicles")
VEHICLES = _veh_df["VehicleType"].dropna().astype(str).tolist()

# ============================================================
# DRIVERS
# Format: "DriverName - PlateNumber"
# Also keep a lookup: driver -> vehicle type
# ============================================================
_drv_df = pd.read_excel(EXCEL_FILE, sheet_name="Drivers")
DRIVERS = []
DRIVER_VEHICLE_TYPE = {}
DRIVER_PLATE = {}

for _, row in _drv_df.iterrows():
    name = str(row["DriverName"]).strip()
    plate = str(row["PlateNumber"]).strip()
    vtype = str(row["VehicleType"]).strip()
    if name and plate:
        combined = f"{name} - {plate}"
        DRIVERS.append(combined)
        DRIVER_VEHICLE_TYPE[name] = vtype
        DRIVER_PLATE[name] = plate

# ============================================================
# USERS
# Format: {email: {password, name, role}}
# ============================================================
_users_df = pd.read_excel(EXCEL_FILE, sheet_name="Users")
USERS = {}
for _, row in _users_df.iterrows():
    email = str(row["Email"]).strip().lower()
    if not email or email == "nan":
        continue
    USERS[email] = {
        "password": str(row["Password"]).strip(),
        "name": str(row["Name"]).strip(),
        "role": str(row["Role"]).strip(),
    }
