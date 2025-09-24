"""
MCP Server for CLM Automation System.
Provides standardized interface for AI agents to interact with contract management tools.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline
from daily_agent import DailyContractAgent
from similarity_detector import DocumentSimilarityDetector
from main import CLMAutomationSystem

# MCP Server Implementation
class CLMMCPServer:
    """
    MCP Server that exposes CLM Automation functionality to AI agents.
    Provides tools for document processing, analysis, and reporting.
    """
    
    def __init__(self):
        self.config = Config()
        self.clm_system = None
        self.tools = {}
        self._initialize_tools()
        
    def _initialize_tools(self):
        """Initialize available MCP tools"""
        self.tools = {
            "process_documents": {
                "name": "process_documents",
                "description": "Process and index contract documents from the documents directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "force_reprocess": {
                            "type": "boolean",
                            "description": "Force reprocessing of all documents",
                            "default": False
                        }
                    }
                }
            },
            "ask_question": {
                "name": "ask_question",
                "description": "Ask questions about contracts using the RAG pipeline",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask about contracts"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["question"]
                }
            },
            "find_similar_documents": {
                "name": "find_similar_documents",
                "description": "Find documents similar to a given document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "Document ID to find similar documents for"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of similar documents to return",
                            "default": 5
                        }
                    },
                    "required": ["doc_id"]
                }
            },
            "search_documents": {
                "name": "search_documents",
                "description": "Search documents by content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            "run_daily_analysis": {
                "name": "run_daily_analysis",
                "description": "Run daily contract analysis and generate report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "send_email": {
                            "type": "boolean",
                            "description": "Whether to send email report",
                            "default": True
                        }
                    }
                }
            },
            "get_system_status": {
                "name": "get_system_status",
                "description": "Get current system status and statistics",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            "generate_report": {
                "name": "generate_report",
                "description": "Generate comprehensive system report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {
                            "type": "string",
                            "description": "Type of report to generate",
                            "enum": ["daily", "comprehensive", "similarity", "conflicts"],
                            "default": "comprehensive"
                        }
                    }
                }
            },
            "detect_conflicts": {
                "name": "detect_conflicts",
                "description": "Detect conflicts in contract documents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "conflict_type": {
                            "type": "string",
                            "description": "Type of conflicts to detect",
                            "enum": ["all", "address", "date", "contact"],
                            "default": "all"
                        }
                    }
                }
            },
            "find_expiring_contracts": {
                "name": "find_expiring_contracts",
                "description": "Find contracts expiring within specified days",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look ahead",
                            "default": 30
                        }
                    }
                }
            }
        }
    
    async def initialize_system(self) -> bool:
        """Initialize the CLM system"""
        try:
            if not self.clm_system:
                self.clm_system = CLMAutomationSystem(self.config)
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.clm_system.initialize
                )
            return True
        except Exception as e:
            logging.error(f"Error initializing CLM system: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return list(self.tools.values())
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with arguments"""
        if not await self.initialize_system():
            return {"error": "Failed to initialize CLM system"}
        
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            if tool_name == "process_documents":
                return await self._process_documents(arguments)
            elif tool_name == "ask_question":
                return await self._ask_question(arguments)
            elif tool_name == "find_similar_documents":
                return await self._find_similar_documents(arguments)
            elif tool_name == "search_documents":
                return await self._search_documents(arguments)
            elif tool_name == "run_daily_analysis":
                return await self._run_daily_analysis(arguments)
            elif tool_name == "get_system_status":
                return await self._get_system_status(arguments)
            elif tool_name == "generate_report":
                return await self._generate_report(arguments)
            elif tool_name == "detect_conflicts":
                return await self._detect_conflicts(arguments)
            elif tool_name == "find_expiring_contracts":
                return await self._find_expiring_contracts(arguments)
            else:
                return {"error": f"Tool '{tool_name}' not implemented"}
                
        except Exception as e:
            logging.error(f"Error calling tool {tool_name}: {e}")
            return {"error": f"Error executing {tool_name}: {str(e)}"}
    
    async def _process_documents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process documents tool"""
        force_reprocess = args.get("force_reprocess", False)
        
        if force_reprocess:
            # Clear existing database and reprocess
            result = self.clm_system.document_processor.process_all_documents()
        else:
            result = self.clm_system.document_processor.process_all_documents()
        
        return {
            "success": result,
            "message": "Documents processed successfully" if result else "Failed to process documents",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _ask_question(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Ask question tool"""
        question = args["question"]
        max_results = args.get("max_results", 5)
        
        result = self.clm_system.ask_question(question)
        
        return {
            "question": question,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "model": result.get("model", "unknown"),
            "timestamp": result.get("timestamp", datetime.now().isoformat())
        }
    
    async def _find_similar_documents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find similar documents tool"""
        doc_id = args["doc_id"]
        n_results = args.get("n_results", 5)
        
        results = self.clm_system.find_similar_documents(doc_id, n_results)
        
        return {
            "doc_id": doc_id,
            "similar_documents": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _search_documents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search documents tool"""
        query = args["query"]
        n_results = args.get("n_results", 5)
        
        results = self.clm_system.search_documents(query, n_results)
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_daily_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run daily analysis tool"""
        send_email = args.get("send_email", True)
        
        if send_email:
            result = self.clm_system.run_daily_report()
        else:
            result = self.clm_system.daily_agent.run_daily_analysis()
        
        return {
            "success": result,
            "message": "Daily analysis completed successfully" if result else "Failed to complete daily analysis",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_system_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system status tool"""
        status = self.clm_system.get_system_status()
        return status
    
    async def _generate_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report tool"""
        report_type = args.get("report_type", "comprehensive")
        
        if report_type == "comprehensive":
            report = self.clm_system.generate_comprehensive_report()
        elif report_type == "daily":
            report = self.clm_system.daily_agent.run_daily_analysis()
        else:
            return {"error": f"Unknown report type: {report_type}"}
        
        return {
            "report_type": report_type,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _detect_conflicts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Detect conflicts tool"""
        conflict_type = args.get("conflict_type", "all")
        
        conflicts = self.clm_system.daily_agent._detect_conflicts()
        
        if conflict_type != "all":
            conflicts = [c for c in conflicts if c.get("type", "").lower() == conflict_type.lower()]
        
        return {
            "conflict_type": conflict_type,
            "conflicts": conflicts,
            "count": len(conflicts),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _find_expiring_contracts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find expiring contracts tool"""
        days = args.get("days", 30)
        
        # Temporarily update the alert days
        original_days = self.clm_system.daily_agent.expiration_alert_days
        self.clm_system.daily_agent.expiration_alert_days = days
        
        expiring = self.clm_system.daily_agent._find_expiring_contracts()
        
        # Restore original setting
        self.clm_system.daily_agent.expiration_alert_days = original_days
        
        return {
            "days_ahead": days,
            "expiring_contracts": expiring,
            "count": len(expiring),
            "timestamp": datetime.now().isoformat()
        }


# MCP Protocol Implementation
class MCPProtocol:
    """MCP Protocol handler for JSON-RPC communication"""
    
    def __init__(self, server: CLMMCPServer):
        self.server = server
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "tools/list":
                tools = await self.server.list_tools()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools}
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = await self.server.call_tool(tool_name, arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }


# Main MCP Server
async def main():
    """Main MCP server entry point"""
    server = CLMMCPServer()
    protocol = MCPProtocol(server)
    
    # Initialize the system
    await server.initialize_system()
    
    print("CLM MCP Server initialized successfully")
    print("Available tools:")
    tools = await server.list_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Handle requests from stdin (for MCP communication)
    while True:
        try:
            line = input()
            if line.strip():
                request = json.loads(line)
                response = await protocol.handle_request(request)
                print(json.dumps(response))
        except EOFError:
            break
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response))


if __name__ == "__main__":
    asyncio.run(main())
