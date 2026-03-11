import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CATALOG_PATH = "catalog/approved_source_catalog.csv"
CHUNKS_PATH = "docs/chunks.csv"

TOP_DOCS = 1
TOP_CHUNKS = 5


# -----------------------------
# Load catalog metadata
# -----------------------------
def load_catalog():
    df = pd.read_csv(CATALOG_PATH)

    df.columns = [c.lower().strip() for c in df.columns]

    df["approved"] = df["approved"].astype(str).str.lower()

    df = df[df["approved"].isin(["yes", "true", "1"])]

    df["search_text"] = (
        df["item_name"].fillna("")
        + " "
        + df["item_type"].fillna("")
        + " "
        + df["tags"].fillna("")
        + " "
        + df["notes"].fillna("")
    )

    return df


# -----------------------------
# Find most relevant document
# -----------------------------
def find_best_document(query, catalog_df):

    vectorizer = TfidfVectorizer(stop_words="english")

    doc_vectors = vectorizer.fit_transform(catalog_df["search_text"])

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(query_vector, doc_vectors).flatten()

    catalog_df["score"] = scores

    best = catalog_df.sort_values("score", ascending=False).head(TOP_DOCS)

    return best


# -----------------------------
# Load chunks
# -----------------------------
def load_chunks():
    chunks_df = pd.read_csv(CHUNKS_PATH)
    return chunks_df


# -----------------------------
# Find best chunks from document
# -----------------------------
def find_best_chunks(query, chunks_df, source_id):

    doc_chunks = chunks_df[chunks_df["source_id"] == source_id]

    if len(doc_chunks) == 0:
        return None

    vectorizer = TfidfVectorizer(stop_words="english")

    chunk_vectors = vectorizer.fit_transform(doc_chunks["text"])

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(query_vector, chunk_vectors).flatten()

    doc_chunks["score"] = scores

    top_chunks = doc_chunks.sort_values("score", ascending=False).head(TOP_CHUNKS)

    return top_chunks


# -----------------------------
# Main search
# -----------------------------
def search(query):

    catalog_df = load_catalog()

    chunks_df = load_chunks()

    best_doc = find_best_document(query, catalog_df)

    print("\nBest matching document:\n")
    print(best_doc[["item_name", "item_type", "tags"]])

    source_id = "IRCC_" + str(best_doc.index[0] + 1).zfill(4)

    print("\nSearching chunks from:", source_id)

    chunks = find_best_chunks(query, chunks_df, source_id)

    if chunks is None:
        print("No chunks found.")
        return

    print("\nTop relevant chunks:\n")

    for i, row in chunks.iterrows():

        print("\n-----------------------------")
        print("Chunk ID:", row["chunk_id"])
        print("Text:", row["text"][:500], "...")
        print("-----------------------------")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":

    while True:

        query = input("\nAsk a question (or type exit): ")

        if query.lower() == "exit":
            break

        search(query)