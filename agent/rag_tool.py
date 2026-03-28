"""
rag_tool.py
Semantic search tool using ChromaDB + HuggingFace embeddings.
Returns relevant text chunks with source metadata.
"""
 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
 
VECTORSTORE_DIR = "vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
 
# Load once at module level (avoids reloading on every query)
_embeddings = None
_vectorstore = None
 
def _load():
    global _embeddings, _vectorstore
    if _vectorstore is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        _vectorstore = Chroma(
            persist_directory=VECTORSTORE_DIR,
            embedding_function=_embeddings
        )
 
def search(query: str, k: int = 4) -> list[dict]:
    """
    Search the vector store for relevant chunks.
    Returns a list of dicts with 'text', 'source_id', 'title', 'url', 'score'.
    """
    _load()
 
    results = _vectorstore.similarity_search_with_relevance_scores(query, k=k)
 
    output = []
    for doc, score in results:
        output.append({
            "text": doc.page_content,
            "source_id": doc.metadata.get("source_id", ""),
            "title": doc.metadata.get("title", ""),
            "url": doc.metadata.get("url", ""),
            "chunk_id": doc.metadata.get("chunk_id", ""),
            "score": round(score, 4)
        })
 
    return output
 
 
def format_context(chunks: list[dict], max_chars: int = 2000) -> str:
    """
    Format retrieved chunks into a context string for the LLM.
    Limits total characters to avoid token limit errors.
    """
    context_parts = []
    total = 0
 
    for chunk in chunks:
        text = chunk["text"]
        title = chunk.get("title", "Unknown Source")
        remaining = max_chars - total
 
        if remaining <= 0:
            break
 
        snippet = text[:remaining]
        context_parts.append(f"[Source: {title}]\n{snippet}")
        total += len(snippet)
 
    return "\n\n".join(context_parts)