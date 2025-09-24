"""
MCP Integration Examples for CLM Automation System.
Demonstrates various ways to use MCP for contract management automation.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from mcp_integration import CLMAutomationOrchestrator
from mcp_client import CLMMCPClient, CLMAIAgent
from mcp_config import MCPConfig

class MCPExamples:
    """Collection of MCP integration examples"""
    
    def __init__(self):
        self.orchestrator = None
        self.mcp_client = None
        self.ai_agent = None
    
    async def initialize(self):
        """Initialize MCP components"""
        self.orchestrator = CLMAutomationOrchestrator()
        await self.orchestrator.initialize()
        
        self.mcp_client = CLMMCPClient()
        await self.mcp_client.start_server()
        
        self.ai_agent = CLMAIAgent(self.mcp_client)
        await self.ai_agent.initialize()
    
    async def shutdown(self):
        """Shutdown MCP components"""
        if self.orchestrator:
            await self.orchestrator.shutdown()
        if self.ai_agent:
            await self.ai_agent.shutdown()
        if self.mcp_client:
            await self.mcp_client.stop_server()
    
    async def example_1_basic_question_answering(self):
        """Example 1: Basic question answering using MCP"""
        print("\n" + "="*60)
        print("EXAMPLE 1: Basic Question Answering")
        print("="*60)
        
        questions = [
            "What contracts are expiring soon?",
            "Are there any address conflicts in our contracts?",
            "What companies are involved in our contracts?",
            "What are the financial terms of our contracts?"
        ]
        
        for question in questions:
            print(f"\nQuestion: {question}")
            print("-" * 40)
            
            result = await self.mcp_client.ask_question(question)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
                print(f"Sources: {len(result.get('sources', []))} documents")
                print(f"Model: {result.get('model', 'Unknown')}")
    
    async def example_2_document_analysis(self):
        """Example 2: Document analysis and similarity detection"""
        print("\n" + "="*60)
        print("EXAMPLE 2: Document Analysis")
        print("="*60)
        
        # Search for documents
        search_query = "service agreement"
        print(f"\nSearching for: '{search_query}'")
        search_results = await self.mcp_client.search_documents(search_query, n_results=3)
        
        if "error" not in search_results:
            print(f"Found {search_results.get('count', 0)} documents")
            for i, doc in enumerate(search_results.get('results', [])[:3], 1):
                print(f"{i}. {doc.get('file_name', 'Unknown')} (similarity: {doc.get('similarity_score', 0):.3f})")
        
        # Find similar documents (if we have a document ID)
        if search_results.get('results'):
            first_doc = search_results['results'][0]
            doc_id = first_doc.get('id', '')
            if doc_id:
                print(f"\nFinding documents similar to: {first_doc.get('file_name', 'Unknown')}")
                similar_results = await self.mcp_client.find_similar_documents(doc_id, n_results=3)
                
                if "error" not in similar_results:
                    print(f"Found {similar_results.get('count', 0)} similar documents")
                    for i, doc in enumerate(similar_results.get('similar_documents', [])[:3], 1):
                        print(f"{i}. {doc.get('file_name', 'Unknown')} (similarity: {doc.get('similarity_score', 0):.3f})")
    
    async def example_3_automated_workflows(self):
        """Example 3: Automated workflow execution"""
        print("\n" + "="*60)
        print("EXAMPLE 3: Automated Workflows")
        print("="*60)
        
        # Run daily analysis workflow
        print("\nRunning daily analysis workflow...")
        daily_result = await self.orchestrator.run_daily_automation()
        
        if "error" in daily_result:
            print(f"Error: {daily_result['error']}")
        else:
            workflow_result = daily_result.get('workflow_result', {})
            print(f"Workflow Status: {workflow_result.get('status', 'Unknown')}")
            print(f"Steps Completed: {workflow_result.get('steps_completed', 0)}/{workflow_result.get('total_steps', 0)}")
            
            if workflow_result.get('status') == 'completed':
                print("✅ Daily analysis workflow completed successfully")
            else:
                print(f"❌ Workflow failed: {workflow_result.get('error', 'Unknown error')}")
        
        # Process documents workflow
        print("\nRunning document processing workflow...")
        processing_result = await self.orchestrator.process_new_documents(force_reprocess=False)
        
        if "error" in processing_result:
            print(f"Error: {processing_result['error']}")
        else:
            workflow_result = processing_result.get('workflow_result', {})
            print(f"Workflow Status: {workflow_result.get('status', 'Unknown')}")
            
            if workflow_result.get('status') == 'completed':
                print("✅ Document processing workflow completed successfully")
            else:
                print(f"❌ Workflow failed: {workflow_result.get('error', 'Unknown error')}")
    
    async def example_4_ai_agent_automation(self):
        """Example 4: AI Agent automation capabilities"""
        print("\n" + "="*60)
        print("EXAMPLE 4: AI Agent Automation")
        print("="*60)
        
        # Contract analysis
        print("\nRunning contract analysis...")
        analysis_result = await self.orchestrator.analyze_contracts("conflicts")
        
        if "error" in analysis_result:
            print(f"Error: {analysis_result['error']}")
        else:
            print(f"Analysis completed: {analysis_result.get('count', 0)} conflicts found")
        
        # Expiring contracts analysis
        print("\nAnalyzing expiring contracts...")
        expiring_result = await self.orchestrator.analyze_contracts("expiring")
        
        if "error" in expiring_result:
            print(f"Error: {expiring_result['error']}")
        else:
            print(f"Expiring contracts analysis: {expiring_result.get('count', 0)} contracts expiring soon")
    
    async def example_5_system_monitoring(self):
        """Example 5: System monitoring and status"""
        print("\n" + "="*60)
        print("EXAMPLE 5: System Monitoring")
        print("="*60)
        
        # Get system status
        print("\nGetting system status...")
        status = await self.mcp_client.get_system_status()
        
        if "error" in status:
            print(f"Error: {status['error']}")
        else:
            print(f"System Status: {status.get('status', 'Unknown')}")
            print(f"Total Documents: {status.get('total_documents', 0)}")
            print(f"Expiring Contracts: {status.get('expiring_contracts', 0)}")
            print(f"Conflicts Detected: {status.get('conflicts_detected', 0)}")
            print(f"Last Updated: {status.get('last_updated', 'Unknown')}")
        
        # Generate comprehensive report
        print("\nGenerating comprehensive report...")
        report = await self.mcp_client.generate_report("comprehensive")
        
        if "error" in report:
            print(f"Error: {report['error']}")
        else:
            print("✅ Comprehensive report generated successfully")
            report_data = report.get('report', {})
            if isinstance(report_data, dict):
                print(f"Report includes:")
                print(f"  - Daily analysis: {len(report_data.get('daily_analysis', {}).get('expiring_contracts', []))} expiring contracts")
                print(f"  - Conflicts: {len(report_data.get('daily_analysis', {}).get('conflicts', []))} detected")
    
    async def example_6_custom_workflow(self):
        """Example 6: Creating and running custom workflows"""
        print("\n" + "="*60)
        print("EXAMPLE 6: Custom Workflows")
        print("="*60)
        
        from mcp_integration import WorkflowStep, CLMWorkflowEngine
        
        # Create a custom workflow for contract review
        custom_workflow = [
            WorkflowStep(
                name="get_system_status",
                function=self.mcp_client.get_system_status,
                parameters={}
            ),
            WorkflowStep(
                name="find_expiring_contracts",
                function=self.mcp_client.find_expiring_contracts,
                parameters={"days": 60}  # Next 60 days
            ),
            WorkflowStep(
                name="detect_conflicts",
                function=self.mcp_client.detect_conflicts,
                parameters={"conflict_type": "all"}
            ),
            WorkflowStep(
                name="generate_summary",
                function=self.mcp_client.generate_report,
                parameters={"report_type": "comprehensive"}
            )
        ]
        
        # Register and run custom workflow
        workflow_engine = CLMWorkflowEngine(self.mcp_client)
        workflow_engine.register_workflow("contract_review", custom_workflow)
        
        print("Running custom contract review workflow...")
        result = await workflow_engine.execute_workflow("contract_review")
        
        print(f"Workflow Status: {result.status.value}")
        print(f"Steps Completed: {result.steps_completed}/{result.total_steps}")
        
        if result.status.value == "completed":
            print("✅ Custom workflow completed successfully")
            print(f"Results: {len(result.results)} steps executed")
        else:
            print(f"❌ Workflow failed: {result.error}")
    
    async def example_7_error_handling(self):
        """Example 7: Error handling and resilience"""
        print("\n" + "="*60)
        print("EXAMPLE 7: Error Handling")
        print("="*60)
        
        # Test with invalid parameters
        print("\nTesting error handling with invalid parameters...")
        
        # Invalid question (empty)
        result = await self.mcp_client.ask_question("")
        if "error" in result:
            print(f"✅ Error handled correctly: {result['error']}")
        else:
            print("❌ Error handling failed")
        
        # Invalid document ID
        result = await self.mcp_client.find_similar_documents("invalid_doc_id")
        if "error" in result:
            print(f"✅ Error handled correctly: {result['error']}")
        else:
            print("❌ Error handling failed")
        
        # Test system resilience
        print("\nTesting system resilience...")
        
        # Multiple concurrent requests
        tasks = []
        for i in range(5):
            task = self.mcp_client.get_system_status()
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for result in results if "error" not in result)
        print(f"✅ Concurrent requests: {success_count}/5 successful")
    
    async def run_all_examples(self):
        """Run all MCP examples"""
        print("🚀 CLM MCP Integration Examples")
        print("=" * 60)
        
        try:
            await self.initialize()
            print("✅ MCP components initialized successfully")
            
            # Run all examples
            await self.example_1_basic_question_answering()
            await self.example_2_document_analysis()
            await self.example_3_automated_workflows()
            await self.example_4_ai_agent_automation()
            await self.example_5_system_monitoring()
            await self.example_6_custom_workflow()
            await self.example_7_error_handling()
            
            print("\n" + "="*60)
            print("✅ All examples completed successfully!")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error running examples: {e}")
        finally:
            await self.shutdown()
            print("🔄 MCP components shutdown complete")

# Configuration examples
def example_configuration():
    """Example of MCP configuration"""
    print("\n" + "="*60)
    print("MCP CONFIGURATION EXAMPLES")
    print("="*60)
    
    # Create default configuration
    config = MCPConfig()
    
    print("Default MCP Configuration:")
    print(f"Server: {config.server.host}:{config.server.port}")
    print(f"Transport: {config.server.transport.value}")
    print(f"Tools enabled: {sum(1 for tool in config.tools.values() if tool.enabled)}")
    print(f"Workflows enabled: {sum(1 for workflow in config.workflows.values() if workflow.get('enabled', False))}")
    
    # Save configuration
    config.save_to_file("mcp_config_example.json")
    print("\n✅ Configuration saved to mcp_config_example.json")
    
    # Load configuration
    loaded_config = MCPConfig.load_from_file("mcp_config_example.json")
    print("✅ Configuration loaded successfully")
    
    # Show tool configurations
    print("\nTool Configurations:")
    for tool_name, tool_config in config.tools.items():
        if tool_config.enabled:
            print(f"  - {tool_name}: timeout={tool_config.timeout}s, retries={tool_config.max_retries}")

# Main execution
async def main():
    """Main execution function"""
    print("CLM MCP Integration Examples")
    print("=" * 60)
    
    # Run configuration examples
    example_configuration()
    
    # Run MCP examples
    examples = MCPExamples()
    await examples.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())

