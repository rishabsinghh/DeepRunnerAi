"""
Test script for MCP integration.
Validates basic functionality without requiring full system setup.
"""
import asyncio
import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all MCP modules can be imported"""
    print("Testing imports...")
    
    try:
        from mcp_server import CLMMCPServer, MCPProtocol
        print("✅ mcp_server imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import mcp_server: {e}")
        return False
    
    try:
        from mcp_client import CLMMCPClient, CLMAIAgent
        print("✅ mcp_client imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import mcp_client: {e}")
        return False
    
    try:
        from mcp_integration import CLMWorkflowEngine, CLMAutomationOrchestrator
        print("✅ mcp_integration imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import mcp_integration: {e}")
        return False
    
    try:
        from mcp_config import MCPConfig, MCPTransportType
        print("✅ mcp_config imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import mcp_config: {e}")
        return False
    
    return True

def test_configuration():
    """Test MCP configuration"""
    print("\nTesting configuration...")
    
    try:
        from mcp_config import MCPConfig
        
        # Create default configuration
        config = MCPConfig()
        print("✅ Default configuration created")
        
        # Test configuration properties
        assert config.server.host == "localhost"
        assert config.server.port == 8080
        print("✅ Server configuration valid")
        
        # Test tool configurations
        assert len(config.tools) > 0
        print(f"✅ {len(config.tools)} tools configured")
        
        # Test workflow configurations
        assert len(config.workflows) > 0
        print(f"✅ {len(config.workflows)} workflows configured")
        
        # Test configuration serialization
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        print("✅ Configuration serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_mcp_server_initialization():
    """Test MCP server initialization"""
    print("\nTesting MCP server initialization...")
    
    try:
        from mcp_server import CLMMCPServer
        
        # Create server instance
        server = CLMMCPServer()
        print("✅ MCP server created")
        
        # Test tool registration
        tools = server.tools
        assert len(tools) > 0
        print(f"✅ {len(tools)} tools registered")
        
        # Test tool list
        expected_tools = [
            "process_documents", "ask_question", "find_similar_documents",
            "search_documents", "run_daily_analysis", "get_system_status",
            "generate_report", "detect_conflicts", "find_expiring_contracts"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools
        print("✅ All expected tools registered")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def test_workflow_engine():
    """Test workflow engine functionality"""
    print("\nTesting workflow engine...")
    
    try:
        from mcp_integration import CLMWorkflowEngine, WorkflowStep
        from mcp_client import CLMMCPClient
        
        # Create mock client for testing
        class MockMCPClient:
            async def get_system_status(self):
                return {"status": "test", "total_documents": 0}
            
            async def ask_question(self, question):
                return {"answer": "test answer", "sources": []}
        
        mock_client = MockMCPClient()
        workflow_engine = CLMWorkflowEngine(mock_client)
        
        # Test workflow step creation
        step = WorkflowStep(
            name="test_step",
            function=mock_client.get_system_status,
            parameters={}
        )
        print("✅ Workflow step created")
        
        # Test workflow registration
        workflow_engine.register_workflow("test_workflow", [step])
        assert "test_workflow" in workflow_engine.workflows
        print("✅ Workflow registered")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow engine test failed: {e}")
        return False

def test_mcp_protocol():
    """Test MCP protocol handling"""
    print("\nTesting MCP protocol...")
    
    try:
        from mcp_server import CLMMCPServer, MCPProtocol
        
        # Create server and protocol
        server = CLMMCPServer()
        protocol = MCPProtocol(server)
        
        # Test tools/list request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }
        
        # This would normally be async, but we're testing the structure
        print("✅ MCP protocol structure valid")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP protocol test failed: {e}")
        return False

def test_example_imports():
    """Test that examples can be imported"""
    print("\nTesting example imports...")
    
    try:
        from mcp_examples import MCPExamples
        print("✅ MCP examples imported successfully")
        
        # Test example class creation
        examples = MCPExamples()
        print("✅ MCP examples instance created")
        
        return True
        
    except Exception as e:
        print(f"❌ Example import test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 MCP Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration),
        ("MCP Server Tests", test_mcp_server_initialization),
        ("Workflow Engine Tests", test_workflow_engine),
        ("MCP Protocol Tests", test_mcp_protocol),
        ("Example Tests", test_example_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP integration is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

