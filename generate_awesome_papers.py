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
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["results"]

def extract_text(rich_text):
    return "".join([t["plain_text"] for t in rich_text]) if rich_text else ""

def parse_date(date_str):
    if not date_str:
        return datetime.min
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.min

def generate_markdown_table(papers):
    md = "# 🧠 Awesome Papers on Scalable Oversight\n\n"
    md += "Automatically updated from [Notion Database](https://www.notion.so/).\n\n"
    # wrap table in <small> for smaller font
    md += "<small>\n\n"
    md += "| # | 🧠 Title | 📅 Published Date | 🔗 arXiv URL | 💡 Key Insights |\n"
    md += "|---|-----------|------------------|--------------|----------------|\n"

    # Extract and filter papers (Relevance Score >=7)
    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = extract_text(props.get("arXiv URL", {}).get("rich_text", []))
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", None)

        if relevance is None or relevance < 7:
            continue

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date,
            "arxiv_url": arxiv_url,
            "key_insights": key_insights.replace("\n", " ").strip(),
        })

    # Sort by Published Date descending
    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    # Add index column
    for idx, paper in enumerate(filtered_papers, 1):
        title = paper["title"]
        pub_date = paper["pub_date"] or "N/A"
        arxiv_url = paper["arxiv_url"]
        key_insights = paper["key_insights"]

        md += f"| {idx} | [{title}]({arxiv_url}) | {pub_date} | [Link]({arxiv_url}) | {key_insights} |\n"

    md += "\n</small>"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    papers = get_database_items()
    generate_markdown_table(papers)
