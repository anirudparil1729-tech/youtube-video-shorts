"""Face detection and tracking for intelligent video cropping."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects and tracks faces in video for intelligent cropping."""

    @staticmethod
    async def detect_faces_in_video(
        video_path: str,
        sample_rate: int = 1,
    ) -> List[Dict[str, Any]]:
        """Detect faces in video frames.
        
        Args:
            video_path: Path to video file
            sample_rate: Sample every Nth frame
            
        Returns:
            List of frame-by-frame face detections
        """
        try:
            import cv2
            import mediapipe as mp

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            mp_face_detection = mp.solutions.face_detection

            detections_list = []
            frame_idx = 0

            with mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            ) as face_detection:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_idx % sample_rate != 0:
                        frame_idx += 1
                        continue

                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(rgb_frame)

                    time_sec = frame_idx / fps

                    if results.detections:
                        faces = []
                        h, w = rgb_frame.shape[:2]

                        for detection in results.detections:
                            bbox = detection.location_data.relative_bounding_box
                            faces.append({
                                "x": bbox.xmin,
                                "y": bbox.ymin,
                                "width": bbox.width,
                                "height": bbox.height,
                                "confidence": detection.score[0],
                            })

                        detections_list.append({
                            "frame": frame_idx,
                            "time": time_sec,
                            "faces": faces,
                        })

                    frame_idx += 1

            cap.release()
            logger.info(f"Detected faces in {len(detections_list)} frames")
            return detections_list

        except ImportError:
            logger.warning("MediaPipe not available, skipping face detection")
            return []

    @staticmethod
    async def get_crop_region(
        detections: List[Dict[str, Any]],
        frame_width: int,
        frame_height: int,
        target_aspect: float = 9 / 16,
    ) -> Dict[str, Any]:
        """Calculate optimal crop region for face tracking.
        
        Args:
            detections: Face detections from video
            frame_width: Video frame width
            frame_height: Video frame height
            target_aspect: Target aspect ratio (width/height)
            
        Returns:
            Crop region (x, y, width, height)
        """
        if not detections:
            # Default center crop for 9:16
            crop_width = frame_height * target_aspect
            if crop_width > frame_width:
                crop_width = frame_width
            crop_height = crop_width / target_aspect

            x = (frame_width - crop_width) / 2
            y = (frame_height - crop_height) / 2

            return {
                "x": int(x),
                "y": int(y),
                "width": int(crop_width),
                "height": int(crop_height),
                "strategy": "center_crop",
            }

        # Calculate average face position across detections
        all_faces = []
        for det in detections:
            all_faces.extend(det["faces"])

        if not all_faces:
            # Fallback to center crop
            return await FaceDetector.get_crop_region(
                [], frame_width, frame_height, target_aspect
            )

        # Average face center and size
        avg_x = sum(f["x"] + f["width"] / 2 for f in all_faces) / len(all_faces)
        avg_y = sum(f["y"] + f["height"] / 2 for f in all_faces) / len(all_faces)
        avg_face_height = sum(f["height"] for f in all_faces) / len(all_faces)

        # Calculate crop box centered on face
        crop_height = frame_height
        crop_width = crop_height * target_aspect

        # If crop too wide, adjust
        if crop_width > frame_width:
            crop_width = frame_width
            crop_height = crop_width / target_aspect

        # Position to keep face centered
        center_x = avg_x * frame_width
        center_y = avg_y * frame_height

        x = center_x - crop_width / 2
        y = center_y - crop_height / 2

        # Clamp to frame boundaries
        x = max(0, min(x, frame_width - crop_width))
        y = max(0, min(y, frame_height - crop_height))

        return {
            "x": int(x),
            "y": int(y),
            "width": int(crop_width),
            "height": int(crop_height),
            "strategy": "face_tracking",
        }
