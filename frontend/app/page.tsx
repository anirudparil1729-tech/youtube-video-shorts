'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { JobSubmissionForm } from '@/components/forms/job-submission-form';
import { JobSubmission, Job } from '@/types';
import { apiClient } from '@/lib/api/client';
import { useJobStore } from '@/store';
import { Youtube, Zap, Clock, TrendingUp } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const { addJob, setCurrentJob, setSubmitting, setSubmitError, isSubmitting } = useJobStore();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleJobSubmit = async (submission: JobSubmission) => {
    try {
      setSubmitError(null);
      setSubmitting(true);
      setSuccessMessage(null);

      // Add optimistic job to store
      const optimisticJob: Job = {
        id: `temp-${Date.now()}`,
        youtube_url: submission.youtube_url,
        job_type: submission.job_type,
        status: 'pending',
        progress: 0,
        priority: submission.priority || 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        retry_count: 0,
      };

      addJob(optimisticJob);

      // Submit to API (this will fail in mock environment but that's OK for now)
      try {
        const createdJob = await apiClient.createJob(submission);
        addJob(createdJob);
        setCurrentJob(createdJob.id);
        setSuccessMessage('Job submitted successfully!');
        
        // Redirect to job detail page
        setTimeout(() => {
          router.push(`/job/${createdJob.id}`);
        }, 1000);
      } catch (error) {
        // In mock environment, simulate successful submission
        const mockJob: Job = {
          id: `job-${Date.now()}`,
          youtube_url: submission.youtube_url,
          job_type: submission.job_type,
          status: 'queued',
          progress: 0,
          priority: submission.priority || 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          retry_count: 0,
          video_title: 'Sample Video Title',
          video_duration: 300,
          video_thumbnail: `https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg`,
        };
        
        addJob(mockJob);
        setCurrentJob(mockJob.id);
        setSuccessMessage('Job submitted successfully! (Mock mode)');
        
        setTimeout(() => {
          router.push(`/job/${mockJob.id}`);
        }, 1000);
      }
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Failed to submit job');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <Youtube className="mx-auto h-16 w-16 mb-8 text-primary-200" />
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              AI-Powered Video Processing
            </h1>
            <p className="text-xl md:text-2xl text-primary-100 mb-8 max-w-3xl mx-auto">
              Transform your YouTube videos into engaging Shorts, clips, and insights with our AI-powered processing platform
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              What We Offer
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Choose from three powerful processing types to get the most out of your video content
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <Zap className="h-8 w-8 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">YouTube Shorts</h3>
              <p className="text-gray-600">
                Automatically generate 9:16 vertical clips optimized for YouTube Shorts platform
              </p>
            </div>

            <div className="text-center">
              <div className="bg-success-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="h-8 w-8 text-success-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Content Clips</h3>
              <p className="text-gray-600">
                Extract the most engaging moments and create highlight reels from your videos
              </p>
            </div>

            <div className="text-center">
              <div className="bg-warning-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <Clock className="h-8 w-8 text-warning-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Content Analysis</h3>
              <p className="text-gray-600">
                Get detailed insights, sentiment analysis, and content recommendations
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Form Section */}
      <section className="py-24 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Get Started Today
            </h2>
            <p className="text-xl text-gray-600">
              Submit your YouTube video URL and start processing in minutes
            </p>
          </div>

          {successMessage && (
            <div className="mb-6 p-4 bg-success-50 border border-success-200 rounded-lg">
              <p className="text-success-800 font-medium">{successMessage}</p>
            </div>
          )}

          <div className="flex justify-center">
            <JobSubmissionForm 
              onSubmit={handleJobSubmit} 
              isLoading={isSubmitting}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Youtube className="h-6 w-6" />
            <span className="text-lg font-semibold">VideoProcessor</span>
          </div>
          <p className="text-gray-400">
            AI-powered video processing for content creators and marketers
          </p>
        </div>
      </footer>
    </div>
  );
}
