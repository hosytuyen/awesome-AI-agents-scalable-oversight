import os
import requests
from datetime import datetime

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
}

# === Notion Fetch Helpers ===
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

# === Markdown / HTML Generation ===
def generate_markdown_table(papers):
    md = "# 🧠 Awesome Papers on Scalable Oversight\n\n"
    md += "A curated collection of research papers on **Scalable Oversight**\n\n"
    md += "Automatically updated database from arXiv to monitor the latest developments in the field.\n\n"
    md += "*If you want to create a similar automated curated collection on your own topics, check out our simple tool in the `paper-agent` folder! If you find this useful, give me a star ⭐ Thank you!!!*\n\n"

    # Filter and prepare papers
    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = props.get("ArXiv URL", {}).get("url", "")
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", 0)

        # Extract tags (multi-select)
        tags_list = [t["name"] for t in props.get("Tags", {}).get("multi_select", [])]
        tags_md = ", ".join(f"`{tag}`" for tag in tags_list) if tags_list else "-"

        # Filtering logic
        keep_paper = ("scalable oversight" in [t.lower() for t in tags_list]) or (relevance > 7)
        if not keep_paper:
            continue

        # Truncate long insights
        key_insights = key_insights.replace("\n", " ").strip()
        if len(key_insights) > 200:
            key_insights = key_insights[:200] + "..."

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date,
            "arxiv_url": arxiv_url,
            "key_insights": key_insights,
            "tags_md": tags_md,
        })

    # Sort by Published Date descending
    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    # === Generate HTML Table ===
    md += '<div style="overflow-x: auto;">\n'
    md += '<table style="border-collapse: collapse; width: 100%;">\n'
    md += '<thead>\n<tr style="background-color: #f2f2f2;">\n'
    md += '<th>#</th><th>🧠 Title</th><th>🏷️ Tags</th><th>📅 Published Date</th><th>🔗 arXiv URL</th><th>💡 Key Insights</th>\n'
    md += '</tr>\n</thead>\n<tbody>\n'

    for idx, paper in enumerate(filtered_papers, 1):
        md += f'<tr style="height: 60px; vertical-align: top;">'  # double-height row
        md += f'<td>{idx}</td>'
        md += f'<td><a href="{paper["arxiv_url"]}">{paper["title"]}</a></td>'
        md += f'<td>{paper["tags_md"]}</td>'
        md += f'<td>{paper["pub_date"] or "N/A"}</td>'
        md += f'<td><a href="{paper["arxiv_url"]}">Link</a></td>'
        md += f'<td>{paper["key_insights"]}</td>'
        md += '</tr>\n'

    md += '</tbody>\n</table>\n</div>'

    # Save README
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    md = "# 🧠 Awesome Papers on Scalable Oversight\n\n"
    md += "A curated collection of research papers on **Scalable Oversight**\n\n"
    md += "Automatically updated database from arXiv to monitor the latest developments in the field.\n\n"
    md += "*If you want to create a similar automated curated collection on your own topics, check out our simple tool in the `paper-agent` folder! If you find this useful, give me a star ⭐ Thank you!!!*\n\n"

    # Wrap the table in a scrollable container
    md += '<div style="overflow-x: auto; white-space: nowrap;">\n\n'
    md += "<small>\n\n"
    md += "| # | 🧠 Title | 🏷️ Tags | 📅 Published Date | 🔗 arXiv URL | 💡 Key Insights |\n"
    md += "|---|-----------|--------|------------------|--------------|----------------|\n"

    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = props.get("ArXiv URL", {}).get("url", "")
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", 0)

        # Extract tags (multi-select)
        tags_list = [t["name"] for t in props.get("Tags", {}).get("multi_select", [])]
        tags_md = ", ".join(f"`{tag}`" for tag in tags_list) if tags_list else "-"

        # Filtering logic
        keep_paper = ("scalable oversight" in [t.lower() for t in tags_list]) or (relevance > 7)
        if not keep_paper:
            continue

        # Truncate long insights for compact rows
        key_insights = key_insights.replace("\n", " ").strip()
        if len(key_insights) > 200:
            key_insights = key_insights[:200] + "..."

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date,
            "arxiv_url": arxiv_url,
            "key_insights": key_insights,
            "tags_md": tags_md,
        })

    # Sort by Published Date descending
    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    # Generate markdown rows
    for idx, paper in enumerate(filtered_papers, 1):
        md += (
            f"| {idx} | [{paper['title']}]({paper['arxiv_url']}) "
            f"| {paper['tags_md']} | {paper['pub_date'] or 'N/A'} "
            f"| [Link]({paper['arxiv_url']}) | {paper['key_insights']} |\n"
        )

    md += "\n</small>\n</div>"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

# === Entry Point ===
if __name__ == "__main__":
    papers = get_database_items()
    generate_markdown_table(papers)