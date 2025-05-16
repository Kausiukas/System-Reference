import chromadb
from chromadb.config import Settings
import os
import sqlite3
import pickle
from collections import Counter, defaultdict

VECTORSTORE_PATH = r"D:/DATA/vectorstore"

client = chromadb.PersistentClient(path=VECTORSTORE_PATH, settings=Settings(allow_reset=True))

print(f"Inspecting ChromaDB at: {VECTORSTORE_PATH}\n")

# --- Metadata summary for communications collection ---
comm_sqlite = os.path.join(VECTORSTORE_PATH, 'collection', 'communications', 'storage.sqlite')
if os.path.exists(comm_sqlite):
    conn = sqlite3.connect(comm_sqlite)
    count = conn.execute('SELECT COUNT(*) FROM points').fetchone()[0]
    print(f"communications collection: {count} documents\n")
    filetypes = Counter()
    categories = Counter()
    sources = Counter()
    sample_metadata = []
    # We'll sample up to 10 docs for metadata field structure
    cursor = conn.execute('SELECT point FROM points LIMIT 1000')
    for i, row in enumerate(cursor):
        obj = pickle.loads(row[0])
        meta = obj.payload.get('metadata', {}) if hasattr(obj, 'payload') else {}
        if meta:
            filetypes[meta.get('filetype', 'unknown')] += 1
            categories[meta.get('category', 'unknown')] += 1
            sources[meta.get('source', 'unknown')] += 1
            if len(sample_metadata) < 10:
                sample_metadata.append(meta)
    conn.close()
    print(f"Unique filetypes: {list(filetypes.keys())}")
    print(f"Filetype counts: {dict(filetypes)}\n")
    print(f"Unique categories: {list(categories.keys())}")
    print(f"Category counts: {dict(categories)}\n")
    print(f"Top 5 sources: {sources.most_common(5)}\n")
    print("Sample metadata entries:")
    for meta in sample_metadata:
        print(meta)
        print()
else:
    print("No communications collection found or storage.sqlite missing.")

# --- List all collections and their document counts ---
collections = client.list_collections()
if not collections:
    print("No collections found.")
else:
    for col in collections:
        collection = client.get_collection(col.name)
        docs = collection.get()
        print(f"Collection: {col.name}")
        print(f"  Document count: {len(docs['ids'])}")
        if len(docs['ids']) > 0:
            print(f"  Example document: {docs['documents'][0][:200]}\n")
        else:
            print("  No documents in this collection.\n") 