'use client';

import { Job } from '@/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { formatRelativeTime, formatDuration, getYouTubeThumbnail, getYouTubeVideoId } from '@/lib/utils';
import { Clock, Play, Download, ExternalLink, AlertCircle } from 'lucide-react';

interface JobCardProps {
  job: Job;
  onViewDetails?: (job: Job) => void;
  onCancel?: (jobId: string) => void;
  onRetry?: (jobId: string) => void;
  onDownload?: (job: Job) => void;
}

export function JobCard({ job, onViewDetails, onCancel, onRetry, onDownload }: JobCardProps) {
  const videoId = getYouTubeVideoId(job.youtube_url);
  const thumbnail = videoId ? getYouTubeThumbnail(videoId, 'medium') : null;
  const isCompleted = job.status === 'completed';
  const isProcessing = job.status === 'processing' || job.status === 'queued' || job.status === 'pending';
  const hasError = job.status === 'failed';
  const canCancel = isProcessing;
  const canRetry = hasError;

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold truncate">
              {job.video_title || 'Video Processing Job'}
            </CardTitle>
            <CardDescription className="mt-1">
              {job.job_type.charAt(0).toUpperCase() + job.job_type.slice(1)} • {formatRelativeTime(job.created_at)}
            </CardDescription>
          </div>
          <Badge status={job.status} size="sm" />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Video Thumbnail */}
        {thumbnail && (
          <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={thumbnail}
              alt="Video thumbnail"
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
              <Play className="h-8 w-8 text-white" />
            </div>
          </div>
        )}

        {/* Progress */}
        {isProcessing && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium">{Math.round(job.progress)}%</span>
            </div>
            <Progress 
              value={job.progress} 
              variant={hasError ? 'error' : isCompleted ? 'success' : 'default'}
              size="sm"
            />
          </div>
        )}

        {/* Error Message */}
        {hasError && job.error_message && (
          <div className="flex items-start space-x-2 p-3 bg-error-50 border border-error-200 rounded-lg">
            <AlertCircle className="h-4 w-4 text-error-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-error-700">{job.error_message}</p>
          </div>
        )}

        {/* Video Info */}
        {job.video_duration && (
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{formatDuration(job.video_duration)}</span>
            </div>
            {job.video_view_count && (
              <div>
                <span>{job.video_view_count.toLocaleString()} views</span>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center space-x-2">
            {onViewDetails && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewDetails(job)}
              >
                View Details
              </Button>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {isCompleted && onDownload && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload(job)}
              >
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
            )}
            
            {canRetry && onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRetry(job.id)}
              >
                Retry
              </Button>
            )}
            
            {canCancel && onCancel && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onCancel(job.id)}
              >
                Cancel
              </Button>
            )}

            <a
              href={job.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
