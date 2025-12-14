"""Generate candidate video segments from transcript with interest scoring."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SegmentGenerator:
    """Generates candidate clips from transcript segments."""

    def __init__(self):
        """Initialize generator."""
        self.min_duration = 30  # seconds
        self.max_duration = 40  # seconds
        self.min_segments = 5

    async def generate_segments(
        self,
        transcript_segments: List[Dict[str, Any]],
        video_duration: float,
        segment_scores: List[float],
    ) -> List[Dict[str, Any]]:
        """Generate candidate clips from transcript segments.
        
        Args:
            transcript_segments: List of transcription segments with timing
            video_duration: Total video duration in seconds
            segment_scores: Interest scores for each segment
            
        Returns:
            List of candidate segments with timing and metadata
        """
        if not transcript_segments:
            logger.warning("No transcript segments provided")
            return []

        candidates = []

        # Try different window sizes and positions
        for start_idx in range(len(transcript_segments)):
            # Find end index that creates 30-40s segment
            current_start_time = transcript_segments[start_idx]["start"]
            current_end_idx = start_idx

            for end_idx in range(start_idx + 1, len(transcript_segments)):
                end_time = transcript_segments[end_idx]["end"]
                duration = end_time - current_start_time

                if duration >= self.min_duration:
                    if duration <= self.max_duration:
                        current_end_idx = end_idx
                    else:
                        break

            if current_end_idx > start_idx:
                end_time = transcript_segments[current_end_idx]["end"]
                duration = end_time - current_start_time

                # Create segment candidate
                segment_text = " ".join(
                    seg["text"]
                    for seg in transcript_segments[start_idx : current_end_idx + 1]
                )

                # Calculate average score for this segment
                segment_slice_scores = segment_scores[start_idx : current_end_idx + 1]
                avg_score = (
                    sum(segment_slice_scores) / len(segment_slice_scores)
                    if segment_slice_scores
                    else 0.5
                )

                candidate = {
                    "start": current_start_time,
                    "end": end_time,
                    "duration": duration,
                    "start_idx": start_idx,
                    "end_idx": current_end_idx,
                    "text": segment_text,
                    "interest_score": avg_score,
                }

                candidates.append(candidate)

        # Sort by interest score
        candidates.sort(key=lambda x: x["interest_score"], reverse=True)

        # Select top candidates with minimum segment requirement
        selected = candidates[: max(self.min_segments, len(candidates))]

        # Sort selected segments by start time
        selected.sort(key=lambda x: x["start"])

        # Add titles and descriptions
        for i, segment in enumerate(selected):
            segment["id"] = i
            segment["title"] = self._generate_title(segment["text"])
            segment["description"] = self._generate_description(segment["text"])

        logger.info(f"Generated {len(selected)} candidate segments")

        return selected

    @staticmethod
    def _generate_title(text: str) -> str:
        """Generate a title from segment text.
        
        Args:
            text: Segment text
            
        Returns:
            Generated title
        """
        # Get first sentence or first 50 chars
        sentences = text.split(".")
        title = sentences[0].strip() if sentences else text

        if len(title) > 60:
            title = title[:57] + "..."

        return title

    @staticmethod
    def _generate_description(text: str) -> str:
        """Generate a description from segment text.
        
        Args:
            text: Segment text
            
        Returns:
            Generated description
        """
        # Use first 150 characters
        desc = text[:150].strip()
        if len(text) > 150:
            desc += "..."
        return desc
