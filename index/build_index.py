#!/usr/bin/env python3
"""
build_index.py — Builds FAISS vector index from PoE2 game data.

Creates embeddings from:
- Skill tree node names and stats
- Currency/item data from poe.ninja
- Wiki articles (item descriptions, build guides)
- Datamined item/mod databases from RePoE
- Build metadata from poe.ninja build index

Usage:
    /usr/bin/python3 index/build_index.py [--rebuild] [--league "League Name"]

Output:
    - index/vector_index.faiss (FAISS index)
    - index/index_metadata.json (metadata for each vector)
"""

import os
import sys
import json
import gc
import logging
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

# Add project root to path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

DATA_DIR = PROJECT_DIR / "data"
INDEX_DIR = Path(__file__).resolve().parent
CACHE_DIR = DATA_DIR / "cache"
INDEX_DIR.mkdir(exist_ok=True)

# ─── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_sentence_transformer():
    """Load the sentence-transformers model with fallback."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info(f"Model loaded, dim={model.get_sentence_embedding_dimension()}")
        return model
    except ImportError:
        logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)


def load_faiss():
    """Load FAISS with error handling."""
    try:
        import faiss
        return faiss
    except ImportError:
        logger.error("faiss not installed. Run: pip install faiss-cpu")
        sys.exit(1)


def extract_text_chunks(data):
    """Extract text chunks from a JSON data structure for embedding.
    
    Handles nested objects/dicts by flattening into key-value string pairs.
    """
    chunks = []
    
    def flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                if isinstance(value, str) and len(value.strip()) > 0:
                    # Create a searchable text chunk
                    chunks.append({
                        "text": f"{key}: {value}",
                        "metadata_path": path,
                    })
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    chunks.append({
                        "text": f"{key}: {value}",
                        "metadata_path": path,
                    })
                elif isinstance(value, (dict, list)):
                    flatten(value, path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                flatten(item, f"{prefix}[{i}]")
        elif isinstance(obj, str) and len(obj.strip()) > 0:
            chunks.append({
                "text": obj,
                "metadata_path": prefix,
            })
    
    flatten(data)
    return chunks


def build_index():
    """Build the FAISS index from all available data sources."""
    faiss = load_faiss()
    model = load_sentence_transformer()
    
    all_vectors = []
    all_metadata = []
    
    BATCH_SIZE = 64
    total_vectors = 0
    
    def process_file(filepath, category):
        """Load JSON, extract text, embed, add to index."""
        nonlocal total_vectors
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            chunks = extract_text_chunks(data)
            # Filter: only keep non-trivial text (>5 chars)
            chunks = [c for c in chunks if len(c["text"].strip()) > 5]
            
            # Truncate metadata_path in chunks
            for c in chunks:
                c["metadata_path"] = c["metadata_path"][:200]
            
            logger.info(f"  {filepath.name}: {len(chunks)} text chunks")
            
            # Batch embed
            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]
                texts = [c["text"][:512] for c in batch]  # Truncate for embedding
                
                embeddings = model.encode(texts, show_progress_bar=False)
                
                for emb, chunk in zip(embeddings, batch):
                    all_vectors.append(emb)
                    all_metadata.append({
                        "text": chunk["text"][:512],
                        "source_file": filepath.name,
                        "category": category,
                        "path": chunk["metadata_path"],
                        "index": total_vectors,
                    })
                    total_vectors += 1
                
                if i % (BATCH_SIZE * 8) == 0:
                    gc.collect()
            
            logger.info(f"  Processed: {len(chunks)} chunks, total={total_vectors}")
            
        except Exception as e:
            logger.error(f"  Failed to process {filepath}: {e}")
    
    # ─── Process data files ───
    
    # 1. Skill tree
    st_file = DATA_DIR / "skill_tree_poe2_v4.5_us.json"
    if st_file.exists():
        logger.info("Processing skill tree...")
        process_file(st_file, "skill_tree")
    
    # 2. Currency data
    for f in sorted(DATA_DIR.glob("cache/ninja_currency_*.json")):
        logger.info(f"Processing currency: {f.name}")
        process_file(f, "currency")
    
    # 3. Item data
    for f in sorted(DATA_DIR.glob("cache/ninja_items_*.json")):
        logger.info(f"Processing items: {f.name}")
        process_file(f, "items")
    
    # 4. Build index
    bi_file = CACHE_DIR / "ninja_build_index.json"
    if bi_file.exists():
        logger.info("Processing build index...")
        process_file(bi_file, "build_index")
    
    # 5. RePoE data
    for f in sorted(DATA_DIR.glob("cache/repoe_*.json")):
        # Skip large files (>5MB) to avoid memory issues
        if f.stat().st_size > 5_000_000:
            logger.info(f"Skipping large file: {f.name} ({f.stat().st_size / 1e6:.1f} MB)")
            continue
        logger.info(f"Processing RePoE: {f.name}")
        process_file(f, "datamined")
    
    # 6. Wiki pages
    for f in sorted(DATA_DIR.glob("cache/wiki_*.json")):
        logger.info(f"Processing wiki: {f.name}")
        process_file(f, "wiki")
    
    # ─── Build FAISS index ───
    logger.info(f"\\nBuilding FAISS index: {total_vectors} vectors, dim={model.get_sentence_embedding_dimension()}")
    
    vectors_np = np.array(all_vectors).astype("float32")
    
    dim = vectors_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors_np)
    
    # Save index
    index_path = INDEX_DIR / "vector_index.faiss"
    faiss.write_index(index, str(index_path))
    logger.info(f"Index saved: {index_path} ({index_path.stat().st_size / 1e6:.1f} MB)")
    
    # Save metadata
    metadata = {
        "version": datetime.now(timezone.utc).isoformat(),
        "total_vectors": total_vectors,
        "dimension": dim,
        "model": "all-MiniLM-L6-v2",
        "league": os.getenv("POE2_DEFAULT_LEAGUE", "Runes of Aldur"),
        "metadata": all_metadata,
    }
    
    metadata_path = INDEX_DIR / "index_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"Metadata saved: {metadata_path} ({metadata_path.stat().st_size / 1e6:.1f} MB)")
    
    # Summary
    by_category = {}
    for m in all_metadata:
        cat = m["category"]
        by_category[cat] = by_category.get(cat, 0) + 1
    
    logger.info(f"\n=== Index Summary ===")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        logger.info(f"  {cat}: {count:,} vectors")
    logger.info(f"  TOTAL: {total_vectors:,} vectors")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build PoE2 FAISS vector index")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild (ignores cache)")
    parser.add_argument("--league", default="Runes of Aldur", help="League name")
    args = parser.parse_args()
    
    logger.info(f"Building PoE2 index (league={args.league})")
    build_index()
