"""
Agent Context Module for Model Context Protocol
Manages context for agent interactions
"""

import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field

from .protocol import MCPContext, MCPMessage, MessageRole, MessageType


class AgentContextMetadata(BaseModel):
    """Metadata for agent context"""
    agent_id: str
    agent_type: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    version: str = "1.0"


class AgentContext:
    """
    Agent Context
    Manages context for agent interactions with enhanced functionality
    """
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        context: Optional[MCPContext] = None,
        max_messages: int = 100,
        tags: Optional[List[str]] = None
    ):
        """Initialize agent context"""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.max_messages = max_messages
        self.tags = set(tags or [])
        
        # Create or use provided context
        metadata = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "tags": list(self.tags),
            "version": "1.0"
        }
        
        self.context = context or MCPContext(metadata=metadata)
        
        # Initialize state with default values
        self._ensure_default_state()
    
    def _ensure_default_state(self) -> None:
        """Ensure default state values exist"""
        defaults = {
            "conversation_start": datetime.utcnow().isoformat(),
            "message_count": 0,
            "last_activity": datetime.utcnow().isoformat(),
            "active_tools": [],
            "memory_references": [],
            "market_data": {},
            "strategy_state": {},
            "execution_state": {}
        }
        
        for key, value in defaults.items():
            if key not in self.context.state:
                self.context.state[key] = value
    
    def add_message(self, message: MCPMessage) -> None:
        """Add a message to the context"""
        self.context.add_message(message)
        self.context.state["message_count"] = len(self.context.messages)
        self.context.state["last_activity"] = datetime.utcnow().isoformat()
        self.context.metadata["updated_at"] = datetime.utcnow().isoformat()
        
        # Trim messages if exceeding max_messages
        if len(self.context.messages) > self.max_messages:
            # Keep system messages and trim oldest user/assistant messages
            system_messages = [m for m in self.context.messages if m.role == MessageRole.SYSTEM]
            other_messages = [m for m in self.context.messages if m.role != MessageRole.SYSTEM]
            
            # Sort by timestamp and keep the newest
            other_messages.sort(key=lambda m: m.timestamp)
            keep_messages = other_messages[-(self.max_messages - len(system_messages)):]
            
            # Rebuild messages list
            self.context.messages = system_messages + keep_messages
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MCPMessage:
        """Add a system message to the context"""
        message = MCPMessage(
            role=MessageRole.SYSTEM,
            type=MessageType.TEXT,
            content=content,
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MCPMessage:
        """Add a user message to the context"""
        message = MCPMessage(
            role=MessageRole.USER,
            type=MessageType.TEXT,
            content=content,
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MCPMessage:
        """Add an assistant message to the context"""
        message = MCPMessage(
            role=MessageRole.ASSISTANT,
            type=MessageType.TEXT,
            content=content,
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_function_call(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a function call message to the context"""
        message = MCPMessage(
            role=MessageRole.ASSISTANT,
            type=MessageType.FUNCTION_CALL,
            function_call={"name": function_name, "arguments": arguments},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_function_result(
        self,
        function_name: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a function result message to the context"""
        message = MCPMessage(
            role=MessageRole.FUNCTION,
            type=MessageType.FUNCTION_RESULT,
            data={"name": function_name, "result": result},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a tool call message to the context"""
        message = MCPMessage(
            role=MessageRole.ASSISTANT,
            type=MessageType.TOOL_CALL,
            tool_call={"name": tool_name, "arguments": arguments},
            metadata=metadata or {}
        )
        self.add_message(message)
        
        # Track active tools
        active_tools = set(self.context.state.get("active_tools", []))
        active_tools.add(tool_name)
        self.context.state["active_tools"] = list(active_tools)
        
        return message
    
    def add_tool_result(
        self,
        tool_name: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a tool result message to the context"""
        message = MCPMessage(
            role=MessageRole.TOOL,
            type=MessageType.TOOL_RESULT,
            data={"name": tool_name, "result": result},
            metadata=metadata or {}
        )
        self.add_message(message)
        
        # Remove from active tools
        active_tools = set(self.context.state.get("active_tools", []))
        if tool_name in active_tools:
            active_tools.remove(tool_name)
        self.context.state["active_tools"] = list(active_tools)
        
        return message
    
    def add_agent_request(
        self,
        target_agent: str,
        request_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add an agent request message to the context"""
        message = MCPMessage(
            role=MessageRole.AGENT,
            type=MessageType.AGENT_REQUEST,
            data={"target_agent": target_agent, "request": request_data},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_agent_response(
        self,
        source_agent: str,
        response_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add an agent response message to the context"""
        message = MCPMessage(
            role=MessageRole.AGENT,
            type=MessageType.AGENT_RESPONSE,
            data={"source_agent": source_agent, "response": response_data},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_data_request(
        self,
        data_type: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a data request message to the context"""
        message = MCPMessage(
            role=MessageRole.ASSISTANT,
            type=MessageType.DATA_REQUEST,
            data={"data_type": data_type, "parameters": parameters},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_data_response(
        self,
        data_type: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a data response message to the context"""
        message = MCPMessage(
            role=MessageRole.DATA,
            type=MessageType.DATA_RESPONSE,
            data={"data_type": data_type, "data": data},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_error(
        self,
        error_type: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add an error message to the context"""
        message = MCPMessage(
            role=MessageRole.SYSTEM,
            type=MessageType.ERROR,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "details": details or {}
            },
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_state_update(
        self,
        state_key: str,
        state_value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Add a state update message and update the state"""
        # Update the state
        self.context.update_state(state_key, state_value)
        
        # Create a message for the update
        message = MCPMessage(
            role=MessageRole.SYSTEM,
            type=MessageType.STATE_UPDATE,
            data={"key": state_key, "value": state_value},
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def get_messages(
        self,
        roles: Optional[List[MessageRole]] = None,
        types: Optional[List[MessageType]] = None,
        limit: Optional[int] = None
    ) -> List[MCPMessage]:
        """Get messages filtered by roles and types"""
        messages = self.context.messages
        
        if roles:
            messages = [msg for msg in messages if msg.role in roles]
        
        if types:
            messages = [msg for msg in messages if msg.type in types]
        
        if limit and limit > 0:
            messages = messages[-limit:]
            
        return messages
    
    def get_messages_by_type(self, message_type: MessageType, limit: Optional[int] = None) -> List[MCPMessage]:
        """Get messages of a specific type from the context"""
        messages = self.context.messages
        
        # Filter by message type
        messages = [m for m in messages if m.type == message_type]
            
        # Limit if specified
        if limit is not None:
            messages = messages[-limit:]
            
        return messages
    
    def get_conversation_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation messages in a format suitable for LLM context"""
        # Get user and assistant messages
        messages = self.get_messages(
            roles=[MessageRole.SYSTEM, MessageRole.USER, MessageRole.ASSISTANT],
            types=[MessageType.TEXT, MessageType.FUNCTION_CALL, MessageType.FUNCTION_RESULT]
        )
        
        if limit and limit > 0:
            messages = messages[-limit:]
        
        # Convert to LLM format
        llm_messages = []
        for msg in messages:
            message_dict = {"role": msg.role.value}
            
            if msg.content:
                message_dict["content"] = msg.content
            
            if msg.function_call:
                message_dict["function_call"] = {
                    "name": msg.function_call.name,
                    "arguments": json.dumps(msg.function_call.arguments)
                }
            
            if msg.type == MessageType.FUNCTION_RESULT and msg.data:
                message_dict["name"] = msg.data.get("name", "")
                message_dict["content"] = json.dumps(msg.data.get("result", {}))
            
            llm_messages.append(message_dict)
            
        return llm_messages
    
    def update_state(self, key: str, value: Any) -> None:
        """Update context state"""
        self.context.update_state(key, value)
        self.context.metadata["updated_at"] = datetime.utcnow().isoformat()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value by key"""
        return self.context.get_state(key, default)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the context"""
        self.tags.add(tag)
        self.context.metadata["tags"] = list(self.tags)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the context"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.context.metadata["tags"] = list(self.tags)
    
    def has_tag(self, tag: str) -> bool:
        """Check if context has a tag"""
        return tag in self.tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent context to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "max_messages": self.max_messages,
            "tags": list(self.tags),
            "context": self.context.to_dict()
        }
    
    def serialize(self) -> str:
        """Serialize agent context to JSON"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def deserialize(cls, json_str: str) -> "AgentContext":
        """Deserialize agent context from JSON"""
        data = json.loads(json_str)
        context_data = data.pop("context", {})
        context = MCPContext.from_dict(context_data)
        
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            context=context,
            max_messages=data.get("max_messages", 100),
            tags=data.get("tags", [])
        )
