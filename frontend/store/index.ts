import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Job, JobStatus } from '@/types';

interface JobStore {
  // State
  jobs: Record<string, Job>;
  currentJobId: string | null;
  isSubmitting: boolean;
  submitError: string | null;
  selectedStatusFilter: JobStatus | 'all';
  
  // Actions
  addJob: (job: Job) => void;
  updateJob: (jobId: string, updates: Partial<Job>) => void;
  removeJob: (jobId: string) => void;
  setCurrentJob: (jobId: string | null) => void;
  setSubmitting: (isSubmitting: boolean) => void;
  setSubmitError: (error: string | null) => void;
  setStatusFilter: (status: JobStatus | 'all') => void;
  clearJobs: () => void;
  
  // Computed
  getJobsArray: () => Job[];
  getJobsByStatus: (status: JobStatus) => Job[];
  getCurrentJob: () => Job | null;
}

export const useJobStore = create<JobStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        jobs: {},
        currentJobId: null,
        isSubmitting: false,
        submitError: null,
        selectedStatusFilter: 'all',

        // Actions
        addJob: (job) => {
          set((state) => ({
            jobs: {
              ...state.jobs,
              [job.id]: job,
            },
          }), false, 'addJob');
        },

        updateJob: (jobId, updates) => {
          set((state) => {
            if (!state.jobs[jobId]) return state;
            
            return {
              jobs: {
                ...state.jobs,
                [jobId]: {
                  ...state.jobs[jobId],
                  ...updates,
                },
              },
            };
          }, false, 'updateJob');
        },

        removeJob: (jobId) => {
          set((state) => {
            const { [jobId]: removed, ...remainingJobs } = state.jobs;
            return {
              jobs: remainingJobs,
              currentJobId: state.currentJobId === jobId ? null : state.currentJobId,
            };
          }, false, 'removeJob');
        },

        setCurrentJob: (jobId) => {
          set({ currentJobId: jobId }, false, 'setCurrentJob');
        },

        setSubmitting: (isSubmitting) => {
          set({ isSubmitting }, false, 'setSubmitting');
        },

        setSubmitError: (submitError) => {
          set({ submitError }, false, 'setSubmitError');
        },

        setStatusFilter: (selectedStatusFilter) => {
          set({ selectedStatusFilter }, false, 'setStatusFilter');
        },

        clearJobs: () => {
          set({
            jobs: {},
            currentJobId: null,
            isSubmitting: false,
            submitError: null,
          }, false, 'clearJobs');
        },

        // Computed
        getJobsArray: () => {
          return Object.values(get().jobs).sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
        },

        getJobsByStatus: (status) => {
          return Object.values(get().jobs)
            .filter(job => job.status === status)
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        },

        getCurrentJob: () => {
          const { currentJobId, jobs } = get();
          return currentJobId ? jobs[currentJobId] || null : null;
        },
      }),
      {
        name: 'job-store',
        partialize: (state) => ({
          jobs: state.jobs,
          currentJobId: state.currentJobId,
          selectedStatusFilter: state.selectedStatusFilter,
        }),
      }
    ),
    { name: 'job-store' }
  )
);
