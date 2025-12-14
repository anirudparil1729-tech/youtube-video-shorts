'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/header';
import { JobCard } from '@/components/ui/job-card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api/client';
import { useJobStore } from '@/store';
import { Job, JobStatus } from '@/types';
import { Plus, Filter, RefreshCw, BarChart3 } from 'lucide-react';

const statusFilters: { value: JobStatus | 'all'; label: string; count?: number }[] = [
  { value: 'all', label: 'All Jobs' },
  { value: 'pending', label: 'Pending' },
  { value: 'queued', label: 'Queued' },
  { value: 'processing', label: 'Processing' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export default function JobsPage() {
  const router = useRouter();
  const { getJobsArray, setCurrentJob, selectedStatusFilter, setStatusFilter } = useJobStore();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch jobs from API (with fallback to local store)
  const { data: jobsResponse, isLoading, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      try {
        return await apiClient.listJobs();
      } catch (error) {
        // Fallback to mock data if API is not available
        const localJobs = getJobsArray();
        return {
          jobs: localJobs,
          total: localJobs.length,
          page: 1,
          per_page: 50,
          pages: 1,
        };
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const jobs = jobsResponse?.jobs || getJobsArray();
  const filteredJobs = selectedStatusFilter === 'all' 
    ? jobs 
    : jobs.filter(job => job.status === selectedStatusFilter);

  const getStatusCounts = () => {
    const counts = jobs.reduce((acc, job) => {
      acc[job.status] = (acc[job.status] || 0) + 1;
      return acc;
    }, {} as Record<JobStatus, number>);
    
    return statusFilters.map(filter => 
      filter.value === 'all' 
        ? { ...filter, count: jobs.length }
        : { ...filter, count: counts[filter.value as JobStatus] || 0 }
    );
  };

  const handleViewDetails = (job: Job) => {
    setCurrentJob(job.id);
    router.push(`/job/${job.id}`);
  };

  const handleRetry = async (jobId: string) => {
    try {
      await apiClient.retryJob(jobId);
      await refetch();
    } catch (error) {
      console.error('Failed to retry job:', error);
      // In mock mode, just update local state
      const job = jobs.find(j => j.id === jobId);
      if (job) {
        job.status = 'queued';
        job.progress = 0;
        job.error_message = undefined;
      }
    }
  };

  const handleCancel = async (jobId: string) => {
    try {
      await apiClient.cancelJob(jobId, 'Cancelled by user');
      await refetch();
    } catch (error) {
      console.error('Failed to cancel job:', error);
      // In mock mode, just update local state
      const job = jobs.find(j => j.id === jobId);
      if (job) {
        job.status = 'cancelled';
        job.progress = 0;
      }
    }
  };

  const handleDownload = (job: Job) => {
    // In a real implementation, this would trigger a download
    console.log('Downloading job:', job.id);
    // For now, create a mock download
    const link = document.createElement('a');
    link.href = '#';
    link.download = `job-${job.id}.zip`;
    link.click();
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Job Dashboard</h1>
            <p className="text-gray-600 mt-2">
              Monitor and manage your video processing jobs
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => router.push('/')}>
              <Plus className="h-4 w-4 mr-2" />
              New Job
            </Button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
          {statusCounts.map((filter) => (
            <Card 
              key={filter.value}
              className={`cursor-pointer transition-colors ${
                selectedStatusFilter === filter.value 
                  ? 'ring-2 ring-primary-500 bg-primary-50' 
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => setStatusFilter(filter.value)}
            >
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {filter.count}
                  </div>
                  <div className="text-sm text-gray-600">
                    {filter.label}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Job Grid */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {selectedStatusFilter === 'all' ? 'All Jobs' : `${selectedStatusFilter.charAt(0).toUpperCase() + selectedStatusFilter.slice(1)} Jobs`}
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({filteredJobs.length})
              </span>
            </h2>
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                {isLoading ? 'Loading...' : 'Showing latest jobs'}
              </span>
            </div>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </CardHeader>
                  <CardContent>
                    <div className="h-32 bg-gray-200 rounded mb-4"></div>
                    <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="text-center py-12">
              <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No jobs found
              </h3>
              <p className="text-gray-600 mb-6">
                {selectedStatusFilter === 'all' 
                  ? "You haven't submitted any jobs yet."
                  : `No jobs with status "${selectedStatusFilter}" found.`
                }
              </p>
              <Button onClick={() => router.push('/')}>
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Job
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onViewDetails={handleViewDetails}
                  onRetry={handleRetry}
                  onCancel={handleCancel}
                  onDownload={handleDownload}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
