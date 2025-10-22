"""
arXiv Paper Monitor

Fetches papers from arXiv based on configured search criteria.
Handles paper metadata extraction and filtering.
"""

from cgi import parse_multipart
import arxiv
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Paper:
    """Represents a paper from arXiv."""
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    published_date: datetime
    categories: List[str]
    pdf_url: str
    arxiv_url: str


class ArxivMonitor:
    """Monitors arXiv for papers matching specified criteria."""
    
    def __init__(self, query: str, main_query: str, max_results: int = 50):
        """
        Initialize the arXiv monitor.
        
        Args:
            query: arXiv search query
            max_results: Maximum number of results to fetch
        """
        self.query = query
        self.main_query = main_query
        self.max_results = max_results
        self.client = arxiv.Client()
    
    def fetch_papers(self, days_back: int = 1) -> List[Paper]:
        """
        Fetch papers from arXiv matching the search criteria.
        
        Args:
            days_back: Number of days to look back for papers
            
        Returns:
            List of Paper objects
        """
        try:
            # Calculate date threshold
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Create search query
            search = arxiv.Search(
                query=self.query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                # Filter by date
                if result.published.date() >= cutoff_date.date():
                    paper = Paper(
                        title=result.title,
                        authors=[author.name for author in result.authors],
                        abstract=result.summary,
                        arxiv_id=result.entry_id.split('/')[-1],
                        published_date=result.published,
                        categories=result.categories,
                        pdf_url=result.pdf_url,
                        arxiv_url=result.entry_id
                    )
                    papers.append(paper)
                    logger.info(f"Found paper: {paper.title}")
            
            # print("Y"*100); exit()

            logger.info(f"Fetched {len(papers)} papers from arXiv")
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching papers from arXiv: {e}")
            return []
    
    def get_paper_details(self, arxiv_id: str) -> Optional[Paper]:
        """
        Get detailed information for a specific paper.
        
        Args:
            arxiv_id: arXiv ID of the paper
            
        Returns:
            Paper object or None if not found
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search), None)
            
            if result:
                return Paper(
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    arxiv_id=result.entry_id.split('/')[-1],
                    published_date=result.published,
                    categories=result.categories,
                    pdf_url=result.pdf_url,
                    arxiv_url=result.entry_id
                )
            return None
            
        except Exception as e:
            logger.error(f"Error fetching paper details for {arxiv_id}: {e}")
            return None
    
    def search_papers_by_keywords(self, keywords: List[str], days_back: int = 7) -> List[Paper]:
        """
        Search for papers containing specific keywords.
        
        Args:
            keywords: List of keywords to search for
            days_back: Number of days to look back
            
        Returns:
            List of matching Paper objects
        """
        try:
            # Build keyword query
            keyword_query = " OR ".join([f'abs:"{keyword}"' for keyword in keywords])
            full_query = f"({keyword_query}) AND {self.query}"
            
            search = arxiv.Search(
                query=full_query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            papers = []
            
            for result in self.client.results(search):
                if result.published.date() >= cutoff_date.date():
                    paper = Paper(
                        title=result.title,
                        authors=[author.name for author in result.authors],
                        abstract=result.summary,
                        arxiv_id=result.entry_id.split('/')[-1],
                        published_date=result.published,
                        categories=result.categories,
                        pdf_url=result.pdf_url,
                        arxiv_url=result.entry_id
                    )
                    papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers matching keywords: {keywords}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers by keywords: {e}")
            return []
