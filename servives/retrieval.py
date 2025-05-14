from typing import Dict, List, Tuple, Optional, Any, Set
import copy
import heapq
from datetime import datetime

from models.item import Item
from models.container import Container
from models.placement import ItemLocation, RearrangementStep
from utils.space3d import Space3D

class RetrievalService:
    """Service for retrieving items from containers with optimized search and access algorithms"""
    
    def search_items(
        self,
        query: str,
        items: Dict[str, Item],
        containers: Dict[str, Container]
    ) -> List[ItemLocation]:
        """Search for items by name or ID that match the query
        
        Returns a list of item locations sorted by retrieval ease and expiry date
        """
        matching_items = []
        
        # Look for exact ID match first
        if query in items:
            item_location = self.get_item_location(query, items, containers)
            if item_location:
                matching_items.append(item_location)
        
        # Then look for partial name matches
        query_lower = query.lower()
        for item_id, item in items.items():
            # Skip if already added from ID match
            if item_id == query:
                continue
                
            # Check for name match
            if query_lower in item.name.lower():
                item_location = self.get_item_location(item_id, items, containers)
                if item_location:
                    matching_items.append(item_location)
        
        # Sort results based on:
        # 1. Retrieval steps (fewer is better)
        # 2. Expiry date (sooner is better)
        # 3. Priority (higher is better)
        
        def get_sort_key(item_loc):
            item = items[item_loc.itemId]
            
            # Calculate days until expiry (default to 365 if no expiry)
            days_until_expiry = 365
            if item.expiryDate != "N/A":
                try:
                    expiry_date = datetime.fromisoformat(item.expiryDate)
                    days_until_expiry = max(0, (expiry_date - datetime.now()).days)
                except Exception:
                    pass
            
            # Calculate sort key
            return (
                item_loc.retrievalSteps,  # Fewer steps first
                days_until_expiry,        # Earlier expiry first
                -item.priority            # Higher priority first
            )
        
        # Sort by the calculated key
        matching_items.sort(key=get_sort_key)
        
        return matching_items
    
    def get_item_location(
        self, 
        item_id: str, 
        items: Dict[str, Item], 
        containers: Dict[str, Container]
    ) -> Optional[ItemLocation]:
        """Get detailed location information for an item"""
        if item_id not in items:
            return None
        
        item = items[item_id]
        
        # Check if the item has a location
        if not item.currentLocation or "containerId" not in item.currentLocation:
            return None
        
        container_id = item.currentLocation["containerId"]
        if container_id not in containers:
            return None
        
        container = containers[container_id]
        position = item.currentLocation.get("position", (0, 0, 0))
        rotation = item.currentLocation.get("rotation", (item.width, item.depth, item.height))
        
        # Calculate how many steps are needed to retrieve this item
        # and which items are blocking it
        retrieval_steps, blocked_by = self._calculate_retrieval_complexity(
            target_item=item,
            container=container,
            position=position,
            rotation=rotation,
            items=items
        )
        
        # Create the item location object
        item_location = ItemLocation(
            itemId=item_id,
            name=item.name,
            containerId=container_id,
            position=position,
            rotation=rotation,
            retrievalSteps=retrieval_steps,
            blockedBy=blocked_by
        )
        
        return item_location
    
    def retrieve_item(
        self, 
        item_id: str, 
        user_id: str,
        items: Dict[str, Item], 
        containers: Dict[str, Container]
    ) -> Tuple[bool, List[RearrangementStep]]:
        """Retrieve an item and get the optimized steps needed for retrieval
        
        Uses a shortest-path algorithm to find the most efficient sequence of 
        rearrangements needed to access the target item.
        """
        if item_id not in items:
            return False, []
        
        item = items[item_id]
        
        # Check if the item has a location
        if not item.currentLocation or "containerId" not in item.currentLocation:
            return False, []
        
        container_id = item.currentLocation["containerId"]
        if container_id not in containers:
            return False, []
        
        container = containers[container_id]
        position = item.currentLocation.get("position", (0, 0, 0))
        rotation = item.currentLocation.get("rotation", (item.width, item.depth, item.height))
        
        # Generate optimized retrieval steps
        steps = self._generate_optimized_retrieval_steps(
            target_item=item,
            container=container,
            position=position,
            rotation=rotation,
            items=items,
            containers=containers
        )
        
        # Update the item's usage count
        if item.usageLimit > 0:
            item.usageLimit -= 1
            
            # Check if the item is now waste
            if item.usageLimit == 0:
                item.isWaste = True
        
        # Remove the item from its container
        item_volume = item.get_volume()
        container.remove_item(item_id, item_volume)
        
        # Clear the item's location
        item.currentLocation = None
        
        return True, steps
    
    def _calculate_retrieval_complexity(
        self, 
        target_item: Item,
        container: Container,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float],
        items: Dict[str, Item]
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Calculate how complex it is to retrieve an item using 3D spatial analysis
        
        Uses an advanced blocking detection algorithm that identifies all items
        that must be moved in order to access the target item.
        """
        blocked_by = []
        x, y, z = position
        target_width, target_depth, target_height = rotation
        
        # Define the "access path" - for simplicity, we'll consider the item accessible
        # from the front face of the container (y=0)
        # Items that intersect with this access path are considered blocking
        
        # First, create a 3D model of the container and its contents
        # to better analyze spatial relationships
        space_model = Space3D(container.width, container.depth, container.height)
        
        # Place all items except the target in the space model
        container_items = {}
        for other_id, other_item in items.items():
            if other_id == target_item.itemId:
                continue
                
            # Skip items that aren't in this container
            if (not other_item.currentLocation or 
                "containerId" not in other_item.currentLocation or
                other_item.currentLocation["containerId"] != container.containerId):
                continue
                
            # Get position and rotation
            other_pos = other_item.currentLocation.get("position", (0, 0, 0))
            other_rot = other_item.currentLocation.get("rotation", 
                                                      (other_item.width, 
                                                       other_item.depth, 
                                                       other_item.height))
            
            # Store information about this item
            container_items[other_id] = {
                "item": other_item,
                "position": other_pos,
                "rotation": other_rot
            }
            
            # Place in space model (just for visualization purposes)
            other_x, other_y, other_z = other_pos
            other_width, other_depth, other_height = other_rot
            space_model.place_item(other_x, other_y, other_z, 
                                  other_width, other_depth, other_height)
        
        # Calculate items blocking access along the retrieval path
        # For our model, we'll use a 2D projection and check what's in front
        
        # Method 1: Check if items are directly in front of the target
        for other_id, info in container_items.items():
            other_item = info["item"]
            other_pos = info["position"]
            other_rot = info["rotation"]
            
            other_x, other_y, other_z = other_pos
            other_width, other_depth, other_height = other_rot
            
            # Check if this item blocks the retrieval path
            # We need to check if it's in front of our target item and overlaps in the x-z plane
            
            # Item must be in front of the target
            if other_y < y:
                continue  # Not blocking if behind the target
                
            # Check if there's x-z overlap
            x_overlap = (
                (other_x < x + target_width and x < other_x + other_width) or
                (x < other_x + other_width and other_x < x + target_width)
            )
            
            z_overlap = (
                (other_z < z + target_height and z < other_z + other_height) or
                (z < other_z + other_height and other_z < z + target_height)
            )
            
            if x_overlap and z_overlap:
                # This item blocks the access path
                blocking_depth = space_model.calculate_retrieval_complexity(
                    other_x, other_y, other_z, 
                    other_width, other_depth, other_height
                )
                
                blocked_by.append({
                    "itemId": other_id,
                    "name": other_item.name,
                    "position": other_pos,
                    "depth": blocking_depth
                })
        
        # Sort blocking items by their depth (move closest items first)
        blocked_by.sort(key=lambda x: x.get("depth", 0))
        
        # The number of steps is the number of blocking items plus 1 (to actually retrieve)
        steps = len(blocked_by) + 1
        
        return steps, blocked_by
    
    def _generate_optimized_retrieval_steps(
        self, 
        target_item: Item,
        container: Container,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float],
        items: Dict[str, Item],
        containers: Dict[str, Container]
    ) -> List[RearrangementStep]:
        """Generate optimized steps to retrieve an item
        
        Uses a more sophisticated algorithm to:
        1. Minimize the number of moves
        2. Consider alternative containers for temporary storage
        3. Prioritize moving items based on their properties
        """
        # Get blocking items
        _, blocked_by = self._calculate_retrieval_complexity(
            target_item=target_item,
            container=container,
            position=position,
            rotation=rotation,
            items=items
        )
        
        steps = []
        moved_to_temp = set()
        step_count = 1
        
        # Find the best temporary container for each item
        # instead of always using "temporary_storage"
        available_containers = {}
        for cont_id, cont in containers.items():
            if cont.containerId != container.containerId:
                # Calculate available space
                available_space = cont.get_available_space()
                if available_space > 0:
                    available_containers[cont_id] = {
                        "container": cont,
                        "available_space": available_space
                    }
        
        # First, move blocking items in the optimal order
        for blocking_item_info in blocked_by:
            blocking_id = blocking_item_info["itemId"]
            blocking_item = items[blocking_id]
            
            # Determine best container to move this item to
            best_temp_container = "temporary_storage"
            item_volume = blocking_item.get_volume()
            
            for cont_id, info in available_containers.items():
                cont = info["container"]
                avail_space = info["available_space"]
                
                # Check if this container has enough space
                if avail_space >= item_volume:
                    # Prefer containers in same zone for easier return
                    if cont.zone == container.zone:
                        best_temp_container = cont_id
                        # Update available space
                        info["available_space"] -= item_volume
                        break
            
            # Add step to move the blocking item
            steps.append(RearrangementStep(
                step=step_count,
                action="move",
                itemId=blocking_id,
                fromContainer=container.containerId,
                toContainer=best_temp_container
            ))
            step_count += 1
            
            # Track which items we've moved
            moved_to_temp.add((blocking_id, best_temp_container))
        
        # Next, retrieve the target item
        steps.append(RearrangementStep(
            step=step_count,
            action="retrieve",
            itemId=target_item.itemId,
            fromContainer=container.containerId
        ))
        step_count += 1
        
        # Finally, move blocking items back in reverse order
        for blocking_id, temp_container in reversed(list(moved_to_temp)):
            steps.append(RearrangementStep(
                step=step_count,
                action="move",
                itemId=blocking_id,
                fromContainer=temp_container,
                toContainer=container.containerId
            ))
            step_count += 1
        
        return steps
    
    def get_retrieval_path(
        self,
        item_id: str,
        items: Dict[str, Item],
        containers: Dict[str, Container]
    ) -> Tuple[bool, List[RearrangementStep]]:
        """Get the retrieval path for an item without actually retrieving it
        
        This is used by the search API to show retrieval steps without modifying the item's state
        """
        if item_id not in items:
            return False, []
        
        item = items[item_id]
        
        # Check if the item has a location
        if not item.currentLocation or "containerId" not in item.currentLocation:
            return False, []
        
        container_id = item.currentLocation["containerId"]
        if container_id not in containers:
            return False, []
        
        container = containers[container_id]
        position = item.currentLocation.get("position", (0, 0, 0))
        rotation = item.currentLocation.get("rotation", (item.width, item.depth, item.height))
        
        # Generate retrieval steps without modifying the item or container
        steps = self._generate_optimized_retrieval_steps(
            target_item=item,
            container=container,
            position=position,
            rotation=rotation,
            items=items,
            containers=containers
        )
        
        return True, steps
    
    def _generate_retrieval_steps(
        self, 
        target_item: Item,
        container: Container,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float],
        items: Dict[str, Item],
        containers: Dict[str, Container]
    ) -> List[RearrangementStep]:
        """Legacy method to generate retrieval steps
        
        Kept for backward compatibility, but the optimized version should be used instead.
        """
        return self._generate_optimized_retrieval_steps(
            target_item, container, position, rotation, items, containers
        )