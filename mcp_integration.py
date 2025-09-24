"""
MCP Integration Module for CLM Automation System.
Provides enhanced AI agent capabilities and workflow automation.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from mcp_client import CLMMCPClient, CLMAIAgent

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    name: str
    function: Callable
    parameters: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes
    depends_on: List[str] = None  # Step dependencies

@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    steps_completed: int = 0
    total_steps: int = 0
    results: Dict[str, Any] = None
    error: Optional[str] = None

class CLMWorkflowEngine:
    """
    Workflow engine for automating CLM processes using MCP.
    Enables complex multi-step automation workflows.
    """
    
    def __init__(self, mcp_client: CLMMCPClient):
        self.mcp_client = mcp_client
        self.workflows = {}
        self.running_workflows = {}
        
    def register_workflow(self, workflow_id: str, steps: List[WorkflowStep]) -> bool:
        """Register a new workflow"""
        try:
            self.workflows[workflow_id] = {
                "steps": steps,
                "created_at": datetime.now(),
                "status": WorkflowStatus.PENDING
            }
            logging.info(f"Workflow '{workflow_id}' registered with {len(steps)} steps")
            return True
        except Exception as e:
            logging.error(f"Error registering workflow '{workflow_id}': {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any] = None) -> WorkflowResult:
        """Execute a registered workflow"""
        if workflow_id not in self.workflows:
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                start_time=datetime.now(),
                error=f"Workflow '{workflow_id}' not found"
            )
        
        workflow = self.workflows[workflow_id]
        steps = workflow["steps"]
        
        result = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now(),
            total_steps=len(steps),
            results={}
        )
        
        self.running_workflows[workflow_id] = result
        
        try:
            # Execute steps in order
            for i, step in enumerate(steps):
                logging.info(f"Executing step {i+1}/{len(steps)}: {step.name}")
                
                # Check dependencies
                if step.depends_on:
                    for dep in step.depends_on:
                        if dep not in result.results:
                            raise Exception(f"Dependency '{dep}' not completed")
                
                # Execute step with retry logic
                step_result = await self._execute_step(step, parameters or {})
                result.results[step.name] = step_result
                result.steps_completed += 1
                
                # Check if step failed
                if "error" in step_result:
                    raise Exception(f"Step '{step.name}' failed: {step_result['error']}")
            
            result.status = WorkflowStatus.COMPLETED
            result.end_time = datetime.now()
            logging.info(f"Workflow '{workflow_id}' completed successfully")
            
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.end_time = datetime.now()
            result.error = str(e)
            logging.error(f"Workflow '{workflow_id}' failed: {e}")
        
        finally:
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]
        
        return result
    
    async def _execute_step(self, step: WorkflowStep, workflow_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step with retry logic"""
        for attempt in range(step.max_retries + 1):
            try:
                # Merge step parameters with workflow parameters
                params = {**workflow_params, **step.parameters}
                
                # Execute step with timeout
                result = await asyncio.wait_for(
                    step.function(**params),
                    timeout=step.timeout
                )
                
                return {
                    "success": True,
                    "result": result,
                    "attempt": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                }
                
            except asyncio.TimeoutError:
                error_msg = f"Step '{step.name}' timed out after {step.timeout} seconds"
                logging.warning(f"{error_msg} (attempt {attempt + 1}/{step.max_retries + 1})")
                
                if attempt == step.max_retries:
                    return {"error": error_msg, "attempt": attempt + 1}
                
            except Exception as e:
                error_msg = f"Step '{step.name}' failed: {str(e)}"
                logging.warning(f"{error_msg} (attempt {attempt + 1}/{step.max_retries + 1})")
                
                if attempt == step.max_retries:
                    return {"error": error_msg, "attempt": attempt + 1}
            
            # Wait before retry
            if attempt < step.max_retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {"error": "Max retries exceeded"}

