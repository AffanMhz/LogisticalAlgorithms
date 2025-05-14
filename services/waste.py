from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import heapq

from models.item import Item
from models.container import Container
from models.placement import WasteItem, WasteReturnStep
from utils.space3d import Space3D

class WasteService:
    """Service for advanced waste management and return planning"""
    
    def identify_waste_items(
        self,
        items: Dict[str, Item],
        containers: Dict[str, Container],
        current_date: datetime
    ) -> Tuple[List[WasteItem], float, List[WasteReturnStep]]:
        """Identify waste items based on expiry date, usage limit, or manual marking
        
        Returns:
        - List of waste items
        - Total waste mass
        - Initial retrieval steps
        """
        waste_items = []
        total_waste_mass = 0.0
        
        # Check each item for waste status
        for item_id, item in items.items():
            is_waste = False
            reason = ""
            days_until_expiry = None
            
            # Check if already marked as waste
            if item.isWaste:
                is_waste = True
                
                # Determine the reason
                if item.usageLimit <= 0:
                    reason = "Out of Uses"
                elif item.expiryDate != "N/A":
                    try:
                        expiry_date = datetime.fromisoformat(item.expiryDate)
                        days_until_expiry = (expiry_date - current_date).days
                        
                        if days_until_expiry <= 0:
                            reason = "Expired"
                        else:
                            reason = "Manually Marked"
                    except Exception:
                        reason = "Manually Marked"
                else:
                    reason = "Manually Marked"
            
            # Check expiry date for non-waste items
            elif item.expiryDate != "N/A":
                try:
                    expiry_date = datetime.fromisoformat(item.expiryDate)
                    days_until_expiry = (expiry_date - current_date).days
                    
                    # If expired or within 5 days of expiry, mark as waste
                    if days_until_expiry <= 0:
                        is_waste = True
                        reason = "Expired"
                        item.isWaste = True
                    elif days_until_expiry <= 5:
                        # Close to expiry, flag for potential disposal
                        is_waste = True
                        reason = f"Expires in {days_until_expiry} days"
                        item.isWaste = True
                except Exception:
                    # Invalid date format, skip this item
                    pass
            
            # Check usage limit
            elif item.usageLimit <= 0:
                is_waste = True
                reason = "Out of Uses"
                item.isWaste = True
            
            # Almost out of uses (<=3)
            elif 0 < item.usageLimit <= 3:
                is_waste = True
                reason = f"Only {item.usageLimit} uses remaining"
                item.isWaste = True
            
            # If it's waste, add to the list
            if is_waste:
                # Get location info
                container_id = None
                position = None
                
                if item.currentLocation and "containerId" in item.currentLocation:
                    container_id = item.currentLocation["containerId"]
                    position = item.currentLocation.get("position")
                
                waste_item = WasteItem(
                    itemId=item_id,
                    name=item.name,
                    reason=reason,
                    containerId=container_id,
                    position=position,
                    mass=item.mass
                )
                
                waste_items.append(waste_item)
                total_waste_mass += item.mass
        
        # Sort waste items by urgency
        sorted_waste_items = self._sort_waste_by_urgency(waste_items, items)
        
        # Generate optimized return steps
        return_steps = self._generate_optimized_waste_return_steps(sorted_waste_items)
        
        return sorted_waste_items, total_waste_mass, return_steps
    
    def _sort_waste_by_urgency(
        self,
        waste_items: List[WasteItem],
        items: Dict[str, Item]
    ) -> List[WasteItem]:
        """Sort waste items based on urgency of disposal"""
        
        def get_urgency_score(waste_item):
            """Calculate urgency score for waste item
            
            Higher score = more urgent for disposal
            """
            item = items.get(waste_item.itemId)
            if not item:
                return 0
            
            # Base urgency score
            score = 0
            
            # Fully expired or used items are most urgent
            if "Expired" in waste_item.reason or "Out of Uses" in waste_item.reason:
                score += 100
            
            # Items close to expiry get moderate urgency
            elif "Expires in" in waste_item.reason:
                # Extract days until expiry from reason
                try:
                    days = int(waste_item.reason.split(" ")[2])
                    score += 100 - days * 10  # Lower days = higher score
                except:
                    score += 50  # Default if parsing fails
            
            # Low usage limit gets moderate urgency
            elif "uses remaining" in waste_item.reason:
                try:
                    uses = int(waste_item.reason.split(" ")[1])
                    score += 50 - uses * 10  # Lower uses = higher score
                except:
                    score += 30  # Default if parsing fails
            
            # Add priority factor - higher priority items might be disposed later
            # due to potential continued usefulness
            score -= min(30, item.priority / 3)
            
            # Add mass factor - heavier items might be more urgently disposed
            # to free up mass capacity
            score += min(20, item.mass * 2)
            
            return score
        
        # Sort by calculated urgency score (highest first)
        return sorted(waste_items, key=get_urgency_score, reverse=True)
    
    def generate_waste_return_plan(
        self,
        waste_items: List[WasteItem],
        max_weight: float,
        undocking_container_id: str
    ) -> List[WasteReturnStep]:
        """Generate an optimized plan to return waste items within a weight limit
        
        Uses a knapsack algorithm to maximize the value of returned items
        while staying within the weight constraint.
        """
        # If there are no waste items, return empty plan
        if not waste_items:
            return []
            
        # Define value of each waste item (combination of mass and urgency)
        # Items already sorted by urgency from identify_waste_items
        item_values = {}
        for i, item in enumerate(waste_items):
            # Value is inverse of position in urgency list (more urgent = higher value)
            # normalized to range 1-10
            urgency_value = 10 * (1 - (i / max(1, len(waste_items))))
            
            # Combine with mass efficiency (heavier items have higher value)
            # to optimize space in return vehicle
            mass_value = min(10, item.mass * 2)
            
            # Combined value
            item_values[item.itemId] = urgency_value * 0.7 + mass_value * 0.3
        
        # Group items by container for more efficient collection
        container_items = {}
        for item in waste_items:
            if item.containerId:
                if item.containerId not in container_items:
                    container_items[item.containerId] = []
                container_items[item.containerId].append(item)
        
        # Use dynamic programming approach for the knapsack problem
        # Discretize weights to use integer knapsack algorithm
        SCALE_FACTOR = 100  # Convert to centigrams for integers
        scaled_max_weight = int(max_weight * SCALE_FACTOR)
        
        # Initialize DP table
        dp = [0] * (scaled_max_weight + 1)
        selected_items = [set() for _ in range(scaled_max_weight + 1)]
        
        # Fill DP table
        for item in waste_items:
            scaled_mass = int(item.mass * SCALE_FACTOR)
            if scaled_mass <= 0:
                continue  # Skip items with no mass
                
            for w in range(scaled_max_weight, scaled_mass - 1, -1):
                # Value if we include this item
                new_value = dp[w - scaled_mass] + item_values[item.itemId]
                
                # Update if better than current value
                if new_value > dp[w]:
                    dp[w] = new_value
                    # Create a new set with all items from the previous weight
                    selected_items[w] = selected_items[w - scaled_mass].copy()
                    selected_items[w].add(item.itemId)
        
        # Find the maximum weight with items
        max_value_weight = scaled_max_weight
        while max_value_weight > 0 and not selected_items[max_value_weight]:
            max_value_weight -= 1
        
        # Get the final selected items
        final_selected_items = selected_items[max_value_weight]
        
        # Create a mapping of item IDs to waste items
        item_map = {item.itemId: item for item in waste_items}
        
        # Generate optimized steps to move the selected items
        steps = []
        step_count = 1
        
        # Process items container by container
        for container_id, container_waste_items in container_items.items():
            # Filter for only selected items
            selected_container_items = [
                item for item in container_waste_items 
                if item.itemId in final_selected_items
            ]
            
            if not selected_container_items:
                continue
                
            # Sort items by position for more efficient retrieval
            # Retrieve from front to back and top to bottom
            if all(item.position is not None for item in selected_container_items):
                sorted_items = sorted(
                    selected_container_items,
                    key=lambda x: (
                        x.position[1],  # y (depth)
                        -x.position[2],  # -z (height, negative to start from top)
                        x.position[0]   # x (width)
                    )
                )
            else:
                sorted_items = selected_container_items
            
            # Add steps to retrieve and move each item
            for item in sorted_items:
                # First remove from original container
                steps.append(WasteReturnStep(
                    step=step_count,
                    action="remove",
                    itemId=item.itemId,
                    fromContainer=container_id
                ))
                step_count += 1
                
                # Then place in undocking container
                steps.append(WasteReturnStep(
                    step=step_count,
                    action="place",
                    itemId=item.itemId,
                    toContainer=undocking_container_id
                ))
                step_count += 1
        
        # Handle selected items without a container
        for item_id in final_selected_items:
            item = item_map.get(item_id)
            if not item or item.containerId:
                continue  # Skip if already processed or not found
                
            # Just place directly in undocking container
            steps.append(WasteReturnStep(
                step=step_count,
                action="place",
                itemId=item.itemId,
                toContainer=undocking_container_id
            ))
            step_count += 1
        
        return steps
    
    def _generate_optimized_waste_return_steps(
        self,
        waste_items: List[WasteItem]
    ) -> List[WasteReturnStep]:
        """Generate optimized steps to retrieve and collect waste items"""
        steps = []
        
        # Group waste items by container for more efficient retrieval
        container_items = {}
        for item in waste_items:
            if item.containerId:
                if item.containerId not in container_items:
                    container_items[item.containerId] = []
                container_items[item.containerId].append(item)
        
        step_count = 1
        
        # Process items container by container
        for container_id, items in container_items.items():
            # Skip empty containers
            if not items:
                continue
                
            # Sort items by position for more efficient retrieval
            if all(item.position is not None for item in items):
                # Create a spatial map of the container to optimize retrieval order
                # We want to retrieve items in a way that minimizes the movement
                # of other items during retrieval
                
                # First, get all items that are directly accessible (no blocking items)
                accessible_items = []
                blocked_items = []
                
                # Simple heuristic: items closer to the front (lower y) are more accessible
                sorted_by_accessibility = sorted(
                    items,
                    key=lambda x: (
                        x.position[1],   # y (depth) - lower is more accessible
                        -x.position[2],  # -z (height) - higher is more accessible
                        x.position[0]    # x (width) - arbitrary tiebreaker
                    )
                )
                
                # Add steps for retrieving items in accessibility order
                for item in sorted_by_accessibility:
                    steps.append(WasteReturnStep(
                        step=step_count,
                        action="remove",
                        itemId=item.itemId,
                        fromContainer=container_id
                    ))
                    step_count += 1
            else:
                # If position information is not available,
                # just retrieve items in their original order
                for item in items:
                    steps.append(WasteReturnStep(
                        step=step_count,
                        action="remove",
                        itemId=item.itemId,
                        fromContainer=container_id
                    ))
                    step_count += 1
        
        # Add steps for items without a container
        for item in waste_items:
            if not item.containerId:
                steps.append(WasteReturnStep(
                    step=step_count,
                    action="remove",
                    itemId=item.itemId
                ))
                step_count += 1
        
        return steps
        
    def _generate_waste_return_steps(
        self,
        waste_items: List[WasteItem]
    ) -> List[WasteReturnStep]:
        """Legacy method for generating basic waste return steps
        
        Kept for backward compatibility.
        """
        return self._generate_optimized_waste_return_steps(waste_items)
        
    def complete_undocking(
        self,
        waste_items: List[WasteItem],
        plan_steps: List[WasteReturnStep], 
        items: Dict[str, Item],
        containers: Dict[str, Container]
    ) -> None:
        """Complete the undocking process by updating the status of waste items
        
        This should be called after the waste return plan has been executed
        to update the inventory system.
        """
        # Extract all item IDs that were part of the plan
        removed_item_ids = set()
        for step in plan_steps:
            if step.action in ["move", "remove", "place"]:
                removed_item_ids.add(step.itemId)
        
        # Update items that were part of the plan
        for item_id in removed_item_ids:
            if item_id in items:
                # Remove from container if needed
                item = items[item_id]
                if item.currentLocation and "containerId" in item.currentLocation:
                    container_id = item.currentLocation["containerId"]
                    if container_id in containers:
                        container = containers[container_id]
                        container.remove_item(item_id, item.get_volume())
                
                # Mark as completely removed from the system
                item.currentLocation = None
                
                # If we want to fully remove from inventory, this would be done at app level
                # by deleting the item from the items dictionary
                
        return len(removed_item_ids)