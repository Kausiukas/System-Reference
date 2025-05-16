import os
import logging
from fastapi import FastAPI, HTTPException, Body
import uvicorn
from chromadb import Client, Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize ChromaDB client
client = Client(Settings(
    persist_directory="D:/DATA/vectorstore",
    anonymized_telemetry=False
))

# Add a degraded mode flag
degraded_mode = False

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global degraded_mode
    try:
        # Check if ChromaDB is responsive
        client.heartbeat()
        degraded_mode = False
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        degraded_mode = True
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/recover")
async def recover():
    """Recovery endpoint to reset the service."""
    global degraded_mode
    try:
        # Reset the ChromaDB client
        client.reset()
        degraded_mode = False
        return {"status": "recovered"}
    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        raise HTTPException(status_code=500, detail="Recovery failed")

@app.post("/search")
async def search(query: str = Body(..., embed=True)):
    """Search endpoint."""
    if degraded_mode:
        raise HTTPException(status_code=503, detail="Service in degraded mode")
    try:
        # Create a collection if it doesn't exist
        collection = client.get_or_create_collection("test_collection")
        
        # Add test documents if the collection is empty
        if collection.count() == 0:
            collection.add(
                documents=["document1", "document2"],
                metadatas=[{"source": "source1"}, {"source": "source2"}],
                ids=["id1", "id2"]
            )
        
        # Perform search using the collection
        results = collection.query(query_texts=[query], n_results=5)
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

if __name__ == "__main__":
    logger.info("Starting Vector Store Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 