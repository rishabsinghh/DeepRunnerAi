# MCP Integration for CLM Automation System

This document describes the integration of Model Context Protocol (MCP) into the CLM Automation System, enabling AI agents to interact with contract management tools through a standardized interface.

## 🚀 Overview

The MCP integration transforms your CLM system into an AI-agent-ready platform, allowing external AI tools to:
- Process and analyze contract documents
- Answer questions about contracts using RAG
- Detect conflicts and expiring contracts
- Generate automated reports
- Execute complex workflows
- Monitor system health and status

## 📁 MCP Components

### Core Files

| File | Description |
|------|-------------|
| `mcp_server.py` | MCP server implementation with JSON-RPC protocol |
| `mcp_client.py` | MCP client for external AI tool integration |
| `mcp_integration.py` | Workflow engine and automation orchestrator |
| `mcp_config.py` | Configuration management for MCP settings |
| `mcp_examples.py` | Comprehensive examples and demonstrations |

### Integration Points

- **Document Processing**: AI agents can trigger document ingestion and indexing
- **RAG Pipeline**: Natural language queries about contracts
- **Daily Agent**: Automated contract analysis and reporting
- **Similarity Detection**: Document comparison and clustering
- **Conflict Detection**: Automated conflict identification
- **System Monitoring**: Health checks and status reporting

## 🛠️ Installation

### 1. Install MCP Dependencies

```bash
# Install MCP-specific dependencies
pip install mcp==0.1.0 jsonrpc-requests==0.4.0 aiohttp==3.9.1 websockets==12.0

# Or install all dependencies
pip install -r requirements_full.txt
```

### 2. Configure MCP Settings

```bash
# Set environment variables (optional)
export MCP_HOST=localhost
export MCP_PORT=8080
export MCP_TRANSPORT=stdio
export MCP_LOG_LEVEL=INFO
export MCP_ENABLE_AUTH=false
```

### 3. Initialize MCP Server

```python
from mcp_server import CLMMCPServer
import asyncio

async def start_mcp_server():
    server = CLMMCPServer()
    await server.initialize_system()
    print("MCP Server ready for connections")

asyncio.run(start_mcp_server())
```

## 🔧 Usage

### Basic MCP Client Usage

```python
from mcp_client import CLMMCPClient
import asyncio

async def basic_example():
    # Create MCP client
    client = CLMMCPClient()
    
    # Start server
    await client.start_server()
    
    # Ask a question about contracts
    result = await client.ask_question("What contracts are expiring soon?")
    print(f"Answer: {result['answer']}")
    
    # Get system status
    status = await client.get_system_status()
    print(f"Total documents: {status['total_documents']}")
    
    # Cleanup
    await client.stop_server()

asyncio.run(basic_example())
```

### AI Agent Integration

```python
from mcp_client import CLMAIAgent
import asyncio

async def ai_agent_example():
    # Create AI agent
    agent = CLMAIAgent(CLMMCPClient())
    await agent.initialize()
    
    # Analyze contracts
    analysis = await agent.analyze_contracts("conflicts")
    print(f"Found {analysis.get('count', 0)} conflicts")
    
    # Answer questions
    answer = await agent.answer_contract_question(
        "What are the financial terms of our contracts?"
    )
    print(f"Answer: {answer['answer']}")
    
    # Start monitoring
    await agent.monitor_contracts(check_interval=3600)  # Check every hour

asyncio.run(ai_agent_example())
```

### Workflow Automation

```python
from mcp_integration import CLMAutomationOrchestrator
import asyncio

async def workflow_example():
    # Create orchestrator
    orchestrator = CLMAutomationOrchestrator()
    await orchestrator.initialize()
    
    # Run daily automation
    result = await orchestrator.run_daily_automation()
    print(f"Daily automation: {result['workflow_result']['status']}")
    
    # Process new documents
    result = await orchestrator.process_new_documents()
    print(f"Document processing: {result['workflow_result']['status']}")
    
    # Custom analysis
    analysis = await orchestrator.analyze_contracts("comprehensive")
    print(f"Analysis completed: {len(analysis)} results")

asyncio.run(workflow_example())
```

