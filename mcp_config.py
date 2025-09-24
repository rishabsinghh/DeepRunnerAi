"""
MCP Configuration for CLM Automation System.
Defines MCP server settings, tool configurations, and integration parameters.
"""
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class MCPTransportType(Enum):
    """MCP transport types"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"

@dataclass
class MCPToolConfig:
    """Configuration for an MCP tool"""
    name: str
    description: str
    enabled: bool = True
    timeout: int = 300
    max_retries: int = 3
    rate_limit: int = 100  # requests per minute

@dataclass
class MCPServerConfig:
    """MCP Server configuration"""
    host: str = "localhost"
    port: int = 8080
    transport: MCPTransportType = MCPTransportType.STDIO
    log_level: str = "INFO"
    max_connections: int = 10
    request_timeout: int = 300
    enable_cors: bool = True
    cors_origins: List[str] = None

class MCPConfig:
    """Main MCP configuration class"""
    
    def __init__(self):
        # Server configuration
        self.server = MCPServerConfig(
            host=os.getenv("MCP_HOST", "localhost"),
            port=int(os.getenv("MCP_PORT", "8080")),
            transport=MCPTransportType(os.getenv("MCP_TRANSPORT", "stdio")),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
            max_connections=int(os.getenv("MCP_MAX_CONNECTIONS", "10")),
            request_timeout=int(os.getenv("MCP_REQUEST_TIMEOUT", "300")),
            enable_cors=os.getenv("MCP_ENABLE_CORS", "true").lower() == "true",
            cors_origins=os.getenv("MCP_CORS_ORIGINS", "*").split(",")
        )
        
        # Tool configurations
        self.tools = {
            "process_documents": MCPToolConfig(
                name="process_documents",
                description="Process and index contract documents",
                timeout=600,  # 10 minutes for document processing
                max_retries=2
            ),
            "ask_question": MCPToolConfig(
                name="ask_question",
                description="Ask questions about contracts using RAG",
                timeout=60,  # 1 minute for question answering
                max_retries=3,
                rate_limit=50  # Lower rate limit for AI queries
            ),
            "find_similar_documents": MCPToolConfig(
                name="find_similar_documents",
                description="Find documents similar to a given document",
                timeout=30,
                max_retries=3
            ),
            "search_documents": MCPToolConfig(
                name="search_documents",
                description="Search documents by content",
                timeout=30,
                max_retries=3
            ),
            "run_daily_analysis": MCPToolConfig(
                name="run_daily_analysis",
                description="Run daily contract analysis and generate report",
                timeout=300,  # 5 minutes for daily analysis
                max_retries=2
            ),
            "get_system_status": MCPToolConfig(
                name="get_system_status",
                description="Get current system status and statistics",
                timeout=10,
                max_retries=5,
                rate_limit=200  # Higher rate limit for status checks
            ),
            "generate_report": MCPToolConfig(
                name="generate_report",
                description="Generate comprehensive system report",
                timeout=180,  # 3 minutes for report generation
                max_retries=2
            ),
            "detect_conflicts": MCPToolConfig(
                name="detect_conflicts",
                description="Detect conflicts in contract documents",
                timeout=120,  # 2 minutes for conflict detection
                max_retries=3
            ),
            "find_expiring_contracts": MCPToolConfig(
                name="find_expiring_contracts",
                description="Find contracts expiring within specified days",
                timeout=60,
                max_retries=3
            )
        }
        
        # Workflow configurations
        self.workflows = {
            "daily_analysis": {
                "enabled": True,
                "schedule": "0 9 * * *",  # Daily at 9 AM
                "timeout": 1800,  # 30 minutes
                "retry_on_failure": True,
                "max_retries": 3
            },
            "document_processing": {
                "enabled": True,
                "trigger": "file_change",  # Triggered by file changes
                "timeout": 3600,  # 1 hour
                "retry_on_failure": True,
                "max_retries": 2
            },
            "contract_analysis": {
                "enabled": True,
                "trigger": "manual",  # Manual trigger only
                "timeout": 900,  # 15 minutes
                "retry_on_failure": False,
                "max_retries": 1
            }
        }
        
        # AI Agent configurations
        self.ai_agent = {
            "enabled": True,
            "model": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 2000,
            "timeout": 60,
            "retry_attempts": 3,
            "rate_limit": 30  # requests per minute
        }
        
        # Monitoring configurations
        self.monitoring = {
            "enabled": True,
            "check_interval": 3600,  # 1 hour
            "alert_thresholds": {
                "expiring_contracts": 5,
                "conflicts": 1,
                "processing_errors": 3
            },
            "notification_channels": ["email", "log"],
            "retention_days": 30
        }
        
        # Security configurations
        self.security = {
            "enable_authentication": os.getenv("MCP_ENABLE_AUTH", "false").lower() == "true",
            "api_key": os.getenv("MCP_API_KEY", ""),
            "allowed_origins": os.getenv("MCP_ALLOWED_ORIGINS", "*").split(","),
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100,
                "burst_limit": 200
            }
        }
    
    def get_tool_config(self, tool_name: str) -> MCPToolConfig:
        """Get configuration for a specific tool"""
        return self.tools.get(tool_name, MCPToolConfig(
            name=tool_name,
            description="Unknown tool",
            enabled=False
        ))
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled"""
        tool_config = self.get_tool_config(tool_name)
        return tool_config.enabled
    
    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get configuration for a specific workflow"""
        return self.workflows.get(workflow_name, {
            "enabled": False,
            "timeout": 300,
            "retry_on_failure": False,
            "max_retries": 1
        })
    
    def is_workflow_enabled(self, workflow_name: str) -> bool:
        """Check if a workflow is enabled"""
        workflow_config = self.get_workflow_config(workflow_name)
        return workflow_config.get("enabled", False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "transport": self.server.transport.value,
                "log_level": self.server.log_level,
                "max_connections": self.server.max_connections,
                "request_timeout": self.server.request_timeout,
                "enable_cors": self.server.enable_cors,
                "cors_origins": self.server.cors_origins
            },
            "tools": {
                name: {
                    "name": config.name,
                    "description": config.description,
                    "enabled": config.enabled,
                    "timeout": config.timeout,
                    "max_retries": config.max_retries,
                    "rate_limit": config.rate_limit
                }
                for name, config in self.tools.items()
            },
            "workflows": self.workflows,
            "ai_agent": self.ai_agent,
            "monitoring": self.monitoring,
            "security": self.security
        }
    
    def save_to_file(self, filepath: str) -> bool:
        """Save configuration to file"""
        try:
            import json
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving MCP configuration: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'MCPConfig':
        """Load configuration from file"""
        try:
            import json
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
            
            config = cls()
            
            # Update server config
            if "server" in config_dict:
                server_config = config_dict["server"]
                config.server.host = server_config.get("host", config.server.host)
                config.server.port = server_config.get("port", config.server.port)
                config.server.transport = MCPTransportType(server_config.get("transport", config.server.transport.value))
                config.server.log_level = server_config.get("log_level", config.server.log_level)
                config.server.max_connections = server_config.get("max_connections", config.server.max_connections)
                config.server.request_timeout = server_config.get("request_timeout", config.server.request_timeout)
                config.server.enable_cors = server_config.get("enable_cors", config.server.enable_cors)
                config.server.cors_origins = server_config.get("cors_origins", config.server.cors_origins)
            
            # Update tool configs
            if "tools" in config_dict:
                for tool_name, tool_config in config_dict["tools"].items():
                    if tool_name in config.tools:
                        config.tools[tool_name].enabled = tool_config.get("enabled", config.tools[tool_name].enabled)
                        config.tools[tool_name].timeout = tool_config.get("timeout", config.tools[tool_name].timeout)
                        config.tools[tool_name].max_retries = tool_config.get("max_retries", config.tools[tool_name].max_retries)
                        config.tools[tool_name].rate_limit = tool_config.get("rate_limit", config.tools[tool_name].rate_limit)
            
            # Update workflow configs
            if "workflows" in config_dict:
                config.workflows.update(config_dict["workflows"])
            
            # Update AI agent config
            if "ai_agent" in config_dict:
                config.ai_agent.update(config_dict["ai_agent"])
            
            # Update monitoring config
            if "monitoring" in config_dict:
                config.monitoring.update(config_dict["monitoring"])
            
            # Update security config
            if "security" in config_dict:
                config.security.update(config_dict["security"])
            
            return config
            
        except Exception as e:
            print(f"Error loading MCP configuration: {e}")
            return cls()  # Return default config

# Default MCP configuration
DEFAULT_MCP_CONFIG = MCPConfig()

# Environment variable mappings
MCP_ENV_VARS = {
    "MCP_HOST": "server.host",
    "MCP_PORT": "server.port",
    "MCP_TRANSPORT": "server.transport",
    "MCP_LOG_LEVEL": "server.log_level",
    "MCP_MAX_CONNECTIONS": "server.max_connections",
    "MCP_REQUEST_TIMEOUT": "server.request_timeout",
    "MCP_ENABLE_CORS": "server.enable_cors",
    "MCP_CORS_ORIGINS": "server.cors_origins",
    "MCP_ENABLE_AUTH": "security.enable_authentication",
    "MCP_API_KEY": "security.api_key",
    "MCP_ALLOWED_ORIGINS": "security.allowed_origins"
}

if __name__ == "__main__":
    # Example usage
    config = MCPConfig()
    
    print("MCP Configuration:")
    print("=" * 50)
    print(f"Server: {config.server.host}:{config.server.port}")
    print(f"Transport: {config.server.transport.value}")
    print(f"Tools enabled: {sum(1 for tool in config.tools.values() if tool.enabled)}")
    print(f"Workflows enabled: {sum(1 for workflow in config.workflows.values() if workflow.get('enabled', False))}")
    print(f"AI Agent enabled: {config.ai_agent['enabled']}")
    print(f"Monitoring enabled: {config.monitoring['enabled']}")
    
    # Save configuration
    config.save_to_file("mcp_config.json")
    print("\nConfiguration saved to mcp_config.json")

