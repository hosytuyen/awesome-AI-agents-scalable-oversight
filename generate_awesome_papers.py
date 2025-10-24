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

        # Keep full insights, just clean up formatting
        key_insights = key_insights.replace("\n", " ").strip()

        filtered_papers.append({
            "title": title,
            "pub_date": pub_date,
            "arxiv_url": arxiv_url,
            "key_insights": key_insights,
            "tags_md": tags_md,
        })

    # Sort by Published Date descending
    filtered_papers.sort(key=lambda x: parse_date(x["pub_date"]), reverse=True)

    # === Generate Compact HTML Table with Horizontal Scroll ===
    md += '<div style="overflow-x: auto; max-width: 100%;">\n'
    md += '<table style="border-collapse: collapse; min-width: 1200px;">\n'
    md += '<thead>\n<tr>\n'
    md += '<th style="min-width: 30px; padding: 8px;">#</th>\n'
    md += '<th style="min-width: 250px; padding: 8px;">🧠 Title</th>\n'
    md += '<th style="min-width: 150px; padding: 8px;">🏷️ Tags</th>\n'
    md += '<th style="min-width: 90px; padding: 8px;">📅 Date</th>\n'
    md += '<th style="min-width: 600px; padding: 8px;">💡 Key Insights</th>\n'
    md += '</tr>\n</thead>\n<tbody>\n'

    for idx, paper in enumerate(filtered_papers, 1):
        # Format date nicely
        date_display = paper["pub_date"] or "N/A"
        if paper["pub_date"]:
            try:
                dt = datetime.fromisoformat(paper["pub_date"])
                date_display = dt.strftime("%Y-%m-%d")
            except:
                pass
        
        md += '<tr style="vertical-align: top; height: 60px;">\n'
        md += f'<td style="padding: 8px;">{idx}</td>\n'
        md += f'<td style="padding: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"><a href="{paper["arxiv_url"]}">{paper["title"]}</a></td>\n'
        md += f'<td style="padding: 8px; font-size: 0.85em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{paper["tags_md"]}</td>\n'
        md += f'<td style="padding: 8px; white-space: nowrap;">{date_display}</td>\n'
        md += f'<td style="padding: 8px; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{paper["key_insights"]}</td>\n'
        md += '</tr>\n'

    md += '</tbody>\n</table>\n</div>\n'

    # Save README
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"✅ Generated README.md with {len(filtered_papers)} papers")

# === Entry Point ===
if __name__ == "__main__":
    papers = get_database_items()
    generate_markdown_table(papers)