## 🎯 Available MCP Tools

### Document Management
- `process_documents`: Process and index contract documents
- `search_documents`: Search documents by content
- `find_similar_documents`: Find documents similar to a given document

### Contract Analysis
- `ask_question`: Ask questions about contracts using RAG
- `detect_conflicts`: Detect conflicts in contract documents
- `find_expiring_contracts`: Find contracts expiring within specified days

### Reporting & Monitoring
- `run_daily_analysis`: Run daily contract analysis and generate report
- `generate_report`: Generate comprehensive system report
- `get_system_status`: Get current system status and statistics

## 🔄 Workflow Examples

### 1. Daily Contract Monitoring

```python
# Automated daily workflow
workflow_steps = [
    WorkflowStep("check_system_status", get_system_status, {}),
    WorkflowStep("run_daily_analysis", run_daily_analysis, {"send_email": True}),
    WorkflowStep("detect_conflicts", detect_conflicts, {"conflict_type": "all"}),
    WorkflowStep("find_expiring_contracts", find_expiring_contracts, {"days": 30})
]

workflow_engine.register_workflow("daily_monitoring", workflow_steps)
result = await workflow_engine.execute_workflow("daily_monitoring")
```

### 2. Document Processing Pipeline

```python
# Document processing workflow
processing_steps = [
    WorkflowStep("process_documents", process_documents, {"force_reprocess": False}),
    WorkflowStep("verify_processing", get_system_status, {}),
    WorkflowStep("generate_summary", generate_report, {"report_type": "comprehensive"})
]

workflow_engine.register_workflow("document_processing", processing_steps)
result = await workflow_engine.execute_workflow("document_processing")
```

### 3. Contract Analysis Workflow

```python
# Contract analysis workflow
analysis_steps = [
    WorkflowStep("search_contracts", search_documents, {"query": "contract terms", "n_results": 10}),
    WorkflowStep("analyze_similarities", find_similar_documents, {"doc_id": "sample_doc", "n_results": 5}),
    WorkflowStep("detect_conflicts", detect_conflicts, {"conflict_type": "all"}),
    WorkflowStep("generate_analysis_report", generate_report, {"report_type": "comprehensive"})
]

workflow_engine.register_workflow("contract_analysis", analysis_steps)
result = await workflow_engine.execute_workflow("contract_analysis")
```

## ⚙️ Configuration

### MCP Server Configuration

```python
from mcp_config import MCPConfig

# Create configuration
config = MCPConfig()

# Customize server settings
config.server.host = "0.0.0.0"
config.server.port = 8080
config.server.transport = MCPTransportType.HTTP

# Enable/disable tools
config.tools["ask_question"].enabled = True
config.tools["ask_question"].timeout = 60
config.tools["ask_question"].rate_limit = 50

# Configure workflows
config.workflows["daily_analysis"]["enabled"] = True
config.workflows["daily_analysis"]["schedule"] = "0 9 * * *"  # Daily at 9 AM

# Save configuration
config.save_to_file("mcp_config.json")
```

### Environment Variables

```bash
# Server configuration
export MCP_HOST=localhost
export MCP_PORT=8080
export MCP_TRANSPORT=stdio
export MCP_LOG_LEVEL=INFO

# Security configuration
export MCP_ENABLE_AUTH=true
export MCP_API_KEY=your_api_key_here
export MCP_ALLOWED_ORIGINS=localhost,127.0.0.1

# Tool configuration
export MCP_TOOL_TIMEOUT=300
export MCP_TOOL_MAX_RETRIES=3
export MCP_TOOL_RATE_LIMIT=100
```

## 🔒 Security Considerations

### Authentication
- API key authentication (optional)
- Origin validation
- Rate limiting per tool
- Request timeout controls

