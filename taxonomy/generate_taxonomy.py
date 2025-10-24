import os
import csv
import requests
from datetime import datetime
from google import genai  # requires: pip install google-genai

# ====== Environment Variables ======
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ====== API Clients ======
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
}

client = genai.Client(api_key=GEMINI_API_KEY)


# ====== Utility Functions ======
def get_database_items():
    """Query all items from the Notion database."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["results"]


def extract_text(rich_text):
    """Extract plain text from Notion rich_text property."""
    return "".join([t["plain_text"] for t in rich_text]) if rich_text else ""


def parse_date(date_str):
    """Parse ISO date safely."""
    if not date_str:
        return datetime.min
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.min


# ====== CSV Generation ======
def generate_csv(papers):
    """Generate papers.csv from Notion items."""
    filtered_papers = []

    for paper in papers:
        props = paper["properties"]
        title = extract_text(props["Title"]["title"])
        pub_date = props.get("Published Date", {}).get("date", {}).get("start", None)
        arxiv_url = props.get("ArXiv URL", {}).get("url", "")
        key_insights = extract_text(props.get("Key Insights", {}).get("rich_text", []))
        relevance = props.get("Relevance Score", {}).get("number", 0)
        tags_list = [t["name"].lower() for t in props.get("Tags", {}).get("multi_select", [])]

        # Keep only relevant papers
        keep_paper = ("scalable oversight" in tags_list) or (relevance > 7)
        if not keep_paper:
            continue

        filtered_papers.append({
            "Title": title,
            "Published Date": pub_date or "N/A",
            "ArXiv URL": arxiv_url,
            "Key Insights": key_insights.replace("\n", " ").strip(),
        })

    # Sort by date (descending)
    filtered_papers.sort(key=lambda x: parse_date(x["Published Date"]), reverse=True)

    csv_path = "papers.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["#", "Title", "Published Date", "ArXiv URL", "Key Insights"])
        writer.writeheader()
        for idx, paper in enumerate(filtered_papers, 1):
            row = {"#": idx, **paper}
            writer.writerow(row)

    print(f"✅ Generated {csv_path} with {len(filtered_papers)} papers.")
    return csv_path


# ====== Gemini Integration ======
def generate_taxonomy_with_gemini(csv_path):
    """Send CSV to Gemini 2.5 Pro and get taxonomy table in Markdown format."""
    prompt = """Role: You are a Machine Learning researcher specializing in scalable oversight and safety for LLMs and AI agents.

Objective: Draft the taxonomy of scalable oversight methods based on the provided collection of papers.

Step-by-step Instructions:
- Data Source: Only use papers listed in the attached CSV file.
- Literature Review: Carefully read and analyze all papers in the dataset.
  Group the scalable oversight methods into coherent method categories based on their approach or mechanism (e.g., “Automated Evaluators,” “Synthetic Feedback,” “Reward Modeling,” etc.).
- Taxonomy Construction: Develop a clear taxonomy of scalable oversight methods using these categories.
- Assign each paper to one or more taxonomy categories, explaining briefly why.

Only return a **Markdown table** representing the taxonomy.
The table must have three columns: **Category**, **Concise Description**, **Paper Indices**.
"""

    # Upload CSV to Gemini
    # --- Upload CSV to Gemini ---
    # Upload the CSV file
    file_obj = client.files.upload(file="papers.csv")
    print(f"📤 Uploaded CSV file to Gemini: {file_obj.name}")


    # Generate taxonomy table
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            {"role": "user", "parts": [
                {"text": prompt},
                {"file_data": {"file_uri": file_obj.uri}}
            ]}
        ]
    )

    taxonomy_md = response.text

    # Save taxonomy as Markdown
    with open("taxonomy.md", "w", encoding="utf-8") as f:
        f.write("# 🧩 Taxonomy of Scalable Oversight Methods\n\n")
        f.write(taxonomy_md.strip() + "\n")

    print("✅ Saved taxonomy to taxonomy.md")


# ====== Main Entry ======
if __name__ == "__main__":
    papers = get_database_items()
    csv_path = generate_csv(papers)
    generate_taxonomy_with_gemini(csv_path)
