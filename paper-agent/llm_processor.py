"""
LLM Paper Processor

Handles LLM-based summarization, tagging, and analysis of papers.
Uses Google Gemini API for processing paper abstracts and generating insights.
"""

import google.generativeai as genai
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import json
import re


@dataclass
class PaperAnalysis:
    """Represents the LLM analysis of a paper."""
    tags: List[str]
    relevance_score: float
    key_insights: List[str]
    methodology: str


class LLMProcessor:
    """Processes papers using LLM for summarization and analysis."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Initialize the LLM processor.
        
        Args:
            api_key: Google API key for Gemini
            model: Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
    
    def analyze_paper(self, paper) -> PaperAnalysis:
        """
        Analyze a paper using LLM to extract insights, tags.
        
        Args:
            paper: Paper object to analyze
            
        Returns:
            PaperAnalysis object with LLM insights
        """
        try:
            prompt = self._create_analysis_prompt(paper)
            full_prompt = f"{self._get_system_prompt()}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1500,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            analysis_text = response.text
            analysis = self._parse_analysis_response(analysis_text)
            
            logger.info(f"Analyzed paper: {paper.title}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing paper {paper.title}: {e}")
            return self._create_default_analysis()
    

    def extract_tags(self, paper) -> List[str]:
        """
        Extract relevant tags for the paper.
        
        Args:
            paper: Paper object to tag
            
        Returns:
            List of relevant tags
        """
        try:
            prompt = f"""
            Extract 3-5 relevant tags for this paper related to AI agent scalable oversight:
            
            Title: {paper.title}
            Abstract: {paper.abstract}
            
            Return only the tags, separated by commas.
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=100,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            tags_text = response.text.strip()
            tags = [tag.strip() for tag in tags_text.split(',')]
            return tags[:5]  # Limit to 5 tags
            
        except Exception as e:
            logger.error(f"Error extracting tags for paper {paper.title}: {e}")
            return ["AI", "Research"]
    
    def _create_analysis_prompt(self, paper) -> str:
        """Create the analysis prompt for the paper."""
        return f"""
        Analyze this research paper for relevance to AI agent scalable oversight:
        
        Title: {paper.title}
        Authors: {', '.join(paper.authors)}
        Abstract: {paper.abstract}
        Categories: {', '.join(paper.categories)}
        
        Please provide:
        2. 3-5 relevant tags
        3. Relevance score (0-10) for scalable oversight
        4. Key insights (2-3 points)
        5. Methodology used (in paragraph format)
        
        Format your response as JSON with these fields: tags, relevance_score, key_insights, methodology
        """
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for analysis."""
        return """
        You are an expert AI researcher specializing in scalable oversight and AI alignment. 
        Analyze papers for their relevance to AI agent oversight, safety, and alignment research.
        Provide structured, insightful analysis focusing on practical implications for AI safety.
        """
    
    def _parse_analysis_response(self, response_text: str) -> PaperAnalysis:
        """Parse the LLM response into structured analysis."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return PaperAnalysis(
                    tags=data.get('tags', []),
                    relevance_score=float(data.get('relevance_score', 0)),
                    key_insights=data.get('key_insights', []),
                    methodology=data.get('methodology', ''),
                )
        except Exception as e:
            logger.warning(f"Could not parse JSON response: {e}")
        
        # Fallback parsing
        return PaperAnalysis(
            tags=self._extract_tags_from_text(response_text),
            relevance_score=self._extract_relevance_score(response_text),
            key_insights=self._extract_list_field(response_text, "key insights"),
            methodology=self._extract_field(response_text, "methodology"),
        )
    
    def _extract_field(self, text: str, field: str) -> str:
        """Extract a specific field from the response text."""
        pattern = rf"{field}.*?:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            return self._clean_malformed_text(result)
        return ""
    
    def _extract_tags_from_text(self, text: str) -> List[str]:
        """Extract tags from response text."""
        tag_pattern = r"tags.*?:\s*(.+?)(?:\n|$)"
        match = re.search(tag_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            tags_text = match.group(1)
            return [tag.strip() for tag in re.split(r'[,;]', tags_text)]
        return []
    
    def _extract_relevance_score(self, text: str) -> float:
        """Extract relevance score from response text."""
        score_pattern = r"relevance.*?score.*?:\s*(\d+(?:\.\d+)?)"
        match = re.search(score_pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else 0.0
    
    def _extract_list_field(self, text: str, field: str) -> List[str]:
        """Extract a list field from response text."""
        pattern = rf"{field}.*?:\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            items_text = match.group(1)
            # Clean up malformed text (characters separated by semicolons)
            items_text = self._clean_malformed_text(items_text)
            return [item.strip() for item in re.split(r'[•\-\*]\s*', items_text) if item.strip()]
        return []
    
    def _clean_malformed_text(self, text: str) -> str:
        """Clean up text that has characters separated by semicolons."""
        # Check if text has the pattern: "T; h; e;  ; p; a; p; e; r;"
        if ';' in text and len(text.split(';')) > 10:
            # This looks like malformed text, try to reconstruct it
            # Split by semicolon and join, removing extra spaces
            parts = text.split(';')
            cleaned = ''.join(parts).replace('  ', ' ').strip()
            return cleaned
        return text
    
    def _create_default_analysis(self) -> PaperAnalysis:
        """Create a default analysis when processing fails."""
        return PaperAnalysis(
            tags=["AI", "Research"],
            relevance_score=0.0,
            key_insights=["Manual review needed"],
            methodology="Unknown",
        )
