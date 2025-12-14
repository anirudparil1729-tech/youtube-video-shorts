export interface Job {
  id: string;
  youtube_url: string;
  job_type: 'shorts' | 'clips' | 'analysis';
  status: JobStatus;
  progress: number;
  priority: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  worker_id?: string;
  
  // Video information
  video_title?: string;
  video_duration?: number;
  video_description?: string;
  video_uploader?: string;
  video_view_count?: number;
  video_thumbnail?: string;
  
  // Processing results
  audio_file_path?: string;
  transcript?: string;
  transcript_segments?: TranscriptSegment[];
  analysis_results?: AnalysisResults;
  generated_clips?: GeneratedClip[];
  output_files?: string[];
  total_file_size?: number;
  processing_time?: number;
  retry_count: number;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  confidence: number;
}

export interface AnalysisResults {
  sentiment?: string;
  topics?: string[];
  keywords?: string[];
  interests?: { [key: string]: number };
}

export interface GeneratedClip {
  id: string;
  start_time: number;
  end_time: number;
  duration: number;
  confidence_score: number;
  file_path?: string;
  thumbnail_path?: string;
  description?: string;
}

export type JobStatus = 
  | 'pending'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface JobSubmission {
  youtube_url: string;
  job_type: 'shorts' | 'clips' | 'analysis';
  priority?: number;
  options?: Record<string, any>;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface QueueStatusResponse {
  is_running: boolean;
  total_jobs: number;
  pending_jobs: number;
  processing_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  active_workers: number;
  queue_size: number;
  estimated_wait_time?: number;
}

export interface WebSocketMessage {
  type: string;
  data: {
    job_id: string;
    status?: JobStatus;
    progress?: number;
    message?: string;
    timestamp: string;
    [key: string]: any;
  };
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}
