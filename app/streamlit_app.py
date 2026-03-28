import os
import sys
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
# Make sure agent/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))
 
import streamlit as st
from agent.router import route_and_answer
 
st.set_page_config(
    page_title="IRCC RAG Assistant",
    page_icon="🍁",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# Load fonts
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Outfit:wght@300;400;500&display=swap" rel="stylesheet">', unsafe_allow_html=True)
 
# -----------------------------
# Custom CSS
# -----------------------------
st.markdown("""
<style>
 
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0a0e1a;
    color: #e8eaf0;
}
 
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1220 50%, #0a0f1c 100%);
}
 
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}
 
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
 
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1525 0%, #0a1020 100%);
    border-right: 1px solid rgba(255, 77, 77, 0.15);
}
 
.sidebar-logo {
    padding: 1.5rem 0 1rem 0;
    text-align: center;
    border-bottom: 1px solid rgba(255, 77, 77, 0.15);
    margin-bottom: 1.5rem;
}
.sidebar-logo .maple { font-size: 2rem; display: block; margin-bottom: 0.25rem; }
.sidebar-logo .brand {
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.85rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #ff4d4d;
    font-weight: 700;
}
.sidebar-logo .sub { font-size: 0.65rem; color: rgba(232, 234, 240, 0.4); margin-top: 0.15rem; }
 
.stButton > button {
    background: rgba(255, 77, 77, 0.06) !important;
    border: 1px solid rgba(255, 77, 77, 0.2) !important;
    color: rgba(232, 234, 240, 0.8) !important;
    border-radius: 8px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 400 !important;
    padding: 0.5rem 0.75rem !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    line-height: 1.4 !important;
}
.stButton > button:hover {
    background: rgba(255, 77, 77, 0.15) !important;
    border-color: rgba(255, 77, 77, 0.5) !important;
    color: #ffffff !important;
    transform: translateX(3px) !important;
}
 
.main-header { padding: 0.25rem 0 1rem 0; border-bottom: 1px solid rgba(255, 77, 77, 0.12); margin-bottom: 2rem; }
.main-header .eyebrow {
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.72rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #ff4d4d;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.main-header h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 3rem !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    line-height: 1.05 !important;
    margin: 0 0 0.5rem 0 !important;
    letter-spacing: -0.01em !important;
}
.main-header h1 span { color: #ff4d4d; font-style: italic; }
.main-header .subtitle {
    font-size: 0.88rem;
    color: rgba(232, 234, 240, 0.45);
    font-weight: 300;
    font-family: 'Outfit', sans-serif;
    letter-spacing: 0.02em;
}
 
.info-banner {
    background: rgba(255, 77, 77, 0.06);
    border: 1px solid rgba(255, 77, 77, 0.2);
    border-left: 3px solid #ff4d4d;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.8rem;
    color: rgba(232, 234, 240, 0.7);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
 
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.tool-rag { background: rgba(77, 144, 255, 0.1); border: 1px solid rgba(77, 144, 255, 0.3); color: #4d90ff; }
.tool-data { background: rgba(77, 255, 144, 0.1); border: 1px solid rgba(77, 255, 144, 0.3); color: #4dff90; }
.tool-combined { background: rgba(255, 144, 77, 0.1); border: 1px solid rgba(255, 144, 77, 0.3); color: #ff904d; }
.tool-small_talk { background: rgba(200, 200, 200, 0.1); border: 1px solid rgba(200,200,200,0.2); color: #aaa; }
 
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.25rem 0 !important;
    margin-bottom: 0.5rem !important;
}
 
[data-testid="stChatInput"] {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(255, 77, 77, 0.4) !important;
    box-shadow: 0 0 0 3px rgba(255, 77, 77, 0.08) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #e8eaf0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.9rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: rgba(232, 234, 240, 0.3) !important; }
 
[data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important; }
[data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.75rem !important;
    color: rgba(232, 234, 240, 0.4) !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
[aria-selected="true"][data-baseweb="tab"] { color: #ff4d4d !important; border-bottom-color: #ff4d4d !important; background: transparent !important; }
 
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 8px !important;
    margin-bottom: 0.5rem !important;
}
 
.source-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
.source-card .label { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(232, 234, 240, 0.35); font-weight: 600; margin-bottom: 0.2rem; }
.source-card .value { font-size: 0.85rem; color: rgba(232, 234, 240, 0.85); }
 
.status-badge {
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: rgba(255, 77, 77, 0.08); border: 1px solid rgba(255, 77, 77, 0.2);
    border-radius: 20px; padding: 0.3rem 0.7rem; font-size: 0.7rem;
    color: rgba(232, 234, 240, 0.6); letter-spacing: 0.05em;
}
.status-dot {
    width: 6px; height: 6px; background: #ff4d4d; border-radius: 50%;
    box-shadow: 0 0 6px rgba(255, 77, 77, 0.8); animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
 
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 77, 77, 0.3); border-radius: 2px; }
 
</style>
""", unsafe_allow_html=True)
 
# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
 
# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span class="maple">🍁</span>
        <div class="brand">IRCC RAG</div>
        <div class="sub">Agentic Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("**MODEL**")
    model_name = st.selectbox(
        "Model",
        ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"],
        index=0,
        label_visibility="collapsed"
    )
 
    st.markdown("---")
    st.markdown("**AGENT MODE**")
    st.caption("🔵 RAG — policy & methodology questions")
    st.caption("🟢 Data — numerical & statistical questions")
    st.caption("🟠 Combined — questions needing both")
 
    st.markdown("---")
    st.markdown("**SUGGESTED QUESTIONS**")
 
    suggested_questions = [
        "What dataset tracks permanent resident admissions?",
        "What is the methodology for processing times?",
        "How many permanent residents were admitted in total?",
        "What information is included in the Operational Processing Monthly dataset?",
        "Which approved sources relate to citizenship applications?",
        "What is the total count of asylum claimants in Canada?",
    ]
 
    for i, q in enumerate(suggested_questions):
        if st.button(q, key=f"suggested_{i}"):
            st.session_state.pending_question = q
 
    st.markdown("---")
    if st.button("↺  Clear conversation", key="clear_chat"):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()
 
# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="main-header">
    <div class="eyebrow">🍁 Immigration, Refugees and Citizenship Canada</div>
    <h1>IRCC <span>RAG</span> Assistant</h1>
    <div class="subtitle">Ask questions about approved IRCC datasets, reports and methodologies</div>
</div>
""", unsafe_allow_html=True)
 
st.markdown("""
<div class="info-banner">
    <div class="status-badge"><div class="status-dot"></div>Agentic mode active</div>
    &nbsp; Routes questions automatically between semantic search, data analysis and combined reasoning.
</div>
""", unsafe_allow_html=True)
 
# -----------------------------
# Tool badge helper
# -----------------------------
def tool_badge(tool_used: str) -> str:
    labels = {
        "rag": ("🔵", "RAG Retrieval"),
        "data": ("🟢", "Data Analysis"),
        "combined": ("🟠", "Combined"),
        "small_talk": ("⚪", "Chat"),
    }
    icon, label = labels.get(tool_used, ("⚪", tool_used))
    css_class = f"tool-{tool_used}"
    return f'<span class="tool-badge {css_class}">{icon} {label}</span>'
 
# -----------------------------
# Render details tabs
# -----------------------------
def render_details(msg: dict):
    sources = msg.get("sources", [])
    context = msg.get("context", "")
    data_summary = msg.get("data_summary", "")
 
    if not sources and not context and not data_summary:
        return
 
    tabs = st.tabs(["📄 Sources", "📋 Context", "📊 Data"])
 
    with tabs[0]:
        if sources:
            for i, chunk in enumerate(sources[:3], 1):
                st.markdown(f"""
                <div class="source-card">
                    <div class="label">Source {i} · Score: {chunk.get('score', 0):.3f}</div>
                    <div class="value">{chunk.get('title', 'Unknown')}</div>
                </div>
                """, unsafe_allow_html=True)
                if chunk.get("url"):
                    st.markdown(f"[↗ Open Source]({chunk['url']})")
        else:
            st.caption("No RAG sources for this response.")
 
    with tabs[1]:
        if context:
            st.text_area("Context sent to LLM", context, height=200,
                        key=f"ctx_{msg.get('message_id', 'x')}")
        else:
            st.caption("No text context for this response.")
 
    with tabs[2]:
        if data_summary:
            st.text_area("Data summary used", data_summary, height=200,
                        key=f"data_{msg.get('message_id', 'x')}")
        else:
            st.caption("No CSV data was used for this response.")
 
# -----------------------------
# Render chat history
# -----------------------------
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("tool_used"):
            st.markdown(tool_badge(msg["tool_used"]), unsafe_allow_html=True)
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            msg["message_id"] = idx
            render_details(msg)
 
# -----------------------------
# Chat input
# -----------------------------
user_input = st.chat_input("Ask anything about IRCC — policy questions or data questions...")
 
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None
 
# -----------------------------
# Process message
# -----------------------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
 
    with st.chat_message("user"):
        st.markdown(user_input)
 
    with st.chat_message("assistant"):
        try:
            with st.spinner("Agent thinking..."):
                result = route_and_answer(user_input, model=model_name)
 
            tool_used = result.get("tool_used", "rag")
            answer = result.get("answer", "I could not find an answer.")
 
            st.markdown(tool_badge(tool_used), unsafe_allow_html=True)
            st.markdown(answer)
 
            assistant_message = {
                "role": "assistant",
                "content": answer,
                "tool_used": tool_used,
                "sources": result.get("sources", []),
                "context": result.get("context", ""),
                "data_summary": result.get("data_summary", ""),
            }
 
            render_details(assistant_message)
            st.session_state.messages.append(assistant_message)
 
        except Exception as e:
            error_text = f"Error: {e}"
            st.error(error_text)
            st.session_state.messages.append({"role": "assistant", "content": error_text})