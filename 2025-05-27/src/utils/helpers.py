import os
from typing import List, Dict, Any
from datetime import datetime
import json
from pathlib import Path

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        "data/profiles",
        "data/raw",
        "client_embeddings"
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def save_client_profile(client_id: str, data: Dict[str, Any], base_dir: str = "data/clients"):
    """Save client profile data to disk."""
    # Create directory if it doesn't exist
    client_dir = Path(base_dir) / client_id
    client_dir.mkdir(parents=True, exist_ok=True)
    
    # Save profile data
    profile_path = client_dir / "profile.json"
    with open(profile_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
        
def load_client_profile(client_id: str, base_dir: str = "data/clients") -> Dict[str, Any]:
    """Load client profile data from disk."""
    profile_path = Path(base_dir) / client_id / "profile.json"
    
    if not profile_path.exists():
        return {}
        
    with open(profile_path, 'r') as f:
        return json.load(f)

def save_raw_content(client_id: str, content: str, source_type: str) -> str:
    """Save raw content to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{client_id}_{timestamp}_{source_type}.txt"
    file_path = f"data/raw/{filename}"
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return file_path

def get_sales_stages() -> List[str]:
    """Return list of valid sales stages."""
    return [
        "lead",
        "qualified",
        "offered",
        "negotiating",
        "closed_won",
        "closed_lost"
    ]

def validate_sales_stage(stage: str) -> bool:
    """Validate if a sales stage is valid."""
    return stage in get_sales_stages()

def format_email_template(template: str, context: Dict[str, Any]) -> str:
    """Format email template with context variables."""
    try:
        return template.format(**context)
    except KeyError as e:
        return f"Error: Missing template variable {str(e)}"
    
def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def format_timestamp(dt: datetime) -> str:
    """Format datetime for filenames."""
    return dt.strftime("%Y%m%d_%H%M%S")
    
def create_temp_dir(base_dir: str = "data/temp") -> str:
    """Create a temporary directory with timestamp."""
    timestamp = format_timestamp(datetime.now())
    temp_dir = Path(base_dir) / timestamp
    temp_dir.mkdir(parents=True, exist_ok=True)
    return str(temp_dir) 