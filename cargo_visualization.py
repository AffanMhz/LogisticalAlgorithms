import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pandas as pd
from datetime import datetime, timedelta
import random
import json

class CargoVisualizer:
    def __init__(self):
        self.containers = {}  # Dictionary to store containers by container_id
        self.items = {}  # Dictionary to store items by item_id
        self.placements = {}  # Dictionary to store item placements {item_id: (container_id, position)}
        self.current_date = datetime.now()
        
    def load_containers_from_csv(self, csv_file):
        """Load containers from a CSV file"""
        try:
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                container_id = row['Container ID']
                zone = row['Zone']
                width = row['Width(cm)']
                depth = row['Depth(cm)']
                height = row['Height(cm)']
                
                self.add_container(container_id, zone, width, depth, height)
            
            print(f"Loaded {len(df)} containers from {csv_file}")
            return True
        except Exception as e:
            print(f"Error loading containers: {e}")
            return False
    
    def load_items_from_csv(self, csv_file):
        """Load items from a CSV file"""
        try:
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                item_id = row['Item ID']
                name = row['Name']
                width = row['Width(cm)']
                depth = row['Depth(cm)']
                height = row['Height(cm)']
                mass = row['Mass(kg)']
                priority = row['Priority(1-100)']
                
                # Handle expiry date (might be N/A)
                expiry_date = None
                if isinstance(row['Expiry Date(ISO Format)'], str) and row['Expiry Date(ISO Format)'] != 'N/A':
                    expiry_date = row['Expiry Date(ISO Format)']
                
                usage_limit = row['Usage Limit']
                preferred_zone = row['Preferred Zone']
                
                self.add_item(item_id, name, width, depth, height, mass, priority, expiry_date, usage_limit, preferred_zone)
            
            print(f"Loaded {len(df)} items from {csv_file}")
            return True
        except Exception as e:
            print(f"Error loading items: {e}")
            return False
    
    def add_container(self, container_id, zone, width, depth, height):
        """Add a container to the system"""
        self.containers[container_id] = {
            'zone': zone,
            'width': width,
            'depth': depth,
            'height': height,
            'occupied_space': np.zeros((width, depth, height), dtype=bool)  # 3D array to track occupied space
        }
        return True
    
    def add_item(self, item_id, name, width, depth, height, mass, priority, expiry_date, usage_limit, preferred_zone):
        """Add an item to the system"""
        self.items[item_id] = {
            'name': name,
            'width': width,
            'depth': depth,
            'height': height,
            'mass': mass,
            'priority': priority,
            'expiry_date': expiry_date,
            'usage_limit': usage_limit,
            'remaining_uses': usage_limit,
            'preferred_zone': preferred_zone,
            'is_waste': False
        }
        return True
    
    def is_position_valid(self, container_id, start_coords, item_dims):
        """Check if an item can be placed at the given position"""
        if container_id not in self.containers:
            return False
        
        container = self.containers[container_id]
        w_start, d_start, h_start = start_coords
        w_size, d_size, h_size = item_dims
        
        # Check if item fits within container bounds
        if (w_start + w_size > container['width'] or
            d_start + d_size > container['depth'] or
            h_start + h_size > container['height']):
            return False
        
        # Check if space is already occupied
        occupied_space = container['occupied_space']
        
        # Check if the entire space needed for the item is free
        item_space = occupied_space[w_start:w_start+w_size, 
                                   d_start:d_start+d_size, 
                                   h_start:h_start+h_size]
        
        if np.any(item_space):
            # Space is already occupied
            return False
        
        return True
    
    def place_item(self, item_id, container_id, start_coords):
        """Place an item in a container at specified position"""
        if item_id not in self.items or container_id not in self.containers:
            return False
        
        item = self.items[item_id]
        item_dims = (item['width'], item['depth'], item['height'])
        
        if not self.is_position_valid(container_id, start_coords, item_dims):
            return False
        
        # Mark space as occupied
        w_start, d_start, h_start = start_coords
        w_size, d_size, h_size = item_dims
        
        container = self.containers[container_id]
        container['occupied_space'][w_start:w_start+w_size, 
                                   d_start:d_start+d_size, 
                                   h_start:h_start+h_size] = True
        
        # Store placement
        end_coords = (w_start + w_size, d_start + d_size, h_start + h_size)
        self.placements[item_id] = {
            'container_id': container_id,
            'position': {
                'startCoordinates': {
                    'width': w_start,
                    'depth': d_start,
                    'height': h_start
                },
                'endCoordinates': {
                    'width': end_coords[0],
                    'depth': end_coords[1],
                    'height': end_coords[2]
                }
            }
        }
        
        return True
    
    def retrieve_item_steps(self, item_id):
        """Calculate steps needed to retrieve an item"""
        if item_id not in self.placements:
            return None, []
        
        placement = self.placements[item_id]
        container_id = placement['container_id']
        container = self.containers[container_id]
        
        # Get item position
        start = placement['position']['startCoordinates']
        end = placement['position']['endCoordinates']
        
        # We need to check if items are blocking the path to the open face
        # For simplicity, we'll assume the open face is at depth=0
        
        # Items to be temporarily removed (blocking items)
        blocking_items = []
        
        # Check for each item if it's blocking the path
        for other_id, other_placement in self.placements.items():
            if other_id == item_id or other_placement['container_id'] != container_id:
                continue
                
            other_start = other_placement['position']['startCoordinates']
            other_end = other_placement['position']['endCoordinates']
            
            # Check if item is in the way (blocking the direct path to the open face)
            # This is a simplified check - in reality this would be more complex
            if (other_start['depth'] < start['depth'] and
                other_end['width'] > start['width'] and other_start['width'] < end['width'] and
                other_end['height'] > start['height'] and other_start['height'] < end['height']):
                blocking_items.append({
                    'itemId': other_id,
                    'itemName': self.items[other_id]['name']
                })
        
        # Generate retrieval steps
        retrieval_steps = []
        
        # First remove blocking items
        for i, blocking_item in enumerate(blocking_items):
            retrieval_steps.append({
                'step': i + 1,
                'action': 'remove',
                'itemId': blocking_item['itemId'],
                'itemName': blocking_item['itemName']
            })
        
        # Next retrieve target item
        step = len(blocking_items) + 1
        retrieval_steps.append({
            'step': step,
            'action': 'retrieve',
            'itemId': item_id,
            'itemName': self.items[item_id]['name']
        })
        
        # Finally place back blocking items in reverse order
        for i, blocking_item in enumerate(reversed(blocking_items)):
            retrieval_steps.append({
                'step': step + i + 1,
                'action': 'placeBack',
                'itemId': blocking_item['itemId'],
                'itemName': blocking_item['itemName']
            })
        
        return len(blocking_items), retrieval_steps
    
    def find_placement_for_item(self, item_id, containers=None):
        """
        Find optimal placement for an item
        This is where your placement algorithm would go
        """
        if item_id not in self.items:
            return None
        
        item = self.items[item_id]
        
        # If no containers specified, use all containers
        if containers is None:
            containers = list(self.containers.keys())
        
        # Sort containers: First by preferred zone, then by space availability
        preferred_containers = []
        other_containers = []
        
        for container_id in containers:
            if container_id not in self.containers:
                continue
                
            container = self.containers[container_id]
            
            # Check if container is in preferred zone
            if container['zone'] == item['preferred_zone']:
                preferred_containers.append(container_id)
            else:
                other_containers.append(container_id)
        
        # Try containers in order of preference
        all_containers = preferred_containers + other_containers
        
        for container_id in all_containers:
            container = self.containers[container_id]
            
            # Simple strategy: place item at the first available position 
            # where we can minimize steps for retrieval (front of container)
            w, d, h = item['width'], item['depth'], item['height']
            
            # Try to place near the open face (assuming depth=0 is the open face)
            for h_start in range(container['height'] - h + 1):
                for w_start in range(container['width'] - w + 1):
                    # Try to place as close to open face as possible
                    d_start = 0
                    
                    # Check if this position is valid
                    if self.is_position_valid(container_id, (w_start, d_start, h_start), (w, d, h)):
                        return {
                            'container_id': container_id,
                            'position': {
                                'startCoordinates': {
                                    'width': w_start,
                                    'depth': d_start,
                                    'height': h_start
                                },
                                'endCoordinates': {
                                    'width': w_start + w,
                                    'depth': d_start + d,
                                    'height': h_start + h
                                }
                            }
                        }
            
            # If no position found at depth=0, try other depths
            for d_start in range(1, container['depth'] - d + 1):
                for h_start in range(container['height'] - h + 1):
                    for w_start in range(container['width'] - w + 1):
                        
                        # Check if this position is valid
                        if self.is_position_valid(container_id, (w_start, d_start, h_start), (w, d, h)):
                            return {
                                'container_id': container_id,
                                'position': {
                                    'startCoordinates': {
                                        'width': w_start,
                                        'depth': d_start,
                                        'height': h_start
                                    },
                                    'endCoordinates': {
                                        'width': w_start + w,
                                        'depth': d_start + d,
                                        'height': h_start + h
                                    }
                                }
                            }
        
        # No valid position found
        return None
    
    def optimize_placement(self, items=None):
        """
        Find optimal placement for multiple items
        This is a simplified algorithm - your real algorithm would be more sophisticated
        """
        if items is None:
            # Use all items that aren't placed yet
            items = [item_id for item_id in self.items 
                    if item_id not in self.placements and not self.items[item_id]['is_waste']]
        
        # Sort items by priority (higher priority first)
        sorted_items = sorted(items, key=lambda item_id: -self.items[item_id]['priority'])
        
        successful_placements = []
        unsuccessful_items = []
        
        for item_id in sorted_items:
            placement = self.find_placement_for_item(item_id)
            
            if placement:
                container_id = placement['container_id']
                start_coords = (
                    placement['position']['startCoordinates']['width'],
                    placement['position']['startCoordinates']['depth'],
                    placement['position']['startCoordinates']['height']
                )
                
                # Try to place the item
                if self.place_item(item_id, container_id, start_coords):
                    successful_placements.append({
                        'itemId': item_id,
                        'containerId': container_id,
                        'position': placement['position']
                    })
                else:
                    unsuccessful_items.append(item_id)
            else:
                unsuccessful_items.append(item_id)
        
        return {
            'success': len(unsuccessful_items) == 0,
            'placements': successful_placements,
            'unplaced_items': unsuccessful_items
        }
    
    def identify_waste_items(self):
        """Identify items that are expired or out of uses"""
        waste_items = []
        
        for item_id, item in self.items.items():
            is_waste = False
            reason = ""
            
            # Check if item is out of uses
            if item['remaining_uses'] <= 0:
                is_waste = True
                reason = "Out of Uses"
            
            # Check if item is expired
            elif item['expiry_date'] and datetime.fromisoformat(item['expiry_date']) <= self.current_date:
                is_waste = True
                reason = "Expired"
            
            if is_waste and not item['is_waste']:
                # Mark item as waste
                self.items[item_id]['is_waste'] = True
                
                # Add to waste items list
                if item_id in self.placements:
                    placement = self.placements[item_id]
                    waste_items.append({
                        'itemId': item_id,
                        'name': item['name'],
                        'reason': reason,
                        'containerId': placement['container_id'],
                        'position': placement['position']
                    })
                else:
                    waste_items.append({
                        'itemId': item_id,
                        'name': item['name'],
                        'reason': reason,
                        'containerId': None,
                        'position': None
                    })
        
        return waste_items
    
    def simulate_days(self, num_days, items_to_use=None):
        """Simulate the passage of days and usage of items"""
        changes = {
            'itemsUsed': [],
            'itemsExpired': [],
            'itemsDepletedToday': []
        }
        
        # Update current date
        new_date = self.current_date + timedelta(days=num_days)
        
        # Simulate item usage if specified
        if items_to_use:
            for item_info in items_to_use:
                item_id = item_info.get('itemId')
                name = item_info.get('name')
                
                # Find item by ID or name
                found_item_id = None
                if item_id and item_id in self.items:
                    found_item_id = item_id
                elif name:
                    # Search by name
                    for id, item in self.items.items():
                        if item['name'] == name:
                            found_item_id = id
                            break
                
                if found_item_id:
                    # Use the item once
                    item = self.items[found_item_id]
                    if item['remaining_uses'] > 0:
                        item['remaining_uses'] -= 1
                        changes['itemsUsed'].append({
                            'itemId': found_item_id,
                            'name': item['name'],
                            'remainingUses': item['remaining_uses']
                        })
                        
                        # Check if item is now depleted
                        if item['remaining_uses'] == 0:
                            changes['itemsDepletedToday'].append({
                                'itemId': found_item_id,
                                'name': item['name']
                            })
        
        # Check for newly expired items
        for item_id, item in self.items.items():
            if item['expiry_date'] and not item['is_waste']:
                expiry_date = datetime.fromisoformat(item['expiry_date'])
                if expiry_date <= new_date and expiry_date > self.current_date:
                    changes['itemsExpired'].append({
                        'itemId': item_id,
                        'name': item['name']
                    })
        
        # Update the current date
        self.current_date = new_date
        
        # Identify waste items
        self.identify_waste_items()
        
        return {
            'success': True,
            'newDate': self.current_date.isoformat(),
            'changes': changes
        }
    
    def visualize_container(self, container_id):
        """Visualize a container and its contents in 3D"""
        if container_id not in self.containers:
            print(f"Container {container_id} not found")
            return
        
        container = self.containers[container_id]
        
        # Create figure
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot container boundaries
        container_w = container['width']
        container_d = container['depth']
        container_h = container['height']
        
        # Create container wireframe
        x = [0, container_w, container_w, 0, 0, container_w, container_w, 0]
        y = [0, 0, container_d, container_d, 0, 0, container_d, container_d]
        z = [0, 0, 0, 0, container_h, container_h, container_h, container_h]
        
        # List of container edges to draw
        verts = [
            [x[0], y[0], z[0]], [x[1], y[1], z[1]], [x[2], y[2], z[2]], [x[3], y[3], z[3]],  # Bottom face
            [x[4], y[4], z[4]], [x[5], y[5], z[5]], [x[6], y[6], z[6]], [x[7], y[7], z[7]],  # Top face
            [x[0], y[0], z[0]], [x[4], y[4], z[4]],  # Front left vertical edge
            [x[1], y[1], z[1]], [x[5], y[5], z[5]],  # Front right vertical edge
            [x[2], y[2], z[2]], [x[6], y[6], z[6]],  # Back right vertical edge
            [x[3], y[3], z[3]], [x[7], y[7], z[7]]   # Back left vertical edge
        ]
        
        # Plot container edges
        ax.plot([x[0], x[1], x[2], x[3], x[0]], [y[0], y[1], y[2], y[3], y[0]], [z[0], z[1], z[2], z[3], z[0]], 'k-', alpha=0.3)  # Bottom
        ax.plot([x[4], x[5], x[6], x[7], x[4]], [y[4], y[5], y[6], y[7], y[4]], [z[4], z[5], z[6], z[7], z[4]], 'k-', alpha=0.3)  # Top
        ax.plot([x[0], x[4]], [y[0], y[4]], [z[0], z[4]], 'k-', alpha=0.3)  # Vertical edges
        ax.plot([x[1], x[5]], [y[1], y[5]], [z[1], z[5]], 'k-', alpha=0.3)
        ax.plot([x[2], x[6]], [y[2], y[6]], [z[2], z[6]], 'k-', alpha=0.3)
        ax.plot([x[3], x[7]], [y[3], y[7]], [z[3], z[7]], 'k-', alpha=0.3)
        
        # Plot items in the container
        for item_id, placement in self.placements.items():
            if placement['container_id'] != container_id:
                continue
                
            item = self.items[item_id]
            start = placement['position']['startCoordinates']
            end = placement['position']['endCoordinates']
            
            # Create cuboid for the item
            x = [start['width'], end['width'], end['width'], start['width'], start['width'], end['width'], end['width'], start['width']]
            y = [start['depth'], start['depth'], end['depth'], end['depth'], start['depth'], start['depth'], end['depth'], end['depth']]
            z = [start['height'], start['height'], start['height'], start['height'], end['height'], end['height'], end['height'], end['height']]
            
            # Define cuboid faces
            verts = [
                [
                    (x[0], y[0], z[0]),
                    (x[1], y[1], z[1]),
                    (x[5], y[5], z[5]),
                    (x[4], y[4], z[4])
                ],  # Front face
                [
                    (x[2], y[2], z[2]),
                    (x[3], y[3], z[3]),
                    (x[7], y[7], z[7]),
                    (x[6], y[6], z[6])
                ],  # Back face
                [
                    (x[0], y[0], z[0]),
                    (x[3], y[3], z[3]),
                    (x[7], y[7], z[7]),
                    (x[4], y[4], z[4])
                ],  # Left face
                [
                    (x[1], y[1], z[1]),
                    (x[2], y[2], z[2]),
                    (x[6], y[6], z[6]),
                    (x[5], y[5], z[5])
                ],  # Right face
                [
                    (x[0], y[0], z[0]),
                    (x[1], y[1], z[1]),
                    (x[2], y[2], z[2]),
                    (x[3], y[3], z[3])
                ],  # Bottom face
                [
                    (x[4], y[4], z[4]),
                    (x[5], y[5], z[5]),
                    (x[6], y[6], z[6]),
                    (x[7], y[7], z[7])
                ]   # Top face
            ]
            
            # Determine color based on item properties
            if item['is_waste']:
                # Red for waste items
                color = 'red'
                alpha = 0.7
            else:
                # Use priority to determine color (higher priority = more intense color)
                priority_normalized = item['priority'] / 100.0
                # Blue color with intensity based on priority
                color = (0.1, 0.1, 0.5 + 0.5 * priority_normalized)
                alpha = 0.7
            
            # Plot the cuboid
            poly = Poly3DCollection(verts, alpha=alpha)
            poly.set_facecolor(color)
            ax.add_collection3d(poly)
            
            # Add text label for the item
            # Mid point of the item
            text_x = (start['width'] + end['width']) / 2
            text_y = (start['depth'] + end['depth']) / 2
            text_z = (start['height'] + end['height']) / 2
            ax.text(text_x, text_y, text_z, item_id, fontsize=8)
        
        # Set labels and title
        ax.set_xlabel('Width')
        ax.set_ylabel('Depth')
        ax.set_zlabel('Height')
        ax.set_title(f'Container {container_id} ({container["zone"]})')
        
        # Set axis limits
        ax.set_xlim([0, container_w])
        ax.set_ylim([0, container_d])
        ax.set_zlim([0, container_h])
        
        # Display the plot
        plt.tight_layout()
        plt.show()
    
    def visualize_all_containers(self):
        """Visualize all containers in a grid layout"""
        num_containers = len(self.containers)
        if num_containers == 0:
            print("No containers to visualize")
            return
        
        # Determine grid layout
        cols = min(3, num_containers)  # Maximum 3 columns
        rows = (num_containers + cols - 1) // cols  # Ceiling division
        
        fig = plt.figure(figsize=(6*cols, 5*rows))
        
        for i, container_id in enumerate(self.containers):
            container = self.containers[container_id]
            
            # Create subplot
            ax = fig.add_subplot(rows, cols, i+1, projection='3d')
            
            # Plot container boundaries
            container_w = container['width']
            container_d = container['depth']
            container_h = container['height']
            
            # Create container wireframe (same as in visualize_container)
            x = [0, container_w, container_w, 0, 0, container_w, container_w, 0]
            y = [0, 0, container_d, container_d, 0, 0, container_d, container_d]
            z = [0, 0, 0, 0, container_h, container_h, container_h, container_h]
            
            # Plot container edges
            ax.plot([x[0], x[1], x[2], x[3], x[0]], [y[0], y[1], y[2], y[3], y[0]], [z[0], z[1], z[2], z[3], z[0]], 'k-', alpha=0.3)  # Bottom
            ax.plot([x[4], x[5], x[6], x[7], x[4]], [y[4], y[5], y[6], y[7], y[4]], [z[4], z[5], z[6], z[7], z[4]], 'k-', alpha=0.3)  # Top
            ax.plot([x[0], x[4]], [y[0], y[4]], [z[0], z[4]], 'k-', alpha=0.3)  # Vertical edges
            ax.plot([x[1], x[5]], [y[1], y[5]], [z[1], z[5]], 'k-', alpha=0.3)
            ax.plot([x[2], x[6]], [y[2], y[6]], [z[2], z[6]], 'k-', alpha=0.3)
            ax.plot([x[3], x[7]], [y[3], y[7]], [z[3], z[7]], 'k-', alpha=0.3)
            
            # Plot items in the container (same as in visualize_container)
            for item_id, placement in self.placements.items():
                if placement['container_id'] != container_id:
                    continue
                    
                item = self.items[item_id]
                start = placement['position']['startCoordinates']
                end = placement['position']['endCoordinates']
                
                # Create cuboid for the item
                x = [start['width'], end['width'], end['width'], start['width'], start['width'], end['width'], end['width'], start['width']]
                y = [start['depth'], start['depth'], end['depth'], end['depth'], start['depth'], start['depth'], end['depth'], end['depth']]
                z = [start['height'], start['height'], start['height'], start['height'], end['height'], end['height'], end['height'], end['height']]
                
                # Define cuboid faces
                verts = [
                    [
                        (x[0], y[0], z[0]),
                        (x[1], y[1], z[1]),
                        (x[5], y[5], z[5]),
                        (x[4], y[4], z[4])
                    ],  # Front face
                    [
                        (x[2], y[2], z[2]),
                        (x[3], y[3], z[3]),
                        (x[7], y[7], z[7]),
                        (x[6], y[6], z[6])
                    ],  # Back face
                    [
                        (x[0], y[0], z[0]),
                        (x[3], y[3], z[3]),
                        (x[7], y[7], z[7]),
                        (x[4], y[4], z[4])
                    ],  # Left face
                    [
                        (x[1], y[1], z[1]),
                        (x[2], y[2], z[2]),
                        (x[6], y[6], z[6]),
                        (x[5], y[5], z[5])
                    ],  # Right face
                    [
                        (x[0], y[0], z[0]),
                        (x[1], y[1], z[1]),
                        (x[2], y[2], z[2]),
                        (x[3], y[3], z[3])
                    ],  # Bottom face
                    [   
                        (x[4], y[4], z[4]),
                        (x[5], y[5], z[5]),
                        (x[6], y[6], z[6]),
                        (x[7], y[7], z[7])
                    ]   # Top face
                ]
                
                # Determine color based on item properties
                if item['is_waste']:
                    # Red for waste items
                    color = 'red'
                    alpha = 0.7
                else:
                    # Use priority to determine color (higher priority = more intense color)
                    priority_normalized = item['priority'] / 100.0
                    # Blue color with intensity based on priority
                    color = (0.1, 0.1, 0.5 + 0.5 * priority_normalized)
                    alpha = 0.7
                
                # Plot the cuboid
                poly = Poly3DCollection(verts, alpha=alpha)
                poly.set_facecolor(color)
                ax.add_collection3d(poly)
                
                # Add text label for the item (simplified for grid view)
                text_x = (start['width'] + end['width']) / 2
                text_y = (start['depth'] + end['depth']) / 2
                text_z = (start['height'] + end['height']) / 2
                ax.text(text_x, text_y, text_z, item_id, fontsize=7)
            
            # Set labels and title
            ax.set_xlabel('Width')
            ax.set_ylabel('Depth')
            ax.set_zlabel('Height')
            ax.set_title(f'{container_id} ({container["zone"]})')
            
            # Set axis limits
            ax.set_xlim([0, container_w])
            ax.set_ylim([0, container_d])
            ax.set_zlim([0, container_h])
        
        plt.tight_layout()
        plt.show()
    
    def generate_sample_data(self, num_containers=3, num_items=10):
        """Generate sample data for testing"""
        # Clear existing data
        self.containers = {}
        self.items = {}
        self.placements = {}
        
        # Generate containers
        zones = ['Crew Quarters', 'Airlock', 'Laboratory', 'Storage', 'Medical Bay']
        for i in range(num_containers):
            container_id = f'cont{chr(65+i)}'  # contA, contB, etc.
            zone = zones[i % len(zones)]
            width = random.randint(50, 200)
            depth = random.randint(50, 100)
            height = random.randint(100, 250)
            
            self.add_container(container_id, zone, width, depth, height)
        
        # Generate items
        item_names = ['Food Packet', 'Oxygen Cylinder', 'First Aid Kit', 'Tool Box', 
                      'Experimental Sample', 'Water Container', 'Spare Parts', 
                      'Scientific Instrument', 'Medicine Box', 'Equipment Kit']
        
        for i in range(num_items):
            item_id = f'{i+1:03d}'  # 001, 002, etc.
            name = item_names[i % len(item_names)]
            width = random.randint(10, 30)
            depth = random.randint(10, 30)
            height = random.randint(10, 50)
            mass = random.randint(1, 50)
            priority = random.randint(1, 100)
            
            # 50% chance of having expiry date
            if random.random() < 0.5:
                expiry_days = random.randint(10, 365)
                expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d')
            else:
                expiry_date = None
            
            usage_limit = random.randint(1, 100)
            preferred_zone = zones[random.randint(0, len(zones)-1)]
            
            self.add_item(item_id, name, width, depth, height, mass, priority, expiry_date, usage_limit, preferred_zone)
        
        print(f"Generated {num_containers} containers and {num_items} items")
        return True
    
    def run_algorithm_test(self, algorithm_name, verbose=True):
        """Run a test of the specified algorithm and evaluate its performance"""
        if algorithm_name == "placement":
            # Test the placement algorithm
            start_time = datetime.now()
            result = self.optimize_placement()
            end_time = datetime.now()
            
            execution_time = (end_time - start_time).total_seconds()
            
            # Calculate metrics
            total_items = len(self.items)
            placed_items = len(result['placements'])
            success_rate = placed_items / total_items if total_items > 0 else 0
            
            # Evaluate priority efficiency
            priority_scores = []
            for placement in result['placements']:
                item_id = placement['itemId']
                item = self.items[item_id]
                container_id = placement['containerId']
                container = self.containers[container_id]
                
                # Calculate priority score - higher is better
                priority_score = item['priority']
                
                # Bonus if item is in preferred zone
                if container['zone'] == item['preferred_zone']:
                    priority_score += 20
                
                priority_scores.append(priority_score)
            
            avg_priority_score = sum(priority_scores) / len(priority_scores) if priority_scores else 0
            
            # Print results
            if verbose:
                print(f"\n--- Placement Algorithm Test Results ---")
                print(f"Total items: {total_items}")
                print(f"Successfully placed: {placed_items}")
                print(f"Success rate: {success_rate:.2%}")
                print(f"Average priority score: {avg_priority_score:.2f}/120")
                print(f"Execution time: {execution_time:.6f} seconds")
                
                if result['unplaced_items']:
                    print(f"Unplaced items: {result['unplaced_items']}")
            
            return {
                'algorithm': algorithm_name,
                'success_rate': success_rate,
                'avg_priority_score': avg_priority_score,
                'execution_time': execution_time
            }
            
        elif algorithm_name == "retrieval":
            # Test retrieval algorithm for all placed items
            retrieval_steps = []
            execution_times = []
            
            for item_id in self.placements:
                start_time = datetime.now()
                steps, _ = self.retrieve_item_steps(item_id)
                end_time = datetime.now()
                
                retrieval_steps.append(steps)
                execution_times.append((end_time - start_time).total_seconds())
            
            avg_steps = sum(retrieval_steps) / len(retrieval_steps) if retrieval_steps else 0
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            if verbose:
                print(f"\n--- Retrieval Algorithm Test Results ---")
                print(f"Items tested: {len(retrieval_steps)}")
                print(f"Average retrieval steps: {avg_steps:.2f}")
                print(f"Average execution time: {avg_execution_time:.6f} seconds")
            
            return {
                'algorithm': algorithm_name,
                'avg_steps': avg_steps,
                'avg_execution_time': avg_execution_time
            }
            
        else:
            print(f"Unknown algorithm: {algorithm_name}")
            return None
    
    def evaluate_all_algorithms(self):
        """Run all algorithm tests and compare results"""
        results = {}
        
        # Test placement algorithm
        results['placement'] = self.run_algorithm_test("placement", verbose=False)
        
        # Test retrieval algorithm
        results['retrieval'] = self.run_algorithm_test("retrieval", verbose=False)
        
        # Print comparison
        print("\n===== Algorithm Evaluation Results =====")
        
        print("\nPlacement Algorithm:")
        print(f"Success rate: {results['placement']['success_rate']:.2%}")
        print(f"Average priority score: {results['placement']['avg_priority_score']:.2f}/120")
        print(f"Execution time: {results['placement']['execution_time']:.6f} seconds")
        
        print("\nRetrieval Algorithm:")
        print(f"Average retrieval steps: {results['retrieval']['avg_steps']:.2f}")
        print(f"Average execution time: {results['retrieval']['avg_execution_time']:.6f} seconds")
        
        return results
    
    def run_comprehensive_test(self, iterations=5):
        """Run multiple tests with different random data to get comprehensive results"""
        placement_success_rates = []
        placement_priority_scores = []
        placement_times = []
        
        retrieval_steps = []
        retrieval_times = []
        
        for i in range(iterations):
            print(f"\n--- Test Iteration {i+1}/{iterations} ---")
            
            # Generate new random data
            num_containers = random.randint(3, 8)
            num_items = random.randint(15, 50)
            self.generate_sample_data(num_containers, num_items)
            
            # Run placement algorithm
            placement_result = self.run_algorithm_test("placement", verbose=False)
            placement_success_rates.append(placement_result['success_rate'])
            placement_priority_scores.append(placement_result['avg_priority_score'])
            placement_times.append(placement_result['execution_time'])
            
            # Run retrieval algorithm if items were placed
            if placement_result['success_rate'] > 0:
                retrieval_result = self.run_algorithm_test("retrieval", verbose=False)
                retrieval_steps.append(retrieval_result['avg_steps'])
                retrieval_times.append(retrieval_result['avg_execution_time'])
        
        # Calculate averages
        avg_placement_success = sum(placement_success_rates) / len(placement_success_rates)
        avg_placement_priority = sum(placement_priority_scores) / len(placement_priority_scores)
        avg_placement_time = sum(placement_times) / len(placement_times)
        
        avg_retrieval_steps = sum(retrieval_steps) / len(retrieval_steps) if retrieval_steps else 0
        avg_retrieval_time = sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0
        
        # Print comprehensive results
        print("\n===== Comprehensive Test Results =====")
        print(f"Number of test iterations: {iterations}")
        
        print("\nPlacement Algorithm:")
        print(f"Average success rate: {avg_placement_success:.2%}")
        print(f"Average priority score: {avg_placement_priority:.2f}/120")
        print(f"Average execution time: {avg_placement_time:.6f} seconds")
        
        print("\nRetrieval Algorithm:")
        print(f"Average retrieval steps: {avg_retrieval_steps:.2f}")
        print(f"Average execution time: {avg_retrieval_time:.6f} seconds")
        
        return {
            'placement': {
                'success_rate': avg_placement_success,
                'priority_score': avg_placement_priority,
                'execution_time': avg_placement_time
            },
            'retrieval': {
                'steps': avg_retrieval_steps,
                'execution_time': avg_retrieval_time
            }
        }
    
    def save_to_csv(self, filename='cargo_state.csv'):
        """Save the current state to CSV files"""
        # Save containers
        containers_df = pd.DataFrame([
            {
                'Container ID': container_id,
                'Zone': container['zone'],
                'Width(cm)': container['width'],
                'Depth(cm)': container['depth'],
                'Height(cm)': container['height']
            }
            for container_id, container in self.containers.items()
        ])
        
        containers_df.to_csv('containers.csv', index=False)
        
        # Save items
        items_df = pd.DataFrame([
            {
                'Item ID': item_id,
                'Name': item['name'],
                'Width(cm)': item['width'],
                'Depth(cm)': item['depth'],
                'Height(cm)': item['height'],
                'Mass(kg)': item['mass'],
                'Priority(1-100)': item['priority'],
                'Expiry Date(ISO Format)': item['expiry_date'] if item['expiry_date'] else 'N/A',
                'Usage Limit': item['usage_limit'],
                'Remaining Uses': item['remaining_uses'],
                'Preferred Zone': item['preferred_zone'],
                'Is Waste': item['is_waste']
            }
            for item_id, item in self.items.items()
        ])
        
        items_df.to_csv('items.csv', index=False)
        
        # Save placements
        placements_df = pd.DataFrame([
            {
                'Item ID': item_id,
                'Container ID': placement['container_id'],
                'Start X': placement['position']['startCoordinates']['width'],
                'Start Y': placement['position']['startCoordinates']['depth'],
                'Start Z': placement['position']['startCoordinates']['height'],
                'End X': placement['position']['endCoordinates']['width'],
                'End Y': placement['position']['endCoordinates']['depth'],
                'End Z': placement['position']['endCoordinates']['height']
            }
            for item_id, placement in self.placements.items()
        ])
        
        placements_df.to_csv('placements.csv', index=False)
        
        print(f"Saved container, item, and placement data to CSV files")
        return True


# Example usage
if __name__ == "__main__":
    # Create a cargo visualizer
    cv = CargoVisualizer()
    
    # Option 1: Generate sample data
    cv.generate_sample_data(num_containers=4, num_items=20)
    
    # Option 2: Load from CSV files
    # cv.load_containers_from_csv('containers.csv')
    # cv.load_items_from_csv('items.csv')
    
    # Run the placement algorithm
    placement_result = cv.optimize_placement()
    print(f"Placed {len(placement_result['placements'])} items")
    
    # Visualize the containers
    cv.visualize_all_containers()
    
    # Run algorithm tests
    cv.run_algorithm_test("placement")
    cv.run_algorithm_test("retrieval")
    
    # Run comprehensive tests
    # cv.run_comprehensive_test(iterations=3)
    
    # Save state to CSV
    # cv.save_to_csv()