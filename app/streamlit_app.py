import os
from pathlib import Path

import pandas as pd
import streamlit as st
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CATALOG_PATH = Path("catalog/approved_source_catalog.csv")
CHUNKS_PATH = Path("chunks/chunks.csv")

st.set_page_config(
    page_title="IRCC Governed RAG Assistant",
    page_icon="📘",
    layout="wide"
)

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
    st.header("Settings")

    top_chunks = st.slider("Top chunks to retrieve", 1, 10, 5)
    show_technical = st.checkbox("Show technical details", value=False)

    model_name = st.selectbox(
        "Groq model",
        ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"],
        index=0
    )

    score_threshold = st.slider(
        "Minimum relevance score",
        min_value=0.00,
        max_value=1.00,
        value=0.15,
        step=0.01
    )

    st.markdown("---")
    st.subheader("Suggested Questions")

    suggested_questions = [
        "What dataset tracks permanent resident admissions?",
        "What is the methodology for processing times?",
        "What information is included in the Operational Processing Monthly IRCC Updates dataset?",
        "Which approved sources relate to citizenship applications?",
        "What information is available about asylum claimants in Canada?"
    ]

    for i, q in enumerate(suggested_questions):
        if st.button(q, key=f"suggested_{i}"):
            st.session_state.pending_question = q

    st.markdown("---")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()

# -----------------------------
# Data loaders
# -----------------------------
@st.cache_data
def load_catalog():
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog file not found: {CATALOG_PATH}")

    df = pd.read_csv(CATALOG_PATH)
    df.columns = [c.lower().strip() for c in df.columns]

    if "approved" not in df.columns:
        raise ValueError("The catalog must contain an 'approved' column.")

    df["approved"] = df["approved"].astype(str).str.strip().str.lower()
    df = df[df["approved"].isin(["yes", "y", "true", "1", "approved"])].copy()

    expected_cols = [
        "item_id",
        "item_name",
        "item_type",
        "tags",
        "notes",
        "publisher",
        "owner_or_contact",
        "last_updated",
        "url",
        "source_url",
        "access_level",
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    for col in expected_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["search_text"] = (
        df["item_name"] + " " +
        df["item_type"] + " " +
        df["tags"] + " " +
        df["notes"] + " " +
        df["publisher"]
    ).str.strip()

    return df.reset_index(drop=True)


@st.cache_data
def load_chunks():
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_PATH}")

    df = pd.read_csv(CHUNKS_PATH)
    df.columns = [c.lower().strip() for c in df.columns]

    required_cols = ["chunk_id", "source_id", "text"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required chunk columns: {missing}")

    df["source_id"] = df["source_id"].fillna("").astype(str).str.strip()
    df["text"] = df["text"].fillna("").astype(str).str.strip()

    return df

# -----------------------------
# Small talk handler
# -----------------------------
def handle_small_talk(user_input: str):

    text = user_input.strip().lower()

    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    thanks = ["thanks", "thank you", "thankyou", "thx", "thank you for your help"]
    bye_words = ["bye", "goodbye", "see you"]

    if any(g in text for g in greetings):
        return "Hello! I can help you explore approved IRCC datasets, reports, and methodologies. What would you like to know?"

    if any(t in text for t in thanks):
        return "You're welcome! If you have any questions about approved IRCC sources, feel free to ask."

    if any(b in text for b in bye_words):
        return "Goodbye! Feel free to return anytime if you need help with IRCC datasets or documents."

    return None

# -----------------------------
# Retrieval
# -----------------------------
def find_best_document(query, catalog_df):
    vectorizer = TfidfVectorizer(stop_words="english")
    doc_vectors = vectorizer.fit_transform(catalog_df["search_text"])
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(query_vector, doc_vectors).flatten()

    ranked = catalog_df.copy()
    ranked["score"] = scores

    return ranked.sort_values("score", ascending=False).head(1)


def find_best_chunks(query, chunks_df, source_id, k):
    doc_chunks = chunks_df[chunks_df["source_id"] == source_id].copy()

    if doc_chunks.empty:
        return pd.DataFrame()

    vectorizer = TfidfVectorizer(stop_words="english")
    chunk_vectors = vectorizer.fit_transform(doc_chunks["text"])
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(query_vector, chunk_vectors).flatten()

    doc_chunks["score"] = scores
    return doc_chunks.sort_values("score", ascending=False).head(k)

# -----------------------------
# LLM
# -----------------------------
def build_prompt(query, context):
    return f"""
You are a helpful IRCC internal assistant.

Use only the provided context to answer the question.
Do not make up information.
If the answer is not clearly supported by the context, say:
"I could not find a complete answer in the approved sources provided."

Do not say "based on the provided context".
Write the answer naturally and directly.
Keep the answer concise, clear, and professional.
Prefer 4 to 6 sentences.

Context:
{context}

Question:
{query}

Answer:
""".strip()


def generate_answer(query, context, model):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please set it in your terminal before running Streamlit.")

    client = Groq(api_key=api_key)

    prompt = build_prompt(query, context)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You answer only from approved retrieved context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )

    return response.choices[0].message.content

# -----------------------------
# UI Header
# -----------------------------
st.title("IRCC Governed RAG Assistant")
st.caption("Ask questions about approved IRCC datasets, reports, and methodologies.")
st.info("This assistant answers using retrieved context from approved IRCC sources only.")