### Access Control
- Tool-level permissions
- Workflow execution limits
- Resource usage monitoring
- Audit logging

### Data Protection
- Encrypted communication (when using HTTP/WebSocket)
- Secure credential storage
- Input validation and sanitization
- Error message sanitization

## 📊 Monitoring & Logging

### System Monitoring
```python
# Get system status
status = await client.get_system_status()
print(f"Documents: {status['total_documents']}")
print(f"Expiring: {status['expiring_contracts']}")
print(f"Conflicts: {status['conflicts_detected']}")
```

### Workflow Monitoring
```python
# Monitor workflow execution
workflow_status = await orchestrator.get_workflow_status("daily_analysis")
print(f"Status: {workflow_status['status']}")
print(f"Progress: {workflow_status['workflow'].steps_completed}/{workflow_status['workflow'].total_steps}")
```

### Logging Configuration
```python
import logging

# Configure MCP logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
```

## 🧪 Testing

### Run Examples
```bash
# Run comprehensive examples
python mcp_examples.py

# Test individual components
python -c "from mcp_client import CLMMCPClient; import asyncio; asyncio.run(CLMMCPClient().start_server())"
```

### Unit Tests
```python
import pytest
from mcp_client import CLMMCPClient

@pytest.mark.asyncio
async def test_ask_question():
    client = CLMMCPClient()
    await client.start_server()
    
    result = await client.ask_question("What contracts are expiring?")
    assert "error" not in result
    assert "answer" in result
    
    await client.stop_server()
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_full.txt .
RUN pip install -r requirements_full.txt

COPY . .
EXPOSE 8080

CMD ["python", "mcp_server.py"]
```

### Production Considerations
- Use persistent storage for ChromaDB
- Implement proper authentication
- Set up monitoring and alerting
- Configure load balancing for multiple instances
- Implement backup and recovery procedures

## 🔧 Troubleshooting

### Common Issues

1. **MCP Server Not Starting**
   ```bash
   # Check dependencies
   pip install -r requirements_full.txt
   
   # Check configuration
   python mcp_config.py
   ```

2. **Tool Execution Failures**
   ```python
   # Check tool configuration
   config = MCPConfig()
   print(config.get_tool_config("ask_question"))
   
   # Test individual tools
   result = await client.ask_question("test question")
   print(result)
   ```

3. **Workflow Execution Issues**
   ```python
   # Check workflow status
   status = await orchestrator.get_workflow_status()
   print(f"Running workflows: {status['running_workflows']}")
   
   # Check step dependencies
   for step in workflow_steps:
       print(f"Step: {step.name}, Dependencies: {step.depends_on}")
   ```

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('mcp').setLevel(logging.DEBUG)

# Run with verbose output
python mcp_server.py --debug
```

## 📈 Performance Optimization

### Tool Optimization
- Adjust timeout values based on tool complexity
- Implement caching for frequently accessed data
- Use connection pooling for database operations
- Optimize retry strategies

### Workflow Optimization
- Parallel execution of independent steps
- Resource usage monitoring
- Workflow result caching
- Error recovery strategies

### System Optimization
- Load balancing for multiple MCP servers
- Database connection optimization
- Memory usage monitoring
- CPU usage optimization

## 🤝 Contributing

### Adding New Tools
1. Define tool in `mcp_server.py`
2. Implement tool logic
3. Add configuration in `mcp_config.py`
4. Create tests
5. Update documentation

### Adding New Workflows
1. Define workflow steps
2. Register workflow in `mcp_integration.py`
3. Add configuration options
4. Create examples
5. Update documentation

## 📚 Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [CLM System Documentation](README.md)
- [API Reference](docs/api_reference.md)

## 🆘 Support

For MCP integration support:
- Check the troubleshooting section
- Review example code in `mcp_examples.py`
- Check system logs for error details
- Create an issue in the repository

---

**Note**: MCP integration enhances your CLM system with AI agent capabilities while maintaining all existing functionality. The integration is designed to be backward compatible and can be enabled/disabled as needed.

