"""NLP analysis for segment detection using spaCy and Transformers."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SegmentAnalyzer:
    """Analyzes text segments for interest scoring using NLP."""

    def __init__(self):
        """Initialize analyzer."""
        self.nlp = None
        self.sentiment_model = None

    async def load_models(self) -> None:
        """Load spaCy and sentiment analysis models."""
        import spacy

        if self.nlp is None:
            logger.info("Loading spaCy model")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.info("Downloading en_core_web_sm model...")
                import subprocess

                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
                self.nlp = spacy.load("en_core_web_sm")

        if self.sentiment_model is None:
            logger.info("Loading sentiment model")
            from transformers import pipeline

            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
            )

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text for sentiment and entities.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment and entity information
        """
        await self.load_models()

        doc = self.nlp(text)

        # Sentiment analysis
        sentiment_result = self.sentiment_model(text[:512])[0]  # Limit to 512 tokens
        sentiment = sentiment_result["label"].lower()
        confidence = sentiment_result["score"]

        # Extract entities
        entities = [
            {"text": ent.text, "label": ent.label_} for ent in doc.ents
        ]

        # Extract key phrases (nouns and noun chunks)
        noun_chunks = [chunk.text for chunk in doc.noun_chunks]

        # Analyze text properties
        is_question = text.rstrip().endswith("?")
        has_exclamation = "!" in text
        text_length = len(doc)

        analysis = {
            "sentiment": sentiment,
            "confidence": confidence,
            "entities": entities,
            "noun_chunks": noun_chunks,
            "is_question": is_question,
            "has_exclamation": has_exclamation,
            "text_length": text_length,
        }

        return analysis

    async def score_segment(
        self,
        text: str,
        segment_index: int,
        total_segments: int,
    ) -> float:
        """Score segment for interest/engagement.
        
        Args:
            text: Segment text
            segment_index: Index in sequence
            total_segments: Total segments
            
        Returns:
            Interest score 0-1
        """
        analysis = await self.analyze_text(text)

        score = 0.0

        # Sentiment score (positive = higher)
        sentiment = analysis["sentiment"]
        confidence = analysis["confidence"]
        if sentiment == "positive":
            score += confidence * 0.3
        elif sentiment == "negative":
            score -= confidence * 0.1

        # Question/exclamation boost
        if analysis["is_question"]:
            score += 0.2
        if analysis["has_exclamation"]:
            score += 0.15

        # Entity presence boost (more entities = more content)
        entity_count = len(analysis["entities"])
        score += min(entity_count * 0.05, 0.2)

        # Text length factor (prefer medium length)
        text_len = analysis["text_length"]
        if 20 <= text_len <= 100:
            score += 0.1
        elif text_len > 150:
            score -= 0.05

        # Position boost (openings slightly favored)
        position_ratio = segment_index / max(total_segments - 1, 1)
        if position_ratio < 0.3:
            score += 0.1

        # Clamp to 0-1
        return max(0.0, min(1.0, score))
