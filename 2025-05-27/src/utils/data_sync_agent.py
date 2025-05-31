import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from .vector_store import VectorStore

class DataSyncAgent:
    def __init__(
        self,
        project_context: Dict,
        local_vectorstore: VectorStore,
        main_vectorstore: VectorStore,
        threshold_local_size: int = 1000
    ):
        self.project_context = project_context
        self.local_vectorstore = local_vectorstore
        self.main_vectorstore = main_vectorstore
        self.threshold_local_size = threshold_local_size
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def analyze_local_db(self) -> Dict:
        """Analyze current state of local vectorstore."""
        stats = self.local_vectorstore.get_collection_stats()
        return {
            "total_documents": stats["total_documents"],
            "collection_name": stats["collection_name"]
        }
        
    def find_missing_topics(self) -> List[str]:
        """Identify topics from project context missing in local DB."""
        missing_topics = []
        for keyword in self.project_context.get("focus_keywords", []):
            results = self.local_vectorstore.similarity_search(keyword, k=1)
            if not results or results[0]["distance"] > 0.7:  # High distance means poor match
                missing_topics.append(keyword)
        return missing_topics
        
    def sync_from_main(self) -> Dict:
        """Sync relevant data from main to local vectorstore."""
        missing_topics = self.find_missing_topics()
        loaded_docs = 0
        skipped_docs = 0
        
        # Load documents for each missing topic
        for topic in missing_topics:
            if self.local_vectorstore.get_collection_stats()["total_documents"] >= self.threshold_local_size:
                break
                
            # Search main DB for relevant documents
            results = self.main_vectorstore.similarity_search(
                topic,
                k=5,  # Get top 5 matches per topic
                filter_criteria={"client_id": {"$in": self.project_context.get("clients", [])}}
            )
            
            # Add relevant documents to local DB
            for doc in results:
                if doc["distance"] < 0.7:  # Only add if relevance is high
                    try:
                        self.local_vectorstore.add_texts(
                            [doc["content"]],
                            [doc["metadata"]]
                        )
                        loaded_docs += 1
                    except Exception as e:
                        self.logger.error(f"Failed to load document: {str(e)}")
                        skipped_docs += 1
                else:
                    skipped_docs += 1
                    
        return {
            "loaded": loaded_docs,
            "skipped": skipped_docs,
            "local_vectorstore_size": self.local_vectorstore.get_collection_stats()["total_documents"],
            "missing_topics": missing_topics
        }
        
    def suggest_main_additions(self) -> List[str]:
        """Suggest documents from local DB to be added to main DB."""
        suggestions = []
        
        # Get frequently accessed documents from local DB
        # This is a placeholder - actual implementation would need tracking of document access
        local_stats = self.local_vectorstore.get_collection_stats()
        
        # For now, just suggest documents with high relevance to project keywords
        for keyword in self.project_context.get("focus_keywords", []):
            results = self.local_vectorstore.similarity_search(keyword, k=2)
            for doc in results:
                if doc["distance"] < 0.3:  # Very high relevance
                    suggestions.append(doc["metadata"].get("file_name", "Unknown document"))
                    
        return list(set(suggestions))  # Remove duplicates
        
    def generate_report(self) -> Dict:
        """Generate comprehensive sync report."""
        local_analysis = self.analyze_local_db()
        main_stats = self.main_vectorstore.get_collection_stats()
        missing_topics = self.find_missing_topics()
        suggestions = self.suggest_main_additions()
        
        return {
            "local_size": local_analysis["total_documents"],
            "main_size": main_stats["total_documents"],
            "project_coverage": f"{100 - len(missing_topics) * 10}%",  # Simple coverage estimate
            "missing_keywords": missing_topics,
            "suggested_additions_to_main": suggestions
        }
        
    def run_sync(self, trigger_analysis: bool = True) -> Dict:
        """Run full synchronization process."""
        # Sync from main to local
        sync_results = self.sync_from_main()
        
        # Generate report if requested
        if trigger_analysis:
            report = self.generate_report()
            sync_results.update({"analysis": report})
            
            # Save report to file
            report_path = Path("reports/sync_report.json")
            report_path.parent.mkdir(exist_ok=True)
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
                
        return sync_results 