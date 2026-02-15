# IRCC Governed RAG Assistant (Capstone Project)

## Overview
This capstone project proposes and prototypes a **governed, read-only conversational Q&A assistant** for internal IRCC employees.  
The goal is to improve discoverability of **authoritative datasets, reports, and reporting methodologies** by allowing staff to ask questions in natural language and receive **traceable answers with citations**.

The assistant follows a **Retrieval-Augmented Generation (RAG)** approach:
**User Question → Retrieve from Approved Sources → Summarize → Answer + Citations**

This solution is designed for a **public-sector environment**, prioritizing governance, auditability, and consistency.

---

## Problem Statement (Summary)
IRCC employees currently face challenges such as:
- Fragmentation and low discoverability of authoritative datasets and reports
- Duplicate reporting work and repeated data requests
- Inconsistent use of definitions and methodologies across teams
- Reporting guidance and policies stored in hard-to-search documents

---

## Key Project Objectives
- Improve discoverability of authoritative datasets, reports, and reporting guidance
- Reduce duplication by directing users to existing approved products
- Increase consistency and compliance through standardized definitions and methodologies
- Enable self-service access to trusted information
- Demonstrate a governed and auditable RAG approach

---

## Governance Model (Approved Source Catalog)
This project uses an **Approved Source Catalog** (spreadsheet) as the governance control.

**Rule:**  
The assistant can only retrieve and summarize content from sources marked:
`Approved = Yes`

This prevents the assistant from using random, outdated, or unverified sources.

---

## Repository Structure

ircc-governed-rag-assistant/
├─ docs/ # proposal, architecture, diagrams, meeting notes
├─ catalog/ # approved catalog template + working spreadsheet
├─ pipeline/ # ingestion, chunking, and index-building scripts
├─ app/ # UI prototype (Streamlit or mock UI)
├─ tests/ # sample questions and evaluation scripts
└─ output/ # generated chunks, logs, demo results (usually gitignored)

---

## Document Store (OneDrive / Shared Folder)
To support collaboration and avoid uploading large files to GitHub, the project uses a shared OneDrive folder as the Document Store.

**OneDrive structure (recommended):**
- `Documents_PDF/` → methodologies, definitions, guidance
- `Dataset_Descriptions/` → dataset pages or extracted text
- `Dataset_Extracts_CSV/` → optional small extracts
- `Approved_Catalog/` → approved_catalog.xlsx

The chunking pipeline reads from this shared folder.

---

## Chunking + Retrieval (RAG Pipeline)
The pipeline works in 3 stages:

1. **Ingest**
   - Extract text from approved PDFs and dataset descriptions.

2. **Chunk**
   - Split documents into smaller sections ("chunks") with overlap.
   - Attach metadata such as document name, link, and page number.

3. **Index + Retrieve**
   - Store chunks in a searchable index (vector store).
   - Retrieve top matching chunks when a user asks a question.

The assistant answers only using retrieved content and provides citations.

---

## MVP Deliverables (Capstone)
- Approved Source Catalog (20–40 items)
- Curated document store (PDFs + dataset descriptions)
- Chunking + retrieval pipeline (prototype-level)
- UI wireframes / prototype demonstrating hybrid interaction:
  - chat interface
  - browse/search catalog
  - dataset/document detail view
- Architecture, governance model, and project plan documentation

---

## Team Members
- Shara Khandakar  
- Anam Vakil  
- Satkirat Kaur  
- Bishnu Katuwal  

---

## Notes
This is a capstone prototype and design package.  
It is intended for demonstration and learning purposes and does not represent a deployed IRCC production system.
