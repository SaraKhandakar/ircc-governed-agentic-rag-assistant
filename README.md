# IRCC Governed RAG Assistant

This project implements a governed Retrieval-Augmented Generation (RAG) assistant designed to help IRCC employees discover datasets, reports, and methodological guidance from approved internal sources.

The system uses a catalog-driven approach to ensure that only authorized sources are used for document ingestion and retrieval.

The project is organized into multiple layers including document ingestion, chunking, metadata-based retrieval, and chunk-level retrieval.

---

# System Architecture

The current architecture follows this pipeline:

User Query  
→ Metadata Retrieval (Approved Source Catalog)  
→ Identify Relevant Document  
→ Chunk Retrieval  
→ Retrieve Relevant Text Segments  
→ (Next Stage) LLM Generation via Groq / Llama  
→ Chatbot Response

This approach ensures:

- Only approved sources are used
- Retrieval is more accurate
- Context sent to the LLM is smaller and more relevant

---

# Project Components

## 1. Approved Source Catalog

Location: `catalog/approved_source_catalog.csv`

This catalog acts as the governance layer of the system.

It contains metadata about all datasets and documents including:

- item_id
- item_name
- item_type
- url
- publisher
- owner/contact
- last_updated
- tags
- notes
- approved status

Only sources marked **approved = yes** are processed by the pipeline.

---

# 2. Chunk Pipeline

Script: `pipeline/chunk_pipeline.py`

Purpose:

Processes approved documents and converts them into smaller searchable text chunks.

Pipeline steps:

1. Load Approved Source Catalog
2. Filter approved sources
3. Download files (PDF / CSV / HTML)
4. Extract text
5. Clean text
6. Perform section-aware splitting
7. Generate overlapping text chunks
8. Save chunk outputs

Output files:





