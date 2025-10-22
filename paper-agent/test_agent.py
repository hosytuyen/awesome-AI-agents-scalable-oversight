"""
Test Suite for arXiv Paper Agent

Basic tests to verify functionality of core components.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arxiv_monitor import ArxivMonitor, Paper
from llm_processor import LLMProcessor, PaperAnalysis
from notion_manager import NotionManager
from scheduler import TaskScheduler, ScheduleConfig
from config import Config


class TestArxivMonitor(unittest.TestCase):
    """Test cases for ArxivMonitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ArxivMonitor("cat:cs.AI", max_results=5)
    
    def test_initialization(self):
        """Test ArxivMonitor initialization."""
        self.assertEqual(self.monitor.query, "cat:cs.AI")
        self.assertEqual(self.monitor.max_results, 5)
        self.assertIsNotNone(self.monitor.client)
    
    @patch('arxiv_monitor.arxiv.Client')
    def test_fetch_papers_mock(self, mock_client):
        """Test paper fetching with mocked client."""
        # Mock the client and results
        mock_result = Mock()
        mock_result.title = "Test Paper"
        mock_result.authors = [Mock(name="Test Author")]
        mock_result.summary = "Test abstract"
        mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
        mock_result.published = datetime.now()
        mock_result.categories = ["cs.AI"]
        mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678.pdf"
        
        mock_client.return_value.results.return_value = [mock_result]
        
        # Test fetching
        papers = self.monitor.fetch_papers(days_back=1)
        
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].title, "Test Paper")
        self.assertEqual(papers[0].arxiv_id, "1234.5678")


class TestLLMProcessor(unittest.TestCase):
    """Test cases for LLMProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = LLMProcessor("test-api-key")
    
    def test_initialization(self):
        """Test LLMProcessor initialization."""
        self.assertEqual(self.processor.model_name, "gemini-1.5-pro")
        self.assertIsNotNone(self.processor.model)
    
    @patch('llm_processor.genai.GenerativeModel')
    def test_analyze_paper_mock(self, mock_model):
        """Test paper analysis with mocked Gemini client."""
        # Mock the response
        mock_response = Mock()
        mock_response.text = '''
        {
            "summary": "Test summary",
            "tags": ["AI", "Research"],
            "relevance_score": 8.5,
            "key_insights": ["Insight 1", "Insight 2"],
            "methodology": "Experimental",
            "limitations": ["Limited data"],
            "future_work": ["More experiments"]
        }
        '''
        
        mock_model.return_value.generate_content.return_value = mock_response
        
        # Create a test paper
        paper = Paper(
            title="Test Paper",
            authors=["Test Author"],
            abstract="Test abstract",
            arxiv_id="1234.5678",
            published_date=datetime.now(),
            categories=["cs.AI"],
            pdf_url="http://example.com/paper.pdf",
            arxiv_url="http://arxiv.org/abs/1234.5678"
        )
        
        # Test analysis
        analysis = self.processor.analyze_paper(paper)
        
        self.assertIsInstance(analysis, PaperAnalysis)
        self.assertEqual(analysis.summary, "Test summary")
        self.assertEqual(len(analysis.tags), 2)
        self.assertEqual(analysis.relevance_score, 8.5)


class TestNotionManager(unittest.TestCase):
    """Test cases for NotionManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = NotionManager("test-api-key", "test-database-id")
    
    def test_initialization(self):
        """Test NotionManager initialization."""
        self.assertEqual(self.manager.database_id, "test-database-id")
        self.assertIsNotNone(self.manager.client)
    
    @patch('notion_manager.Client')
    def test_paper_exists_mock(self, mock_client):
        """Test paper existence check with mocked client."""
        # Mock the response
        mock_client.return_value.databases.query.return_value = {
            "results": [{"id": "test-page-id"}]
        }
        
        # Test paper existence
        exists = self.manager._paper_exists("1234.5678")
        
        self.assertTrue(exists)


