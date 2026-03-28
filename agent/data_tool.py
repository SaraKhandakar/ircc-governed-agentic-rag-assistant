import pandas as pd
import os
 
# ── File registry ────────────────────────────────────────────────────────────
# All ODP files are tab-separated. IRCC_0009 and IRCC_0014 are comma-separated.
 
DATA_DIR = "data_raw/csv"
 
FILES = {
    # ── Work permits (existing) ───────────────────────────────────────────────
    "work_permits_main": {
        "file": "IRCC_0009_data.csv",
        "sep": ",",
        "description": "IMP and TFWP work permit holders by province, program, NOC, year",
        "key_cols": ["Year", "Quarter", "Province_Territory", "Program", "NOC"],
    },
    "work_permits_occupation": {
        "file": "IRCC_0014_source_14.csv",
        "sep": "\t",
        "description": "IMP/TFWP work permit holders by province, occupation and month",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_MONTH", "EN_PROVINCE_TERRITORY", "EN_OCCUPATION", "TOTAL"],
    },
 
    # ── Permanent residents ───────────────────────────────────────────────────
    "pr_by_citizenship": {
        "file": "ODP-PR-Citz.csv",
        "sep": "\t",
        "description": "Permanent residents by country of citizenship and year",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_COUNTRY_OF_CITIZENSHIP", "TOTAL"],
    },
    "pr_by_gender": {
        "file": "ODP-PR-Gender.csv",
        "sep": "\t",
        "description": "Permanent residents by province/territory and gender",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_PROVINCE_TERRITORY", "EN_GENDER", "TOTAL"],
    },
    "pr_by_age": {
        "file": "ODP-PR-AgeGroup.csv",
        "sep": "\t",
        "description": "Permanent residents by province/territory and age group",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_PROVINCE_TERRITORY", "EN_AGE", "TOTAL"],
    },
 
    # ── IMP work permits (additional breakdowns) ──────────────────────────────
    "imp_by_citizenship": {
        "file": "ODP-WP-IMP-Citizenship.csv",
        "sep": "\t",
        "description": "IMP work permit holders by country of citizenship and year",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_COUNTRY_OF_CITIZENSHIP", "TOTAL"],
    },
    "imp_by_gender_skill": {
        "file": "ODP-WP-IMP-Gender-Skill.csv",
        "sep": "\t",
        "description": "IMP work permit holders by gender and occupational skill level",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_GENDER", "EN_SKILL_LEVEL", "TOTAL"],
    },
    "imp_by_province_program": {
        "file": "ODP-WP-IMP-Province-Program.csv",
        "sep": "\t",
        "description": "IMP work permit holders by province and program stream",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_PROVINCE_TERRITORY", "EN_PROGRAM_LEVEL_2", "TOTAL"],
    },
 
    # ── Post-graduate work permits ────────────────────────────────────────────
    "pgwp_by_province_cma": {
        "file": "ODP-WP-PGWP-Province-CMA.csv",
        "sep": "\t",
        "description": "PGWP holders by province and census metropolitan area (city)",
        "key_cols": ["EN_YEAR", "EN_QUARTER", "EN_PROVINCE_TERRITORY", "EN_CENSUS_METROPOLITAN_AREA", "TOTAL"],
    },
 
    # ── Permit holders snapshot ───────────────────────────────────────────────
    "permit_holders_snapshot": {
        "file": "IRCC_0029_source_29.csv",
        "sep": ",",
        "description": "Snapshot of permit holders summary statistics",
        "key_cols": [],
    },
}
 
# ── Keyword routing ───────────────────────────────────────────────────────────
# Maps question keywords → which dataset(s) to query
 
