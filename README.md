# IRCC Governed Agentic RAG Assistant

An agentic Retrieval-Augmented Generation (RAG) system for exploring IRCC immigration data and policy documents.

## Tech Stack
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store:** ChromaDB (2,239 chunks from 29 approved IRCC sources)
- **LLM:** Groq API `llama-3.1-8b-instant`
- **Orchestration:** LangChain
- **UI:** Streamlit

## Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/anamvakil/ircc-governed-rag-assistant.git
cd ircc-governed-rag-assistant
```

### 2. Create a virtual environment
```bash
python -m venv .venv
```

Activate it:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at: https://console.groq.com

### 5. Run the app
```bash
streamlit run app/streamlit_app.py
```

Then open your browser at `http://localhost:8501`

---

## What It Can Answer

### Policy & Methodology (RAG)
- What is the International Mobility Program?
- How does IRCC process work permit applications?
- What are the eligibility criteria for Express Entry?

### Data Questions (CSV Analysis)
- How many permanent residents came from India?
- Which cities have the most PGWP holders?
- What skill levels do IMP work permit holders have?
- Which age group has the most permanent residents?
- What is the gender breakdown of permanent residents by province?

### Combined (RAG + Data)
- How does the methodology for counting work permit holders work, and what are the latest numbers?

---

## Dataset Sources
All data sourced from IRCC's official open data portal (open.canada.ca), updated monthly.

| File | Description |
|------|-------------|
| `IRCC_0009_data.csv` | IMP/TFWP work permit holders by province, program, NOC |
| `IRCC_0014_source_14.csv` | Work permit holders by province and occupation |
| `ODP-PR-Citz.csv` | Permanent residents by country of citizenship |
| `ODP-PR-Gender.csv` | Permanent residents by province and gender |
| `ODP-PR-AgeGroup.csv` | Permanent residents by province and age group |
| `ODP-WP-IMP-Citizenship.csv` | IMP holders by country of citizenship |
| `ODP-WP-IMP-Gender-Skill.csv` | IMP holders by gender and skill level |
| `ODP-WP-IMP-Province-Program.csv` | IMP holders by province and program |
| `ODP-WP-PGWP-Province-CMA.csv` | PGWP holders by province and city |

---

## Agent Routing
| Badge | Tool | Used For |
|-------|------|----------|
| 🔵 RAG | ChromaDB semantic search | Policy and methodology questions |
| 🟢 DATA ANALYSIS | Pandas CSV analysis | Numerical and statistical questions |
| 🟠 COMBINED | RAG + Data | Questions needing both policy and numbers |
| ⚪ SMALL TALK | Direct response | Greetings and farewells |
