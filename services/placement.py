from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
from datetime import datetime
from utils.space3d import Space3D, FreeSpace

from models.item import Item
from models.container import Container
from models.placement import ItemPlacement, RearrangementStep, PlacementResponse

class PlacementService:
    """Service for optimal placement of items in containers using advanced bin packing algorithms"""
    
    def calculate_placement(
        self,
        items: Dict[str, Item],
        containers: Dict[str, Container]
    ) -> PlacementResponse:
        """Calculate optimal placement for items in containers
        
        Uses a weighted scoring system for prioritization and a modified
        Best-Fit-Decreasing algorithm with rotation strategies.
        """
        # Create container 3D space models to track used/free space
        container_spaces = {}
        for container_id, container in containers.items():
            container_spaces[container_id] = Space3D(
                container.width, 
                container.depth, 
                container.height
            )
            
        # Sort items by weighted importance score based on:
        # 1. Priority (highest first)
        # 2. Days until expiry (soonest expiry items first)
        # 3. Usage limit (items with fewer remaining uses first)
        # 4. Volume (larger items first for better packing efficiency)
        current_date = datetime.now()
        
        def get_weighted_score(item):
            # Calculate days until expiry 
            days_until_expiry = 365  # Default to a year if no expiry
            if item.expiryDate != "N/A":
                try:
                    expiry_date = datetime.fromisoformat(item.expiryDate)
                    days_until_expiry = max(0, (expiry_date - current_date).days)
                except Exception:
                    pass
            
            # Calculate weighted score based on research algorithm
            # score = priority * 2 - days_until_expiry + usage_limit * 1.5
            score = (
                item.priority * 2 - 
                min(100, days_until_expiry) + 
                min(100, item.usageLimit) * 0.5
            )
            return score
        
        # Sort items by weighted score (highest first)
        sorted_items = sorted(
            items.values(),
            key=lambda x: (
                -get_weighted_score(x),  # Negative to sort highest first
                -x.get_volume()  # Negative to sort largest first as tiebreaker
            )
        )
        
        # Track placements and rearrangements
        placements = []
        rearrangements = []
        placed_items = set()
        
        # Iterate through items in priority order
        for item in sorted_items:
            # Skip items that already have a location
            if item.currentLocation is not None and "containerId" in item.currentLocation:
                continue
                
            # Find best container and placement
            best_container = None
            best_position = None
            best_rotation = None
            best_score = float('-inf')
            best_space_model = None
            
            # Get all possible rotations for this item
            rotations = item.get_all_rotations()
            
            # Try each container
            for container_id, container in containers.items():
                # Skip full containers
                if container.is_full():
                    continue
                
                # Calculate base score with zone preference
                preferred_zone_match = (container.zone == item.preferredZone)
                base_score = 1000 if preferred_zone_match else 0
                
                # Get container space model
                space_model = container_spaces[container_id]
                
                # Try each rotation
                for rotation in rotations:
                    width, depth, height = rotation
                    
                    # Skip if dimensions don't fit in container
                    if (width > container.width or
                        depth > container.depth or
                        height > container.height):
                        continue
                    
                    # Find best position for this rotation using Space3D model
                    position = space_model.find_position(width, depth, height)
                    if position is None:
                        continue  # No valid position found for this rotation
                    
                    # Calculate score for this position
                    # Priority affects depth placement (higher priority = closer to front)
                    # Score formula based on priority, zone match, and retrieval complexity
                    x, y, z = position
                    
                    # Calculate retrieval complexity (higher is worse)
                    retrieval_complexity = space_model.calculate_retrieval_complexity(
                        x, y, z, width, depth, height
                    )
                    
                    # Calculate final position score
                    position_score = (
                        base_score +
                        500 * (item.priority / 100) -
                        retrieval_complexity * 50  # Penalty for difficult retrieval
                    )
                    
                    # Update best score
                    if position_score > best_score:
                        best_score = position_score
                        best_container = container
                        best_position = position
                        best_rotation = rotation
                        best_space_model = space_model
            
            # If we found a valid placement, place the item
            if best_container is not None and best_position is not None and best_rotation is not None and best_space_model is not None:
                # Add item to the placement plan
                placement = ItemPlacement(
                    itemId=item.itemId,
                    containerId=best_container.containerId,
                    position=best_position,
                    rotation=best_rotation
                )
                placements.append(placement)
                
                # Update 3D space model
                width, depth, height = best_rotation
                x, y, z = best_position
                best_space_model.place_item(x, y, z, width, depth, height)
                
                # Update container
                best_container.add_item(item.itemId, item.get_volume())
                
                # Update item location
                if item.currentLocation is None:
                    item.currentLocation = {}
                item.currentLocation["containerId"] = best_container.containerId
                item.currentLocation["position"] = best_position
                item.currentLocation["rotation"] = best_rotation
                
                # Mark item as placed
                placed_items.add(item.itemId)
        
        # Handle unplaced items with rearrangement recommendations
        unplaced_items = [item for item in sorted_items 
                         if item.itemId not in placed_items and
                            (item.currentLocation is None or 
                             "containerId" not in item.currentLocation)]
        
        if unplaced_items:
            # Generate rearrangement plan for high-priority unplaced items
            rearrangements = self._generate_rearrangement_plan(
                unplaced_items,
                items,
                containers,
                container_spaces
            )
        
        # Return the placement plan
        return PlacementResponse(
            placements=placements,
            rearrangements=rearrangements
        )
    
    def _generate_rearrangement_plan(
        self,
        unplaced_items: List[Item],
        all_items: Dict[str, Item],
        containers: Dict[str, Container],
        container_spaces: Dict[str, Space3D]
    ) -> List[RearrangementStep]:
        """Generate a rearrangement plan to make space for unplaced high-priority items"""
        rearrangement_steps = []
        step_count = 1
        
        # Focus on high-priority unplaced items first (up to 5)
        high_priority_unplaced = sorted(
            unplaced_items,
            key=lambda x: -x.priority
        )[:5]
        
        # For each priority item that couldn't be placed
        for target_item in high_priority_unplaced:
            preferred_zone = target_item.preferredZone
            
            # Find low-priority items in the preferred zone
            low_priority_candidates = []
            
            # Search all containers in the preferred zone
            for container_id, container in containers.items():
                if container.zone != preferred_zone:
                    continue
                    
                # Find items in this container
                for item_id in container.items:
                    if item_id in all_items:
                        item = all_items[item_id]
                        # Add to candidates if lower priority than our target
                        if item.priority < target_item.priority:
                            # Calculate a "value density" score (priority per volume)
                            # Lower is better to move
                            value_density = item.priority / max(0.1, item.get_volume())
                            low_priority_candidates.append({
                                'item': item,
                                'container': container,
                                'value_density': value_density
                            })
            
            # Sort candidates by value density (lower first)
            low_priority_candidates.sort(key=lambda x: x['value_density'])
            
            # Move items until we free enough space
            target_volume = target_item.get_volume()
            moved_volume = 0
            
            for candidate in low_priority_candidates:
                item = candidate['item']
                container = candidate['container']
                
                # Skip if we've freed enough space
                if moved_volume >= target_volume:
                    break
                    
                # Add rearrangement step
                rearrangements = []
                
                # Find alternative container for this item (not in preferred zone)
                best_alt_container = None
                
                for alt_container_id, alt_container in containers.items():
                    # Skip containers in the same zone or if full
                    if (alt_container.zone == preferred_zone or 
                        alt_container.is_full() or
                        item.get_volume() > alt_container.get_available_space()):
                        continue
                        
                    # This is a viable alternative
                    best_alt_container = alt_container
                    break
                
                # If we found an alternative container, move the item
                if best_alt_container:
                    rearrangement_steps.append(
                        RearrangementStep(
                            step=step_count,
                            action="move",
                            itemId=item.itemId,
                            fromContainer=container.containerId,
                            toContainer=best_alt_container.containerId
                        )
                    )
                    step_count += 1
                    
                    # Track the volume we've moved
                    moved_volume += item.get_volume()
                else:
                    # No alternative container, try temporary storage
                    rearrangement_steps.append(
                        RearrangementStep(
                            step=step_count,
                            action="move",
                            itemId=item.itemId,
                            fromContainer=container.containerId,
                            toContainer="temporary_storage"
                        )
                    )
                    step_count += 1
                    
                    # Track the volume we've moved
                    moved_volume += item.get_volume()
            
            # Add step to place the target item
            if moved_volume >= target_volume:
                preferred_containers = [c for c_id, c in containers.items() 
                                      if c.zone == preferred_zone]
                if preferred_containers:
                    # Add placement step
                    rearrangement_steps.append(
                        RearrangementStep(
                            step=step_count,
                            action="place",
                            itemId=target_item.itemId,
                            toContainer=preferred_containers[0].containerId
                        )
                    )
                    step_count += 1
        
        return rearrangement_steps
    
    def _find_best_position(
        self,
        item: Item,
        container: Container
    ) -> Tuple[Optional[Tuple[float, float, float]], Optional[Tuple[float, float, float]]]:
        """Legacy method for finding the best position and rotation for an item in a container
        
        Note: This is kept for backward compatibility but the main calculate_placement
        method now uses the Space3D model directly.
        """
        # Create a space model for this container
        space_model = Space3D(container.width, container.depth, container.height)
        
        # Get all possible rotations
        rotations = item.get_all_rotations()
        
        # Try each rotation
        for rotation in rotations:
            width, depth, height = rotation
            
            # Skip if dimensions don't fit in container
            if (width > container.width or
                depth > container.depth or
                height > container.height):
                continue
            
            # Find position for this rotation
            position = space_model.find_position(width, depth, height)
            if position:
                return position, rotation
        
        # No valid position found
        return None, None