ROUTING_RULES = [
    # PR questions
    (["permanent resident", "pr ", "landed", "immigration category", "country of citizenship", "citizenship"], ["pr_by_citizenship"]),
    (["permanent resident", "pr ", "gender", "female", "male", "women", "men"], ["pr_by_gender"]),
    (["permanent resident", "pr ", "age", "age group", "young", "senior"], ["pr_by_age"]),
    (["permanent resident", "province", "territory", "ontario", "bc", "alberta", "quebec"], ["pr_by_gender", "pr_by_age"]),
 
    # IMP / work permit questions
    (["imp", "international mobility", "work permit", "citizenship", "country"], ["imp_by_citizenship"]),
    (["imp", "international mobility", "gender", "skill", "skill level", "noc"], ["imp_by_gender_skill"]),
    (["imp", "international mobility", "program", "stream", "province"], ["imp_by_province_program"]),
    (["work permit", "occupation", "job", "noc", "tfwp", "temporary foreign"], ["work_permits_occupation", "work_permits_main"]),
 
    # PGWP questions
    (["pgwp", "post-graduate", "post graduate", "postgraduate", "graduate work", "international student.*work"], ["pgwp_by_province_cma"]),
    (["pgwp", "city", "cma", "metropolitan", "toronto", "vancouver", "ottawa", "calgary"], ["pgwp_by_province_cma"]),
]
 
 
def load_file(key: str) -> pd.DataFrame:
    """Load a dataset by registry key."""
    meta = FILES[key]
    path = os.path.join(DATA_DIR, meta["file"])
    return pd.read_csv(path, sep=meta["sep"])
 
 
def route_question(question: str) -> list[str]:
    """Return list of dataset keys relevant to the question."""
    q = question.lower()
    matched = []
    for keywords, keys in ROUTING_RULES:
        if any(kw in q for kw in keywords):
            for k in keys:
                if k not in matched:
                    matched.append(k)
    # Default fallback
    if not matched:
        matched = ["work_permits_main"]
    return matched
 
 
