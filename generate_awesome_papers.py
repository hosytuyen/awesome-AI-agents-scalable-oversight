import os
import requests
from datetime import datetime

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
}

def get_database_items():
    """Fetch all entries from the Notion database"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["results"]

def extract_text(rich_text):
    """Extract plain text from Notion rich_text fields"""
    return "".join([t["plain_text"] for t in rich_text]) if rich_text else ""

def parse_date(date_str):
    """Convert Notion date string to datetime object for sorting"""
    if not date_str:
        return datetime.min
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.min

def generate_markdown_table(papers):
    md = "# 🧠 Awesome Papers on Scalable Oversight\n\n"
    md += "Automatically updated from [Notion Database](https://www.notion.so/).\n\n"
    md += "| # | 🧠 Title | 📅 Published Date | 🔢 Relevance Score | 🔗 arXiv URL | 💡 Key Insights | ⚙️ Methodology |\n"
    md += "|---|-----------|------------------|--------------------|--------------|----------------|----------------|\n"

    # --- Step 1: Extract relevant info from Notion results ---
    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = extract_text(props.get("arXiv URL", {}).get("rich_text", []))
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        methodology = extract_text(props.get("Methodology", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", None)

        # --- Step 2: Filter out low relevance ---
        if relevance is None or relevance < 7:
            continue

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date,
            "arxiv_url": arxiv_url,
            "key_insights": key_insights.replace("\n", " ").strip(),
            "methodology": methodology.replace("\n", " ").strip(),
            "relevance": relevance,
        })

    # --- Step 3: Sort by published date (newest first) ---
    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    # --- Step 4: Generate markdown rows with index ---
    for idx, paper in enumerate(filtered_papers, 1):
        title = paper["title"]
        pub_date = paper["pub_date"] or "N/A"
        relevance = paper["relevance"]
        arxiv_url = paper["arxiv_url"]
        key_insights = paper["key_insights"]
        methodology = paper["methodology"]

        md += f"| {idx} | [{title}]({arxiv_url}) | {pub_date} | {relevance} | [Link]({arxiv_url}) | {key_insights} | {methodology} |\n"

    # --- Step 5: Write output ---
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    papers = get_database_items()
    generate_markdown_table(papers)
