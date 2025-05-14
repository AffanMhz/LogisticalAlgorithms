from typing import List
from pydantic import BaseModel, Field, validator

class ContainerBase(BaseModel):
    containerId: str
    zone: str
    width: float = Field(gt=0, description="Width in cm (X-axis)")
    depth: float = Field(gt=0, description="Depth in cm (Y-axis)")
    height: float = Field(gt=0, description="Height in cm (Z-axis)")
    
    @validator('width', 'depth', 'height', pre=True)
    def positive_dimensions(cls, v):
        if v <= 0:
            raise ValueError("Dimensions must be greater than 0")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "containerId": "contA",
                "zone": "Crew Quarters",
                "width": 100.0,
                "depth": 85.0,
                "height": 200.0
            }
        }

class ContainerCreate(ContainerBase):
    """Schema for creating a new container"""
    pass

class Container(ContainerBase):
    """Full container model with additional properties"""
    occupiedSpace: float = 0
    items: List[str] = []  # List of item IDs stored in this container
    
    def get_available_space(self) -> float:
        """Get available space in cubic cm"""
        total_space = self.width * self.depth * self.height
        return total_space - self.occupiedSpace
    
    def is_full(self) -> bool:
        """Check if container is effectively full"""
        # Consider a container full if it has less than 5% space available
        total_space = self.width * self.depth * self.height
        return self.occupiedSpace >= 0.95 * total_space
    
    def add_item(self, item_id: str, volume: float) -> bool:
        """Add an item to the container"""
        if volume > self.get_available_space():
            return False
        
        if item_id not in self.items:
            self.items.append(item_id)
        
        self.occupiedSpace += volume
        return True
    
    def remove_item(self, item_id: str, volume: float) -> bool:
        """Remove an item from the container"""
        if item_id in self.items:
            self.items.remove(item_id)
        
        # Adjust occupied space
        self.occupiedSpace = max(0, self.occupiedSpace - volume)
        return True