"""
Sample code for testing the code analysis functionality.
This module demonstrates various Python features and best practices.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Represents a document in the system."""
    id: str
    content: str
    metadata: Dict[str, str]
    created_at: datetime
    updated_at: Optional[datetime] = None

class DocumentProcessor:
    """Handles document processing operations."""
    
    def __init__(self, chunk_size: int = 1000):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Size of text chunks for processing
        """
        self.chunk_size = chunk_size
        self.processed_docs: List[Document] = []
    
    def process_document(self, doc: Document) -> Dict:
        """
        Process a document and return analysis results.
        
        Args:
            doc: Document to process
            
        Returns:
            Dict containing analysis results
            
        Raises:
            ValueError: If document is empty
        """
        if not doc.content:
            raise ValueError("Document content cannot be empty")
            
        try:
            # Split content into chunks
            chunks = self._split_into_chunks(doc.content)
            
            # Process each chunk
            results = []
            for chunk in chunks:
                result = self._process_chunk(chunk)
                results.append(result)
            
            # Combine results
            return self._combine_results(results)
            
        except Exception as e:
            logger.error(f"Error processing document {doc.id}: {str(e)}")
            raise
    
    def _split_into_chunks(self, content: str) -> List[str]:
        """Split content into chunks of specified size."""
        return [content[i:i + self.chunk_size] 
                for i in range(0, len(content), self.chunk_size)]
    
    def _process_chunk(self, chunk: str) -> Dict:
        """Process a single chunk of text."""
        # Implement chunk processing logic here
        return {
            "length": len(chunk),
            "word_count": len(chunk.split()),
            "processed_at": datetime.now().isoformat()
        }
    
    def _combine_results(self, results: List[Dict]) -> Dict:
        """Combine results from multiple chunks."""
        return {
            "total_chunks": len(results),
            "total_words": sum(r["word_count"] for r in results),
            "processing_time": datetime.now().isoformat()
        }

def main():
    """Main function to demonstrate usage."""
    # Create a sample document
    doc = Document(
        id="test-001",
        content="This is a sample document for testing purposes.",
        metadata={"type": "test", "author": "tester"},
        created_at=datetime.now()
    )
    
    # Process the document
    processor = DocumentProcessor()
    try:
        result = processor.process_document(doc)
        logger.info(f"Processing result: {result}")
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    main() 