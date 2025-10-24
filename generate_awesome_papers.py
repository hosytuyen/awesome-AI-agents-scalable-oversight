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
    md += "A curated collection of research papers on **Scalable Oversight**\n\n"
    md += "Automatically updated database from arXiv to monitor the latest developments in the field.\n\n"
    md += "*If you want to create a similar automated curated collection on your own topics, check out our simple tool in the `paper-agent` folder! If you find this useful, give me a star ⭐ Thank you!!!*"
    md += "\n\n"

    md += """
<small>
<table>
<colgroup>
<col style="width: 3%;">
<col style="width: 25%;">
<col style="width: 15%;">
<col style="width: 12%;">
<col style="width: 10%;">
<col style="width: 35%;">
</colgroup>
<thead>
<tr>
<th>#</th>
<th>🧠 Title</th>
<th>🏷️ Tags</th>
<th>📅 Published Date</th>
<th>🔗 Link</th>
<th>💡 Key Insights</th>
</tr>
</thead>
<tbody>
"""

    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = props.get("ArXiv URL", {}).get("url", "")
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", 0)

        tags_list = [t["name"] for t in props.get("Tags", {}).get("multi_select", [])]
        tags_md = ", ".join(f"<code>{tag}</code>" for tag in tags_list) if tags_list else "-"

        keep_paper = ("scalable oversight" in [t.lower() for t in tags_list]) or (relevance > 7)
        if not keep_paper:
            continue

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date or "N/A",
            "arxiv_url": arxiv_url,
            "key_insights": key_insights.replace("\n", " ").strip(),
            "tags_md": tags_md,
        })

    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    for idx, paper in enumerate(filtered_papers, 1):
        md += f"""
<tr>
<td>{idx}</td>
<td><a href="{paper['arxiv_url']}">{paper['title']}</a></td>
<td>{paper['tags_md']}</td>
<td>{paper['pub_date']}</td>
<td><a href="{paper['arxiv_url']}">Link</a></td>
<td>{paper['key_insights']}</td>
</tr>
"""

    md += """
</tbody>
</table>
</small>
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    papers = get_database_items()
    generate_markdown_table(papers)
