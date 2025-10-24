import os
import csv
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

def generate_csv(papers):
    filtered_papers = []
    for paper in papers:
        props = paper["properties"]

        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = props.get("ArXiv URL", {}).get("url", "")
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", 0)

        tags_list = [t["name"].lower() for t in props.get("Tags", {}).get("multi_select", [])]

        # Filtering logic
        keep_paper = ("scalable oversight" in tags_list) or (relevance > 7)
        if not keep_paper:
            continue

        filtered_papers.append({
            "Title": title,
            "Published Date": pub_date or "N/A",
            "ArXiv URL": arxiv_url,
            "Key Insights": key_insights.replace("\n", " ").strip(),
        })

    # Sort by Published Date descending
    filtered_papers.sort(key=lambda x: parse_date(x["Published Date"]), reverse=True)

    # Write to CSV file
    with open("papers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["#", "Title", "Published Date", "ArXiv URL", "Key Insights"])
        writer.writeheader()
        for idx, paper in enumerate(filtered_papers, 1):
            row = {"#": idx, **paper}
            writer.writerow(row)

    print(f"✅ Generated papers.csv with {len(filtered_papers)} papers.")

if __name__ == "__main__":
    papers = get_database_items()
    generate_csv(papers)
