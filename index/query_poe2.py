#!/usr/bin/env python3
"""
query_poe2.py — Query the PoE2 RAG vector index.

Uses FAISS to search for semantically similar content in:
- Skill tree nodes (passive skills, stats)
- Currency exchange rates
- Unique items
- Build metadata (class distribution)
- Wiki articles

Usage:
    /usr/bin/python3 index/query_poe2.py --q "best starter build for mapping"
    /usr/bin/python3 index/query_poe2.py --q "cheap life unique" --k 10
    /usr/bin/python3 index/query_poe2.py --q "Divine Orb price" --category currency
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

INDEX_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"


def load_model_and_index():
    """Load sentence-transformer model and FAISS index."""
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info(f"Model loaded, dim={model.get_embedding_dimension()}")
    
    index_path = INDEX_DIR / "vector_index.faiss"
    metadata_path = INDEX_DIR / "index_metadata.json"
    
    if not index_path.exists():
        print(f"❌ FAISS index not found at {index_path}")
        print("   Run: python3 index/build_index.py")
        sys.exit(1)
    
    index = faiss.read_index(str(index_path))
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    return model, index, metadata


def query(model, index, metadata, query_text, k=10, category=None):
    """Query the index and return top-k results."""
    import numpy as np
    
    # Embed the query
    query_vec = model.encode([query_text], show_progress_bar=False)[0]
    query_vec = np.array([query_vec]).astype("float32")
    
    # Search
    distances, indices = index.search(query_vec, k)
    
    # Get metadata for results
    results = []
    all_metadata = metadata["metadata"]
    
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx == -1 or idx >= len(all_metadata):
            continue
        
        meta = all_metadata[idx]
        
        # Filter by category if specified
        if category and meta.get("category") != category:
            continue
        
        results.append({
            "rank": i + 1,
            "score": float(dist),
            "text": meta.get("text", ""),
            "source": meta.get("source_file", ""),
            "category": meta.get("category", ""),
            "path": meta.get("path", ""),
        })
    
    return results[:k]


def format_results(results, query_text):
    """Format query results for display."""
    print(f"\n🔍 Query: \"{query_text}\"")
    print(f"Found {len(results)} results:\n")
    
    for r in results:
        print(f"  {r['rank']}. [{r['category']}] (score: {r['score']:.4f})")
        print(f"     Source: {r['source']}")
        print(f"     Path: {r['path']}")
        print(f"     Text: {r['text']}")
        print()


def main():
    global logger
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    parser = argparse.ArgumentParser(description="Query PoE2 vector index")
    parser.add_argument("--q", "--query", dest="query", required=True, help="Search query")
    parser.add_argument("--k", type=int, default=10, help="Number of results to return")
    parser.add_argument("--category", choices=["skill_tree", "currency", "items", "build_index", "wiki", "datamined"], 
                       help="Filter by category")
    args = parser.parse_args()
    
    model, index, metadata = load_model_and_index()
    results = query(model, index, metadata, args.query, k=args.k, category=args.category)
    format_results(results, args.query)
    
    # Summary
    by_cat = {}
    for r in results:
        cat = r["category"]
        by_cat[cat] = by_cat.get(cat, 0) + 1
    
    print("---")
    print(f"Results by category:")
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
