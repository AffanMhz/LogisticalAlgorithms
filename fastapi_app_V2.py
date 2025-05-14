from datetime import datetime
import json
import os
import csv
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, Request, Query, UploadFile, File, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from io import StringIO
from pathlib import Path

from models.container import Container
from models.item import Item
from models.placement import PlacementRequest, PlacementResponse, ItemPlacement, RearrangementStep, WasteItem
from services.placement import PlacementService
from services.retrieval import RetrievalService
from services.waste import WasteService
from services.simulation import SimulationService

app = FastAPI(title="Space Station Cargo Management System")

# --- CORS and Static Files ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend/src"), name="static")

# --- Paths and Data Files ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CONTAINERS_FILE = DATA_DIR / "containers.json"
ITEMS_FILE = DATA_DIR / "items.json"
LOGS_FILE = DATA_DIR / "logs.json"
CURRENT_DATE_FILE = DATA_DIR / "current_date.txt"

# --- Initialize Data Files if Needed ---
for file, default in [
    (CONTAINERS_FILE, []), (ITEMS_FILE, []), (LOGS_FILE, [])
]:
    if not file.exists():
        with open(file, "w") as f:
            json.dump(default, f)
if not CURRENT_DATE_FILE.exists():
    with open(CURRENT_DATE_FILE, "w") as f:
        f.write(datetime.now().isoformat())

# --- Load Data into Memory ---
def load_data():
    def json_load(file, default):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except Exception:
            return default
    containers = json_load(CONTAINERS_FILE, [])
    items = json_load(ITEMS_FILE, [])
    logs = json_load(LOGS_FILE, [])
    try:
        with open(CURRENT_DATE_FILE, "r") as f:
            current_date = datetime.fromisoformat(f.read().strip())
    except Exception:
        current_date = datetime.now()
    return containers, items, logs, current_date

def save_data(containers, items, logs, current_date):
    with open(CONTAINERS_FILE, "w") as f:
        json.dump(containers, f, indent=2)
    with open(ITEMS_FILE, "w") as f:
        json.dump(items, f, indent=2)
    with open(LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=2)
    with open(CURRENT_DATE_FILE, "w") as f:
        f.write(current_date.isoformat())

containers_data, items_data, logs_data, CURRENT_DATE = load_data()

# --- Helper Converters ---
def dict_to_item(item_dict: Dict) -> Item:
    item = Item(
        itemId=item_dict["itemId"],
        name=item_dict["name"],
        width=item_dict["width"],
        depth=item_dict["depth"],
        height=item_dict["height"],
        mass=item_dict["mass"],
        priority=item_dict["priority"],
        expiryDate=item_dict["expiryDate"],
        usageLimit=item_dict["usageLimit"],
        preferredZone=item_dict["preferredZone"]
    )
    item.isWaste = item_dict.get("isWaste", False)
    item.currentLocation = item_dict.get("currentLocation")
    return item

def dict_to_container(container_dict: Dict) -> Container:
    container = Container(
        containerId=container_dict["containerId"],
        zone=container_dict["zone"],
        width=container_dict["width"],
        depth=container_dict["depth"],
        height=container_dict["height"]
    )
    container.occupiedSpace = container_dict.get("occupiedSpace", 0)
    container.items = container_dict.get("items", [])
    return container

def item_to_dict(item: Item) -> dict:
    return item.dict() if hasattr(item, "dict") else dict(item)

def container_to_dict(container: Container) -> dict:
    return container.dict() if hasattr(container, "dict") else dict(container)

# --- Logging ---
def add_log(action: str, details: Optional[Dict[str, Any]] = None, user: str = "system", item_id: Optional[str] = None):
    global logs_data, CURRENT_DATE
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user": user,
        "details": details or {},
        "itemId": item_id
    }
    if not log_entry["details"].get("currentDate") and CURRENT_DATE:
        log_entry["details"]["currentDate"] = CURRENT_DATE.isoformat()
    logs_data.append(log_entry)
    if len(logs_data) > 1000:
        logs_data.pop(0)
    save_data(containers_data, items_data, logs_data, CURRENT_DATE)
    return log_entry