class TestTaskScheduler(unittest.TestCase):
    """Test cases for TaskScheduler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = TaskScheduler()
    
    def test_initialization(self):
        """Test TaskScheduler initialization."""
        self.assertFalse(self.scheduler.running)
        self.assertEqual(len(self.scheduler.jobs), 0)
    
    def test_schedule_daily_task(self):
        """Test daily task scheduling."""
        def test_task():
            pass
        
        self.scheduler.schedule_daily_task(test_task, "09:00", "test_task")
        
        self.assertEqual(len(self.scheduler.jobs), 1)
        self.assertIn("test_task", self.scheduler.jobs)
    
    def test_schedule_from_config(self):
        """Test scheduling from configuration."""
        def test_task():
            pass
        
        config = ScheduleConfig(
            frequency="daily",
            time="10:00"
        )
        
        self.scheduler.schedule_from_config(test_task, config, "config_task")
        
        self.assertEqual(len(self.scheduler.jobs), 1)
        self.assertIn("config_task", self.scheduler.jobs)


class TestConfig(unittest.TestCase):
    """Test cases for Config."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_initialization(self):
        """Test Config initialization."""
        self.assertIsNotNone(self.config.arxiv)
        self.assertIsNotNone(self.config.llm)
        self.assertIsNotNone(self.config.notion)
        self.assertIsNotNone(self.config.scheduler)
        self.assertIsNotNone(self.config.logging)
    
    def test_validation(self):
        """Test configuration validation."""
        issues = self.config.validate()
        
        # Should have issues since we're using test values
        self.assertIsInstance(issues, dict)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    @patch('arxiv_monitor.arxiv.Client')
    @patch('llm_processor.genai.GenerativeModel')
    @patch('notion_manager.Client')
    def test_full_workflow_mock(self, mock_notion, mock_gemini, mock_arxiv):
        """Test the full workflow with mocked dependencies."""
        # Mock arXiv response
        mock_arxiv_result = Mock()
        mock_arxiv_result.title = "Integration Test Paper"
        mock_arxiv_result.authors = [Mock(name="Test Author")]
        mock_arxiv_result.summary = "Test abstract for integration"
        mock_arxiv_result.entry_id = "http://arxiv.org/abs/9999.9999"
        mock_arxiv_result.published = datetime.now()
        mock_arxiv_result.categories = ["cs.AI"]
        mock_arxiv_result.pdf_url = "http://arxiv.org/pdf/9999.9999.pdf"
        
        mock_arxiv.return_value.results.return_value = [mock_arxiv_result]
        
        # Mock Gemini response
        mock_gemini_response = Mock()
        mock_gemini_response.text = '''
        {
            "summary": "Integration test summary",
            "tags": ["AI", "Test"],
            "relevance_score": 7.0,
            "key_insights": ["Test insight"],
            "methodology": "Simulation",
            "limitations": ["Test limitation"],
            "future_work": ["Test future work"]
        }
        '''
        mock_gemini.return_value.generate_content.return_value = mock_gemini_response
        
        # Mock Notion response
        mock_notion.return_value.pages.create.return_value = {"id": "test-page-id"}
        mock_notion.return_value.databases.query.return_value = {"results": []}
        
        # Test the workflow
        monitor = ArxivMonitor("cat:cs.AI", max_results=1)
        processor = LLMProcessor("test-key")
        manager = NotionManager("test-key", "test-db")
        
        # Fetch papers
        papers = monitor.fetch_papers(days_back=1)
        self.assertEqual(len(papers), 1)
        
        # Process paper
        analysis = processor.analyze_paper(papers[0])
        self.assertIsInstance(analysis, PaperAnalysis)
        
        # Add to database
        page_id = manager.add_paper(papers[0], analysis)
        self.assertIsNotNone(page_id)


def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestArxivMonitor,
        TestLLMProcessor,
        TestNotionManager,
        TestTaskScheduler,
        TestConfig,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running arXiv Paper Agent Tests...")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
