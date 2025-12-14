'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ClipPreview } from '@/components/ui/clip-preview';
import { apiClient } from '@/lib/api/client';
import { useJobStore } from '@/store';
import { useWebSocket } from '@/hooks/use-websocket';
import { Job } from '@/types';
import { formatRelativeTime, formatDuration, getYouTubeThumbnail, getYouTubeVideoId } from '@/lib/utils';
import { 
  ArrowLeft, 
  Play, 
  Download, 
  Share2, 
  Clock, 
  User, 
  Eye, 
  Calendar,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  RotateCcw,
  X
} from 'lucide-react';

const processingStages = [
  'video_download',
  'audio_extraction', 
  'transcription',
  'content_analysis',
  'clip_generation',
  'face_detection',
  'video_encoding',
  'finalization'
];

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const { getCurrentJob, updateJob } = useJobStore();
  const [isRetrying, setIsRetrying] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  // Fetch job details
  const { data: job, isLoading, refetch } = useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      try {
        return await apiClient.getJob(jobId);
      } catch (error) {
        // Fallback to local store
        const localJob = getCurrentJob();
        if (localJob && localJob.id === jobId) {
          return localJob;
        }
        throw error;
      }
    },
    enabled: !!jobId,
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  });

  // WebSocket connection for real-time updates
  const wsUrl = job ? 
    `${process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http', 'ws')}/api/v1/websocket/${jobId}` :
    null;

  const { isConnected } = useWebSocket(wsUrl || '', {
    onMessage: (message) => {
      if (message.data.job_id === jobId && job) {
        // Update job with WebSocket data
        updateJob(jobId, {
          status: message.data.status || job.status,
          progress: message.data.progress || job.progress,
          ...message.data,
        });
      }
    },
    onOpen: () => {
      console.log('WebSocket connected for job:', jobId);
    },
    onClose: () => {
      console.log('WebSocket disconnected for job:', jobId);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  const handleRetry = async () => {
    if (!job) return;
    
    setIsRetrying(true);
    try {
      const updatedJob = await apiClient.retryJob(jobId);
      updateJob(jobId, updatedJob);
      await refetch();
    } catch (error) {
      // Mock retry for demo purposes
      updateJob(jobId, {
        status: 'queued',
        progress: 0,
        error_message: undefined,
      });
    } finally {
      setIsRetrying(false);
    }
  };

  const handleCancel = async () => {
    if (!job) return;
    
    setIsCancelling(true);
    try {
      await apiClient.cancelJob(jobId, 'Cancelled by user');
      updateJob(jobId, { status: 'cancelled' });
      await refetch();
    } catch (error) {
      // Mock cancel for demo purposes
      updateJob(jobId, { status: 'cancelled' });
    } finally {
      setIsCancelling(false);
    }
  };

  const handleDownload = () => {
    if (!job?.generated_clips) return;
    
    // In a real implementation, this would download the generated clips
    console.log('Downloading clips for job:', jobId);
    // For demo, create a mock download
    const link = document.createElement('a');
    link.href = '#';
    link.download = `job-${jobId}-clips.zip`;
    link.click();
  };

  const getStageProgress = () => {
    if (!job?.progress) return { current: 0, stages: [] };
    
    const currentStage = Math.floor((job.progress / 100) * processingStages.length);
    
    return {
      current: currentStage,
      stages: processingStages.map((stage, index) => ({
        name: stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        completed: index < currentStage,
        current: index === currentStage && job.status === 'processing',
      }))
    };
  };

  const stageProgress = getStageProgress();
  const videoId = job ? getYouTubeVideoId(job.youtube_url) : null;
  const thumbnail = videoId ? getYouTubeThumbnail(videoId, 'high') : null;
  const isCompleted = job?.status === 'completed';
  const isProcessing = job?.status === 'processing' || job?.status === 'queued' || job?.status === 'pending';
  const hasError = job?.status === 'failed';

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded w-full"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Job Not Found</h1>
            <Button onClick={() => router.push('/jobs')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Jobs
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/jobs')}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Jobs
          </Button>
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {job.video_title || 'Video Processing Job'}
              </h1>
              <p className="text-gray-600">
                Job #{job.id} • Created {formatRelativeTime(job.created_at)}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {isConnected && (
                <Badge variant="success" size="sm">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-2 animate-pulse"></div>
                  Live
                </Badge>
              )}
              <Badge status={job.status} />
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Preview */}
            {thumbnail && (
              <Card>
                <CardContent className="p-6">
                  <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden group cursor-pointer">
                    <img
                      src={thumbnail}
                      alt="Video thumbnail"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Play className="h-12 w-12 text-white" />
                    </div>
                    <a
                      href={job.youtube_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="absolute top-4 right-4 bg-black bg-opacity-50 p-2 rounded-full text-white hover:bg-opacity-70"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Progress Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Processing Progress</CardTitle>
                <CardDescription>
                  {isProcessing ? 'Your video is being processed' : 'Processing completed'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isProcessing && (
                  <div className="mb-6">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Overall Progress</span>
                      <span>{Math.round(job.progress)}%</span>
                    </div>
                    <Progress 
                      value={job.progress} 
                      variant={hasError ? 'error' : isCompleted ? 'success' : 'default'}
                      size="lg"
                    />
                  </div>
                )}

                <div className="space-y-3">
                  {stageProgress.stages.map((stage, index) => (
                    <div key={stage.name} className="flex items-center space-x-3">
                      {stage.completed ? (
                        <CheckCircle className="h-5 w-5 text-success-500" />
                      ) : stage.current ? (
                        <div className="h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <div className="h-5 w-5 border-2 border-gray-300 rounded-full"></div>
                      )}
                      <span className={`text-sm ${
                        stage.completed ? 'text-success-700 font-medium' :
                        stage.current ? 'text-primary-700 font-medium' :
                        'text-gray-500'
                      }`}>
                        {stage.name}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Generated Clips */}
            {isCompleted && job.generated_clips && job.generated_clips.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated Clips</CardTitle>
                  <CardDescription>
                    {job.generated_clips.length} clip{job.generated_clips.length !== 1 ? 's' : ''} ready for download
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4">
                    {job.generated_clips.map((clip) => (
                      <ClipPreview 
                        key={clip.id} 
                        clip={clip} 
                        job={job}
                        onPlay={() => console.log('Playing clip:', clip.id)}
                        onDownload={() => console.log('Downloading clip:', clip.id)}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Error Message */}
            {hasError && job.error_message && (
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-error-500 mt-0.5" />
                    <div>
                      <h3 className="font-medium text-error-900 mb-1">Processing Failed</h3>
                      <p className="text-error-700 text-sm">{job.error_message}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Job Details */}
            <Card>
              <CardHeader>
                <CardTitle>Job Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Type</span>
                  <span className="font-medium capitalize">{job.job_type}</span>
                </div>
                
                {job.video_duration && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Duration</span>
                    <span className="font-medium">{formatDuration(job.video_duration)}</span>
                  </div>
                )}
                
                {job.video_uploader && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Uploader</span>
                    <span className="font-medium">{job.video_uploader}</span>
                  </div>
                )}
                
                {job.video_view_count && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Views</span>
                    <span className="font-medium">{job.video_view_count.toLocaleString()}</span>
                  </div>
                )}
                
                {job.processing_time && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Processing Time</span>
                    <span className="font-medium">{formatDuration(job.processing_time)}</span>
                  </div>
                )}

                {job.total_file_size && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Output Size</span>
                    <span className="font-medium">{Math.round(job.total_file_size / (1024 * 1024))} MB</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {isCompleted && (
                  <Button 
                    className="w-full" 
                    onClick={handleDownload}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Clips
                  </Button>
                )}
                
                <Button variant="outline" className="w-full">
                  <Share2 className="h-4 w-4 mr-2" />
                  Share Results
                </Button>

                {hasError && (
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={handleRetry}
                    disabled={isRetrying}
                    isLoading={isRetrying}
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Retry Job
                  </Button>
                )}

                {isProcessing && (
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={handleCancel}
                    disabled={isCancelling}
                    isLoading={isCancelling}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel Job
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Original Video Info */}
            <Card>
              <CardHeader>
                <CardTitle>Original Video</CardTitle>
              </CardHeader>
              <CardContent>
                <a
                  href={job.youtube_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <ExternalLink className="h-4 w-4 text-gray-400" />
                    <div>
                      <div className="font-medium text-sm text-gray-900">
                        {job.video_title || 'Untitled Video'}
                      </div>
                      <div className="text-xs text-gray-600">
                        Open on YouTube
                      </div>
                    </div>
                  </div>
                </a>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