# --- Services ---
placement_service = PlacementService()
retrieval_service = RetrievalService()
waste_service = WasteService()
simulation_service = SimulationService()

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = Path("frontend/src/index.html")
    if index_path.exists():
        return index_path.read_text()
    return "<h1>Space Station Cargo Management System</h1>"

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# --- Placement Recommendation ---
@app.post("/api/placement/recommend")
async def calculate_placement(payload: dict = Body(...)):
    global containers_data, items_data, CURRENT_DATE
    # Load data if not provided
    containers_in = payload.get("containers") or containers_data
    items_in = payload.get("items") or items_data
    containers = [dict_to_container(c) for c in containers_in]
    items = [dict_to_item(i) for i in items_in]
    items_dict = {item.itemId: item for item in items}
    containers_dict = {c.containerId: c for c in containers}
    placement_response = placement_service.calculate_placement(
        items=items_dict, containers=containers_dict
    )
    placements = placement_response.placements
    rearrangements = placement_response.rearrangements

    # Update items and containers in-memory
    for placement in placements:
        item_idx = next((i for i, item in enumerate(items_in) if item['itemId'] == placement.itemId), None)
        if item_idx is not None:
            items_in[item_idx]['currentLocation'] = {
                "containerId": placement.containerId,
                "position": placement.position,
                "rotation": placement.rotation
            }
            container_idx = next((i for i, c in enumerate(containers_in) if c['containerId'] == placement.containerId), None)
            if container_idx is not None:
                if placement.itemId not in containers_in[container_idx]['items']:
                    containers_in[container_idx]['items'].append(placement.itemId)
                item = next((it for it in items if it.itemId == placement.itemId), None)
                if item:
                    volume = item.get_volume()
                    containers_in[container_idx]['occupiedSpace'] += volume

    # Save updated data
    containers_data = containers_in
    items_data = items_in
    save_data(containers_data, items_data, logs_data, CURRENT_DATE)

    add_log(
        action="calculate_placement",
        details={"numItems": len(items), "numPlacements": len(placements), "numRearrangements": len(rearrangements)}
    )
    placements_dict = [p.dict() for p in placements]
    rearrangements_dict = [r.dict() for r in rearrangements]
    return {"placements": placements_dict, "rearrangements": rearrangements_dict}

# --- Item Search ---
@app.get("/api/items/search")
async def search_item(itemId: Optional[str] = Query(None), itemName: Optional[str] = Query(None), userId: Optional[str] = Query("anonymous")):
    add_log(
        action="search_item",
        details={"itemId": itemId, "itemName": itemName},
        user=userId
    )
    items = items_data
    results = []
    if itemId:
        results = [item for item in items if item['itemId'] == itemId]
    elif itemName:
        search_term = itemName.lower()
        results = [item for item in items if search_term in item['name'].lower()]
    return results

# --- Item Retrieval ---
@app.post("/api/items/retrieve")
async def retrieve_item(payload: dict = Body(...)):
    item_id = payload.get("itemId")
    user_id = payload.get("userId", "anonymous")
    if not item_id:
        return {"error": "No item ID provided"}
    items_dict = {item['itemId']: dict_to_item(item) for item in items_data}
    containers_dict = {c['containerId']: dict_to_container(c) for c in containers_data}
    if item_id not in items_dict:
        return {"error": f"Item {item_id} not found"}
    item = items_dict[item_id]
    try:
        item_location = retrieval_service.get_item_location(
            item_id=item_id, items=items_dict, containers=containers_dict
        )
        success, retrieval_steps = retrieval_service.retrieve_item(
            item_id=item_id, user_id=user_id, items=items_dict, containers=containers_dict
        )
        if not item_location:
            return {"error": "Unable to locate item"}
        add_log(
            action="retrieve_item",
            details={
                "itemId": item_id,
                "containerId": item_location.containerId,
                "numSteps": len(retrieval_steps) if isinstance(retrieval_steps, list) else 0
            },
            user=user_id
        )
        # Sync back to items_data and containers_data if needed
        updated_items_list = []
        for old_item_dict in items_data:
            iid = old_item_dict['itemId']
            if iid in items_dict:
                updated_item = items_dict[iid]
                updated_dict = item_to_dict(updated_item)
                updated_items_list.append(updated_dict)
            else:
                updated_items_list.append(old_item_dict)
        items_data[:] = updated_items_list
        save_data(containers_data, items_data, logs_data, CURRENT_DATE)
        item_location_dict = item_location.dict() if hasattr(item_location, "dict") else dict(item_location)
        retrieval_steps_dict = [step if isinstance(step, dict) else step.dict() for step in retrieval_steps]
        return {"itemLocation": item_location_dict, "retrievalSteps": retrieval_steps_dict}
    except Exception as e:
        return {"error": str(e), "itemLocation": None, "retrievalSteps": []}

