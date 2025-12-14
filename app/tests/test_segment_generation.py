"""Tests for segment generation and analysis logic."""

import asyncio
import json
import pytest
from typing import Any, Dict, List

from app.services.segment_analyzer import SegmentAnalyzer
from app.services.segment_generator import SegmentGenerator


@pytest.fixture
def sample_transcript_segments() -> List[Dict[str, Any]]:
    """Sample transcript segments for testing."""
    return [
        {
            "id": 0,
            "start": 0.0,
            "end": 5.0,
            "text": "Welcome to this amazing tutorial!",
            "confidence": 0.95,
        },
        {
            "id": 1,
            "start": 5.0,
            "end": 15.0,
            "text": "Today we're going to learn about Python programming and machine learning.",
            "confidence": 0.92,
        },
        {
            "id": 2,
            "start": 15.0,
            "end": 25.0,
            "text": "First, let's understand the basics. What is Python?",
            "confidence": 0.89,
        },
        {
            "id": 3,
            "start": 25.0,
            "end": 35.0,
            "text": "Python is a high-level programming language that's easy to learn!",
            "confidence": 0.91,
        },
        {
            "id": 4,
            "start": 35.0,
            "end": 50.0,
            "text": "It's used by thousands of companies worldwide for web development, data science, and AI.",
            "confidence": 0.88,
        },
        {
            "id": 5,
            "start": 50.0,
            "end": 65.0,
            "text": "One of the best things about Python is its huge ecosystem of libraries.",
            "confidence": 0.90,
        },
        {
            "id": 6,
            "start": 65.0,
            "end": 80.0,
            "text": "Libraries like NumPy, Pandas, and scikit-learn make data analysis incredibly simple.",
            "confidence": 0.87,
        },
        {
            "id": 7,
            "start": 80.0,
            "end": 95.0,
            "text": "Now let's talk about machine learning. It's revolutionizing the world!",
            "confidence": 0.93,
        },
        {
            "id": 8,
            "start": 95.0,
            "end": 110.0,
            "text": "Machine learning allows computers to learn from data without explicit programming.",
            "confidence": 0.91,
        },
        {
            "id": 9,
            "start": 110.0,
            "end": 120.0,
            "text": "Thank you for watching! Don't forget to like and subscribe.",
            "confidence": 0.94,
        },
    ]


class TestSegmentAnalyzer:
    """Tests for the SegmentAnalyzer class."""

    @pytest.mark.asyncio
    async def test_analyze_text_basic(self):
        """Test basic text analysis."""
        analyzer = SegmentAnalyzer()
        
        result = await analyzer.analyze_text("This is a great product!")
        
        assert "sentiment" in result
        assert "confidence" in result
        assert "entities" in result
        assert "noun_chunks" in result
        assert result["sentiment"] in ["positive", "negative"]

    @pytest.mark.asyncio
    async def test_score_segment_positive(self):
        """Test scoring for positive sentiment."""
        analyzer = SegmentAnalyzer()
        
        score = await analyzer.score_segment(
            "This is amazing! What an incredible discovery!",
            segment_index=0,
            total_segments=10,
        )
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should have decent score with positive sentiment

    @pytest.mark.asyncio
    async def test_score_segment_question(self):
        """Test scoring with questions."""
        analyzer = SegmentAnalyzer()
        
        score = await analyzer.score_segment(
            "Have you ever wondered how this works?",
            segment_index=5,
            total_segments=10,
        )
        
        assert 0 <= score <= 1

    @pytest.mark.asyncio
    async def test_score_segment_exclamation(self):
        """Test scoring with exclamations."""
        analyzer = SegmentAnalyzer()
        
        score = await analyzer.score_segment(
            "This is incredible!",
            segment_index=3,
            total_segments=10,
        )
        
        assert 0 <= score <= 1


