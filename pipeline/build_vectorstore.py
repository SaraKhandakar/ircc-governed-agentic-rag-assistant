"""
build_vectorstore.py
Builds a ChromaDB vector store from existing chunks using HuggingFace embeddings.
Run once (or whenever chunks are updated):
    py pipeline/build_vectorstore.py
"""
 
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
 
load_dotenv()
 
# -----------------------------
# Config
# -----------------------------
CHUNKS_PATH = Path("docs/chunks.csv")
VECTORSTORE_DIR = "vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
 
def build():
    print("Loading chunks...")
    df = pd.read_csv(CHUNKS_PATH)
    df.columns = [c.lower().strip() for c in df.columns]
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df = df[df["text"].str.len() > 50].reset_index(drop=True)
    print(f"Loaded {len(df)} chunks.")
 
    print("Loading HuggingFace embedding model (first run downloads ~80MB)...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
 
    print("Building documents...")
    docs = []
    for _, row in df.iterrows():
        doc = Document(
            page_content=row["text"],
            metadata={
                "chunk_id": str(row.get("chunk_id", "")),
                "source_id": str(row.get("source_id", "")),
                "title": str(row.get("title", "")),
                "url": str(row.get("url", "")),
                "type": str(row.get("type", "")),
            }
        )
        docs.append(doc)
 
    print(f"Embedding {len(docs)} documents into ChromaDB...")
    print("This may take a few minutes on first run...")
 
    # Build in batches to avoid memory issues
    batch_size = 100
    vectorstore = None
 
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=VECTORSTORE_DIR
            )
        else:
            vectorstore.add_documents(batch)
 
        print(f"  Embedded {min(i + batch_size, len(docs))}/{len(docs)} chunks...")
 
    print(f"Vector store saved to: {VECTORSTORE_DIR}/")
    print("Done!")
 
if __name__ == "__main__":
    build()