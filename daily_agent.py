"""
Daily AI Agent for Contract Lifecycle Management.
Automatically generates daily reports on contract status, conflicts, and expirations.
"""
import os
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from config import Config
from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline
from loguru import logger

class DailyContractAgent:
    """
    AI Agent that runs daily to analyze contracts and generate reports.
    Identifies expiring contracts, conflicts, and other important issues.
    """
    
    def __init__(self, config: Config, document_processor: DocumentProcessor, rag_pipeline: RAGPipeline):
        self.config = config
        self.document_processor = document_processor
        self.rag_pipeline = rag_pipeline
        self.expiration_alert_days = config.EXPIRATION_ALERT_DAYS
        
        logger.info("Daily Contract Agent initialized successfully")

    def run_daily_analysis(self) -> Dict[str, Any]:
        """
        Run the daily contract analysis.
        Returns a comprehensive report of findings.
        """
        logger.info("Starting daily contract analysis...")
        
        report = {
            "date": datetime.now().isoformat(),
            "expiring_contracts": self._find_expiring_contracts(),
            "conflicts": self._detect_conflicts(),
            "summary": {},
            "recommendations": []
        }
        
        # Generate summary
        report["summary"] = self._generate_summary(report)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        logger.info("Daily contract analysis completed")
        return report

    def _find_expiring_contracts(self) -> List[Dict[str, Any]]:
        """Find contracts expiring within the alert period"""
        expiring_contracts = []
        cutoff_date = datetime.now() + timedelta(days=self.expiration_alert_days)
        
        # Get all documents
        all_docs = self.document_processor.get_all_documents()
        
        for doc in all_docs:
            expiration_date = self._extract_expiration_date(doc)
            if expiration_date:
                if expiration_date <= cutoff_date:
                    days_until_expiry = (expiration_date - datetime.now()).days
                    
                    expiring_contracts.append({
                        "document_id": doc['id'],
                        "file_name": doc['metadata'].get('file_name', 'Unknown'),
                        "contract_id": doc['metadata'].get('contract_id', 'N/A'),
                        "contract_type": doc['metadata'].get('contract_type', 'Unknown'),
                        "companies": doc['metadata'].get('companies', []),
                        "expiration_date": expiration_date.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "urgency": self._get_urgency_level(days_until_expiry)
                    })
        
        # Sort by urgency (most urgent first)
        expiring_contracts.sort(key=lambda x: x['days_until_expiry'])
        
        logger.info(f"Found {len(expiring_contracts)} expiring contracts")
        return expiring_contracts

    def _extract_expiration_date(self, doc: Dict[str, Any]) -> Optional[datetime]:
        """Extract expiration date from document metadata or content"""
        # First try metadata
        expiration_str = doc['metadata'].get('expiration_date')
        if expiration_str:
            try:
                return datetime.strptime(expiration_str, "%B %d, %Y")
            except ValueError:
                try:
                    return datetime.strptime(expiration_str, "%Y-%m-%d")
                except ValueError:
                    pass
        
        # Try to extract from content
        content = doc['content']
        date_patterns = [
            r'Expiration Date:\s*([A-Za-z0-9\s,]+)',
            r'End Date:\s*([A-Za-z0-9\s,]+)',
            r'expires?\s+on\s+([A-Za-z0-9\s,]+)',
            r'terminates?\s+on\s+([A-Za-z0-9\s,]+)'
        ]
        
        for pattern in date_patterns:
            import re
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                try:
                    return datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        continue
        
        return None

    def _get_urgency_level(self, days_until_expiry: int) -> str:
        """Determine urgency level based on days until expiry"""
        if days_until_expiry <= 7:
            return "CRITICAL"
        elif days_until_expiry <= 14:
            return "HIGH"
        elif days_until_expiry <= 30:
            return "MEDIUM"
        else:
            return "LOW"

    def _detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicts in contract information"""
        conflicts = []
        
        # Get all documents
        all_docs = self.document_processor.get_all_documents()
        
        # Check for address conflicts
        address_conflicts = self._detect_address_conflicts(all_docs)
        conflicts.extend(address_conflicts)
        
        # Check for date conflicts
        date_conflicts = self._detect_date_conflicts(all_docs)
        conflicts.extend(date_conflicts)
        
        # Check for company name conflicts
        company_conflicts = self._detect_company_conflicts(all_docs)
        conflicts.extend(company_conflicts)
        
        logger.info(f"Found {len(conflicts)} conflicts")
        return conflicts

    def _detect_address_conflicts(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicting addresses for the same company"""
        conflicts = []
        company_addresses = {}
        
        for doc in docs:
            companies = doc['metadata'].get('companies', [])
            content = doc['content']
            
            # Extract addresses from content
            import re
            address_patterns = [
                r'Address:\s*([^\n]+)',
                r'Business Address:\s*([^\n]+)',
                r'Office Address:\s*([^\n]+)'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    address = match.strip()
                    for company in companies:
                        if company not in company_addresses:
                            company_addresses[company] = []
                        
                        company_addresses[company].append({
                            'address': address,
                            'document': doc['metadata'].get('file_name', 'Unknown'),
                            'document_id': doc['id']
                        })
        
        # Check for conflicts
        for company, addresses in company_addresses.items():
            unique_addresses = set(addr['address'] for addr in addresses)
            if len(unique_addresses) > 1:
                conflicts.append({
                    "type": "address_conflict",
                    "company": company,
                    "conflicting_addresses": addresses,
                    "description": f"Multiple addresses found for {company}",
                    "severity": "HIGH"
                })
        
        return conflicts

    def _detect_date_conflicts(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicting dates for the same contract"""
        conflicts = []
        contract_dates = {}
        
        for doc in docs:
            contract_id = doc['metadata'].get('contract_id')
            if not contract_id:
                continue
            
            expiration_date = self._extract_expiration_date(doc)
            if expiration_date:
                if contract_id not in contract_dates:
                    contract_dates[contract_id] = []
                
                contract_dates[contract_id].append({
                    'date': expiration_date,
                    'document': doc['metadata'].get('file_name', 'Unknown'),
                    'document_id': doc['id']
                })
        
        # Check for conflicts
        for contract_id, dates in contract_dates.items():
            unique_dates = set(date['date'] for date in dates)
            if len(unique_dates) > 1:
                conflicts.append({
                    "type": "date_conflict",
                    "contract_id": contract_id,
                    "conflicting_dates": dates,
                    "description": f"Multiple expiration dates found for contract {contract_id}",
                    "severity": "HIGH"
                })
        
        return conflicts

    def _detect_company_conflicts(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicting company information"""
        conflicts = []
        company_info = {}
        
        for doc in docs:
            companies = doc['metadata'].get('companies', [])
            content = doc['content']
            
            for company in companies:
                if company not in company_info:
                    company_info[company] = []
                
                # Extract contact information
                import re
                contact_patterns = [
                    r'Contact:\s*([^\n]+)',
                    r'Email:\s*([^\n]+)',
                    r'Phone:\s*([^\n]+)'
                ]
                
                contact_info = {}
                for pattern in contact_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        key = pattern.split(':')[0].strip().lower()
                        contact_info[key] = match.group(1).strip()
                
                if contact_info:
                    company_info[company].append({
                        'contact_info': contact_info,
                        'document': doc['metadata'].get('file_name', 'Unknown'),
                        'document_id': doc['id']
                    })
        
        # Check for conflicts
        for company, info_list in company_info.items():
            if len(info_list) > 1:
                # Check for conflicting contact info
                emails = set()
                phones = set()
                
                for info in info_list:
                    if 'email' in info['contact_info']:
                        emails.add(info['contact_info']['email'])
                    if 'phone' in info['contact_info']:
                        phones.add(info['contact_info']['phone'])
                
                if len(emails) > 1 or len(phones) > 1:
                    conflicts.append({
                        "type": "contact_conflict",
                        "company": company,
                        "conflicting_info": info_list,
                        "description": f"Multiple contact information found for {company}",
                        "severity": "MEDIUM"
                    })
        
        return conflicts

    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the daily report"""
        expiring_count = len(report['expiring_contracts'])
        conflict_count = len(report['conflicts'])
        
        # Count by urgency
        urgency_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for contract in report['expiring_contracts']:
            urgency_counts[contract['urgency']] += 1
        
        # Count by conflict type
        conflict_types = {}
        for conflict in report['conflicts']:
            conflict_type = conflict['type']
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
        
        return {
            "total_expiring_contracts": expiring_count,
            "total_conflicts": conflict_count,
            "urgency_breakdown": urgency_counts,
            "conflict_types": conflict_types,
            "requires_immediate_attention": urgency_counts["CRITICAL"] > 0 or conflict_count > 0
        }

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the analysis"""
        recommendations = []
        
        # Expiration recommendations
        critical_expiring = [c for c in report['expiring_contracts'] if c['urgency'] == 'CRITICAL']
        if critical_expiring:
            recommendations.append(f"URGENT: {len(critical_expiring)} contracts expire within 7 days. Immediate action required.")
        
        high_expiring = [c for c in report['expiring_contracts'] if c['urgency'] == 'HIGH']
        if high_expiring:
            recommendations.append(f"Review {len(high_expiring)} contracts expiring within 14 days for renewal decisions.")
        
        # Conflict recommendations
        address_conflicts = [c for c in report['conflicts'] if c['type'] == 'address_conflict']
        if address_conflicts:
            recommendations.append(f"Resolve {len(address_conflicts)} address conflicts to ensure accurate billing and legal compliance.")
        
        date_conflicts = [c for c in report['conflicts'] if c['type'] == 'date_conflict']
        if date_conflicts:
            recommendations.append(f"Clarify {len(date_conflicts)} date conflicts to prevent legal issues.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("No immediate issues detected. Continue regular monitoring.")
        
        return recommendations

    def generate_email_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML email report"""
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .critical {{ color: #d32f2f; font-weight: bold; }}
                .high {{ color: #f57c00; font-weight: bold; }}
                .medium {{ color: #fbc02d; font-weight: bold; }}
                .low {{ color: #388e3c; }}
                .conflict {{ background-color: #ffebee; padding: 10px; border-left: 4px solid #f44336; margin: 10px 0; }}
                .contract {{ background-color: #f9f9f9; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Daily Contract Management Report</h1>
                <p>Generated on: {report['date']}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <ul>
                    <li>Contracts expiring soon: {report['summary']['total_expiring_contracts']}</li>
                    <li>Conflicts detected: {report['summary']['total_conflicts']}</li>
                    <li>Requires immediate attention: {'Yes' if report['summary']['requires_immediate_attention'] else 'No'}</li>
                </ul>
            </div>
        """
        
        # Expiring contracts section
        if report['expiring_contracts']:
            html_content += """
            <div class="section">
                <h2>Expiring Contracts</h2>
            """
            
            for contract in report['expiring_contracts']:
                urgency_class = contract['urgency'].lower()
                html_content += f"""
                <div class="contract">
                    <h3 class="{urgency_class}">{contract['file_name']} - {contract['urgency']}</h3>
                    <p><strong>Contract ID:</strong> {contract['contract_id']}</p>
                    <p><strong>Type:</strong> {contract['contract_type']}</p>
                    <p><strong>Companies:</strong> {', '.join(contract['companies'])}</p>
                    <p><strong>Expires:</strong> {contract['expiration_date']} ({contract['days_until_expiry']} days)</p>
                </div>
                """
            
            html_content += "</div>"
        
        # Conflicts section
        if report['conflicts']:
            html_content += """
            <div class="section">
                <h2>Detected Conflicts</h2>
            """
            
            for conflict in report['conflicts']:
                html_content += f"""
                <div class="conflict">
                    <h3>{conflict['type'].replace('_', ' ').title()}</h3>
                    <p><strong>Description:</strong> {conflict['description']}</p>
                    <p><strong>Severity:</strong> {conflict['severity']}</p>
                </div>
                """
            
            html_content += "</div>"
        
        # Recommendations section
        if report['recommendations']:
            html_content += """
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
            """
            
            for rec in report['recommendations']:
                html_content += f"<li>{rec}</li>"
            
            html_content += """
                </ul>
            </div>
            """
        
        html_content += """
            <div class="section">
                <p><em>This report was generated automatically by the CLM Automation System.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_content

    def send_email_report(self, report: Dict[str, Any]) -> bool:
        """Send the daily report via email"""
        try:
            if not all([self.config.SMTP_SERVER, self.config.EMAIL_USERNAME, 
                       self.config.EMAIL_PASSWORD, self.config.REPORT_RECIPIENT]):
                logger.warning("Email configuration incomplete, skipping email send")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Contract Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = self.config.REPORT_RECIPIENT
            
            # Create HTML content
            html_content = self.generate_email_report(report)
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Daily report sent to {self.config.REPORT_RECIPIENT}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email report: {e}")
            return False

    def run_daily_task(self) -> bool:
        """Run the complete daily task"""
        try:
            logger.info("Starting daily contract management task...")
            
            # Run analysis
            report = self.run_daily_analysis()
            
            # Save report to file
            report_file = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Daily report saved to {report_file}")
            
            # Send email if configured
            email_sent = self.send_email_report(report)
            
            logger.info("Daily contract management task completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in daily task: {e}")
            return False


if __name__ == "__main__":
    # Test the daily agent
    from config import Config
    from document_processor import DocumentProcessor
    from rag_pipeline import RAGPipeline
    
    config = Config()
    processor = DocumentProcessor(config)
    
    # Process documents first
    processor.process_all_documents()
    
    # Initialize RAG pipeline
    rag = RAGPipeline(config, processor)
    
    # Initialize daily agent
    agent = DailyContractAgent(config, processor, rag)
    
    # Run daily analysis
    print("Running daily contract analysis...")
    report = agent.run_daily_analysis()
    
    print("\nDaily Report Summary:")
    print("=" * 50)
    print(f"Date: {report['date']}")
    print(f"Expiring contracts: {report['summary']['total_expiring_contracts']}")
    print(f"Conflicts detected: {report['summary']['total_conflicts']}")
    print(f"Requires immediate attention: {report['summary']['requires_immediate_attention']}")
    
    if report['expiring_contracts']:
        print("\nExpiring Contracts:")
        for contract in report['expiring_contracts']:
            print(f"  - {contract['file_name']} ({contract['urgency']}) - {contract['days_until_expiry']} days")
    
    if report['conflicts']:
        print("\nConflicts:")
        for conflict in report['conflicts']:
            print(f"  - {conflict['type']}: {conflict['description']}")
    
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")

