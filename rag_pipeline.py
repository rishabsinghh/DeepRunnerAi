"""
RAG (Retrieval-Augmented Generation) Pipeline for CLM Automation System.
Handles document retrieval and AI-powered question answering.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Try to import required libraries
try:
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import Document
    from langchain.prompts import PromptTemplate
    from langchain.chains import RetrievalQA
    from langchain.embeddings import OpenAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available. Using mock RAG pipeline.")
    
    # Define mock Document class for fallback
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

from config import Config
from document_processor import DocumentProcessor
from loguru import logger

class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline for contract document analysis.
    Combines document retrieval with AI-powered question answering.
    """
    
    def __init__(self, config: Config, document_processor: DocumentProcessor):
        self.config = config
        self.document_processor = document_processor
        self.llm = None
        self.embeddings = None
        self.qa_chain = None
        
        # Initialize AI components
        self._initialize_ai_components()
        
        logger.info("RAG Pipeline initialized successfully")

    def _initialize_ai_components(self):
        """Initialize AI models and components"""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available, using mock AI components")
            return
        
        try:
            # Check if OpenAI API key is available
            if not self.config.OPENAI_API_KEY:
                logger.warning("OpenAI API key not found, using mock AI components")
                return
            
            # Initialize OpenAI LLM
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.1,
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            # Create QA chain
            self._create_qa_chain()
            
            logger.info("AI components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI components: {e}")
            self.llm = None
            self.embeddings = None

    def _create_qa_chain(self):
        """Create the question-answering chain"""
        if not self.llm:
            return
        
        # Define prompt template
        prompt_template = """
You are a contract analysis assistant. Use the following pieces of context to answer the question about contracts.
If you don't know the answer based on the context, say that you don't know.

Context:
{context}

Question: {question}

Answer: Provide a detailed answer based on the context. Always cite the source documents you used to generate your answer.
Include document names and relevant sections when possible.

Sources used:
"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self._create_retriever(),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )

    def _create_retriever(self):
        """Create document retriever"""
        if not LANGCHAIN_AVAILABLE:
            return MockRetriever(self.document_processor)
        
        # For now, use a simple retriever that searches the document processor
        return MockRetriever(self.document_processor)

    def ask_question(self, question: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Ask a question about contracts and get an AI-generated answer.
        
        Args:
            question: The question to ask
            max_results: Maximum number of relevant documents to retrieve
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            if self.qa_chain and LANGCHAIN_AVAILABLE:
                # Use LangChain QA chain
                result = self.qa_chain({"query": question})
                
                return {
                    "answer": result["result"],
                    "sources": self._extract_sources(result.get("source_documents", [])),
                    "question": question,
                    "timestamp": datetime.now().isoformat(),
                    "model": "gpt-3.5-turbo"
                }
            else:
                # Use mock RAG pipeline
                return self._mock_ask_question(question, max_results)
                
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "model": "mock"
            }

    def _mock_ask_question(self, question: str, max_results: int) -> Dict[str, Any]:
        """Mock question answering when AI components are not available"""
        # Search for relevant documents
        search_results = self.document_processor.search_documents(question, max_results)
        
        if not search_results:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "model": "mock"
            }
        
        # Create a simple answer based on retrieved content
        context = "\n\n".join([result['content'] for result in search_results])
        
        # Simple keyword-based answer generation
        answer = self._generate_simple_answer(question, context, search_results)
        
        # Extract sources
        sources = self._extract_sources_from_results(search_results)
        
        return {
            "answer": answer,
            "sources": sources,
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "model": "mock"
        }

    def _generate_simple_answer(self, question: str, context: str, search_results: List[Dict]) -> str:
        """Generate a simple answer based on context and search results"""
        question_lower = question.lower()
        
        # Check for specific question types
        if "expir" in question_lower or "expir" in question_lower:
            return self._answer_expiration_question(context, search_results)
        elif "conflict" in question_lower or "conflict" in question_lower:
            return self._answer_conflict_question(context, search_results)
        elif "address" in question_lower:
            return self._answer_address_question(context, search_results)
        elif "company" in question_lower or "party" in question_lower:
            return self._answer_company_question(context, search_results)
        elif "amount" in question_lower or "price" in question_lower or "cost" in question_lower:
            return self._answer_financial_question(context, search_results)
        else:
            return self._answer_general_question(question, context, search_results)

    def _answer_expiration_question(self, context: str, search_results: List[Dict]) -> str:
        """Answer questions about contract expiration"""
        answer = "Based on the contract documents, here are the expiration-related information:\n\n"
        
        for result in search_results:
            doc_name = result['metadata'].get('file_name', 'Unknown')
            content = result['content']
            
            # Look for expiration dates
            if 'expir' in content.lower():
                answer += f"• {doc_name}: Contains expiration information\n"
                # Extract relevant lines
                lines = content.split('\n')
                for line in lines:
                    if 'expir' in line.lower():
                        answer += f"  - {line.strip()}\n"
        
        return answer

    def _answer_conflict_question(self, context: str, search_results: List[Dict]) -> str:
        """Answer questions about conflicts"""
        answer = "I found the following potential conflicts in the contract documents:\n\n"
        
        # Check for address conflicts
        addresses = {}
        for result in search_results:
            doc_name = result['metadata'].get('file_name', 'Unknown')
            content = result['content']
            
            # Extract addresses
            lines = content.split('\n')
            for line in lines:
                if 'address' in line.lower() and ('techcorp' in line.lower() or 'global' in line.lower()):
                    company = 'TechCorp' if 'techcorp' in line.lower() else 'Global Industries'
                    if company not in addresses:
                        addresses[company] = []
                    addresses[company].append((doc_name, line.strip()))
        
        for company, addr_list in addresses.items():
            if len(addr_list) > 1:
                answer += f"• {company} has different addresses:\n"
                for doc_name, addr in addr_list:
                    answer += f"  - {doc_name}: {addr}\n"
        
        return answer

    def _answer_address_question(self, context: str, search_results: List[Dict]) -> str:
        """Answer questions about addresses"""
        answer = "Here are the addresses found in the contract documents:\n\n"
        
        for result in search_results:
            doc_name = result['metadata'].get('file_name', 'Unknown')
            content = result['content']
            
            lines = content.split('\n')
            for line in lines:
                if 'address' in line.lower() and ('techcorp' in line.lower() or 'global' in line.lower()):
                    answer += f"• {doc_name}: {line.strip()}\n"
        
        return answer

    def _answer_company_question(self, context: str, search_results: List[Dict]) -> str:
        """Answer questions about companies"""
        answer = "Here are the companies mentioned in the contract documents:\n\n"
        
        companies = set()
        for result in search_results:
            content = result['content']
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['client:', 'company:', 'vendor:', 'service provider:']):
                    companies.add(line.strip())
        
        for company in sorted(companies):
            answer += f"• {company}\n"
        
        return answer

    def _answer_financial_question(self, context: str, search_results: List[Dict]) -> str:
        """Answer questions about financial information"""
        answer = "Here are the financial details found in the contract documents:\n\n"
        
        for result in search_results:
            doc_name = result['metadata'].get('file_name', 'Unknown')
            content = result['content']
            
            # Look for monetary values
            lines = content.split('\n')
            for line in lines:
                if '$' in line:
                    answer += f"• {doc_name}: {line.strip()}\n"
        
        return answer

    def _answer_general_question(self, question: str, context: str, search_results: List[Dict]) -> str:
        """Answer general questions"""
        answer = f"Based on the contract documents, here's what I found regarding '{question}':\n\n"
        
        for i, result in enumerate(search_results, 1):
            doc_name = result['metadata'].get('file_name', 'Unknown')
            content = result['content']
            
            answer += f"{i}. {doc_name}:\n"
            # Extract relevant sentences
            sentences = content.split('.')
            relevant_sentences = [s.strip() for s in sentences if any(word in s.lower() for word in question.lower().split())]
            
            if relevant_sentences:
                answer += f"   {'. '.join(relevant_sentences[:2])}.\n\n"
            else:
                answer += f"   {content[:200]}...\n\n"
        
        return answer

    def _extract_sources(self, source_documents: List) -> List[Dict[str, str]]:
        """Extract source information from LangChain documents"""
        sources = []
        for doc in source_documents:
            if hasattr(doc, 'metadata'):
                sources.append({
                    "document": doc.metadata.get('file_name', 'Unknown'),
                    "page": doc.metadata.get('chunk_index', 'N/A'),
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        return sources

    def _extract_sources_from_results(self, search_results: List[Dict]) -> List[Dict[str, str]]:
        """Extract source information from search results"""
        sources = []
        for result in search_results:
            sources.append({
                "document": result['metadata'].get('file_name', 'Unknown'),
                "page": result['metadata'].get('chunk_index', 'N/A'),
                "content": result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                "similarity": f"{1-result['distance']:.3f}" if 'distance' in result else "N/A"
            })
        return sources

    def get_contract_summary(self, contract_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of contracts"""
        if contract_id:
            # Get specific contract
            doc = self.document_processor.get_document_by_id(contract_id)
            if not doc:
                return {"error": "Contract not found"}
            
            documents = [doc]
        else:
            # Get all contracts
            documents = self.document_processor.get_all_documents()
        
        summary = {
            "total_contracts": len(documents),
            "contracts": [],
            "expiring_soon": [],
            "conflicts": []
        }
        
        for doc in documents:
            contract_info = {
                "id": doc['id'],
                "name": doc['metadata'].get('file_name', 'Unknown'),
                "type": doc['metadata'].get('contract_type', 'Unknown'),
                "companies": doc['metadata'].get('companies', []),
                "expiration_date": doc['metadata'].get('expiration_date', 'Unknown')
            }
            summary["contracts"].append(contract_info)
        
        return summary


class MockRetriever:
    """Mock retriever for when LangChain is not available"""
    
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents for a query"""
        results = self.document_processor.search_documents(query, n_results=5)
        
        documents = []
        for result in results:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents


if __name__ == "__main__":
    # Test the RAG pipeline
    from config import Config
    from document_processor import DocumentProcessor
    
    config = Config()
    processor = DocumentProcessor(config)
    
    # Process documents first
    processor.process_all_documents()
    
    # Initialize RAG pipeline
    rag = RAGPipeline(config, processor)
    
    # Test questions
    test_questions = [
        "What contracts are expiring soon?",
        "Are there any address conflicts in the contracts?",
        "What companies are involved in the contracts?",
        "What are the financial terms of the contracts?"
    ]
    
    print("Testing RAG Pipeline:")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 30)
        
        result = rag.ask_question(question)
        print(f"Answer: {result['answer']}")
        
        if result['sources']:
            print("\nSources:")
            for source in result['sources']:
                print(f"  - {source['document']} (similarity: {source.get('similarity', 'N/A')})")
        
        print("\n" + "=" * 50)
