"""
router.py
Agent router — decides which tool(s) to use based on the user question,
then synthesizes a final answer using the Groq LLM.
"""
 
import os
from dotenv import load_dotenv
from groq import Groq
 
from agent.rag_tool import search, format_context
from agent.data_tool import is_quantitative, analyze
 
load_dotenv()
 
# -----------------------------
# LLM setup
# -----------------------------
def _get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")
    return Groq(api_key=api_key)
 
 
def _generate(system_prompt: str, user_prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()
 
# -----------------------------
# Tool: RAG
# -----------------------------
def _run_rag(query: str, model: str) -> dict:
    chunks = search(query, k=8)
 
    if not chunks:
        return {
            "answer": "I could not find a relevant answer in the approved IRCC sources.",
            "sources": [],
            "tool_used": "rag",
            "context": ""
        }
 
    context = format_context(chunks, max_chars=1800)
 
    system = """You are a helpful IRCC internal assistant.
Answer only from the provided context.
Do not make up information.
If the answer is only partially available, answer with what is available and note any gaps. Only if there is truly nothing relevant, say: "I could not find a complete answer in the approved sources provided."
Write naturally and directly. Keep it concise — 3 to 5 sentences."""
 
    user = f"""Context:
{context}
 
Question: {query}
 
Answer:"""
 
    answer = _generate(system, user, model)
 
    return {
        "answer": answer,
        "sources": chunks,
        "tool_used": "rag",
        "context": context
    }
 
# -----------------------------
# Tool: Data Analyst
# -----------------------------
def _run_data(query: str, model: str) -> dict:
    result = analyze(query)
 
    if not result["success"]:
        # Fall back to RAG if no CSV data found
        return _run_rag(query, model)
 
    system = """You are a data analyst assistant for IRCC.
You are given a statistical summary of CSV data files.
Use the data to answer the question with specific numbers.
Be concise and precise. Cite the figures directly.
If the data doesn't contain enough info to answer, say so clearly."""
 
    user = f"""Data Summary:
{result['data_summary']}
 
Question: {query}
 
Answer with specific numbers:"""
 
    answer = _generate(system, user, model)
 
    return {
        "answer": answer,
        "sources": [],
        "tool_used": "data",
        "context": result["data_summary"],
        "source_file": result.get("source_file", "")
    }
 
# -----------------------------
# Tool: Combined (data + RAG)
# -----------------------------
def _run_combined(query: str, model: str) -> dict:
    data_result = analyze(query)
    rag_chunks = search(query, k=2)
    rag_context = format_context(rag_chunks, max_chars=800) if rag_chunks else ""
 
    system = """You are a data analyst and policy assistant for IRCC.
You have access to both statistical CSV data and approved policy documents.
Combine both sources to give a complete, accurate answer.
Cite specific numbers where available.
Keep it concise — 4 to 6 sentences."""
 
    user = f"""Statistical Data:
{data_result.get('data_summary', 'No data available')}
 
Policy Context:
{rag_context}
 
Question: {query}
 
Answer:"""
 
    answer = _generate(system, user, model)
 
    return {
        "answer": answer,
        "sources": rag_chunks,
        "tool_used": "combined",
        "context": rag_context,
        "data_summary": data_result.get("data_summary", "")
    }
 
# -----------------------------
# Main router
# -----------------------------
def route_and_answer(query: str, model: str = "llama-3.1-8b-instant") -> dict:
    """
    Main entry point. Routes the query to the right tool and returns the answer.
 
    Returns dict with:
        - answer: str
        - tool_used: str (rag / data / combined)
        - sources: list of chunk dicts (for RAG results)
        - context: str
    """
    query_stripped = query.strip()
 
    # Skip small talk check for substantive queries (more than 5 words)
    word_count = len(query_stripped.split())
 
    # Small talk handler
    text = query_stripped.lower()
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    thanks = ["thanks", "thank you", "thankyou", "thx"]
    bye_words = ["bye", "goodbye", "see you"]
 
    if word_count <= 4 and any(g in text for g in greetings):
        return {"answer": "Hello! I can help you explore approved IRCC datasets, reports, and methodologies. What would you like to know?", "tool_used": "small_talk", "sources": [], "context": ""}
    if word_count <= 4 and any(t in text for t in thanks):
        return {"answer": "You're welcome! Feel free to ask anything about approved IRCC sources.", "tool_used": "small_talk", "sources": [], "context": ""}
    if word_count <= 3 and any(b in text for b in bye_words):
        return {"answer": "Goodbye! Feel free to return anytime.", "tool_used": "small_talk", "sources": [], "context": ""}
 
    # Route based on question type
    quantitative = is_quantitative(query_stripped)
 
    if quantitative:
        # Check if there's also policy context needed
        policy_keywords = ["methodology", "policy", "process", "guideline", "regulation", "how does", "what is", "explain"]
        needs_policy = any(kw in text for kw in policy_keywords)
 
        if needs_policy:
            return _run_combined(query_stripped, model)
        else:
            return _run_data(query_stripped, model)
    else:
        return _run_rag(query_stripped, model)