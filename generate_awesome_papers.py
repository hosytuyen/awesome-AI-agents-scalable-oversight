import os
import requests

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

def generate_markdown_table(papers):
    md = "# 🧠 Awesome Papers on Scalable Oversight\n\n"
    md += "Automatically updated from [Notion Database](https://www.notion.so/).\n\n"
    md += "| 🧠 Title | 📝 Abstract | 📅 Published Date | 🔗 arXiv URL | 💡 Key Insights | ⚙️ Methodology |\n"
    md += "|-----------|-------------|------------------|--------------|----------------|----------------|\n"

    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        abstract = extract_text(props.get("Abstract", {}).get("rich_text", []))
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", "N/A")
        arxiv_url = extract_text(props.get("arXiv URL", {}).get("rich_text", []))
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        methodology = extract_text(props.get("Methodology", {}).get("rich_text", []))

        abstract = abstract.replace("\n", " ").strip()
        key_insights = key_insights.replace("\n", " ").strip()
        methodology = methodology.replace("\n", " ").strip()

        md += f"| [{title}]({arxiv_url}) | {abstract} | {pub_date} | [Link]({arxiv_url}) | {key_insights} | {methodology} |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    papers = get_database_items()
    generate_markdown_table(papers)
