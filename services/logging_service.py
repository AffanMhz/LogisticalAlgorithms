from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path

class LoggingService:
    """Service for comprehensive logging of system activities
    
    Supports advanced filtering by date range, user ID, item ID, and action types.
    Log entries follow a standardized format and are persisted to disk.
    """
    
    # Define valid action types for better consistency
    VALID_ACTION_TYPES = {
        "placement", "retrieval", "rearrangement", "disposal",
        "import", "export", "search", "simulation", "system",
        "waste_management", "undocking"
    }
    
    def __init__(self, logs_dir: str = "./data"):
        """Initialize logging service
        
        Args:
            logs_dir: Directory to store log files
        """
        self.logs: List[Dict[str, Any]] = []
        self.logs_dir = Path(logs_dir)
        
        # Create logs directory if it doesn't exist
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Default log file path
        self.log_file = self.logs_dir / "system_logs.json"
        
        # Try to load existing logs
        self.load_logs_from_file(self.log_file)
    
    def add_log(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: str = "system",
        item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a standardized log entry
        
        Args:
            action: Type of action performed (should be one of VALID_ACTION_TYPES)
            details: Additional details about the action
            user_id: ID of the user who performed the action
            item_id: ID of the item involved (if applicable)
            
        Returns:
            The created log entry
        """
        # Standardize action type
        action_type = action.lower()
        if action_type not in self.VALID_ACTION_TYPES:
            action_type = "system"  # Default for unknown actions
        
        # Create standardized log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "userId": user_id,
            "actionType": action_type,
            "itemId": item_id or "",
            "details": details or {}
        }
        
        # Extract container info for standardized format
        if details and "fromContainer" in details:
            log_entry["details"]["fromContainer"] = details["fromContainer"]
        if details and "toContainer" in details:
            log_entry["details"]["toContainer"] = details["toContainer"]
        if details and "reason" in details:
            log_entry["details"]["reason"] = details["reason"]
        
        # Add to logs
        self.logs.append(log_entry)
        
        # Keep only the last 5000 logs for performance
        if len(self.logs) > 5000:
            self.logs = self.logs[-5000:]
        
        # Save logs to file after each addition for persistence
        self.save_logs_to_file(self.log_file)
        
        return log_entry
    
    def get_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        item_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get logs with advanced filtering options
        
        Args:
            start_date: ISO format date string for filtering (inclusive)
            end_date: ISO format date string for filtering (inclusive)
            item_id: Filter by item ID
            user_id: Filter by user ID
            action_type: Filter by action type
            limit: Maximum number of logs to return
            
        Returns:
            Filtered list of log entries
        """
        filtered_logs = self.logs
        
        # Filter by date range
        if start_date or end_date:
            try:
                start = datetime.fromisoformat(start_date) if start_date else datetime.min
                # If end_date is provided but no time, set it to end of day
                if end_date and "T" not in end_date:
                    end = datetime.fromisoformat(end_date) + timedelta(days=1, microseconds=-1)
                else:
                    end = datetime.fromisoformat(end_date) if end_date else datetime.max
                
                filtered_logs = [
                    log for log in filtered_logs
                    if start <= datetime.fromisoformat(log["timestamp"]) <= end
                ]
            except ValueError:
                # Invalid date format, ignore filter
                pass
        
        # Filter by item ID
        if item_id:
            filtered_logs = [log for log in filtered_logs if log["itemId"] == item_id]
        
        # Filter by user ID
        if user_id:
            filtered_logs = [log for log in filtered_logs if log["userId"] == user_id]
        
        # Filter by action type
        if action_type and action_type.lower() in self.VALID_ACTION_TYPES:
            filtered_logs = [log for log in filtered_logs if log["actionType"] == action_type.lower()]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply limit
        return filtered_logs[:limit] if limit > 0 else filtered_logs
    
    def get_logs_by_action(self, action: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs filtered by action"""
        return self.get_logs(action_type=action, limit=limit)
    
    def get_logs_by_user(self, user: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs filtered by user"""
        return self.get_logs(user_id=user, limit=limit)
    
    def get_logs_by_item(self, item_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs filtered by item ID"""
        return self.get_logs(item_id=item_id, limit=limit)
    
    def save_logs_to_file(self, filepath: str) -> bool:
        """Save logs to a file
        
        Args:
            filepath: Path to save logs to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.logs, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving logs: {e}")
            return False
    
    def load_logs_from_file(self, filepath: str) -> bool:
        """Load logs from a file
        
        Args:
            filepath: Path to load logs from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.logs = json.load(f)
                return True
            return False
        except Exception as e:
            print(f"Error loading logs: {e}")
            self.logs = []  # Reset to empty if there's an error
            return False