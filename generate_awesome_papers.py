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
    md += "A curated collection of research papers on **Scalable Oversight**, highlighting methods to supervise and evaluate AI systems reliably at scale."
    md += "Automatically updated from a Notion database, each entry includes a summary, publication date, and arXiv link to help researchers and practitioners stay up-to-date with the latest developments."
    md += "*If you want to create a similar automated curated collection on your own topics, check out our simple tool in the `paper-agent` folder! If you find this useful, give me a star ⭐ Thank you!!!*"
    md += "\n\n"
    # Wrap table in <small> for smaller font
    md += "<small>\n\n"
    md += "| # | 🧠 Title | 📅 Published Date | 🔗 arXiv URL | 💡 Key Insights |\n"
    md += "|---|-----------|------------------|--------------|----------------|\n"

    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = props.get("ArXiv URL", {}).get("url", "")
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", 0)

        # print(arxiv_url)


        # Extract tags (multi-select)
        tags_list = [t["name"].lower() for t in props.get("Tags", {}).get("multi_select", [])]

        # Filtering logic
        keep_paper = ("scalable oversight" in tags_list) or (relevance > 7)
        if not keep_paper:
            continue

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date,
            "arxiv_url": arxiv_url,
            "key_insights": key_insights.replace("\n", " ").strip(),
        })

    # Sort by Published Date descending
    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    # Generate table with index
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
