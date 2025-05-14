from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ItemBase(BaseModel):
    itemId: str
    name: str
    width: float = Field(gt=0, description="Width in cm (X-axis)")
    depth: float = Field(gt=0, description="Depth in cm (Y-axis)")
    height: float = Field(gt=0, description="Height in cm (Z-axis)")
    mass: float = Field(gt=0, description="Mass in kg")
    priority: int = Field(ge=1, le=100, description="Priority 1-100, higher = more critical")
    expiryDate: str  # ISO format date or "N/A"
    usageLimit: int = Field(ge=0, description="Max number of uses")
    preferredZone: str  # Preferred storage zone
    
    @validator('width', 'depth', 'height', 'mass', pre=True)
    def positive_values(cls, v):
        if v <= 0:
            raise ValueError("Dimensions and mass must be greater than 0")
        return v
    
    @validator('priority', pre=True)
    def priority_range(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Priority must be between 1 and 100")
        return v
    
    @validator('usageLimit', pre=True)
    def usage_limit_positive(cls, v):
        if v < 0:
            raise ValueError("Usage limit cannot be negative")
        return v
    
    @validator('expiryDate', pre=True)
    def validate_expiry_date(cls, v):
        if v == "N/A":
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("Expiry date must be a valid ISO format date or 'N/A'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "itemId": "002",
                "name": "Oxygen Cylinder",
                "width": 15.0,
                "depth": 15.0,
                "height": 50.0,
                "mass": 30.0,
                "priority": 95,
                "expiryDate": "2025-05-20",
                "usageLimit": 100,
                "preferredZone": "Airlock"
            }
        }

class ItemCreate(ItemBase):
    """Schema for creating a new item"""
    pass

class Item(ItemBase):
    """Full item model with additional properties"""
    isWaste: bool = False
    currentLocation: Optional[Dict[str, Any]] = None
    
    def get_volume(self) -> float:
        """Calculate the volume of the item in cubic cm"""
        return self.width * self.depth * self.height
    
    def get_all_rotations(self) -> List[Tuple[float, float, float]]:
        """Get all possible rotations of the item"""
        # Since we're dealing with 3D objects, there are 6 possible orientations
        return [
            (self.width, self.depth, self.height),
            (self.width, self.height, self.depth),
            (self.depth, self.width, self.height),
            (self.depth, self.height, self.width),
            (self.height, self.width, self.depth),
            (self.height, self.depth, self.width)
        ]
    
    def is_expired(self) -> bool:
        """Check if item is expired"""
        if self.expiryDate == "N/A":
            return False
        
        try:
            expiry_date = datetime.fromisoformat(self.expiryDate)
            current_date = datetime.now()
            return current_date > expiry_date
        except Exception:
            return False
    
    def get_effective_priority(self) -> float:
        """Calculate effective priority based on expiry and usage"""
        base_priority = float(self.priority)
        
        # Increase priority for items close to expiry
        if self.expiryDate != "N/A":
            try:
                expiry_date = datetime.fromisoformat(self.expiryDate)
                current_date = datetime.now()
                days_until_expiry = (expiry_date - current_date).days
                
                if days_until_expiry <= 0:
                    # Already expired, mark as waste but keep high priority
                    self.isWaste = True
                    # Add expiry boost
                    base_priority += 20
                elif days_until_expiry < 30:
                    # Add urgency boost for items expiring soon
                    base_priority += (30 - days_until_expiry) / 3
            except Exception:
                pass
        
        # Adjust priority based on usage limit
        if self.usageLimit <= 5 and self.usageLimit > 0:
            # Items with few uses left get priority boost
            base_priority += (5 - self.usageLimit) * 3
        elif self.usageLimit == 0:
            # Used up items are waste but might need priority for disposal
            self.isWaste = True
            base_priority += 10
        
        return min(base_priority, 130)  # Cap at 130 (100 base + 30 bonus)