def query_data(question: str) -> str:
    """
    Main entry point for the data tool.
    Routes the question, loads relevant files, runs pandas analysis,
    and returns a plain-text summary.
    """
    dataset_keys = route_question(question)
    results = []
 
    for key in dataset_keys:
        try:
            df = load_file(key)
            meta = FILES[key]
            desc = meta["description"]
            q = question.lower()
 
            # Clean TOTAL column — remove suppressed '--' values
            if "TOTAL" in df.columns:
                df["TOTAL"] = pd.to_numeric(df["TOTAL"].astype(str).str.replace(",", ""), errors="coerce")
 
            summary_lines = [f"\n📊 [{desc}]"]
 
            # ── Province/territory breakdown ──────────────────────────────────
            if "EN_PROVINCE_TERRITORY" in df.columns and any(w in q for w in ["province", "territory", "ontario", "bc", "alberta", "quebec", "breakdown"]):
                col = "EN_PROVINCE_TERRITORY"
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby(col)["TOTAL"].sum().sort_values(ascending=False).head(10)
                summary_lines.append(f"Top provinces/territories ({latest_year}):")
                for prov, val in grouped.items():
                    summary_lines.append(f"  {prov}: {int(val):,}")
 
            # ── Country of citizenship breakdown ──────────────────────────────
            elif "EN_COUNTRY_OF_CITIZENSHIP" in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby("EN_COUNTRY_OF_CITIZENSHIP")["TOTAL"].sum().sort_values(ascending=False).head(10)
                summary_lines.append(f"Top countries of citizenship ({latest_year}):")
                for country, val in grouped.items():
                    summary_lines.append(f"  {country}: {int(val):,}")
 
            # ── Gender breakdown ──────────────────────────────────────────────
            elif "EN_GENDER" in df.columns and "EN_SKILL_LEVEL" not in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby("EN_GENDER")["TOTAL"].sum()
                summary_lines.append(f"Gender breakdown ({latest_year}):")
                for gender, val in grouped.items():
                    summary_lines.append(f"  {gender}: {int(val):,}")
 
            # ── Gender + skill level breakdown ────────────────────────────────
            elif "EN_SKILL_LEVEL" in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby(["EN_GENDER", "EN_SKILL_LEVEL"])["TOTAL"].sum().sort_values(ascending=False)
                summary_lines.append(f"Gender and skill level breakdown ({latest_year}):")
                for (gender, skill), val in grouped.items():
                    summary_lines.append(f"  {gender} / {skill}: {int(val):,}")
 
            # ── Age group breakdown ───────────────────────────────────────────
            elif "EN_AGE" in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby("EN_AGE")["TOTAL"].sum().sort_values(ascending=False)
                summary_lines.append(f"Age group breakdown ({latest_year}):")
                for age, val in grouped.items():
                    summary_lines.append(f"  {age}: {int(val):,}")
 
            # ── CMA/city breakdown ────────────────────────────────────────────
            elif "EN_CENSUS_METROPOLITAN_AREA" in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby("EN_CENSUS_METROPOLITAN_AREA")["TOTAL"].sum().sort_values(ascending=False).head(10)
                summary_lines.append(f"Top cities (CMA) ({latest_year}):")
                for city, val in grouped.items():
                    summary_lines.append(f"  {city}: {int(val):,}")
 
            # ── Program breakdown ─────────────────────────────────────────────
            elif "EN_PROGRAM_LEVEL_2" in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby("EN_PROGRAM_LEVEL_2")["TOTAL"].sum().sort_values(ascending=False).head(10)
                summary_lines.append(f"Top IMP programs ({latest_year}):")
                for prog, val in grouped.items():
                    summary_lines.append(f"  {prog}: {int(val):,}")
 
            # ── Occupation breakdown ──────────────────────────────────────────
            elif "EN_OCCUPATION" in df.columns:
                latest_year = df["EN_YEAR"].max()
                subset = df[df["EN_YEAR"] == latest_year]
                grouped = subset.groupby("EN_OCCUPATION")["TOTAL"].sum().sort_values(ascending=False).head(10)
                summary_lines.append(f"Top occupations ({latest_year}):")
                for occ, val in grouped.items():
                    summary_lines.append(f"  {occ}: {int(val):,}")
 
            # ── Fallback: yearly totals ───────────────────────────────────────
            else:
                if "EN_YEAR" in df.columns and "TOTAL" in df.columns:
                    yearly = df.groupby("EN_YEAR")["TOTAL"].sum().tail(5)
                    summary_lines.append("Yearly totals (last 5 years):")
                    for year, val in yearly.items():
                        summary_lines.append(f"  {year}: {int(val):,}")
                else:
                    summary_lines.append(f"Rows: {len(df)}, Columns: {list(df.columns)}")
 
            results.append("\n".join(summary_lines))
 
        except Exception as e:
            results.append(f"\n⚠️ Could not load [{key}]: {e}")
 
    return "\n".join(results) if results else "No data found for this question."
 
 
# ── Public API expected by router.py ─────────────────────────────────────────
 
QUANTITATIVE_KEYWORDS = [
    "how many", "how much", "number of", "total", "count", "percentage",
    "percent", "%", "rate", "average", "breakdown", "statistic", "data",
    "figure", "trend", "increase", "decrease", "grew", "declined", "top",
    "most", "least", "highest", "lowest", "compare", "between", "by year",
    "by province", "by country", "by gender", "by age", "by skill",
    "permanent resident", "work permit", "study permit", "pgwp",
    "imp", "tfwp", "post-graduate", "postgraduate", "immigration category",
]
 
def is_quantitative(question: str) -> bool:
    """Return True if the question is numerical/data-oriented."""
    q = question.lower()
    return any(kw in q for kw in QUANTITATIVE_KEYWORDS)
 
 
def analyze(question: str) -> dict:
    """
    Wrapper expected by router.py.
    Returns dict with keys: success, data_summary, source_file.
    """
    try:
        dataset_keys = route_question(question)
        summary = query_data(question)
 
        if not summary or summary == "No data found for this question.":
            return {"success": False, "data_summary": "", "source_file": ""}
 
        source_files = [FILES[k]["file"] for k in dataset_keys if k in FILES]
        return {
            "success": True,
            "data_summary": summary,
            "source_file": ", ".join(source_files),
        }
    except Exception as e:
        return {"success": False, "data_summary": str(e), "source_file": ""}