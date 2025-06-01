from pydantic import BaseModel, Field
from typing import Dict, Any

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolError(BaseModel):
    name: str
    error: str
