from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

class Position(BaseModel):
    x: float  # Width coordinate
    y: float  # Depth coordinate
    z: float  # Height coordinate
    
    class Config:
        json_schema_extra = {
            "example": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0
            }
        }

class ItemPlacement(BaseModel):
    itemId: str
    containerId: str
    position: Tuple[float, float, float]  # (x, y, z) - start position
    rotation: Tuple[float, float, float]  # (width, depth, height) after rotation
    
    class Config:
        json_schema_extra = {
            "example": {
                "itemId": "002",
                "containerId": "contA",
                "position": (0.0, 0.0, 0.0),
                "rotation": (15.0, 15.0, 50.0)
            }
        }

class RearrangementStep(BaseModel):
    step: int
    action: str  # "move", "remove", "place"
    itemId: str
    fromContainer: Optional[str] = None
    toContainer: Optional[str] = None
    position: Optional[Tuple[float, float, float]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "action": "move",
                "itemId": "001",
                "fromContainer": "contA",
                "toContainer": "contB",
                "position": (10.0, 0.0, 0.0)
            }
        }

class PlacementRequest(BaseModel):
    items: List
    containers: Optional[List] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "itemId": "002",
                        "name": "Oxygen Cylinder",
                        "width": 15.0,
                        "depth": 15.0,
                        "height": 50.0,
                        "mass": 30.0,
                        "priority": 95,
                        "expiryDate": "N/A",
                        "usageLimit": 100,
                        "preferredZone": "Airlock"
                    }
                ],
                "containers": [
                    {
                        "containerId": "contA",
                        "zone": "Airlock",
                        "width": 100.0,
                        "depth": 85.0,
                        "height": 200.0,
                        "occupiedSpace": 0,
                        "items": []
                    }
                ]
            }
        }

class PlacementResponse(BaseModel):
    placements: List[ItemPlacement]
    rearrangements: List[RearrangementStep]
    
    class Config:
        json_schema_extra = {
            "example": {
                "placements": [
                    {
                        "itemId": "002",
                        "containerId": "contA",
                        "position": (0.0, 0.0, 0.0),
                        "rotation": (15.0, 15.0, 50.0)
                    }
                ],
                "rearrangements": []
            }
        }

class ItemLocation(BaseModel):
    itemId: str
    name: str
    containerId: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    retrievalSteps: int
    blockedBy: List[Dict[str, Any]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "itemId": "002",
                "name": "Oxygen Cylinder",
                "containerId": "contA",
                "position": (0.0, 0.0, 0.0),
                "rotation": (15.0, 15.0, 50.0),
                "retrievalSteps": 0,
                "blockedBy": []
            }
        }

class WasteItem(BaseModel):
    itemId: str
    name: str
    reason: str  # "Expired" or "Out of Uses"
    containerId: Optional[str] = None
    position: Optional[Tuple[float, float, float]] = None
    mass: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "itemId": "003",
                "name": "Food Package",
                "reason": "Expired",
                "containerId": "contB",
                "position": (10.0, 0.0, 20.0),
                "mass": 0.5
            }
        }

class WasteReturnStep(BaseModel):
    step: int
    action: str  # "move", "place", "remove"
    itemId: str
    fromContainer: Optional[str] = None
    toContainer: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "action": "move",
                "itemId": "003",
                "fromContainer": "contB",
                "toContainer": "undockingCont"
            }
        }
