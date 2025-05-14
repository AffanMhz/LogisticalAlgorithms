from datetime import datetime
import json
import os
import csv
from typing import Dict, List, Optional, Any, Union, Tuple

from fastapi import FastAPI, Request, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import numpy as np
from io import StringIO
from pathlib import Path
from pydantic import BaseModel

# Import models
from models.container import Container, ContainerCreate
from models.item import Item, ItemCreate
from models.placement import PlacementRequest, PlacementResponse, ItemLocation, WasteItem, Position

# Import services
from services.placement import PlacementService
from services.retrieval import RetrievalService
from services.waste import WasteService
from services.simulation import SimulationService

app = FastAPI(title="Space Station Cargo Management System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
placement_service = PlacementService()
retrieval_service = RetrievalService()
waste_service = WasteService()
simulation_service = SimulationService()

# In-memory data storage
containers_data: Dict[str, Container] = {}
items_data: Dict[str, Item] = {}
logs_data: List[Dict[str, Any]] = []
current_date = datetime.now()

# Create data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Load any existing data from files
try:
    if os.path.exists(data_dir / "containers.json"):
        with open(data_dir / "containers.json", "r") as f:
            containers_json = json.load(f)
            for container_dict in containers_json:
                container = Container(**container_dict)
                containers_data[container.containerId] = container

    if os.path.exists(data_dir / "items.json"):
        with open(data_dir / "items.json", "r") as f:
            items_json = json.load(f)
            for item_dict in items_json:
                item = Item(**item_dict)
                items_data[item.itemId] = item

    if os.path.exists(data_dir / "logs.json"):
        with open(data_dir / "logs.json", "r") as f:
            logs_data = json.load(f)

    if os.path.exists(data_dir / "current_date.txt"):
        with open(data_dir / "current_date.txt", "r") as f:
            date_str = f.read().strip()
            current_date = datetime.fromisoformat(date_str)
except Exception as e:
    print(f"Error loading data: {e}")
    # Continue with empty data if files don't exist or have issues

# Helper to save data to files
def save_data():
    try:
        with open(data_dir / "containers.json", "w") as f:
            json.dump([container.dict() for container in containers_data.values()], f)
        
        with open(data_dir / "items.json", "w") as f:
            json.dump([item.dict() for item in items_data.values()], f)
        
        with open(data_dir / "logs.json", "w") as f:
            json.dump(logs_data, f)
        
        with open(data_dir / "current_date.txt", "w") as f:
            f.write(current_date.isoformat())
    except Exception as e:
        print(f"Error saving data: {e}")

# Helper to add logs
def add_log(action: str, details: Optional[Dict[str, Any]] = None, user: str = "system"):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user": user,
        "details": details or {}
    }
    logs_data.append(log_entry)
    # Keep only the last 1000 logs
    if len(logs_data) > 1000:
        logs_data.pop(0)
    return log_entry

# Root endpoint - serve the HTML template
@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("templates/index.html", "r") as f:
        return f.read()

# Calculate optimal placement for items
@app.post("/calculate_placement", response_model=PlacementResponse)
async def calculate_placement(request: PlacementRequest):
    global containers_data, items_data
    
    items_to_place = []
    request_containers = []
    
    # Handle if request contains item IDs instead of full items
    for item in request.items:
        if isinstance(item, str) and item in items_data:
            items_to_place.append(items_data[item])
        elif hasattr(item, "itemId") and item.itemId in items_data:
            items_to_place.append(items_data[item.itemId])
        elif hasattr(item, "dict"):
            # Create a new Item instance from dict
            new_item = Item(**item.dict())
            items_to_place.append(new_item)
            # Optionally add to items_data if not already there
            if new_item.itemId not in items_data:
                items_data[new_item.itemId] = new_item
    
    # Use provided containers or default to stored containers
    if request.containers:
        for container in request.containers:
            if isinstance(container, str) and container in containers_data:
                request_containers.append(containers_data[container])
            elif hasattr(container, "containerId") and container.containerId in containers_data:
                request_containers.append(containers_data[container.containerId])
            elif hasattr(container, "dict"):
                # Create a new Container instance from dict
                new_container = Container(**container.dict())
                request_containers.append(new_container)
    else:
        request_containers = list(containers_data.values())
    
    # Calculate placement
    placements, rearrangements = placement_service.calculate_placement(
        items=items_to_place,
        containers=request_containers,
        current_date=current_date
    )
    
    # Update items and containers data with new placements
    for placement in placements:
        if placement.itemId in items_data and placement.containerId in containers_data:
            item = items_data[placement.itemId]
            container = containers_data[placement.containerId]
            
            # Update item location
            item.currentLocation = {
                "containerId": placement.containerId,
                "position": placement.position,
                "rotation": placement.rotation
            }
            
            # Update container space
            if placement.itemId not in container.items:
                container.items.append(placement.itemId)
                container.occupiedSpace += item.get_volume()
    
    # Add log entry
    add_log(
        action="item_placement",
        details={
            "items_placed": [p.itemId for p in placements],
            "rearrangements": len(rearrangements)
        }
    )
    
    # Save updated data
    save_data()
    
    return PlacementResponse(placements=placements, rearrangements=rearrangements)

