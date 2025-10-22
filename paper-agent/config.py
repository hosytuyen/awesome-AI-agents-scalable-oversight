"""
Configuration Management

Handles application configuration, environment variables, and settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class ArxivConfig:
    """Configuration for arXiv monitoring."""
    query: str
    max_results: int = 50
    days_back: int = 1
    categories: list = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = ["cs.AI", "cs.LG", "cs.CL"]


@dataclass
class LLMConfig:
    """Configuration for LLM processing."""
    api_key: str
    model: str = "gemini-1.5-flash"
    temperature: float = 0.3
    max_tokens: int = 1500
    timeout: int = 30


@dataclass
class NotionConfig:
    """Configuration for Notion integration."""
    api_key: str
    database_id: str
    page_size: int = 100


@dataclass
class SchedulerConfig:
    """Configuration for task scheduling."""
    frequency: str = "daily"
    time: str = "09:00"
    days: list = None
    custom_interval: int = None
    
    def __post_init__(self):
        if self.days is None:
            self.days = ["monday", "tuesday", "wednesday", "thursday", "friday"]


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    file_path: str = "logs/paper_agent.log"
    max_file_size: str = "10 MB"
    backup_count: int = 5
    rotation: str = "1 day"
    retention: str = "30 days"


class Config:
    """Main configuration class."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Path to environment file
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables."""
        # ArXiv configuration
        self.arxiv = ArxivConfig(
            query=os.getenv(
                "ARXIV_QUERY", 
                'cat:cs.AI AND (abstract:"scalable oversight" OR abstract:"AI agents" OR abstract:"agent oversight" OR abstract:"supervision" OR abstract:"alignment")'
            ),
            max_results=int(os.getenv("ARXIV_MAX_RESULTS", "50")),
            days_back=int(os.getenv("ARXIV_DAYS_BACK", "1")),
            categories=os.getenv("ARXIV_CATEGORIES", "cs.AI,cs.LG,cs.CL").split(",")
        )
        
        # LLM configuration
        self.llm = LLMConfig(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=os.getenv("LLM_MODEL", "gemini-1.5-flash"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1500")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )
        
        # Notion configuration
        self.notion = NotionConfig(
            api_key=os.getenv("NOTION_API_KEY"),
            database_id=os.getenv("NOTION_DATABASE_ID"),
            page_size=int(os.getenv("NOTION_PAGE_SIZE", "100"))
        )
        
        # Scheduler configuration
        self.scheduler = SchedulerConfig(
            frequency=os.getenv("SCHEDULER_FREQUENCY", "daily"),
            time=os.getenv("SCHEDULER_TIME", "09:00"),
            days=os.getenv("SCHEDULER_DAYS", "monday,tuesday,wednesday,thursday,friday").split(","),
            custom_interval=int(os.getenv("SCHEDULER_CUSTOM_INTERVAL", "0")) or None
        )
        
        # Logging configuration
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_FILE_PATH", "logs/paper_agent.log"),
            max_file_size=os.getenv("LOG_MAX_FILE_SIZE", "10 MB"),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            rotation=os.getenv("LOG_ROTATION", "1 day"),
            retention=os.getenv("LOG_RETENTION", "30 days")
        )
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate configuration and return any issues.
        
        Returns:
            Dictionary of validation results
        """
        issues = {}
        
        # Check required API keys
        if not self.llm.api_key:
            issues["llm"] = "Google API key is required"
        
        if not self.notion.api_key:
            issues["notion"] = "Notion API key is required"
        
        if not self.notion.database_id:
            issues["notion"] = "Notion database ID is required"
        
        # Validate numeric values
        if self.arxiv.max_results <= 0:
            issues["arxiv"] = "Max results must be positive"
        
        if self.llm.temperature < 0 or self.llm.temperature > 2:
            issues["llm"] = "Temperature must be between 0 and 2"
        
        if self.llm.max_tokens <= 0:
            issues["llm"] = "Max tokens must be positive"
        
        # Validate scheduler configuration
        if self.scheduler.frequency not in ["daily", "weekly", "custom"]:
            issues["scheduler"] = "Frequency must be daily, weekly, or custom"
        
        if self.scheduler.frequency == "custom" and not self.scheduler.custom_interval:
            issues["scheduler"] = "Custom interval required for custom frequency"
        
        return issues
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "arxiv": {
                "query": self.arxiv.query,
                "max_results": self.arxiv.max_results,
                "days_back": self.arxiv.days_back,
                "categories": self.arxiv.categories
            },
            "llm": {
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "api_key_configured": bool(self.llm.api_key)
            },
            "notion": {
                "database_id": self.notion.database_id,
                "page_size": self.notion.page_size,
                "api_key_configured": bool(self.notion.api_key)
            },
            "scheduler": {
                "frequency": self.scheduler.frequency,
                "time": self.scheduler.time,
                "days": self.scheduler.days,
                "custom_interval": self.scheduler.custom_interval
            },
            "logging": {
                "level": self.logging.level,
                "file_path": self.logging.file_path
            }
        }
