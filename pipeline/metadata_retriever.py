import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CATALOG_PATH = Path("catalog/approved_source_catalog.csv")
TOP_K = 3


def load_metadata(csv_path: Path) -> pd.DataFrame:
    """
    Load the approved source catalog using the user's actual column names.
    Keeps only rows where approved == yes.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Catalog file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # standardize column names
    df.columns = [col.strip().lower() for col in df.columns]

    required_columns = [
        "item_id",
        "item_name",
        "item_type",
        "approved",
        "tags",
        "notes",
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in catalog: {missing_cols}\n"
            f"Found columns: {list(df.columns)}"
        )

    # keep only approved rows
    df["approved"] = df["approved"].astype(str).str.strip().str.lower()
    df = df[df["approved"].isin(["yes", "y", "true", "1", "approved"])].copy()

    # fill optional columns if missing
    optional_cols = [
        "url",
        "source_url",
        "publisher",
        "owner_or_contact",
        "last_updated",
        "access_level",
    ]
    for col in optional_cols:
        if col not in df.columns:
            df[col] = ""

    # fill nulls
    fill_cols = [
        "item_id",
        "item_name",
        "item_type",
        "tags",
        "notes",
        "url",
        "source_url",
        "publisher",
        "owner_or_contact",
        "last_updated",
        "access_level",
    ]
    for col in fill_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # make a searchable text field from metadata
    df["search_text"] = (
        df["item_name"] + " " +
        df["item_type"] + " " +
        df["tags"] + " " +
        df["notes"] + " " +
        df["publisher"]
    ).str.strip()

    return df


def rank_documents(query: str, df: pd.DataFrame, top_k: int = 3) -> pd.DataFrame:
    """
    Rank approved documents based on metadata similarity.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if df.empty:
        raise ValueError("No approved documents available in the catalog.")

    vectorizer = TfidfVectorizer(stop_words="english")
    doc_vectors = vectorizer.fit_transform(df["search_text"])
    query_vector = vectorizer.transform([query])

    similarity_scores = cosine_similarity(query_vector, doc_vectors).flatten()

    ranked_df = df.copy()
    ranked_df["score"] = similarity_scores

    ranked_df = ranked_df.sort_values(by="score", ascending=False).head(top_k)

    return ranked_df[
        [
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
            "score",
        ]
    ]


def pretty_print_results(results: pd.DataFrame) -> None:
    """
    Print ranked results clearly.
    """
    if results.empty:
        print("\nNo matching documents found.")
        return

    print("\nTop matching documents:\n")
    for i, row in enumerate(results.itertuples(index=False), start=1):
        print(f"{i}. {row.item_name}")
        print(f"   Item ID          : {row.item_id}")
        print(f"   Item Type        : {row.item_type}")
        print(f"   Tags             : {row.tags}")
        print(f"   Notes            : {row.notes}")
        print(f"   Publisher        : {row.publisher}")
        print(f"   Owner/Contact    : {row.owner_or_contact}")
        print(f"   Last Updated     : {row.last_updated}")
        print(f"   URL              : {row.url}")
        print(f"   Source URL       : {row.source_url}")
        print(f"   Access Level     : {row.access_level}")
        print(f"   Score            : {row.score:.4f}")
        print("-" * 90)


def save_results(results: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")


def main():
    try:
        df = load_metadata(CATALOG_PATH)
        print("Metadata loaded successfully.")
        print(f"Approved documents available: {len(df)}")
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return

    while True:
        query = input("\nEnter your question (or type 'exit'): ").strip()

        if query.lower() == "exit":
            print("Exiting metadata retriever.")
            break

        try:
            results = rank_documents(query, df, top_k=TOP_K)
            pretty_print_results(results)

            save_choice = input("Do you want to save these results? (y/n): ").strip().lower()
            if save_choice == "y":
                save_results(results, Path("output/metadata_results/latest_results.csv"))

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()