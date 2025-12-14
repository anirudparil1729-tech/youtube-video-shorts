import { 
  Job, 
  JobSubmission, 
  JobListResponse, 
  QueueStatusResponse, 
  ApiError,
  WebSocketMessage 
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiErrorResponse extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiErrorResponse';
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorData: ApiError;
      
      try {
        errorData = await response.json();
      } catch {
        errorData = {
          error: 'Request failed',
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date().toISOString(),
        };
      }

      throw new ApiErrorResponse(errorData.message || errorData.error, response.status, errorData.details);
    }

    return response.json();
  }

  async createJob(jobData: JobSubmission): Promise<Job> {
    return this.request<Job>('/api/v1/jobs/', {
      method: 'POST',
      body: JSON.stringify(jobData),
    });
  }

  async getJob(jobId: string): Promise<Job> {
    return this.request<Job>(`/api/v1/jobs/${jobId}`);
  }

  async listJobs(options: {
    status_filter?: string;
    job_type?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<JobListResponse> {
    const params = new URLSearchParams();
    
    if (options.status_filter) params.append('status_filter', options.status_filter);
    if (options.job_type) params.append('job_type', options.job_type);
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());

    const queryString = params.toString();
    return this.request<JobListResponse>(`/api/v1/jobs${queryString ? `?${queryString}` : ''}`);
  }

  async cancelJob(jobId: string, reason?: string): Promise<{ message: string; reason: string }> {
    return this.request<{ message: string; reason: string }>(`/api/v1/jobs/${jobId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async retryJob(jobId: string, force?: boolean): Promise<Job> {
    return this.request<Job>(`/api/v1/jobs/${jobId}/retry`, {
      method: 'POST',
      body: JSON.stringify({ force }),
    });
  }

  async getQueueStatus(): Promise<QueueStatusResponse> {
    return this.request<QueueStatusResponse>('/api/v1/jobs/queue/status');
  }

  async clearQueue(): Promise<void> {
    await this.request('/api/v1/jobs/queue/clear', {
      method: 'DELETE',
    });
  }

  async getJobStatistics(): Promise<{
    total_jobs: number;
    by_status: Record<string, number>;
    queue_running: boolean;
    active_workers: number;
  }> {
    return this.request('/api/v1/jobs/statistics');
  }

  createWebSocketConnection(jobId: string): WebSocket {
    const wsUrl = this.baseUrl
      .replace('http', 'ws')
      .replace('https', 'wss');
    
    return new WebSocket(`${wsUrl}/api/v1/websocket/${jobId}`);
  }

  createHealthWebSocket(): WebSocket {
    const wsUrl = this.baseUrl
      .replace('http', 'ws')
      .replace('https', 'wss');
    
    return new WebSocket(`${wsUrl}/api/v1/websocket/health`);
  }
}

export const apiClient = new ApiClient();
export { ApiErrorResponse };
