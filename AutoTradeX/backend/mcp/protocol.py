"""
Model Context Protocol (MCP) - Core Protocol Definition
Defines the standardized protocol for agent communication and context management
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Roles for MCP messages"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"
    DATA = "data"
    AGENT = "agent"


class MessageType(str, Enum):
    """Types of MCP messages"""
    TEXT = "text"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    ERROR = "error"
    STATE_UPDATE = "state_update"


class FunctionCall(BaseModel):
    """Function call details"""
    name: str
    arguments: Dict[str, Any]


class ToolCall(BaseModel):
    """Tool call details"""
    name: str
    arguments: Dict[str, Any]


class MCPMessage(BaseModel):
    """
    Model Context Protocol Message
    Standardized message format for agent communication
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    type: MessageType
    content: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    tool_call: Optional[ToolCall] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create message from dictionary"""
        return cls(**data)


class MCPContext(BaseModel):
    """
    Model Context Protocol Context
    Maintains the context for agent interactions
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[MCPMessage] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    def add_message(self, message: MCPMessage) -> None:
        """Add a message to the context"""
        self.messages.append(message)
    
    def get_messages(self, roles: Optional[List[MessageRole]] = None) -> List[MCPMessage]:
        """Get messages filtered by roles"""
        if roles is None:
            return self.messages
        return [msg for msg in self.messages if msg.role in roles]
    
    def update_state(self, key: str, value: Any) -> None:
        """Update context state"""
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value by key"""
        return self.state.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPContext":
        """Create context from dictionary"""
        if "messages" in data:
            data["messages"] = [MCPMessage.from_dict(msg) for msg in data["messages"]]
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert context to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "MCPContext":
        """Create context from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ModelContextProtocol:
    """
    Model Context Protocol
    Implements the protocol for standardized agent communication
    """
    def __init__(self):
        """Initialize the protocol"""
        self.contexts: Dict[str, MCPContext] = {}
    
    def create_context(self, metadata: Optional[Dict[str, Any]] = None) -> MCPContext:
        """Create a new context"""
        context = MCPContext(metadata=metadata or {})
        self.contexts[context.id] = context
        return context
    
    def get_context(self, context_id: str) -> Optional[MCPContext]:
        """Get context by ID"""
        return self.contexts.get(context_id)
    
    def delete_context(self, context_id: str) -> bool:
        """Delete context by ID"""
        if context_id in self.contexts:
            del self.contexts[context_id]
            return True
        return False
    
    def create_message(
        self,
        role: Union[MessageRole, str],
        type: Union[MessageType, str],
        content: Optional[str] = None,
        function_call: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Create a new message"""
        if isinstance(role, str):
            role = MessageRole(role)
        if isinstance(type, str):
            type = MessageType(type)
            
        message_data = {
            "role": role,
            "type": type,
            "metadata": metadata or {}
        }
        
        if content is not None:
            message_data["content"] = content
        if function_call is not None:
            message_data["function_call"] = FunctionCall(**function_call)
        if tool_call is not None:
            message_data["tool_call"] = ToolCall(**tool_call)
        if data is not None:
            message_data["data"] = data
            
        return MCPMessage(**message_data)
    
    def add_message_to_context(self, context_id: str, message: MCPMessage) -> bool:
        """Add message to context"""
        context = self.get_context(context_id)
        if context:
            context.add_message(message)
            return True
        return False
    
    def update_context_state(self, context_id: str, key: str, value: Any) -> bool:
        """Update context state"""
        context = self.get_context(context_id)
        if context:
            context.update_state(key, value)
            return True
        return False
    
    def get_context_state(self, context_id: str, key: str, default: Any = None) -> Any:
        """Get context state value"""
        context = self.get_context(context_id)
        if context:
            return context.get_state(key, default)
        return default
    
    def serialize_context(self, context_id: str) -> Optional[str]:
        """Serialize context to JSON"""
        context = self.get_context(context_id)
        if context:
            return context.to_json()
        return None
    
    def deserialize_context(self, json_str: str) -> MCPContext:
        """Deserialize context from JSON"""
        context = MCPContext.from_json(json_str)
        self.contexts[context.id] = context
        return context