# Search for an item by ID or name
@app.get("/search_item")
async def search_item(
    itemId: Optional[str] = Query(None),
    itemName: Optional[str] = Query(None),
    userId: Optional[str] = Query("anonymous")
):
    if not itemId and not itemName:
        return []
    
    found_items = []
    
    # Search by ID
    if itemId and itemId in items_data:
        item = items_data[itemId]
        if item.currentLocation:
            location = await retrieval_service.get_item_location(
                item=item,
                items_data=items_data,
                containers_data=containers_data
            )
            found_items.append(location)
    
    # Search by name
    if itemName:
        for item in items_data.values():
            if itemName.lower() in item.name.lower() and item.currentLocation:
                location = await retrieval_service.get_item_location(
                    item=item,
                    items_data=items_data,
                    containers_data=containers_data
                )
                found_items.append(location)
    
    # Add log entry
    add_log(
        action="item_search",
        details={
            "itemId": itemId,
            "itemName": itemName,
            "results_count": len(found_items)
        },
        user=userId
    )
    
    return found_items

# Get detailed retrieval steps for an item
@app.post("/retrieve_item")
async def retrieve_item(request: dict):
    item_id = request.get("itemId")
    if not item_id or item_id not in items_data:
        return {"error": "Item not found"}
    
    item = items_data[item_id]
    if not item.currentLocation:
        return {"error": "Item is not stored in any container"}
    
    # Get retrieval steps
    steps = await retrieval_service.get_retrieval_steps(
        item=item,
        items_data=items_data,
        containers_data=containers_data
    )
    
    # Add log entry
    add_log(
        action="item_retrieval",
        details={
            "itemId": item_id,
            "steps": len(steps)
        }
    )
    
    return {"item": item, "steps": steps}

# Simulate the passage of time
@app.post("/simulate_days")
async def simulate_days(request: dict):
    global current_date, items_data
    
    days = request.get("days", 1)
    if days <= 0:
        return {"error": "Days must be positive"}
    
    # Simulate time passage
    new_date, updated_items, waste_items = simulation_service.simulate_days(
        num_days=days,
        current_date=current_date,
        items=items_data
    )
    
    # Update current date and items
    current_date = new_date
    items_data = updated_items
    
    # Add log entry
    add_log(
        action="time_simulation",
        details={
            "days": days,
            "new_date": new_date.isoformat(),
            "waste_items_count": len(waste_items)
        }
    )
    
    # Save updated data
    save_data()
    
    return {
        "newDate": new_date.isoformat(),
        "wasteItems": [waste.dict() for waste in waste_items]
    }

# Identify waste items
@app.get("/identify_waste")
async def identify_waste():
    # Find waste items
    waste_items, total_mass, return_steps = waste_service.identify_waste_items(
        items=items_data,
        containers=containers_data,
        current_date=current_date
    )
    
    # Add log entry
    add_log(
        action="waste_identification",
        details={
            "waste_count": len(waste_items),
            "total_mass": total_mass
        }
    )
    
    return {
        "wasteItems": [waste.dict() for waste in waste_items],
        "totalMass": total_mass,
        "returnSteps": return_steps
    }

# Import items from CSV
@app.post("/import_items")
async def import_items(file: UploadFile = File(...)):
    global items_data
    
    contents = await file.read()
    contents = contents.decode("utf-8")
    csv_reader = csv.DictReader(StringIO(contents))
    
    count = 0
    for row in csv_reader:
        try:
            # Convert row data to expected types
            item_data = {
                "itemId": row.get("item_id"),
                "name": row.get("name"),
                "width": float(row.get("width_cm", 0)),
                "depth": float(row.get("depth_cm", 0)),
                "height": float(row.get("height_cm", 0)),
                "mass": float(row.get("mass_kg", 0)),
                "priority": int(row.get("priority", 0)),
                "expiryDate": row.get("expiry_date", "N/A"),
                "usageLimit": int(row.get("usage_limit", 0)),
                "preferredZone": row.get("preferred_zone", "Storage_Bay"),
                "isWaste": False,
                "currentLocation": None
            }
            
            item = Item(**item_data)
            items_data[item.itemId] = item
            count += 1
        except Exception as e:
            print(f"Error processing row {row}: {e}")
    
    # Add log entry
    add_log(
        action="import_items",
        details={
            "filename": file.filename,
            "items_imported": count
        }
    )
    
    # Save updated data
    save_data()
    
    return {"count": count, "message": f"Successfully imported {count} items"}

# Import containers from CSV
@app.post("/import_containers")
async def import_containers(file: UploadFile = File(...)):
    global containers_data
    
    contents = await file.read()
    contents = contents.decode("utf-8")
    csv_reader = csv.DictReader(StringIO(contents))
    
    count = 0
    for row in csv_reader:
        try:
            # Convert row data to expected types
            container_data = {
                "containerId": row.get("container_id"),
                "zone": row.get("zone"),
                "width": float(row.get("width_cm", 0)),
                "depth": float(row.get("depth_cm", 0)),
                "height": float(row.get("height_cm", 0)),
                "occupiedSpace": 0,
                "items": []
            }
            
            container = Container(**container_data)
            containers_data[container.containerId] = container
            count += 1
        except Exception as e:
            print(f"Error processing row {row}: {e}")
    
    # Add log entry
    add_log(
        action="import_containers",
        details={
            "filename": file.filename,
            "containers_imported": count
        }
    )
    
    # Save updated data
    save_data()
    
    return {"count": count, "message": f"Successfully imported {count} containers"}

# Get all containers
@app.get("/containers")
async def get_containers():
    return list(containers_data.values())

# Get all items
@app.get("/items")
async def get_items():
    return list(items_data.values())

# Get system logs
@app.get("/logs")
async def get_logs():
    return logs_data

# Add a log entry
@app.post("/add_log")
async def add_log(log_data: dict):
    action = log_data.get("action", "unknown_action")
    details = log_data.get("details", {})
    user = log_data.get("user", "anonymous")
    
    log_entry = add_log(action=action, details=details, user=user)
    
    # Save logs data
    save_data()
    
    return log_entry