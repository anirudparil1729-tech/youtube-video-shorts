'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { JobSubmission } from '@/types';
import { isValidYouTubeUrl } from '@/lib/utils';
import { Youtube, Zap, TrendingUp, BarChart3 } from 'lucide-react';

const jobTypes = [
  {
    value: 'shorts',
    label: 'YouTube Shorts',
    description: 'Generate 9:16 vertical clips optimized for Shorts',
    icon: Zap,
  },
  {
    value: 'clips',
    label: 'Clips',
    description: 'Create short clips from your video content',
    icon: TrendingUp,
  },
  {
    value: 'analysis',
    label: 'Analysis',
    description: 'Get detailed content analysis and insights',
    icon: BarChart3,
  },
];

const jobSubmissionSchema = z.object({
  youtube_url: z.string()
    .min(1, 'YouTube URL is required')
    .refine(isValidYouTubeUrl, 'Please enter a valid YouTube URL'),
  job_type: z.enum(['shorts', 'clips', 'analysis']),
  priority: z.number().min(0).max(10).default(0),
});

type FormData = z.infer<typeof jobSubmissionSchema>;

interface JobSubmissionFormProps {
  onSubmit: (data: JobSubmission) => Promise<void>;
  isLoading?: boolean;
}

export function JobSubmissionForm({ onSubmit, isLoading = false }: JobSubmissionFormProps) {
  const [selectedJobType, setSelectedJobType] = useState<'shorts' | 'clips' | 'analysis'>('shorts');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<FormData>({
    resolver: zodResolver(jobSubmissionSchema),
    defaultValues: {
      job_type: 'shorts',
      priority: 0,
    },
  });

  const watchedJobType = watch('job_type');

  const handleFormSubmit = async (data: FormData) => {
    const submission: JobSubmission = {
      youtube_url: data.youtube_url,
      job_type: data.job_type,
      priority: data.priority,
    };
    await onSubmit(submission);
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">Submit Video for Processing</CardTitle>
        <CardDescription>
          Enter a YouTube URL and choose your processing type to get started
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {/* YouTube URL Input */}
          <div className="space-y-2">
            <label htmlFor="youtube_url" className="label">
              YouTube URL
            </label>
            <div className="relative">
              <Youtube className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                {...register('youtube_url')}
                id="youtube_url"
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                className="input pl-10"
                disabled={isLoading}
              />
            </div>
            {errors.youtube_url && (
              <p className="text-sm text-error-600">{errors.youtube_url.message}</p>
            )}
          </div>

          {/* Job Type Selection */}
          <div className="space-y-3">
            <label className="label">Processing Type</label>
            <div className="grid gap-3">
              {jobTypes.map((type) => {
                const Icon = type.icon;
                const isSelected = watchedJobType === type.value;
                
                return (
                  <label
                    key={type.value}
                    className={`
                      flex items-start space-x-3 p-4 border rounded-lg cursor-pointer transition-colors
                      ${isSelected 
                        ? 'border-primary-500 bg-primary-50' 
                        : 'border-gray-200 hover:border-gray-300'
                      }
                      ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                  >
                    <input
                      {...register('job_type')}
                      type="radio"
                      value={type.value}
                      className="mt-1"
                      disabled={isLoading}
                      onChange={(e) => {
                        setSelectedJobType(e.target.value as typeof selectedJobType);
                        setValue('job_type', e.target.value as typeof watchedJobType);
                      }}
                    />
                    <Icon className={`h-5 w-5 mt-0.5 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`} />
                    <div className="flex-1">
                      <div className={`font-medium ${isSelected ? 'text-primary-900' : 'text-gray-900'}`}>
                        {type.label}
                      </div>
                      <div className={`text-sm ${isSelected ? 'text-primary-700' : 'text-gray-600'}`}>
                        {type.description}
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
            {errors.job_type && (
              <p className="text-sm text-error-600">{errors.job_type.message}</p>
            )}
          </div>

          {/* Priority Input */}
          <div className="space-y-2">
            <label htmlFor="priority" className="label">
              Priority (0-10)
            </label>
            <input
              {...register('priority', { valueAsNumber: true })}
              id="priority"
              type="number"
              min="0"
              max="10"
              defaultValue="0"
              className="input"
              disabled={isLoading}
            />
            <p className="text-sm text-gray-600">
              Higher numbers get processed faster (default: 0)
            </p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            isLoading={isLoading || isSubmitting}
            disabled={isLoading}
          >
            {isLoading ? 'Submitting...' : 'Start Processing'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
