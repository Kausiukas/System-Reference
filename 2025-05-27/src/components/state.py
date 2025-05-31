from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from datetime import datetime

class ClientState(BaseModel):
    """State object for the client profile workflow."""
    
    # Input data
    raw_content: Optional[str] = Field(default=None, description="Raw content from email or document")
    chunks: List[str] = Field(default_factory=list, description="Chunked content for processing")
    
    # Profile data
    client_id: Optional[str] = Field(default=None, description="Unique identifier for the client")
    company_name: Optional[str] = Field(default=None, description="Name of the client company")
    contacts: List[Dict] = Field(default_factory=list, description="List of contact persons")
    needs: List[str] = Field(default_factory=list, description="Identified client needs")
    sentiment: Optional[str] = Field(default=None, description="Overall client sentiment")
    
    # Sales tracking
    sales_stage: Optional[str] = Field(default=None, description="Current stage in sales pipeline")
    last_action: Optional[Dict] = Field(default=None, description="Details of the last action taken")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    
    # Memory and context
    relevant_history: List[Dict] = Field(default_factory=list, description="Retrieved relevant past interactions")
    current_summary: Optional[str] = Field(default=None, description="Current situation summary")
    
    # Output
    generated_email: Optional[str] = Field(default=None, description="Generated email content if applicable")
    
    # New fields from the dataclass
    messages: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    last_interaction: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Dict[str, Any]):
        """Add a message to the state."""
        self.messages.append(message)
        self.last_interaction = datetime.now()
        
    def add_attachment(self, file_path: str):
        """Add an attachment to the state."""
        self.attachments.append(file_path)
        self.last_interaction = datetime.now()
        
    def update_metadata(self, key: str, value: Any):
        """Update metadata."""
        self.metadata[key] = value
        self.last_interaction = datetime.now()
    
    class Config:
        arbitrary_types_allowed = True 