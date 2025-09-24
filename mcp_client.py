"""
MCP Client for CLM Automation System.
Provides a client interface for external AI tools to interact with the CLM system.
"""
import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

class CLMMCPClient:
    """
    MCP Client for interacting with the CLM MCP Server.
    Provides a Python interface for external AI tools to use CLM functionality.
    """
    
    def __init__(self, server_path: str = "python mcp_server.py"):
        self.server_path = server_path
        self.server_process = None
        self.initialized = False
        
    async def start_server(self) -> bool:
        """Start the MCP server process"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.initialized = True
            return True
        except Exception as e:
            logging.error(f"Error starting MCP server: {e}")
            return False
    
    async def stop_server(self):
        """Stop the MCP server process"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
        self.initialized = False
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.initialized:
            await self.start_server()
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        try:
            # Send request
            self.server_process.stdin.write(json.dumps(request) + "\n")
            self.server_process.stdin.flush()
            
            # Read response
            response_line = self.server_process.stdout.readline()
            response = json.loads(response_line.strip())
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']['message']}")
            
            return response.get("result", {})
            
        except Exception as e:
            logging.error(f"Error communicating with MCP server: {e}")
            return {"error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        result = await self._send_request("tools/list")
        return result.get("tools", [])
    
    async def process_documents(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """Process contract documents"""
        return await self._send_request("tools/call", {
            "name": "process_documents",
            "arguments": {"force_reprocess": force_reprocess}
        })
    
    async def ask_question(self, question: str, max_results: int = 5) -> Dict[str, Any]:
        """Ask a question about contracts"""
        return await self._send_request("tools/call", {
            "name": "ask_question",
            "arguments": {
                "question": question,
                "max_results": max_results
            }
        })
    
    async def find_similar_documents(self, doc_id: str, n_results: int = 5) -> Dict[str, Any]:
        """Find similar documents"""
        return await self._send_request("tools/call", {
            "name": "find_similar_documents",
            "arguments": {
                "doc_id": doc_id,
                "n_results": n_results
            }
        })
    
    async def search_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search documents by content"""
        return await self._send_request("tools/call", {
            "name": "search_documents",
            "arguments": {
                "query": query,
                "n_results": n_results
            }
        })
    
    async def run_daily_analysis(self, send_email: bool = True) -> Dict[str, Any]:
        """Run daily contract analysis"""
        return await self._send_request("tools/call", {
            "name": "run_daily_analysis",
            "arguments": {"send_email": send_email}
        })
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return await self._send_request("tools/call", {
            "name": "get_system_status",
            "arguments": {}
        })
    
    async def generate_report(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate a report"""
        return await self._send_request("tools/call", {
            "name": "generate_report",
            "arguments": {"report_type": report_type}
        })
    
    async def detect_conflicts(self, conflict_type: str = "all") -> Dict[str, Any]:
        """Detect conflicts in contracts"""
        return await self._send_request("tools/call", {
            "name": "detect_conflicts",
            "arguments": {"conflict_type": conflict_type}
        })
    
    async def find_expiring_contracts(self, days: int = 30) -> Dict[str, Any]:
        """Find expiring contracts"""
        return await self._send_request("tools/call", {
            "name": "find_expiring_contracts",
            "arguments": {"days": days}
        })


class CLMAIAgent:
    """
    AI Agent that uses MCP to interact with the CLM system.
    Provides high-level automation capabilities.
    """
    
    def __init__(self, mcp_client: CLMMCPClient):
        self.mcp_client = mcp_client
        self.agent_id = f"clm_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def initialize(self) -> bool:
        """Initialize the AI agent"""
        return await self.mcp_client.start_server()
    
    async def shutdown(self):
        """Shutdown the AI agent"""
        await self.mcp_client.stop_server()
    
    async def analyze_contracts(self, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Perform comprehensive contract analysis"""
        print(f"[{self.agent_id}] Starting contract analysis...")
        
        # Get system status first
        status = await self.mcp_client.get_system_status()
        print(f"[{self.agent_id}] System status: {status.get('total_documents', 0)} documents")
        
        # Run analysis based on type
        if analysis_type == "comprehensive":
            # Run daily analysis
            daily_result = await self.mcp_client.run_daily_analysis(send_email=False)
            print(f"[{self.agent_id}] Daily analysis: {daily_result.get('success', False)}")
            
            # Generate comprehensive report
            report = await self.mcp_client.generate_report("comprehensive")
            print(f"[{self.agent_id}] Comprehensive report generated")
            
            return {
                "agent_id": self.agent_id,
                "analysis_type": analysis_type,
                "daily_analysis": daily_result,
                "comprehensive_report": report,
                "timestamp": datetime.now().isoformat()
            }
        
        elif analysis_type == "conflicts":
            conflicts = await self.mcp_client.detect_conflicts("all")
            print(f"[{self.agent_id}] Found {conflicts.get('count', 0)} conflicts")
            return conflicts
        
        elif analysis_type == "expiring":
            expiring = await self.mcp_client.find_expiring_contracts(30)
            print(f"[{self.agent_id}] Found {expiring.get('count', 0)} expiring contracts")
            return expiring
        
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    
    async def answer_contract_question(self, question: str) -> Dict[str, Any]:
        """Answer a question about contracts using RAG"""
        print(f"[{self.agent_id}] Answering question: {question}")
        
        result = await self.mcp_client.ask_question(question)
        
        if "error" not in result:
            print(f"[{self.agent_id}] Answer: {result.get('answer', 'No answer')[:100]}...")
            print(f"[{self.agent_id}] Sources: {len(result.get('sources', []))}")
        
        return result
    
    async def find_related_documents(self, query: str, doc_id: str = None) -> Dict[str, Any]:
        """Find documents related to a query or document"""
        if doc_id:
            print(f"[{self.agent_id}] Finding documents similar to: {doc_id}")
            result = await self.mcp_client.find_similar_documents(doc_id)
        else:
            print(f"[{self.agent_id}] Searching documents for: {query}")
            result = await self.mcp_client.search_documents(query)
        
        print(f"[{self.agent_id}] Found {result.get('count', 0)} related documents")
        return result
    
    async def monitor_contracts(self, check_interval: int = 3600) -> None:
        """Monitor contracts continuously"""
        print(f"[{self.agent_id}] Starting contract monitoring (interval: {check_interval}s)")
        
        while True:
            try:
                # Check for expiring contracts
                expiring = await self.mcp_client.find_expiring_contracts(7)  # Next 7 days
                if expiring.get('count', 0) > 0:
                    print(f"[{self.agent_id}] ALERT: {expiring['count']} contracts expiring in 7 days")
                
                # Check for conflicts
                conflicts = await self.mcp_client.detect_conflicts("all")
                if conflicts.get('count', 0) > 0:
                    print(f"[{self.agent_id}] ALERT: {conflicts['count']} conflicts detected")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                print(f"[{self.agent_id}] Monitoring stopped by user")
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error in monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry


# Example usage and testing
async def main():
    """Example usage of the MCP client"""
    # Create MCP client
    mcp_client = CLMMCPClient()
    
    # Create AI agent
    agent = CLMAIAgent(mcp_client)
    
    try:
        # Initialize
        if not await agent.initialize():
            print("Failed to initialize AI agent")
            return
        
        print("AI Agent initialized successfully")
        
        # List available tools
        tools = await mcp_client.list_tools()
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Example: Ask a question
        question = "What contracts are expiring soon?"
        answer = await agent.answer_contract_question(question)
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer.get('answer', 'No answer')}")
        
        # Example: Run analysis
        analysis = await agent.analyze_contracts("conflicts")
        print(f"\nConflict Analysis: {analysis.get('count', 0)} conflicts found")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

