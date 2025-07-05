"""
Agent Orchestrator Module for Model Context Protocol
Coordinates agent interactions using LangGraph
"""

import os
import json
import logging
import importlib
from typing import Dict, List, Any, Optional, Callable, Union, Type
from datetime import datetime
from enum import Enum

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = Any
    END = "END"

from .protocol import MCPMessage, MCPContext, MessageRole, MessageType
from .context import AgentContext

# Set up logging
logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents in the system"""
    DATA = "data_agent"
    STRATEGY = "strategy_agent"
    NEGOTIATION = "negotiation_agent"
    EXECUTION = "execution_agent"
    RISK = "risk_agent"
    SENTIMENT = "sentiment_agent"


class AgentOrchestrator:
    """
    Agent Orchestrator
    Coordinates interactions between agents using LangGraph
    """
    def __init__(self, use_langgraph: bool = False):
        """Initialize agent orchestrator"""
        self.use_langgraph = use_langgraph and LANGGRAPH_AVAILABLE
        if self.use_langgraph and not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph is not installed. Falling back to simple orchestration.")
            self.use_langgraph = False
        
        self.agents: Dict[str, Any] = {}
        self.agent_handlers: Dict[str, Callable] = {}
        self.workflows: Dict[str, Any] = {}
        self.graph = None
        
        # Initialize state
        self.state = {
            "contexts": {},
            "current_agent": None,
            "workflow_state": "idle",
            "last_activity": datetime.utcnow().isoformat()
        }
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: Union[AgentType, str],
        handler: Callable,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an agent with the orchestrator"""
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type)
            except ValueError:
                # Use as custom agent type
                pass
        
        agent_info = {
            "id": agent_id,
            "type": agent_type,
            "description": description or f"{agent_type} agent",
            "metadata": metadata or {},
            "registered_at": datetime.utcnow().isoformat()
        }
        
        self.agents[agent_id] = agent_info
        self.agent_handlers[agent_id] = handler
        
        logger.info(f"Registered agent: {agent_id} of type {agent_type}")
    
    def create_agent_context(
        self,
        agent_id: str,
        agent_type: Optional[str] = None,
        max_messages: int = 100,
        tags: Optional[List[str]] = None
    ) -> AgentContext:
        """Create a context for an agent"""
        # If agent_id is registered, use its type unless overridden
        if agent_id in self.agents and not agent_type:
            agent_info = self.agents[agent_id]
            agent_type = str(agent_info["type"])
        elif not agent_type:
            agent_type = "generic"  # Default type if not specified
        
        agent_context = AgentContext(
            agent_id=agent_id,
            agent_type=agent_type,
            max_messages=max_messages,
            tags=tags
        )
        
        # Store context in state
        context_id = agent_context.context.id
        self.state["contexts"][context_id] = agent_context
        
        return agent_context
    
    def get_agent_context(self, context_id: str) -> Optional[AgentContext]:
        """Get agent context by ID"""
        return self.state["contexts"].get(context_id)
        
    def route_message(self, message_data: Dict[str, Any], context: Optional[AgentContext] = None) -> Dict[str, Any]:
        """
        Route a message to the appropriate agent
        
        Args:
            message_data: Message data including next_agent field
            context: Optional agent context
            
        Returns:
            Response from the agent
        """
        # Extract next agent from message data
        next_agent = message_data.get("next_agent")
        if not next_agent:
            raise ValueError("Message does not specify next_agent")
            
        # Check if agent is registered
        if next_agent not in self.agents:
            raise ValueError(f"Agent {next_agent} is not registered")
            
        # Route message to agent
        agent_handler = self.agent_handlers[next_agent]
        
        # Add context to message if provided
        if context:
            message_data["context"] = context
            
        return agent_handler(message_data)
        
    def call_agent(self, agent_id: str, message: Optional[Dict[str, Any]] = None, context: Optional[AgentContext] = None, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call a specific agent directly
        
        Args:
            agent_id: ID of the agent to call
            message: Message to send to the agent
            context: Optional agent context
            input_data: Optional input data (alternative to message)
            
        Returns:
            Agent response
        """
        # Check if agent is registered
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} is not registered")
            
        # Get agent handler
        handler = self.agent_handlers[agent_id]
        
        # Use input_data if provided, otherwise use message
        if input_data is not None:
            message = input_data
        elif message is None:
            message = {}
        
        # Add context to message if provided
        if context:
            message["context"] = context
            
        # Call agent handler
        return handler(message)
        
    def create_workflow(self, name: str, agents: List[str], description: Optional[str] = None) -> str:
        """
        Create a new workflow
        
        Args:
            name: Workflow name
            agents: List of agent IDs to include in the workflow
            description: Optional workflow description
            
        Returns:
            Workflow ID
        """
        # Generate workflow ID
        workflow_id = f"workflow_{len(self.workflows) + 1}"
        
        # Create workflow
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description or f"Workflow for {name}",
            "agents": agents,
            "status": "created",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store workflow
        self.workflows[workflow_id] = workflow
        
        return workflow_id
        
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any], context: Optional[AgentContext] = None) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            context: Optional agent context
            
        Returns:
            Workflow execution result
        """
        # Check if workflow exists
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} does not exist")
            
        workflow = self.workflows[workflow_id]
        
        # Update workflow status
        workflow["status"] = "running"
        workflow["started_at"] = datetime.utcnow().isoformat()
        
        # Create context if not provided
        if not context:
            context = self.create_agent_context(
                agent_id=workflow_id,
                agent_type="workflow",
                max_messages=100
            )
        
        # Execute workflow using LangGraph if available
        if self.use_langgraph and self.graph:
            result = self._execute_langgraph_workflow(workflow, input_data, context)
        else:
            result = self._execute_simple_workflow(workflow, input_data, context)
        
        # Update workflow status
        workflow["status"] = "completed"
        workflow["completed_at"] = datetime.utcnow().isoformat()
        
        # Add status to result
        result["status"] = workflow["status"]
        
        return result
        
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow
        
        Args:
            workflow_id: ID of the workflow to get status for
            
        Returns:
            Workflow status information
        """
        # Check if workflow exists
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} does not exist")
            
        workflow = self.workflows[workflow_id]
        
        # Return workflow status
        return {
            "id": workflow["id"],
            "name": workflow["name"],
            "status": workflow.get("status", "created"),
            "created_at": workflow["created_at"],
            "started_at": workflow.get("started_at"),
            "completed_at": workflow.get("completed_at"),
            "agents": workflow["agents"]
        }
        
    def execute_custom_workflow(self, name: str, agents: List[str], input_data: Dict[str, Any], context: Optional[AgentContext] = None) -> Dict[str, Any]:
        """
        Create and execute a custom workflow
        
        Args:
            name: Workflow name
            agents: List of agent IDs to include in the workflow
            input_data: Input data for the workflow
            context: Optional agent context
            
        Returns:
            Workflow execution result
        """
        # Create workflow
        workflow_id = self.create_workflow(
            name=name,
            agents=agents
        )
        
        # Execute workflow
        return self.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            context=context
        )
    
    def _execute_simple_workflow(self, workflow: Dict[str, Any], input_data: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """
        Execute workflow without LangGraph
        
        Args:
            workflow: Workflow definition
            input_data: Input data for the workflow
            context: Agent context
            
        Returns:
            Workflow execution result
        """
        agents = workflow["agents"]
        results = []
        current_data = input_data
        
        # Execute each agent in sequence
        for agent_id in agents:
            # Check if agent exists
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} in workflow is not registered")
                
            # Call agent
            agent_result = self.call_agent(
                agent_id=agent_id,
                message=current_data,
                context=context
            )
            
            # Add result to results list
            results.append({
                "agent_id": agent_id,
                "result": agent_result
            })
            
            # Update current data for next agent
            current_data = agent_result
        
        # Return final result
        return {
            "workflow_id": workflow["id"],
            "results": results,
            "final_result": current_data
        }
    
    def _execute_langgraph_workflow(self, workflow: Dict[str, Any], input_data: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """
        Execute workflow using LangGraph
        
        Args:
            workflow: Workflow definition
            input_data: Input data for the workflow
            context: Agent context
            
        Returns:
            Workflow execution result
        """
        if not self.graph:
            self.graph = self._build_graph()
            
        # Execute graph
        # This is a placeholder - in a real implementation, we would use the LangGraph StateGraph
        return self._execute_simple_workflow(workflow, input_data, context)
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is not installed")
            
        # Define state schema
        state_schema = {
            "context_id": str,
            "current_agent": str,
            "next_agent": str,
            "input": dict,
            "output": dict,
            "error": Optional[str]
        }
        
        # Create graph
        graph = StateGraph(state_schema)
        
        # Define agent nodes
        for agent_id, agent_info in self.agents.items():
            graph.add_node(agent_id, self._create_agent_node(agent_id))
            
        # Add router node
        graph.add_node("router", self._route_to_next_agent)
        
        # Set entry point
        if any(str(a.get("type")) == AgentType.DATA.value for a in self.agents.values()):
            data_agent_id = next(aid for aid, a in self.agents.items() 
                                if str(a.get("type")) == AgentType.DATA.value)
            graph.set_entry_point(data_agent_id)
        else:
            # Start with router if no data agent
            graph.set_entry_point("router")
        
        # Connect agents to router
        for agent_id in self.agents.keys():
            graph.add_edge(agent_id, "router")
        
        # Compile graph
        self.graph = graph.compile()
        return self.graph
    
    def _create_agent_node(self, agent_id: str) -> Callable:
        """Create a node function for an agent"""
        handler = self.agent_handlers[agent_id]
        
        def node_function(state):
            try:
                # Get context
                context_id = state.get("context_id")
                agent_context = self.get_agent_context(context_id)
                
                if not agent_context:
                    raise ValueError(f"Context {context_id} not found")
                
                # Update state
                self.state["current_agent"] = agent_id
                self.state["workflow_state"] = "processing"
                self.state["last_activity"] = datetime.utcnow().isoformat()
                
                # Call agent handler
                input_data = state.get("input", {})
                result = handler(agent_context, input_data)
                
                # Return updated state
                return {
                    "output": result,
                    "current_agent": agent_id,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Error in agent {agent_id}: {e}")
                return {
                    "output": {},
                    "current_agent": agent_id,
                    "error": str(e)
                }
        
        return node_function
    
    def _route_to_next_agent(self, state: Dict[str, Any]) -> str:
        """
        Route to the next agent based on state
        
        Args:
            state: Current workflow state
            
        Returns:
            ID of the next agent or END
        """
        # Check for errors
        if state.get("error"):
            return END
            
        # Get output from previous agent
        output = state.get("output", {})
        
        # Check if next agent is specified
        next_agent = output.get("next_agent") or state.get("next_agent")
        
        # Return next agent if valid
        if next_agent and next_agent in self.agents:
            return next_agent
            
        # Default to END
        return END
    
    def run_workflow(
        self,
        initial_input: Dict[str, Any],
        context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the agent workflow"""
        # Create context if not provided
        if not context_id:
            # Use data agent as default if available
            if AgentType.DATA.value in [str(a["type"]) for a in self.agents.values()]:
                data_agent_id = next(aid for aid, a in self.agents.items() 
                                    if str(a["type"]) == AgentType.DATA.value)
                agent_context = self.create_agent_context(data_agent_id)
                context_id = agent_context.context.id
            else:
                # Use first registered agent
                first_agent_id = next(iter(self.agents.keys()))
                agent_context = self.create_agent_context(first_agent_id)
                context_id = agent_context.context.id
        
        # Initialize workflow state
        self.state["workflow_state"] = "starting"
        self.state["last_activity"] = datetime.utcnow().isoformat()
        
        # Run workflow using LangGraph if available
        if self.use_langgraph:
            if not self.graph:
                self._build_graph()
            
            # Prepare initial state
            initial_state = {
                "context_id": context_id,
                "current_agent": None,
                "next_agent": None,
                "input": initial_input,
                "output": {},
                "error": None
            }
            
            # Run the graph
            result = self.graph.invoke(initial_state)
            
            # Update orchestrator state
            self.state["workflow_state"] = "completed"
            self.state["last_activity"] = datetime.utcnow().isoformat()
            
            return result
        else:
            # Simple sequential execution without LangGraph
            return self._run_simple_workflow(context_id, initial_input)
    
    def _run_simple_workflow(
        self,
        context_id: str,
        initial_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a simple sequential workflow without LangGraph"""
        agent_context = self.get_agent_context(context_id)
        if not agent_context:
            raise ValueError(f"Context {context_id} not found")
        
        # Start with data agent if available
        if AgentType.DATA.value in [str(a["type"]) for a in self.agents.values()]:
            current_agent_id = next(aid for aid, a in self.agents.items() 
                                   if str(a["type"]) == AgentType.DATA.value)
        else:
            # Start with first registered agent
            current_agent_id = next(iter(self.agents.keys()))
        
        # Initialize workflow
        current_input = initial_input
        results = {}
        max_steps = len(self.agents) * 2  # Prevent infinite loops
        steps = 0
        
        # Run workflow
        while current_agent_id and steps < max_steps:
            # Update state
            self.state["current_agent"] = current_agent_id
            self.state["workflow_state"] = "processing"
            self.state["last_activity"] = datetime.utcnow().isoformat()
            
            # Get handler
            handler = self.agent_handlers.get(current_agent_id)
            if not handler:
                break
            
            try:
                # Call agent handler
                result = handler(agent_context, current_input)
                
                # Store result
                results[current_agent_id] = result
                
                # Determine next agent
                next_agent = result.get("next_agent")
                if not next_agent or next_agent == "end" or next_agent not in self.agents:
                    break
                
                # Prepare for next agent
                current_agent_id = next_agent
                current_input = result
                steps += 1
            except Exception as e:
                logger.error(f"Error in agent {current_agent_id}: {e}")
                results["error"] = str(e)
                break
        
        # Update state
        self.state["workflow_state"] = "completed"
        self.state["last_activity"] = datetime.utcnow().isoformat()
        
        return {
            "results": results,
            "steps": steps,
            "final_agent": current_agent_id
        }
    
    def send_message_to_agent(
        self,
        agent_id: str,
        message_type: Union[MessageType, str],
        content: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a specific agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} is not registered")
        
        # Get or create context
        agent_context = None
        if context_id:
            agent_context = self.get_agent_context(context_id)
        
        if not agent_context:
            agent_context = self.create_agent_context(agent_id)
        
        # Create message
        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        
        message = MCPMessage(
            role=MessageRole.USER,
            type=message_type,
            content=content,
            data=data,
            metadata={"source": "orchestrator"}
        )
        
        # Add to context
        agent_context.add_message(message)
        
        # Call agent handler
        handler = self.agent_handlers[agent_id]
        try:
            result = handler(agent_context, {"message": message.to_dict()})
            return result
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {e}")
            return {"error": str(e)}
    
    def get_workflow_state(self) -> Dict[str, Any]:
        """Get the current workflow state"""
        return {
            "current_agent": self.state.get("current_agent"),
            "workflow_state": self.state.get("workflow_state"),
            "last_activity": self.state.get("last_activity"),
            "registered_agents": list(self.agents.keys()),
            "context_count": len(self.state.get("contexts", {}))
        }
