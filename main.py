"""
Main Application Entry Point for CLM Automation System.
Orchestrates all components and provides command-line interface.
"""
import os
import sys
import argparse
from datetime import datetime
from typing import Optional

from config import Config
from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline
from daily_agent import DailyContractAgent
from similarity_detector import DocumentSimilarityDetector
from chatbot_interface import ChatbotInterface
from loguru import logger

class CLMAutomationSystem:
    """
    Main CLM Automation System that orchestrates all components.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.document_processor = None
        self.rag_pipeline = None
        self.daily_agent = None
        self.similarity_detector = None
        self.chatbot_interface = None
        self.initialized = False
        
        # Setup logging
        self._setup_logging()
        
        logger.info("CLM Automation System initialized")

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.LOG_LEVEL
        log_file = f"clm_system_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configure loguru
        logger.remove()  # Remove default handler
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="7 days"
        )

    def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("Initializing CLM Automation System...")
            
            # Initialize document processor
            logger.info("Initializing document processor...")
            self.document_processor = DocumentProcessor(self.config)
            
            # Process documents
            if not self.document_processor.process_all_documents():
                logger.error("Failed to process documents")
                return False
            
            # Initialize RAG pipeline
            logger.info("Initializing RAG pipeline...")
            self.rag_pipeline = RAGPipeline(self.config, self.document_processor)
            
            # Initialize daily agent
            logger.info("Initializing daily agent...")
            self.daily_agent = DailyContractAgent(self.config, self.document_processor, self.rag_pipeline)
            
            # Initialize similarity detector
            logger.info("Initializing similarity detector...")
            self.similarity_detector = DocumentSimilarityDetector(self.config, self.document_processor)
            self.similarity_detector.build_similarity_index()
            
            # Initialize chatbot interface
            logger.info("Initializing chatbot interface...")
            self.chatbot_interface = ChatbotInterface(self.config)
            
            self.initialized = True
            logger.info("CLM Automation System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            return False

    def run_chatbot(self):
        """Run the Streamlit chatbot interface"""
        if not self.initialized:
            logger.error("System not initialized")
            return
        
        logger.info("Starting chatbot interface...")
        self.chatbot_interface.run_streamlit_app()

    def run_daily_report(self) -> bool:
        """Run the daily contract analysis and generate report"""
        if not self.initialized:
            logger.error("System not initialized")
            return False
        
        logger.info("Running daily contract analysis...")
        return self.daily_agent.run_daily_task()

    def ask_question(self, question: str) -> dict:
        """Ask a question about contracts"""
        if not self.initialized:
            return {"error": "System not initialized"}
        
        return self.rag_pipeline.ask_question(question)

    def find_similar_documents(self, doc_id: str, n_results: int = 5) -> list:
        """Find documents similar to a given document"""
        if not self.initialized:
            return []
        
        return self.similarity_detector.find_similar_documents(doc_id, n_results)

    def search_documents(self, query: str, n_results: int = 5) -> list:
        """Search documents by content"""
        if not self.initialized:
            return []
        
        return self.similarity_detector.search_by_content(query, n_results)

    def get_system_status(self) -> dict:
        """Get system status and statistics"""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        # Get document statistics
        all_docs = self.document_processor.get_all_documents()
        
        # Get similarity statistics
        similarity_stats = self.similarity_detector.get_similarity_statistics()
        
        # Get expiring contracts
        expiring_contracts = self.daily_agent._find_expiring_contracts()
        
        # Get conflicts
        conflicts = self.daily_agent._detect_conflicts()
        
        return {
            "status": "initialized",
            "total_documents": len(all_docs),
            "expiring_contracts": len(expiring_contracts),
            "conflicts_detected": len(conflicts),
            "similarity_statistics": similarity_stats,
            "last_updated": datetime.now().isoformat()
        }

    def generate_comprehensive_report(self) -> dict:
        """Generate a comprehensive system report"""
        if not self.initialized:
            return {"error": "System not initialized"}
        
        logger.info("Generating comprehensive system report...")
        
        # Run daily analysis
        daily_report = self.daily_agent.run_daily_analysis()
        
        # Get similarity statistics
        similarity_stats = self.similarity_detector.get_similarity_statistics()
        
        # Get duplicate documents
        duplicates = self.similarity_detector.find_duplicate_documents()
        
        # Get document clusters
        clusters = self.similarity_detector.cluster_documents()
        
        comprehensive_report = {
            "report_date": datetime.now().isoformat(),
            "daily_analysis": daily_report,
            "similarity_analysis": {
                "statistics": similarity_stats,
                "duplicate_groups": len(duplicates),
                "clusters": len(clusters)
            },
            "system_health": self.get_system_status()
        }
        
        # Save report
        report_file = f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        logger.info(f"Comprehensive report saved to {report_file}")
        return comprehensive_report


def main():
    """Main entry point with command-line interface"""
    parser = argparse.ArgumentParser(description="CLM Automation System")
    parser.add_argument("--mode", choices=["chatbot", "daily", "question", "similarity", "status", "report"], 
                       default="chatbot", help="Operation mode")
    parser.add_argument("--question", type=str, help="Question to ask (for question mode)")
    parser.add_argument("--doc-id", type=str, help="Document ID for similarity search")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--n-results", type=int, default=5, help="Number of results to return")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Initialize system
    config = Config()
    system = CLMAutomationSystem(config)
    
    if not system.initialize():
        logger.error("Failed to initialize system")
        sys.exit(1)
    
    # Execute based on mode
    if args.mode == "chatbot":
        system.run_chatbot()
    
    elif args.mode == "daily":
        success = system.run_daily_report()
        if success:
            print("Daily report generated successfully")
        else:
            print("Failed to generate daily report")
            sys.exit(1)
    
    elif args.mode == "question":
        if not args.question:
            print("Please provide a question with --question")
            sys.exit(1)
        
        result = system.ask_question(args.question)
        print(f"Question: {args.question}")
        print(f"Answer: {result['answer']}")
        
        if result['sources']:
            print("\nSources:")
            for i, source in enumerate(result['sources'], 1):
                print(f"{i}. {source['document']} (similarity: {source.get('similarity', 'N/A')})")
    
    elif args.mode == "similarity":
        if not args.doc_id and not args.query:
            print("Please provide either --doc-id or --query")
            sys.exit(1)
        
        if args.doc_id:
            results = system.find_similar_documents(args.doc_id, args.n_results)
            print(f"Similar documents to {args.doc_id}:")
            for doc in results:
                print(f"  - {doc['file_name']} (similarity: {doc['similarity_score']:.3f})")
        
        if args.query:
            results = system.search_documents(args.query, args.n_results)
            print(f"Search results for '{args.query}':")
            for doc in results:
                print(f"  - {doc['file_name']} (similarity: {doc['similarity_score']:.3f})")
    
    elif args.mode == "status":
        status = system.get_system_status()
        print("System Status:")
        print(f"  Status: {status['status']}")
        print(f"  Total Documents: {status['total_documents']}")
        print(f"  Expiring Contracts: {status['expiring_contracts']}")
        print(f"  Conflicts Detected: {status['conflicts_detected']}")
        print(f"  Last Updated: {status['last_updated']}")
    
    elif args.mode == "report":
        report = system.generate_comprehensive_report()
        print("Comprehensive report generated successfully")
        print(f"Report includes:")
        print(f"  - Daily analysis: {len(report['daily_analysis']['expiring_contracts'])} expiring contracts")
        print(f"  - Conflicts: {len(report['daily_analysis']['conflicts'])} detected")
        print(f"  - Similarity analysis: {report['similarity_analysis']['statistics']['total_documents']} documents analyzed")


if __name__ == "__main__":
    main()
