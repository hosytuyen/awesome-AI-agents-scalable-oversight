"""
Main Application Entry Point

Orchestrates the paper monitoring workflow including arXiv fetching,
LLM processing, and Notion database updates.
"""

import keyword
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger
from dotenv import load_dotenv

from arxiv_monitor import ArxivMonitor, Paper
from llm_processor import LLMProcessor, PaperAnalysis
from notion_manager import NotionManager
from scheduler import TaskScheduler, ScheduleConfig


class PaperAgent:
    """Main application class that orchestrates the paper monitoring workflow."""
    
    def __init__(self):
        """Initialize the paper agent with configuration."""
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.arxiv_monitor = None
        self.llm_processor = None
        self.notion_manager = None
        self.scheduler = TaskScheduler()
        
        # Configuration
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self._initialize_components()
    
    def _load_config(self) -> dict:
        """Load configuration from environment variables."""
        return {
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "notion_api_key": os.getenv("NOTION_API_KEY"),
            "notion_database_id": os.getenv("NOTION_DATABASE_ID"),
            "arxiv_query": os.getenv("ARXIV_QUERY", 'cat:cs.AI AND (abstract:"scalable oversight" OR abstract:"AI agents" OR abstract:"agent oversight" OR abstract:"supervision" OR abstract:"alignment" OR abstract:"AI safety" OR abstract:"AI alignment" OR abstract:"superhuman AI" OR abstract:"AI governance")'),
            "check_frequency": os.getenv("CHECK_FREQUENCY", "daily"),
            "check_time": os.getenv("CHECK_TIME", "09:00"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "max_papers": int(os.getenv("MAX_PAPERS", "200")),
            "main_query": os.getenv("MAIN_QUERY", 'scalable oversight')
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = self.config["log_level"]
        
        # Remove default handler
        logger.remove()
        
        # Add console handler
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # Add file handler
        logger.add(
            "logs/paper_agent_{time:YYYY-MM-DD}.log",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="30 days"
        )
    
    def _initialize_components(self):
        """Initialize all components with proper error handling."""
        try:
            # Initialize arXiv monitor
            self.arxiv_monitor = ArxivMonitor(
                query=self.config["arxiv_query"],
                max_results=self.config["max_papers"],
                main_query=self.config["main_query"]
            )
            logger.info("arXiv monitor initialized")
            
            # Initialize LLM processor
            if not self.config["google_api_key"]:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            self.llm_processor = LLMProcessor(
                api_key=self.config["google_api_key"]
            )
            logger.info("LLM processor initialized")
            
            # Initialize Notion manager
            if not self.config["notion_api_key"] or not self.config["notion_database_id"]:
                raise ValueError("Notion API credentials not found in environment variables")
            
            self.notion_manager = NotionManager(
                api_key=self.config["notion_api_key"],
                database_id=self.config["notion_database_id"]
            )
            logger.info("Notion manager initialized")
            
            # Ensure database schema
            self.notion_manager.create_database_if_empty()
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            sys.exit(1)
    
    def run_daily_check(self):
        """Run the daily paper check workflow."""
        logger.info("Starting daily paper check")
        
        try:
            # Fetch papers from arXiv
            papers = self.arxiv_monitor.fetch_papers(days_back=1)
            logger.info(f"Found {len(papers)} new papers")
            
            if not papers:
                logger.info("No new papers found")
                return
            
            # Process each paper
            processed_count = 0
            for paper in papers:
                try:
                    # Check if paper already exists in database to save LLM costs
                    if self.notion_manager._paper_exists(paper.arxiv_id):
                        logger.info(f"Paper {paper.arxiv_id} already exists in database, skipping LLM analysis")
                        continue
                    
                    # Analyze paper with LLM
                    analysis = self.llm_processor.analyze_paper(paper)
                    
                    # Check if paper should be included based on tags
                    if not self._should_include_paper(analysis):
                        logger.info(f"Skipping paper (no relevant tags): {paper.title}")
                        continue
                    
                    # Add to Notion database
                    page_id = self.notion_manager.add_paper(paper, analysis)
                    
                    if page_id:
                        processed_count += 1
                        logger.info(f"Processed paper: {paper.title}")
                    else:
                        logger.warning(f"Failed to add paper to database: {paper.title}")
                        
                except Exception as e:
                    logger.error(f"Error processing paper {paper.title}: {e}")
                    continue
            
            logger.info(f"Daily check completed. Processed {processed_count} papers")
            
        except Exception as e:
            logger.error(f"Error in daily check: {e}")
    
    def run_manual_check(self, days_back: int = 7) -> List[dict]:
        """
        Run a manual check for papers from the last N days.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of processed papers
        """
        logger.info(f"Starting manual check for last {days_back} days")
        
        try:
            # Fetch papers
            papers = self.arxiv_monitor.fetch_papers(days_back=days_back)

            logger.info(f"Found {len(papers)} papers")
            
            processed_papers = []
            
            for paper in papers:
                try:
                    # Check if paper already exists in database to save LLM costs
                    if self.notion_manager._paper_exists(paper.arxiv_id):
                        logger.info(f"Paper {paper.arxiv_id} already exists in database, skipping LLM analysis")
                        continue

                    if paper.arxiv_id == "2508.19461":
                        print("2508.19461"); exit()
                    
                    # Analyze paper
                    analysis = self.llm_processor.analyze_paper(paper, self.config["main_query"])
                    
                    # Check if paper should be included based on tags
                    if not self._should_include_paper(analysis):
                        logger.info(f"Skipping paper (no relevant tags): {paper.title}")
                        continue
                    
                    # print(self.config["main_query"])
                    # print(analysis.tags)

                    # Add to database
                    page_id = self.notion_manager.add_paper(paper, analysis)
                    
                    if page_id:
                        processed_papers.append({
                            "title": paper.title,
                            "arxiv_id": paper.arxiv_id,
                            "relevance_score": analysis.relevance_score,
                            "notion_page_id": page_id
                        })
                        logger.info(f"Processed: {paper.title}")
                    
                except Exception as e:
                    logger.error(f"Error processing {paper.title}: {e}")
                    continue
            
            logger.info(f"Manual check completed. Processed {len(processed_papers)} papers")
            return processed_papers
            
        except Exception as e:
            logger.error(f"Error in manual check: {e}")
            return []
    
    def start_scheduled_monitoring(self):
        """Start the scheduled monitoring system."""
        try:
            # Create schedule configuration
            schedule_config = ScheduleConfig(
                frequency=self.config["check_frequency"],
                time=self.config["check_time"]
            )
            
            # Schedule the daily check
            self.scheduler.schedule_from_config(
                task_func=self.run_daily_check,
                config=schedule_config,
                task_name="daily_paper_monitor"
            )
            
            # Start the scheduler
            self.scheduler.start_scheduler()
            
            logger.info(f"Scheduled monitoring started. Frequency: {self.config['check_frequency']}, Time: {self.config['check_time']}")
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                self.scheduler.stop_scheduler()
                logger.info("Scheduler stopped")
                
        except Exception as e:
            logger.error(f"Error starting scheduled monitoring: {e}")
    
    def _should_include_paper(self, analysis) -> bool:
        """
        Check if a paper should be included based on tag filtering.
        
        Args:
            analysis: PaperAnalysis object with tags
            
        Returns:
            True if paper should be included, False otherwise
        """
        # Use MAIN_QUERY from environment instead of hardcoded keywords
        main_query = self.config["main_query"].lower()
        
        # Split the main query into individual keywords for matching
        keywords = [word.strip() for word in main_query.split() if len(word.strip()) > 2]
        
        # Check if any tag contains any of the keywords from MAIN_QUERY
        for tag in analysis.tags:
            tag_lower = tag.lower()
            for keyword in keywords:
                if keyword in tag_lower:
                    return True
        
        logger.info(f"Paper filtered out - no tags contain keywords from MAIN_QUERY '{main_query}': {analysis.tags}")
        return False
    
    def get_database_status(self) -> dict:
        """Get the current status of the Notion database."""
        try:
            papers = self.notion_manager.get_papers(limit=1000)
            
            status = {
                "total_papers": len(papers),
                "new_papers": len([p for p in papers if p.get("status") == "New"]),
                "reviewed_papers": len([p for p in papers if p.get("status") == "Reviewed"]),
                "rejected_papers": len([p for p in papers if p.get("status") == "Rejected"]),
                "recent_papers": len([p for p in papers if p.get("published_date") and 
                                    datetime.fromisoformat(p.get("published_date", "").replace("Z", "+00:00")).date() >= 
                                    (datetime.now().date() - timedelta(days=7))])
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {"error": str(e)}
    
    def search_papers(self, query: str, limit: int = 200) -> List[dict]:
        """
        Search for papers in the database.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching papers
        """
        try:
            # This would need to be implemented in NotionManager
            # For now, return all papers and filter client-side
            papers = self.notion_manager.get_papers(limit=limit)
            
            # Simple text search (Notion API doesn't support full-text search easily)
            matching_papers = []
            query_lower = query.lower()
            
            for paper in papers:
                if (query_lower in paper.get("title", "").lower() or 
                    query_lower in paper.get("abstract", "").lower() or
                    query_lower in paper.get("summary", "").lower()):
                    matching_papers.append(paper)
            
            return matching_papers[:limit]
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []


def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="arXiv Paper Agent")
    parser.add_argument("--mode", choices=["manual", "scheduled"], default="scheduled",
                       help="Run mode: manual check or scheduled monitoring")
    parser.add_argument("--days", type=int, default=1,
                       help="Number of days to look back for manual mode")
    parser.add_argument("--status", action="store_true",
                       help="Show database status and exit")
    
    args = parser.parse_args()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Initialize the paper agent
    agent = PaperAgent()
    
    if args.status:
        # Show database status
        status = agent.get_database_status()
        print(f"Database Status: {status}")
        return
    
    if args.mode == "manual":
        # Run manual check
        papers = agent.run_manual_check(days_back=args.days)
        print(f"Processed {len(papers)} papers")
        for paper in papers:
            print(f"- {paper['title']} (Score: {paper['relevance_score']})")
    
    elif args.mode == "scheduled":
        # Start scheduled monitoring
        agent.start_scheduled_monitoring()


if __name__ == "__main__":
    main()