# --- Time Simulation ---
@app.post("/api/simulate/day")
async def simulate_days(payload: dict = Body(...)):
    global CURRENT_DATE, items_data
    days = payload.get("numOfDays", 1)
    items_to_use = payload.get("itemsToBeUsedPerDay", [])
    items_list = items_data
    items_dict = {item['itemId']: dict_to_item(item) for item in items_list}
    for item_id in items_to_use:
        if item_id in items_dict and items_dict[item_id].usageLimit > 0:
            items_dict[item_id].usageLimit -= 1
            for i, item_dict in enumerate(items_list):
                if item_dict['itemId'] == item_id:
                    item_dict['usageLimit'] = items_dict[item_id].usageLimit
                    if items_dict[item_id].usageLimit <= 0:
                        item_dict['isWaste'] = True
                    break
    old_date = CURRENT_DATE
    new_date, updated_items, waste_items = simulation_service.simulate_days(
        num_days=days,
        current_date=CURRENT_DATE,
        items=items_dict
    )
    CURRENT_DATE = new_date
    for item_id, item in updated_items.items():
        for i, item_dict in enumerate(items_list):
            if item_dict['itemId'] == item_id:
                item_dict['isWaste'] = item.isWaste
                break
    items_data[:] = items_list
    save_data(containers_data, items_data, logs_data, CURRENT_DATE)
    expiring_items = [w.dict() for w in waste_items if w.reason == 'Expired']
    usage_depleted_items = [w.dict() for w in waste_items if w.reason == 'Out of Uses']
    add_log(
        action="simulate_days",
        details={
            "days": days,
            "oldDate": old_date.isoformat(),
            "newDate": new_date.isoformat(),
            "numExpiringItems": len(expiring_items),
            "numUsageDepletedItems": len(usage_depleted_items),
            "itemsUsed": items_to_use
        }
    )
    return {
        "oldDate": old_date.isoformat(),
        "newDate": new_date.isoformat(),
        "expiringItems": expiring_items,
        "usageDepletedItems": usage_depleted_items
    }

# --- Waste Identification ---
@app.get("/api/waste/identify")
async def identify_waste():
    items_list = items_data
    containers_list = containers_data
    items_dict = {item['itemId']: dict_to_item(item) for item in items_list}
    containers_dict = {c['containerId']: dict_to_container(c) for c in containers_list}
    waste_items, total_mass, return_steps = waste_service.identify_waste_items(
        items=items_dict,
        containers=containers_dict,
        current_date=CURRENT_DATE
    )
    for waste_item in waste_items:
        for i, item_dict in enumerate(items_list):
            if item_dict['itemId'] == waste_item.itemId:
                item_dict['isWaste'] = True
                break
    items_data[:] = items_list
    save_data(containers_data, items_data, logs_data, CURRENT_DATE)
    waste_items_dict = [w.dict() for w in waste_items]
    return_steps_dict = [step.dict() for step in return_steps]
    add_log(
        action="identify_waste",
        details={
            "numWasteItems": len(waste_items), "totalMass": total_mass, "numReturnSteps": len(return_steps)
        }
    )
    return {
        "wasteItems": waste_items_dict,
        "totalMass": total_mass,
        "returnSteps": return_steps_dict
    }

