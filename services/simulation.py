from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from models.item import Item
from models.placement import WasteItem

class SimulationService:
    """Service for simulating the passage of time and effects on items"""
    
    def simulate_days(
        self,
        num_days: int,
        current_date: datetime,
        items: Dict[str, Item]
    ) -> Tuple[datetime, Dict[str, Item], List[WasteItem]]:
        """Simulate the passage of time and identify items that expire"""
        # Calculate the new current date
        new_date = current_date + timedelta(days=num_days)
        
        # Make a copy of items to avoid modifying the originals
        updated_items = items.copy()
        
        # Track waste items
        waste_items = []
        
        # Check each item for expiry
        for item_id, item in updated_items.items():
            # Skip items that are already waste
            if item.isWaste:
                continue
                
            # Check if the item expires during this period
            if item.expiryDate != "N/A":
                try:
                    expiry_date = datetime.fromisoformat(item.expiryDate)
                    
                    # If the item expires before or on the new date, mark it as waste
                    if expiry_date <= new_date and expiry_date > current_date:
                        item.isWaste = True
                        
                        # Add to waste items list
                        waste_item = WasteItem(
                            itemId=item_id,
                            name=item.name,
                            reason="Expired",
                            containerId=item.currentLocation.get("containerId") if item.currentLocation else None,
                            position=item.currentLocation.get("position") if item.currentLocation else None,
                            mass=item.mass
                        )
                        waste_items.append(waste_item)
                except Exception:
                    # Invalid date format, skip this item
                    pass
        
        return new_date, updated_items, waste_items