class CLMAutomationOrchestrator:
    """
    High-level orchestrator for CLM automation using MCP.
    Combines AI agents, workflows, and monitoring capabilities.
    """
    
    def __init__(self):
        self.mcp_client = CLMMCPClient()
        self.ai_agent = CLMAIAgent(self.mcp_client)
        self.workflow_engine = CLMWorkflowEngine(self.mcp_client)
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the automation orchestrator"""
        try:
            if await self.ai_agent.initialize():
                self.initialized = True
                await self._register_default_workflows()
                logging.info("CLM Automation Orchestrator initialized successfully")
                return True
            return False
        except Exception as e:
            logging.error(f"Error initializing orchestrator: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the orchestrator"""
        await self.ai_agent.shutdown()
        self.initialized = False
    
    async def _register_default_workflows(self):
        """Register default workflows"""
        
        # Daily Analysis Workflow
        daily_workflow = [
            WorkflowStep(
                name="check_system_status",
                function=self.mcp_client.get_system_status,
                parameters={}
            ),
            WorkflowStep(
                name="run_daily_analysis",
                function=self.mcp_client.run_daily_analysis,
                parameters={"send_email": True}
            ),
            WorkflowStep(
                name="detect_conflicts",
                function=self.mcp_client.detect_conflicts,
                parameters={"conflict_type": "all"}
            ),
            WorkflowStep(
                name="find_expiring_contracts",
                function=self.mcp_client.find_expiring_contracts,
                parameters={"days": 30}
            )
        ]
        
        self.workflow_engine.register_workflow("daily_analysis", daily_workflow)
        
        # Document Processing Workflow
        processing_workflow = [
            WorkflowStep(
                name="process_documents",
                function=self.mcp_client.process_documents,
                parameters={"force_reprocess": False}
            ),
            WorkflowStep(
                name="verify_processing",
                function=self.mcp_client.get_system_status,
                parameters={},
                depends_on=["process_documents"]
            )
        ]
        
        self.workflow_engine.register_workflow("document_processing", processing_workflow)
        
        # Contract Analysis Workflow
        analysis_workflow = [
            WorkflowStep(
                name="search_contracts",
                function=self.mcp_client.search_documents,
                parameters={"query": "contract terms", "n_results": 10}
            ),
            WorkflowStep(
                name="analyze_similarities",
                function=self.mcp_client.find_similar_documents,
                parameters={"doc_id": "sample_doc", "n_results": 5},
                depends_on=["search_contracts"]
            ),
            WorkflowStep(
                name="generate_analysis_report",
                function=self.mcp_client.generate_report,
                parameters={"report_type": "comprehensive"}
            )
        ]
        
        self.workflow_engine.register_workflow("contract_analysis", analysis_workflow)
    
    async def run_daily_automation(self) -> Dict[str, Any]:
        """Run daily automation workflow"""
        if not self.initialized:
            return {"error": "Orchestrator not initialized"}
        
        result = await self.workflow_engine.execute_workflow("daily_analysis")
        return {
            "workflow_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_new_documents(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """Process new documents workflow"""
        if not self.initialized:
            return {"error": "Orchestrator not initialized"}
        
        result = await self.workflow_engine.execute_workflow(
            "document_processing",
            {"force_reprocess": force_reprocess}
        )
        return {
            "workflow_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_contracts(self, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze contracts using AI agent"""
        if not self.initialized:
            return {"error": "Orchestrator not initialized"}
        
        return await self.ai_agent.analyze_contracts(analysis_type)
    
    async def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question about contracts"""
        if not self.initialized:
            return {"error": "Orchestrator not initialized"}
        
        return await self.ai_agent.answer_contract_question(question)
    
    async def start_monitoring(self, check_interval: int = 3600) -> None:
        """Start continuous contract monitoring"""
        if not self.initialized:
            logging.error("Orchestrator not initialized")
            return
        
        await self.ai_agent.monitor_contracts(check_interval)
    
    async def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """Get status of workflows"""
        if workflow_id:
            if workflow_id in self.workflow_engine.running_workflows:
                return {"status": "running", "workflow": self.workflow_engine.running_workflows[workflow_id]}
            elif workflow_id in self.workflow_engine.workflows:
                return {"status": "registered", "workflow": self.workflow_engine.workflows[workflow_id]}
            else:
                return {"error": f"Workflow '{workflow_id}' not found"}
        else:
            return {
                "registered_workflows": list(self.workflow_engine.workflows.keys()),
                "running_workflows": list(self.workflow_engine.running_workflows.keys())
            }

# Example usage and testing
async def main():
    """Example usage of the MCP integration"""
    orchestrator = CLMAutomationOrchestrator()
    
    try:
        # Initialize
        if not await orchestrator.initialize():
            print("Failed to initialize orchestrator")
            return
        
        print("CLM Automation Orchestrator initialized successfully")
        
        # Run daily automation
        print("\nRunning daily automation...")
        daily_result = await orchestrator.run_daily_automation()
        print(f"Daily automation result: {daily_result}")
        
        # Answer a question
        print("\nAnswering a question...")
        question = "What contracts are expiring in the next 30 days?"
        answer = await orchestrator.answer_question(question)
        print(f"Question: {question}")
        print(f"Answer: {answer.get('answer', 'No answer')[:200]}...")
        
        # Get workflow status
        print("\nWorkflow status:")
        status = await orchestrator.get_workflow_status()
        print(f"Registered workflows: {status.get('registered_workflows', [])}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

