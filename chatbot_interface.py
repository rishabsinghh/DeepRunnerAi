"""
Streamlit Chatbot Interface for CLM Automation System.
Provides an interactive web interface for contract queries and analysis.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
from typing import List, Dict, Any
import json

# Try to import required libraries
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("Warning: Streamlit not available. Chatbot interface cannot be used.")

from config import Config
from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline
from daily_agent import DailyContractAgent
from loguru import logger

class ChatbotInterface:
    """
    Streamlit-based chatbot interface for contract management.
    Provides interactive querying, document similarity, and reporting features.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.document_processor = None
        self.rag_pipeline = None
        self.daily_agent = None
        self.initialized = False
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Chatbot Interface initialized successfully")

    def _initialize_components(self):
        """Initialize document processor, RAG pipeline, and daily agent"""
        try:
            # Initialize document processor
            self.document_processor = DocumentProcessor(self.config)
            
            # Process documents
            if not self.document_processor.process_all_documents():
                logger.error("Failed to process documents")
                return
            
            # Initialize RAG pipeline
            self.rag_pipeline = RAGPipeline(self.config, self.document_processor)
            
            # Initialize daily agent
            self.daily_agent = DailyContractAgent(self.config, self.document_processor, self.rag_pipeline)
            
            self.initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            self.initialized = False

    def run_streamlit_app(self):
        """Run the Streamlit chatbot application"""
        if not STREAMLIT_AVAILABLE:
            st.error("Streamlit is not available. Please install it with: pip install streamlit")
            return
        
        if not self.initialized:
            st.error("Failed to initialize the system. Please check the logs.")
            return
        
        # Configure page
        st.set_page_config(
            page_title="CLM Automation System",
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Main title
        st.title("📄 Contract Lifecycle Management (CLM) Automation System")
        st.markdown("---")
        
        # Sidebar
        self._create_sidebar()
        
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["🤖 Chatbot", "📊 Contract Analysis", "🔍 Document Similarity", "📈 Daily Reports"])
        
        with tab1:
            self._chatbot_tab()
        
        with tab2:
            self._analysis_tab()
        
        with tab3:
            self._similarity_tab()
        
        with tab4:
            self._reports_tab()

    def _create_sidebar(self):
        """Create the sidebar with system information and controls"""
        st.sidebar.title("System Controls")
        
        # System status
        st.sidebar.subheader("System Status")
        if self.initialized:
            st.sidebar.success("✅ System Online")
        else:
            st.sidebar.error("❌ System Offline")
        
        # Document statistics
        if self.initialized:
            all_docs = self.document_processor.get_all_documents()
            st.sidebar.subheader("Document Statistics")
            st.sidebar.metric("Total Documents", len(all_docs))
            
            # Count by type
            doc_types = {}
            for doc in all_docs:
                doc_type = doc['metadata'].get('directory', 'Unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            for doc_type, count in doc_types.items():
                st.sidebar.metric(f"{doc_type.title()} Documents", count)
        
        # Quick actions
        st.sidebar.subheader("Quick Actions")
        if st.sidebar.button("🔄 Refresh Documents"):
            st.rerun()
        
        if st.sidebar.button("📊 Generate Daily Report"):
            with st.spinner("Generating daily report..."):
                report = self.daily_agent.run_daily_analysis()
                st.session_state['daily_report'] = report
            st.success("Daily report generated!")
        
        # Sample questions
        st.sidebar.subheader("Sample Questions")
        sample_questions = [
            "What contracts are expiring soon?",
            "Are there any address conflicts?",
            "What companies are involved?",
            "Show me financial terms",
            "Find similar contracts"
        ]
        
        for question in sample_questions:
            if st.sidebar.button(question, key=f"sample_{question}"):
                # Queue the question to be processed by the chat tab
                st.session_state['queued_question'] = question
                st.rerun()

    def _chatbot_tab(self):
        """Create the main chatbot interface"""
        st.header("🤖 Contract Query Assistant")
        st.markdown("Ask questions about your contracts and get AI-powered answers with source citations.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Always render the chat input
        user_input = st.chat_input("Ask a question about your contracts...")

        # Support queued question from sidebar, but keep input visible
        queued = st.session_state.pop('queued_question', None) if 'queued_question' in st.session_state else None

        # Prioritize queued question once, otherwise use user input
        prompt = queued or user_input
        if prompt:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self.rag_pipeline.ask_question(prompt)

                # Stream the answer text progressively
                answer_placeholder = st.empty()
                streamed_text = ""
                for token in response.get('answer', "").split():
                    streamed_text += (" " if streamed_text else "") + token
                    answer_placeholder.markdown(streamed_text)
                    time.sleep(0.01)

                # After streaming, show sources
                if response.get('sources'):
                    st.markdown("**Sources:**")
                    for i, source in enumerate(response['sources'], 1):
                        with st.expander(f"Source {i}: {source['document']}"):
                            st.write(f"**Similarity:** {source.get('similarity', 'N/A')}")
                            st.write(f"**Content:** {source['content']}")

                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get('answer', "")
                })

    def _analysis_tab(self):
        """Create the contract analysis tab"""
        st.header("📊 Contract Analysis Dashboard")
        
        if not self.initialized:
            st.error("System not initialized")
            return
        
        # Get all documents
        all_docs = self.document_processor.get_all_documents()
        
        if not all_docs:
            st.warning("No documents found")
            return
        
        # Create analysis sections
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Contract Overview")
            
            # Basic statistics
            total_docs = len(all_docs)
            doc_types = {}
            companies = set()
            
            for doc in all_docs:
                # Count by type
                doc_type = doc['metadata'].get('contract_type', 'Unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                # Collect companies
                doc_companies = doc['metadata'].get('companies', [])
                companies.update(doc_companies)
            
            st.metric("Total Contracts", total_docs)
            st.metric("Unique Companies", len(companies))
            
            # Contract types chart
            if doc_types:
                st.subheader("Contract Types")
                df_types = pd.DataFrame(list(doc_types.items()), columns=['Type', 'Count'])
                st.bar_chart(df_types.set_index('Type'))
        
        with col2:
            st.subheader("Expiration Analysis")
            
            # Find expiring contracts
            expiring_contracts = self.daily_agent._find_expiring_contracts()
            
            if expiring_contracts:
                st.metric("Contracts Expiring Soon", len(expiring_contracts))
                
                # Urgency breakdown
                urgency_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for contract in expiring_contracts:
                    urgency_counts[contract['urgency']] += 1
                
                df_urgency = pd.DataFrame(list(urgency_counts.items()), columns=['Urgency', 'Count'])
                st.bar_chart(df_urgency.set_index('Urgency'))
            else:
                st.info("No contracts expiring in the next 30 days")
        
        # Detailed contract table
        st.subheader("Contract Details")
        
        # Prepare data for table
        table_data = []
        for doc in all_docs:
            table_data.append({
                'File Name': doc['metadata'].get('file_name', 'Unknown'),
                'Type': doc['metadata'].get('contract_type', 'Unknown'),
                'Companies': ', '.join(doc['metadata'].get('companies', [])),
                'Contract ID': doc['metadata'].get('contract_id', 'N/A'),
                'Directory': doc['metadata'].get('directory', 'Unknown')
            })
        
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
        
        # Conflict analysis
        st.subheader("Conflict Detection")
        
        if st.button("🔍 Detect Conflicts"):
            with st.spinner("Analyzing contracts for conflicts..."):
                conflicts = self.daily_agent._detect_conflicts()
            
            if conflicts:
                st.warning(f"Found {len(conflicts)} conflicts")
                
                for i, conflict in enumerate(conflicts, 1):
                    with st.expander(f"Conflict {i}: {conflict['type'].replace('_', ' ').title()}"):
                        st.write(f"**Description:** {conflict['description']}")
                        st.write(f"**Severity:** {conflict['severity']}")
                        
                        if 'company' in conflict:
                            st.write(f"**Company:** {conflict['company']}")
                        
                        if 'conflicting_addresses' in conflict:
                            st.write("**Conflicting Addresses:**")
                            for addr in conflict['conflicting_addresses']:
                                st.write(f"- {addr['document']}: {addr['address']}")
            else:
                st.success("No conflicts detected!")

    def _similarity_tab(self):
        """Create the document similarity tab"""
        st.header("🔍 Document Similarity Search")
        st.markdown("Find documents similar to a selected contract.")
        
        if not self.initialized:
            st.error("System not initialized")
            return
        
        # Get all documents
        all_docs = self.document_processor.get_all_documents()
        
        if not all_docs:
            st.warning("No documents found")
            return
        
        # Document selection
        st.subheader("Select a Document")
        
        doc_options = {}
        for doc in all_docs:
            display_name = f"{doc['metadata'].get('file_name', 'Unknown')} ({doc['metadata'].get('contract_type', 'Unknown')})"
            doc_options[display_name] = doc['id']
        
        selected_display = st.selectbox("Choose a document:", list(doc_options.keys()))
        selected_doc_id = doc_options[selected_display]
        
        # Similarity search
        if st.button("🔍 Find Similar Documents"):
            with st.spinner("Finding similar documents..."):
                similar_docs = self.document_processor.get_similar_documents(selected_doc_id, n_results=5)
            
            if similar_docs:
                st.subheader("Similar Documents")
                
                for i, similar_doc in enumerate(similar_docs, 1):
                    # Skip the document itself
                    if similar_doc['id'] == selected_doc_id:
                        continue
                    
                    with st.expander(f"Similar Document {i}: {similar_doc['metadata'].get('file_name', 'Unknown')}"):
                        st.write(f"**Type:** {similar_doc['metadata'].get('contract_type', 'Unknown')}")
                        st.write(f"**Companies:** {', '.join(similar_doc['metadata'].get('companies', []))}")
                        st.write(f"**Similarity:** {1-similar_doc['distance']:.3f}")
                        st.write(f"**Content Preview:** {similar_doc['content'][:300]}...")
            else:
                st.info("No similar documents found")
        
        # Manual similarity search
        st.subheader("Custom Similarity Search")
        
        search_query = st.text_input("Enter search terms:")
        n_results = st.slider("Number of results:", 1, 10, 5)
        
        if st.button("🔍 Search") and search_query:
            with st.spinner("Searching..."):
                search_results = self.document_processor.search_documents(search_query, n_results)
            
            if search_results:
                st.subheader("Search Results")
                
                for i, result in enumerate(search_results, 1):
                    with st.expander(f"Result {i}: {result['metadata'].get('file_name', 'Unknown')}"):
                        st.write(f"**Type:** {result['metadata'].get('contract_type', 'Unknown')}")
                        st.write(f"**Similarity:** {1-result['distance']:.3f}")
                        st.write(f"**Content:** {result['content'][:500]}...")
            else:
                st.info("No results found")

    def _reports_tab(self):
        """Create the daily reports tab"""
        st.header("📈 Daily Reports & Analytics")
        
        if not self.initialized:
            st.error("System not initialized")
            return
        
        # Generate new report
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("📊 Generate New Report"):
                with st.spinner("Generating daily report..."):
                    report = self.daily_agent.run_daily_analysis()
                    st.session_state['daily_report'] = report
                st.success("Report generated!")
        
        with col2:
            if st.button("📧 Send Email Report"):
                if 'daily_report' in st.session_state:
                    with st.spinner("Sending email report..."):
                        success = self.daily_agent.send_email_report(st.session_state['daily_report'])
                    
                    if success:
                        st.success("Email report sent!")
                    else:
                        st.error("Failed to send email report")
                else:
                    st.warning("Please generate a report first")
        
        # Display report
        if 'daily_report' in st.session_state:
            report = st.session_state['daily_report']
            
            st.subheader(f"Daily Report - {report['date']}")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Expiring Contracts", report['summary']['total_expiring_contracts'])
            
            with col2:
                st.metric("Conflicts Detected", report['summary']['total_conflicts'])
            
            with col3:
                attention_required = "Yes" if report['summary']['requires_immediate_attention'] else "No"
                st.metric("Immediate Attention", attention_required)
            
            # Expiring contracts
            if report['expiring_contracts']:
                st.subheader("Expiring Contracts")
                
                for contract in report['expiring_contracts']:
                    urgency_color = {
                        'CRITICAL': 'red',
                        'HIGH': 'orange',
                        'MEDIUM': 'yellow',
                        'LOW': 'green'
                    }.get(contract['urgency'], 'gray')
                    
                    with st.container():
                        st.markdown(f"**{contract['file_name']}** - <span style='color:{urgency_color}'>{contract['urgency']}</span>", unsafe_allow_html=True)
                        st.write(f"Expires: {contract['expiration_date']} ({contract['days_until_expiry']} days)")
                        st.write(f"Type: {contract['contract_type']}")
                        st.write(f"Companies: {', '.join(contract['companies'])}")
                        st.markdown("---")
            
            # Conflicts
            if report['conflicts']:
                st.subheader("Detected Conflicts")
                
                for conflict in report['conflicts']:
                    with st.expander(f"{conflict['type'].replace('_', ' ').title()} - {conflict['severity']}"):
                        st.write(f"**Description:** {conflict['description']}")
                        
                        if 'company' in conflict:
                            st.write(f"**Company:** {conflict['company']}")
                        
                        if 'conflicting_addresses' in conflict:
                            st.write("**Conflicting Addresses:**")
                            for addr in conflict['conflicting_addresses']:
                                st.write(f"- {addr['document']}: {addr['address']}")
            
            # Recommendations
            if report['recommendations']:
                st.subheader("Recommendations")
                
                for i, rec in enumerate(report['recommendations'], 1):
                    st.write(f"{i}. {rec}")
        else:
            st.info("No report available. Click 'Generate New Report' to create one.")


def main():
    """Main function to run the Streamlit app"""
    if not STREAMLIT_AVAILABLE:
        print("Streamlit is not available. Please install it with: pip install streamlit")
        return
    
    # Initialize configuration
    config = Config()
    
    # Create and run the chatbot interface
    chatbot = ChatbotInterface(config)
    chatbot.run_streamlit_app()


if __name__ == "__main__":
    main()