# -----------------------------
# Helper: render assistant details
# -----------------------------
def render_assistant_details(msg):
    if "source" not in msg:
        return

    tabs = st.tabs(["Sources", "Retrieved Chunks", "Context", "Technical"])

    with tabs[0]:
        source = msg["source"]
        st.write(f"**Item ID:** {source.get('item_id', '')}")
        st.write(f"**Item Name:** {source.get('item_name', '')}")
        st.write(f"**Item Type:** {source.get('item_type', '')}")
        st.write(f"**Publisher:** {source.get('publisher', '')}")
        st.write(f"**Owner/Contact:** {source.get('owner_or_contact', '')}")
        st.write(f"**Last Updated:** {source.get('last_updated', '')}")
        st.write(f"**Access Level:** {source.get('access_level', '')}")
        st.write(f"**Tags:** {source.get('tags', '')}")

        source_url = source.get("source_url") or source.get("url") or ""
        if source_url:
            st.markdown(f"[Open Source]({source_url})")

    with tabs[1]:
        chunks = msg.get("chunks", [])
        if not chunks:
            st.write("No retrieved chunks available.")
        else:
            for i, chunk in enumerate(chunks, start=1):
                label = f"Chunk {i} | {chunk.get('chunk_id', '')} | Score: {chunk.get('score', 0):.4f}"
                with st.expander(label):
                    st.write(chunk.get("text", ""))

    with tabs[2]:
        st.text_area(
            "Context sent to the LLM",
            msg.get("context", ""),
            height=250,
            key=f"context_{msg.get('message_id', 'x')}"
        )

    with tabs[3]:
        if show_technical:
            st.write(f"**Mapped Source ID:** `{msg.get('source_id', '')}`")
            st.write(f"**Model:** `{msg.get('model_name', '')}`")
            if "relevance_score" in msg:
                st.write(f"**Metadata Relevance Score:** `{msg.get('relevance_score', 0):.4f}`")
            if "threshold" in msg:
                st.write(f"**Threshold Used:** `{msg.get('threshold', 0):.2f}`")
        else:
            st.caption("Enable 'Show technical details' in the sidebar to view debug information.")

# -----------------------------
# Render chat history
# -----------------------------
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            msg["message_id"] = idx
            render_assistant_details(msg)

# -----------------------------
# Chat input
# -----------------------------
user_input = st.chat_input("Ask a question about approved IRCC sources...")

if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

# -----------------------------
# Process new message
# -----------------------------
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            # Step 1: small talk / greeting
            small_talk_response = handle_small_talk(user_input)

            if small_talk_response:
                st.markdown(small_talk_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": small_talk_response
                })

            else:
                # Step 2: run RAG pipeline
                catalog_df = load_catalog()
                chunks_df = load_chunks()

                best_doc = find_best_document(user_input, catalog_df)

                # Relevance threshold
                if best_doc.empty or best_doc["score"].iloc[0] < score_threshold:
                    answer_text = (
                        "I could not find a relevant answer in the approved IRCC sources. "
                        "This assistant focuses on immigration datasets, reports, and methodologies."
                    )

                    st.markdown(answer_text)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer_text
                    })

                else:
                    doc = best_doc.iloc[0]
                    relevance_score = float(best_doc["score"].iloc[0])

                    # Current mapping logic using catalog row position
                    # Keep this until chunk pipeline is updated to use real item_id
                    source_index = best_doc.index[0] + 1
                    source_id = f"IRCC_{source_index:04d}"

                    retrieved_chunks = find_best_chunks(user_input, chunks_df, source_id, top_chunks)

                    if retrieved_chunks.empty:
                        answer_text = (
                            "I found a relevant approved document, "
                            "but no chunks were available for retrieval."
                        )

                        st.markdown(answer_text)

                        assistant_message = {
                            "role": "assistant",
                            "content": answer_text,
                            "source": doc.to_dict(),
                            "chunks": [],
                            "context": "",
                            "source_id": source_id,
                            "model_name": model_name,
                            "relevance_score": relevance_score,
                            "threshold": score_threshold
                        }

                        render_assistant_details(assistant_message)
                        st.session_state.messages.append(assistant_message)

                    else:
                        context = "\n\n".join(retrieved_chunks["text"].head(3).tolist())

                        with st.spinner("Generating answer..."):
                            answer_text = generate_answer(user_input, context, model_name)
                        st.markdown(answer_text)

                        # If the LLM refuses or says answer is not in approved sources,
                        # do NOT show sources/chunks for that response.
                        refusal_markers = [
                             "i could not find a complete answer",
                             "i could not find a relevant answer",
                             "not clearly supported by the context",
                             "not available in the approved sources"
                        ]

                        if any(marker in answer_text.lower() for marker in refusal_markers):
                            assistant_message = {
                                "role": "assistant",
                                "content": answer_text
                             }
                            st.session_state.messages.append(assistant_message)

                        else:
                            assistant_message = {
                                "role": "assistant",
                                "content": answer_text,
                                "source": doc.to_dict(),
                                "chunks": retrieved_chunks.to_dict(orient="records"),
                                "context": context,
                                "source_id": source_id,
                                "model_name": model_name,
                                "relevance_score": relevance_score,
                                "threshold": score_threshold
                         }

                        render_assistant_details(assistant_message)
                        st.session_state.messages.append(assistant_message)
        except Exception as e:
            error_text = f"Error: {e}"
            st.error(error_text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_text
            })