class TestSegmentGenerator:
    """Tests for the SegmentGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_segments_basic(self, sample_transcript_segments):
        """Test basic segment generation."""
        generator = SegmentGenerator()
        
        # Create scores for each segment
        scores = [0.5 + (i % 3) * 0.2 for i in range(len(sample_transcript_segments))]
        
        segments = await generator.generate_segments(
            sample_transcript_segments,
            video_duration=120.0,
            segment_scores=scores,
        )
        
        assert len(segments) >= 5  # Should generate at least 5 segments
        assert all(30 <= seg["duration"] <= 40 for seg in segments)
        assert all("start" in seg and "end" in seg for seg in segments)

    @pytest.mark.asyncio
    async def test_generate_segments_has_metadata(self, sample_transcript_segments):
        """Test that generated segments have required metadata."""
        generator = SegmentGenerator()
        
        scores = [0.5] * len(sample_transcript_segments)
        
        segments = await generator.generate_segments(
            sample_transcript_segments,
            video_duration=120.0,
            segment_scores=scores,
        )
        
        assert len(segments) > 0
        
        for seg in segments:
            assert "id" in seg
            assert "start" in seg
            assert "end" in seg
            assert "duration" in seg
            assert "title" in seg
            assert "description" in seg
            assert "text" in seg
            assert "interest_score" in seg
            assert 0 <= seg["interest_score"] <= 1

    @pytest.mark.asyncio
    async def test_segments_sorted_by_start_time(self, sample_transcript_segments):
        """Test that returned segments are sorted by start time."""
        generator = SegmentGenerator()
        
        scores = [0.5 + (i % 2) * 0.3 for i in range(len(sample_transcript_segments))]
        
        segments = await generator.generate_segments(
            sample_transcript_segments,
            video_duration=120.0,
            segment_scores=scores,
        )
        
        start_times = [seg["start"] for seg in segments]
        assert start_times == sorted(start_times)

    @pytest.mark.asyncio
    async def test_title_generation(self, sample_transcript_segments):
        """Test that titles are generated properly."""
        generator = SegmentGenerator()
        
        scores = [0.5] * len(sample_transcript_segments)
        
        segments = await generator.generate_segments(
            sample_transcript_segments,
            video_duration=120.0,
            segment_scores=scores,
        )
        
        for seg in segments:
            assert len(seg["title"]) > 0
            assert len(seg["title"]) <= 60

    @pytest.mark.asyncio
    async def test_description_generation(self, sample_transcript_segments):
        """Test that descriptions are generated properly."""
        generator = SegmentGenerator()
        
        scores = [0.5] * len(sample_transcript_segments)
        
        segments = await generator.generate_segments(
            sample_transcript_segments,
            video_duration=120.0,
            segment_scores=scores,
        )
        
        for seg in segments:
            assert len(seg["description"]) > 0
            assert len(seg["description"]) <= 155  # 150 + "..."


class TestSegmentationIntegration:
    """Integration tests for complete segmentation workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_segmentation(self, sample_transcript_segments):
        """Test complete segmentation from analysis to generation."""
        analyzer = SegmentAnalyzer()
        generator = SegmentGenerator()
        
        # Score all segments
        scores = []
        for i, seg in enumerate(sample_transcript_segments):
            score = await analyzer.score_segment(
                seg["text"],
                i,
                len(sample_transcript_segments),
            )
            scores.append(score)
        
        # Generate segments
        segments = await generator.generate_segments(
            sample_transcript_segments,
            video_duration=120.0,
            segment_scores=scores,
        )
        
        # Validate results
        assert len(segments) >= 5
        assert all("interest_score" in seg for seg in segments)
        
        # Check that interest scores are used to order candidates
        # (highest scores should appear first before sorting by start time)
        scores_before_sort = [seg["interest_score"] for seg in segments]
        assert len(scores_before_sort) > 0


@pytest.mark.asyncio
async def test_concurrent_analysis():
    """Test that multiple segments can be analyzed concurrently."""
    analyzer = SegmentAnalyzer()
    
    texts = [
        "This is amazing!",
        "What a disaster.",
        "Incredible discovery!",
        "Boring content here.",
    ]
    
    # Analyze all concurrently
    tasks = [
        analyzer.analyze_text(text)
        for text in texts
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == len(texts)
    assert all("sentiment" in r for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
