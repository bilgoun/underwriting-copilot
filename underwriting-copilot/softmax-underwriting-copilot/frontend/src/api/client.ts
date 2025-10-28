import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient

export interface DashboardSummary {
  total_jobs: number
  succeeded_jobs: number
  failed_jobs: number
  average_processing_seconds: number | null
}

export interface JobSummary {
  job_id: string
  tenant_id: string
  client_job_id: string
  status: string
  decision: string | null
  risk_score: number | null
  created_at: string
  updated_at: string
  processing_seconds: number | null
}

export interface JobDetail {
  summary: JobSummary
  raw_input: any | null
  llm_input: any | null
  llm_output_markdown: string | null
  llm_output_metadata: any | null
  audits: Array<{
    id: string
    actor: string
    action: string
    created_at: string
  }>
}

export interface TenantOverview {
  tenant_id: string
  name: string
  total_jobs_24h: number
  failure_rate_24h: number
}

export interface ChatMessagePayload {
  role: 'user' | 'assistant'
  content: string
}

export const dashboardApi = {
  // Bank endpoints
  async getTenantJobs(limit = 20, status?: string) {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (status) params.append('status', status)
    const { data } = await apiClient.get(`/dashboard/tenant/jobs?${params}`)
    return data
  },

  async getTenantJobDetail(jobId: string): Promise<JobDetail> {
    const { data } = await apiClient.get(`/dashboard/tenant/jobs/${jobId}`)
    return data
  },

  async getTenantSummary(lookbackHours = 24) {
    const { data } = await apiClient.get(`/dashboard/tenant/summary?lookback_hours=${lookbackHours}`)
    return data
  },

  // Admin endpoints
  async getAdminTenants(lookbackHours = 24): Promise<{ tenants: TenantOverview[] }> {
    const { data } = await apiClient.get(`/dashboard/admin/tenants?lookback_hours=${lookbackHours}`)
    return data
  },

  async getAdminJobs(limit = 50, tenantId?: string) {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (tenantId) params.append('tenant_id', tenantId)
    const { data } = await apiClient.get(`/dashboard/admin/jobs?${params}`)
    return data
  },

  async getAdminJobDetail(jobId: string): Promise<JobDetail> {
    const { data } = await apiClient.get(`/dashboard/admin/jobs/${jobId}`)
    return data
  },

  // Auth
  async login(clientId: string, clientSecret: string, scope: string) {
    // OAuth endpoint is at /oauth/token, not /v1/oauth/token
    const { data } = await axios.post('/oauth/token', {
      grant_type: 'client_credentials',
      client_id: clientId,
      client_secret: clientSecret,
      scope,
    })
    return data
  },
}

export const chatApi = {
  async sendLoanAssistant(messages: ChatMessagePayload[]): Promise<{ reply: string }> {
    const { data } = await apiClient.post('/chat/loan-assistant', { messages })
    return data
  },
}
