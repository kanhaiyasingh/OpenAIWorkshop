import os  
import json
import logging  
from typing import Any, Dict, List, Optional, Union  
from dotenv import load_dotenv  

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.core.credentials import TokenCredential

load_dotenv()  # Load environment variables from .env file if needed  


class ToolCallTrackingMixin:
    """
    Mixin class that provides tool call tracking functionality.
    
    Use this mixin in agents that need to track tool calls for evaluation.
    The mixin handles:
    - Accumulating streaming function call arguments
    - Finalizing function calls with parsed arguments
    - Providing access to tool calls made during a request
    
    Usage:
        class MyAgent(ToolCallTrackingMixin, BaseAgent):
            def __init__(self, state_store, session_id):
                super().__init__(state_store, session_id)
                self.init_tool_tracking()  # Call this in __init__
    """
    
    def init_tool_tracking(self) -> None:
        """Initialize tool tracking state. Call this in agent's __init__."""
        self._tool_calls: List[Dict[str, Any]] = []
        self._current_function_call: Dict[str, Any] | None = None
        self._current_function_args: List[str] = []
    
    def clear_tool_calls(self) -> None:
        """Clear tool calls from previous request. Call at start of chat_async."""
        self._tool_calls = []
        self._current_function_call = None
        self._current_function_args = []
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Return the list of tool calls made during the last request.
        
        Returns list of dicts with:
        - name: tool name
        - args: arguments passed to the tool
        """
        return self._tool_calls.copy()
    
    def track_function_call_start(self, name: str) -> None:
        """Start tracking a new function call. Call when function_call content is received."""
        # Finalize any previous function call first
        self._finalize_current_function_call()
        self._current_function_call = {"name": name}
        self._current_function_args = []
    
    def track_function_call_arguments(self, arguments: str) -> None:
        """Accumulate streaming function call arguments."""
        if arguments:
            self._current_function_args.append(arguments)
    
    def _finalize_current_function_call(self) -> None:
        """Finalize the current function call by parsing accumulated arguments."""
        if self._current_function_call is None:
            return
        
        # Join accumulated argument chunks
        args_str = ''.join(self._current_function_args)
        
        # Parse the arguments
        args = {}
        if args_str:
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, store raw string
                args = {"_raw": args_str} if args_str.strip() else {}
        
        self._tool_calls.append({
            "name": self._current_function_call["name"],
            "args": args
        })
        
        # Reset accumulators
        self._current_function_call = None
        self._current_function_args = []
    
    def finalize_tool_tracking(self) -> None:
        """Finalize any pending function calls. Call at end of streaming."""
        self._finalize_current_function_call()
    
    def add_tool_call(self, name: str, args: Dict[str, Any] | None = None) -> None:
        """Directly add a tool call (for non-streaming scenarios)."""
        self._tool_calls.append({
            "name": name,
            "args": args or {}
        })


class BaseAgent:  
    """  
    Base class for all agents.  
    Not intended to be used directly.  
    Handles environment variables, state store, and chat history.
    
    Supports both API key and managed identity authentication for Azure OpenAI.
    When AZURE_OPENAI_API_KEY is not set, uses DefaultAzureCredential (or 
    ManagedIdentityCredential if AZURE_CLIENT_ID is set for user-assigned identity).
    """  
  
    def __init__(self, state_store: Dict[str, Any], session_id: str) -> None:  
        self.azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")  
        self.azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")  
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")  
        self.mcp_server_uri = os.getenv("MCP_SERVER_URI") 
        self.openai_model_name = os.getenv("OPENAI_MODEL_NAME")
        
        # Initialize credential for managed identity authentication
        self.azure_credential: Optional[TokenCredential] = None
        if not self.azure_openai_key:
            azure_client_id = os.getenv("AZURE_CLIENT_ID")
            if azure_client_id:
                # Use user-assigned managed identity
                self.azure_credential = ManagedIdentityCredential(client_id=azure_client_id)
                logging.info(f"Using ManagedIdentityCredential with client_id: {azure_client_id}")
            else:
                # Use DefaultAzureCredential (works with system-assigned MI, Azure CLI, etc.)
                self.azure_credential = DefaultAzureCredential()
                logging.info("Using DefaultAzureCredential for Azure OpenAI authentication")  
  
        self.session_id = session_id  
        self.state_store = state_store  
  
        self.chat_history: List[Dict[str, str]] = self.state_store.get(f"{session_id}_chat_history", [])  
        self.state: Optional[Any] = self.state_store.get(session_id, None) 
        logging.debug(f"Chat history for session {session_id}: {self.chat_history}")  
  
    def _setstate(self, state: Any) -> None:  
        self.state_store[self.session_id] = state  
  
    def append_to_chat_history(self, messages: List[Dict[str, str]]) -> None:  
        self.chat_history.extend(messages)  
        self.state_store[f"{self.session_id}_chat_history"] = self.chat_history  
  
    def set_websocket_manager(self, manager: Any) -> None:
        """
        Allow backend to inject WebSocket manager for streaming events.
        Override in child class if streaming support is needed.
        """
        pass  # Default: no-op for agents that don't support streaming
  
    async def chat_async(self, prompt: str) -> str:  
        """  
        Override in child class!  
        """  
        raise NotImplementedError("chat_async should be implemented in subclass.")  