# --- Waste Return Plan ---
@app.post("/api/waste/return-plan")
async def waste_return_plan(payload: dict = Body(...)):
    undocking_container_id = payload.get("undockingContainerId")
    undocking_date = payload.get("undockingDate")
    max_weight = payload.get("maxWeight", 100.0)
    if not undocking_container_id:
        return {"success": False, "error": "Undocking container ID is required"}
    items_dict = {item['itemId']: dict_to_item(item) for item in items_data}
    containers_dict = {c['containerId']: dict_to_container(c) for c in containers_data}
    try:
        waste_items, total_mass, _ = waste_service.identify_waste_items(
            items=items_dict,
            containers=containers_dict,
            current_date=CURRENT_DATE
        )
        return_steps = waste_service.generate_waste_return_plan(
            waste_items=waste_items,
            max_weight=float(max_weight),
            undocking_container_id=undocking_container_id
        )
        return_items = []
        total_volume = 0.0
        total_weight = 0.0
        item_ids_in_plan = set()
        for step in return_steps:
            item_id = step.itemId
            if item_id in items_dict and item_id not in item_ids_in_plan:
                item = items_dict[item_id]
                item_ids_in_plan.add(item_id)
                waste_item = next((w for w in waste_items if w.itemId == item_id), None)
                if waste_item:
                    return_items.append({
                        "itemId": item_id,
                        "name": item.name,
                        "reason": waste_item.reason
                    })
                    item_volume = item.width * item.depth * item.height
                    total_volume += item_volume
                    total_weight += item.mass
        return_manifest = {
            "undockingContainerId": undocking_container_id,
            "undockingDate": undocking_date or CURRENT_DATE.isoformat(),
            "returnItems": return_items,
            "totalVolume": total_volume,
            "totalWeight": total_weight
        }
        formatted_steps = [
            {
                "step": i + 1,
                "itemId": step.itemId,
                "itemName": items_dict[step.itemId].name if step.itemId in items_dict else "Unknown",
                "fromContainer": step.fromContainer,
                "toContainer": step.toContainer
            }
            for i, step in enumerate(return_steps)
        ]
        retrieval_steps = [
            {
                "step": i + 1,
                "action": "retrieve" if step.action == "move" else step.action,
                "itemId": step.itemId,
                "itemName": items_dict[step.itemId].name if step.itemId in items_dict else "Unknown"
            }
            for i, step in enumerate(return_steps)
        ]
        add_log(
            action="waste_return_plan",
            details={
                "undockingContainerId": undocking_container_id,
                "maxWeight": max_weight,
                "itemsSelected": len(return_items),
                "totalWeight": total_weight,
                "totalVolume": total_volume
            }
        )
        return {
            "success": True,
            "returnPlan": formatted_steps,
            "retrievalSteps": retrieval_steps,
            "returnManifest": return_manifest
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Complete Undocking ---
@app.post("/api/waste/complete-undocking")
async def complete_undocking(payload: dict = Body(...)):
    undocking_container_id = payload.get("undockingContainerId")
    timestamp = payload.get("timestamp")
    if not undocking_container_id:
        return {"success": False, "error": "Undocking container ID is required"}
    items_dict = {item['itemId']: dict_to_item(item) for item in items_data}
    containers_dict = {c['containerId']: dict_to_container(c) for c in containers_data}
    try:
        waste_items, _, _ = waste_service.identify_waste_items(
            items=items_dict,
            containers=containers_dict,
            current_date=CURRENT_DATE
        )
        items_removed = 0
        items_to_remove = []
        for waste_item in waste_items:
            item_id = waste_item.itemId
            if waste_item.containerId == undocking_container_id:
                items_to_remove.append(item_id)
                container = next((c for c in containers_data if c['containerId'] == waste_item.containerId), None)
                if container and item_id in container.get('items', []):
                    container['items'].remove(item_id)
                    item = next((i for i in items_data if i['itemId'] == item_id), None)
                    if item:
                        item_volume = item['width'] * item['depth'] * item['height']
                        container['occupiedSpace'] = max(0, container['occupiedSpace'] - item_volume)
                items_removed += 1
        items_data[:] = [item for item in items_data if item['itemId'] not in items_to_remove]
        save_data(containers_data, items_data, logs_data, CURRENT_DATE)
        add_log(
            action="complete_undocking",
            details={
                "undockingContainerId": undocking_container_id,
                "timestamp": timestamp or CURRENT_DATE.isoformat(),
                "itemsRemoved": items_removed
            }
        )
        return {
            "success": True,
            "itemsRemoved": items_removed
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Import Items ---
@app.post("/api/items/import")
async def import_items(file: UploadFile = File(...)):
    contents = await file.read()
    contents = contents.decode("utf-8")
    csv_reader = csv.DictReader(StringIO(contents))
    items = items_data
    imported_count = 0
    errors = []
    for row_num, row in enumerate(csv_reader, start=1):
        try:
            item_id = row.get('item_id', row.get('itemId', '')).strip()
            if not item_id:
                errors.append(f"Row {row_num}: Missing item ID")
                continue
            name = row.get('name', '').strip()
            width = float(row.get('width_cm', row.get('width', 0)))
            depth = float(row.get('depth_cm', row.get('depth', 0)))
            height = float(row.get('height_cm', row.get('height', 0)))
            mass = float(row.get('mass_kg', row.get('mass', 0)))
            priority = int(row.get('priority', 50))
            expiry_date = row.get('expiry_date', row.get('expiryDate', 'N/A')).strip()
            usage_limit = int(row.get('usage_limit', row.get('usageLimit', 1)))
            preferred_zone = row.get('preferred_zone', row.get('preferredZone', '')).strip()
            item = {
                "itemId": item_id,
                "name": name,
                "width": width,
                "depth": depth,
                "height": height,
                "mass": mass,
                "priority": priority,
                "expiryDate": expiry_date,
                "usageLimit": usage_limit,
                "preferredZone": preferred_zone,
                "isWaste": False,
                "currentLocation": None
            }
            existing_item_index = next((i for i, existing in enumerate(items) if existing['itemId'] == item['itemId']), None)
            if existing_item_index is not None:
                items[existing_item_index] = item
            else:
                items.append(item)
            imported_count += 1
        except Exception as row_error:
            errors.append(f"Row {row_num}: {str(row_error)}")
    items_data[:] = items
    save_data(containers_data, items_data, logs_data, CURRENT_DATE)
    add_log(
        action="import_items",
        details={"importedCount": imported_count, "filename": file.filename, "errors": errors}
    )
    return {"success": True, "importedCount": imported_count, "errors": errors}

# --- Import Containers ---
@app.post("/api/containers/import")
async def import_containers(file: UploadFile = File(...)):
    contents = await file.read()
    contents = contents.decode("utf-8")
    csv_reader = csv.DictReader(StringIO(contents))
    containers = containers_data
    imported_count = 0
    errors = []
    for row_num, row in enumerate(csv_reader, start=1):
        try:
            container_id = row.get('container_id', row.get('containerId', '')).strip()
            if not container_id:
                errors.append(f"Row {row_num}: Missing container ID")
                continue
            zone = row.get('zone', '').strip()
            width = float(row.get('width_cm', row.get('width', 0)))
            depth = float(row.get('depth_cm', row.get('depth', 0)))
            height = float(row.get('height_cm', row.get('height', 0)))
            container = {
                "containerId": container_id,
                "zone": zone,
                "width": width,
                "depth": depth,
                "height": height,
                "occupiedSpace": 0,
                "items": []
            }
            existing_container_index = next((i for i, existing in enumerate(containers) if existing['containerId'] == container['containerId']), None)
            if existing_container_index is not None:
                container["items"] = containers[existing_container_index].get("items", [])
                container["occupiedSpace"] = containers[existing_container_index].get("occupiedSpace", 0)
                containers[existing_container_index] = container
            else:
                containers.append(container)
            imported_count += 1
        except Exception as row_error:
            errors.append(f"Row {row_num}: {str(row_error)}")
    containers_data[:] = containers
    save_data(containers_data, items_data, logs_data, CURRENT_DATE)
    add_log(
        action="import_containers",
        details={"importedCount": imported_count, "filename": file.filename, "errors": errors}
    )
    return {"success": True, "importedCount": imported_count, "errors": errors}

# --- Get All Containers ---
@app.get("/api/containers")
async def get_containers():
    return containers_data

# --- Get All Items ---
@app.get("/api/items")
async def get_items():
    return items_data

# --- Get Logs ---
@app.get("/api/logs")
async def get_logs():
    return {"logs": logs_data}

# --- Add Log ---
@app.post("/api/logs/add")
async def add_log_route(log_data: dict = Body(...)):
    action = log_data.get("actionType", "")
    details = log_data.get("details", {})
    user_id = log_data.get("userId", "user")
    item_id = log_data.get("itemId")
    log_entry = add_log(action=action, details=details, user=user_id, item_id=item_id)
    return log_entry

# --- Clear Data on Startup if Desired ---
def clear_data_files():
    with open(ITEMS_FILE, 'w') as f:
        json.dump([], f)
    with open(CONTAINERS_FILE, 'w') as f:
        json.dump([], f)
    with open(LOGS_FILE, 'w') as f:
        json.dump([], f)
    add_log(action="system_startup", details={"message": "Data files cleared for clean state"})

# Uncomment the next line to clear data at each startup:
# clear_data_files()