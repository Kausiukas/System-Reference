import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.vector_store import VectorStore
from src.utils.data_sync_agent import DataSyncAgent

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/import_data.log'),
            logging.StreamHandler()
        ]
    )

def import_data(
    main_data_dir: str = "D:/DATA",
    local_data_dir: str = "data",
    project_context: dict = None
):
    """Import data using both main and local vectorstores with sync agent."""
    logging.info(f"Starting data import process")
    
    # Ensure local data directory exists
    local_data_dir = os.path.abspath(local_data_dir)
    os.makedirs(local_data_dir, exist_ok=True)
    
    # Initialize vectorstores
    main_vectorstore = VectorStore(persist_directory=main_data_dir, collection_name="main_documents", reset=False)
    local_vectorstore = VectorStore(persist_directory=local_data_dir, collection_name="project_documents", reset=True)
    
    # Default project context if none provided
    if project_context is None:
        project_context = {
            "project_id": Path.cwd().name,
            "focus_keywords": ["project", "document"],
            "clients": [],
            "sales_stage": "initial"
        }
    
    # Initialize sync agent
    sync_agent = DataSyncAgent(
        project_context=project_context,
        local_vectorstore=local_vectorstore,
        main_vectorstore=main_vectorstore
    )
    
    try:
        # Import project-specific documents to local vectorstore
        local_stats = local_vectorstore.import_directory(".")
        logging.info("Local import completed:")
        logging.info(f"- Emails processed: {local_stats['emails']}")
        logging.info(f"- Profiles processed: {local_stats['profiles']}")
        logging.info(f"- Documents processed: {local_stats['documents']}")
        logging.info(f"- Errors encountered: {local_stats['errors']}")
        
        # Run sync agent to get relevant documents from main store
        sync_results = sync_agent.run_sync(trigger_analysis=True)
        logging.info("Sync completed:")
        logging.info(f"- Documents loaded from main: {sync_results['loaded']}")
        logging.info(f"- Documents skipped: {sync_results['skipped']}")
        logging.info(f"- Current local store size: {sync_results['local_vectorstore_size']}")
        
        if "analysis" in sync_results:
            logging.info("Sync Analysis:")
            logging.info(f"- Project coverage: {sync_results['analysis']['project_coverage']}")
            logging.info(f"- Missing keywords: {sync_results['analysis']['missing_keywords']}")
            if sync_results['analysis']['suggested_additions_to_main']:
                logging.info("Suggested documents to add to main store:")
                for doc in sync_results['analysis']['suggested_additions_to_main']:
                    logging.info(f"  - {doc}")
        
    except Exception as e:
        logging.error(f"Error during import/sync: {str(e)}")
        raise

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Set up logging
    setup_logging()
    
    # Example project context
    project_context = {
        "project_id": "2025-05-27",
        "focus_keywords": ["pricing", "proposal", "project", "document"],
        "clients": [],
        "sales_stage": "initial"
    }
    
    # Import data with project context
    import_data(project_context=project_context) 