'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { GeneratedClip, Job } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { formatDuration } from '@/lib/utils';
import { Play, Pause, Download, Clock, TrendingUp, Eye } from 'lucide-react';

// Dynamic import for react-player to avoid SSR issues
const ReactPlayer = dynamic(() => import('react-player'), { ssr: false });

interface ClipPreviewProps {
  clip: GeneratedClip;
  job: Job;
  onPlay?: (clip: GeneratedClip) => void;
  onDownload?: (clip: GeneratedClip) => void;
}

export function ClipPreview({ clip, job, onPlay, onDownload }: ClipPreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handlePlay = () => {
    if (!isPlaying) {
      setIsPlaying(true);
      onPlay?.(clip);
    }
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  const handleDownload = () => {
    // In a real implementation, this would download the actual clip
    console.log('Downloading clip:', clip.id);
    const link = document.createElement('a');
    link.href = clip.file_path || '#';
    link.download = `clip-${clip.id}.mp4`;
    link.click();
    onDownload?.(clip);
  };

  const getVideoUrl = () => {
    // For demo purposes, use the original YouTube URL with start/end times
    // In real implementation, this would be the generated clip URL
    if (clip.file_path) {
      return clip.file_path;
    }
    
    // Fallback to original video with timestamp (for demo)
    const separator = job.youtube_url.includes('?') ? '&' : '?';
    return `${job.youtube_url}${separator}t=${clip.start_time}&end=${clip.end_time}`;
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <div className="relative">
          {/* Video Player */}
          <div className="relative aspect-video bg-gray-900">
            {clip.thumbnail_path ? (
              <img
                src={clip.thumbnail_path}
                alt={`Clip ${clip.id} thumbnail`}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
                <Play className="h-12 w-12 text-white opacity-60" />
              </div>
            )}
            
            {/* Play/Pause Overlay */}
            <div 
              className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-30 transition-all cursor-pointer group"
              onClick={isPlaying ? handlePause : handlePlay}
            >
              <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                {isPlaying ? (
                  <Pause className="h-12 w-12 text-white" />
                ) : (
                  <Play className="h-12 w-12 text-white" />
                )}
              </div>
            </div>

            {/* Duration Badge */}
            <div className="absolute bottom-2 right-2">
              <Badge variant="default" size="sm" className="bg-black bg-opacity-70 text-white">
                {formatDuration(clip.duration)}
              </Badge>
            </div>

            {/* Confidence Score */}
            <div className="absolute top-2 left-2">
              <Badge 
                variant={clip.confidence_score > 0.8 ? 'success' : clip.confidence_score > 0.6 ? 'warning' : 'default'} 
                size="sm"
              >
                <TrendingUp className="h-3 w-3 mr-1" />
                {Math.round(clip.confidence_score * 100)}%
              </Badge>
            </div>
          </div>

          {/* Clip Info */}
          <div className="p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate">
                  Clip {clip.id.slice(-6)}
                </h4>
                <p className="text-sm text-gray-600">
                  {formatDuration(clip.start_time)} - {formatDuration(clip.end_time)}
                </p>
              </div>
            </div>

            {/* Description */}
            {clip.description && (
              <p className="text-sm text-gray-700 line-clamp-2">
                {clip.description}
              </p>
            )}

            {/* Metadata */}
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{formatDuration(clip.duration)}</span>
              </div>
              
              <div className="flex items-center space-x-1">
                <TrendingUp className="h-3 w-3" />
                <span>Score: {Math.round(clip.confidence_score * 100)}%</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2 pt-2">
              <Button
                size="sm"
                onClick={isPlaying ? handlePause : handlePlay}
                disabled={isLoading}
              >
                {isPlaying ? (
                  <>
                    <Pause className="h-3 w-3 mr-1" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-3 w-3 mr-1" />
                    Play
                  </>
                )}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
              >
                <Download className="h-3 w-3 mr-1" />
                Download
              </Button>
            </div>

            {/* Progress Indicator (if processing) */}
            {isLoading && (
              <div className="pt-2">
                <Progress value={33} size="sm" />
                <p className="text-xs text-gray-500 mt-1">Preparing clip...</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
