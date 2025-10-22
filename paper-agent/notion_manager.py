"""
Notion Database Manager

Handles Notion database operations including creating, updating, and querying papers.
Manages database schema and ensures data consistency.
"""

from notion_client import Client
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from loguru import logger
import json
from datetime import datetime


@dataclass
class NotionPaper:
    """Represents a paper entry in Notion database."""
    title: str
    authors: str
    abstract: str
    arxiv_id: str
    published_date: str
    categories: str
    arxiv_url: str
    tags: str
    relevance_score: float
    key_insights: str
    methodology: str
    status: str = "New"


class NotionManager:
    """Manages Notion database operations for paper tracking."""
    
    def __init__(self, api_key: str, database_id: str):
        """
        Initialize the Notion manager.
        
        Args:
            api_key: Notion integration API key
            database_id: Notion database ID
        """
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self._ensure_database_schema()
    
    def create_database_if_empty(self) -> bool:
        """
        Create the database schema if it doesn't exist or is empty.
        
        Returns:
            True if database was created/configured successfully
        """
        try:
            # Check if database exists and has proper schema
            db_info = self.client.databases.retrieve(database_id=self.database_id)
            
            # Define required properties
            required_properties = {
                "Title": {"title": {}},
                "Authors": {"rich_text": {}},
                "Abstract": {"rich_text": {}},
                "ArXiv ID": {"rich_text": {}},
                "Published Date": {"date": {}},
                "Categories": {"multi_select": {"options": []}},
                "ArXiv URL": {"url": {}},
                "Tags": {"multi_select": {"options": []}},
                "Relevance Score": {"number": {}},
                "Key Insights": {"rich_text": {}},
                "Methodology": {"rich_text": {}},
                "Status": {"select": {"options": [
                    {"name": "New", "color": "blue"},
                    {"name": "Reviewed", "color": "green"},
                    {"name": "Rejected", "color": "red"}
                ]}}
            }
            
            # Check if all required properties exist
            existing_properties = db_info.get("properties", {})
            missing_properties = set(required_properties.keys()) - set(existing_properties.keys())
            
            if missing_properties:
                logger.info(f"Missing properties: {missing_properties}")
                # Update database with missing properties
                self._update_database_schema(required_properties)
            
            logger.info("Database schema verified/updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error managing database schema: {e}")
            return False
    
    def add_paper(self, paper, analysis) -> Optional[str]:
        """
        Add a new paper to the Notion database.
        
        Args:
            paper: Paper object
            analysis: PaperAnalysis object
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            # Check if paper already exists
            if self._paper_exists(paper.arxiv_id):
                logger.info(f"Paper {paper.arxiv_id} already exists in database")
                return None
            
            # Prepare paper data for Notion
            notion_paper = self._prepare_paper_data(paper, analysis)
            
            # Create page in Notion
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=notion_paper
            )
            
            page_id = response["id"]
            logger.info(f"Added paper {paper.title} to Notion database")
            return page_id
            
        except Exception as e:
            logger.error(f"Error adding paper {paper.title}: {e}")
            return None
    
    def update_paper(self, arxiv_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing paper in the database.
        
        Args:
            arxiv_id: arXiv ID of the paper to update
            updates: Dictionary of properties to update
            
        Returns:
            True if update was successful
        """
        try:
            # Find the paper page
            page_id = self._find_paper_page(arxiv_id)
            if not page_id:
                logger.warning(f"Paper {arxiv_id} not found in database")
                return False
            
            # Update the page
            self.client.pages.update(
                page_id=page_id,
                properties=updates
            )
            
            logger.info(f"Updated paper {arxiv_id} in database")
            return True
            
        except Exception as e:
            logger.error(f"Error updating paper {arxiv_id}: {e}")
            return False
    
    def get_papers(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve papers from the database.
        
        Args:
            status: Filter by status (New, Reviewed, Rejected)
            limit: Maximum number of papers to retrieve
            
        Returns:
            List of paper dictionaries
        """
        try:
            query = {"page_size": limit}
            
            if status:
                query["filter"] = {
                    "property": "Status",
                    "select": {"equals": status}
                }
            
            response = self.client.databases.query(
                database_id=self.database_id,
                **query
            )
            
            papers = []
            for page in response["results"]:
                paper_data = self._extract_paper_data(page)
                papers.append(paper_data)
            
            logger.info(f"Retrieved {len(papers)} papers from database")
            return papers
            
        except Exception as e:
            logger.error(f"Error retrieving papers: {e}")
            return []
    
    def mark_paper_reviewed(self, arxiv_id: str) -> bool:
        """
        Mark a paper as reviewed.
        
        Args:
            arxiv_id: arXiv ID of the paper
            
        Returns:
            True if successful
        """
        return self.update_paper(arxiv_id, {
            "Status": {"select": {"name": "Reviewed"}}
        })
    
    def mark_paper_rejected(self, arxiv_id: str) -> bool:
        """
        Mark a paper as rejected.
        
        Args:
            arxiv_id: arXiv ID of the paper
            
        Returns:
            True if successful
        """
        return self.update_paper(arxiv_id, {
            "Status": {"select": {"name": "Rejected"}}
        })
    
    def _ensure_database_schema(self):
        """Ensure the database has the correct schema."""
        self.create_database_if_empty()
    
    def _update_database_schema(self, properties: Dict[str, Any]):
        """Update database schema with new properties."""
        try:
            self.client.databases.update(
                database_id=self.database_id,
                properties=properties
            )
            logger.info("Database schema updated successfully")
        except Exception as e:
            logger.error(f"Error updating database schema: {e}")
    
    def _paper_exists(self, arxiv_id: str) -> bool:
        """Check if a paper already exists in the database."""
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "ArXiv ID",
                    "rich_text": {"equals": arxiv_id}
                }
            )
            return len(response["results"]) > 0
        except Exception as e:
            logger.error(f"Error checking if paper exists: {e}")
            return False
    
    def _find_paper_page(self, arxiv_id: str) -> Optional[str]:
        """Find the Notion page ID for a paper."""
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "ArXiv ID",
                    "rich_text": {"equals": arxiv_id}
                }
            )
            
            if response["results"]:
                return response["results"][0]["id"]
            return None
            
        except Exception as e:
            logger.error(f"Error finding paper page: {e}")
            return None
    
    def _prepare_paper_data(self, paper, analysis) -> Dict[str, Any]:
        """Prepare paper data for Notion database."""
        return {
            "Title": {"title": [{"text": {"content": paper.title}}]},
            "Authors": {"rich_text": [{"text": {"content": ", ".join(paper.authors)}}]},
            "Abstract": {"rich_text": [{"text": {"content": paper.abstract}}]},
            "ArXiv ID": {"rich_text": [{"text": {"content": paper.arxiv_id}}]},
            "Published Date": {"date": {"start": paper.published_date.strftime("%Y-%m-%d")}},
            "Categories": {"multi_select": [{"name": cat} for cat in paper.categories]},
            "ArXiv URL": {"url": paper.arxiv_url},
            "Tags": {"multi_select": [{"name": tag} for tag in analysis.tags]},
            "Relevance Score": {"number": analysis.relevance_score},
            "Key Insights": {"rich_text": [{"text": {"content": ", ".join(analysis.key_insights)}}]},
            "Methodology": {"rich_text": [{"text": {"content": analysis.methodology}}]},
            "Status": {"select": {"name": "New"}}
        }
    
    def _extract_paper_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract paper data from Notion page."""
        properties = page.get("properties", {})
        
        return {
            "id": page["id"],
            "title": self._extract_text_property(properties.get("Title", {})),
            "authors": self._extract_text_property(properties.get("Authors", {})),
            "abstract": self._extract_text_property(properties.get("Abstract", {})),
            "arxiv_id": self._extract_text_property(properties.get("ArXiv ID", {})),
            "published_date": properties.get("Published Date", {}).get("date", {}).get("start"),
            "categories": [cat["name"] for cat in properties.get("Categories", {}).get("multi_select", [])],
            "arxiv_url": properties.get("ArXiv URL", {}).get("url"),
            "tags": [tag["name"] for tag in properties.get("Tags", {}).get("multi_select", [])],
            "relevance_score": properties.get("Relevance Score", {}).get("number", 0),
            "key_insights": self._extract_text_property(properties.get("Key Insights", {})),
            "methodology": self._extract_text_property(properties.get("Methodology", {})),
            "status": properties.get("Status", {}).get("select", {}).get("name", "New")
        }
    
    def _extract_text_property(self, property_data: Dict[str, Any]) -> str:
        """Extract text content from Notion property."""
        if "rich_text" in property_data:
            return "".join([text["text"]["content"] for text in property_data["rich_text"]])
        elif "title" in property_data:
            return "".join([text["text"]["content"] for text in property_data["title"]])
        return ""
