import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { dashboardApi, JobSummary, DashboardSummary } from '../api/client'
import { useAuth } from '../utils/auth'
import { Clock, CheckCircle, Activity, LogOut, TrendingUp } from 'lucide-react'
import MarkdownRenderer from '../components/MarkdownRenderer'

export default function BankDashboard() {
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const navigate = useNavigate()
  const { logout } = useAuth()

  const { data: summary } = useQuery<DashboardSummary>({
    queryKey: ['tenant-summary'],
    queryFn: () => dashboardApi.getTenantSummary(24),
    refetchInterval: 30000,
  })

  const { data: jobs } = useQuery<{ jobs: JobSummary[] }>({
    queryKey: ['tenant-jobs', statusFilter],
    queryFn: () => dashboardApi.getTenantJobs(20, statusFilter || undefined),
    refetchInterval: 10000,
  })

  const { data: jobDetail } = useQuery({
    queryKey: ['tenant-job-detail', selectedJob],
    queryFn: () => dashboardApi.getTenantJobDetail(selectedJob!),
    enabled: !!selectedJob,
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const successRate = summary
    ? summary.total_jobs > 0
      ? ((summary.succeeded_jobs / summary.total_jobs) * 100).toFixed(1)
      : '0.0'
    : '0.0'

  return (
    <div style={{ minHeight: '100vh', background: '#f7fafc' }}>
      {/* Header */}
      <div style={{
        background: 'white',
        borderBottom: '1px solid #e2e8f0',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1a202c' }}>
          Bank Dashboard
        </h1>
        <button
          onClick={handleLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            background: '#e53e3e',
            color: 'white',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: '500'
          }}
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>

      <div style={{ padding: '2rem' }}>
        {/* Metrics Summary */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem'
        }}>
          <MetricCard
            icon={<Activity size={24} />}
            label="Total Jobs (24h)"
            value={summary?.total_jobs.toString() || '0'}
            color="#667eea"
          />
          <MetricCard
            icon={<CheckCircle size={24} />}
            label="Success Rate"
            value={`${successRate}%`}
            color="#48bb78"
          />
          <MetricCard
            icon={<Clock size={24} />}
            label="Avg Processing Time"
            value={
              summary?.average_processing_seconds
                ? `${summary.average_processing_seconds.toFixed(2)}s`
                : 'N/A'
            }
            color="#ed8936"
          />
          <MetricCard
            icon={<TrendingUp size={24} />}
            label="Succeeded Jobs"
            value={summary?.succeeded_jobs.toString() || '0'}
            color="#38b2ac"
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: selectedJob ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
          {/* Jobs List */}
          <div style={{
            background: 'white',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '1.5rem',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1a202c' }}>
                Recent Jobs
              </h2>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: '0.5rem',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  color: '#4a5568'
                }}
              >
                <option value="">All Status</option>
                <option value="succeeded">Succeeded</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {jobs?.jobs.map((job) => (
                <div
                  key={job.job_id}
                  onClick={() => setSelectedJob(job.job_id)}
                  style={{
                    padding: '1rem 1.5rem',
                    borderBottom: '1px solid #f7fafc',
                    cursor: 'pointer',
                    background: selectedJob === job.job_id ? '#edf2f7' : 'white',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (selectedJob !== job.job_id) {
                      e.currentTarget.style.background = '#f7fafc'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedJob !== job.job_id) {
                      e.currentTarget.style.background = 'white'
                    }
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#2d3748' }}>
                      {job.client_job_id}
                    </span>
                    <StatusBadge status={job.status} />
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#718096' }}>
                    <span>Decision: {job.decision || 'N/A'}</span>
                    {job.risk_score !== null && <span>Risk: {job.risk_score.toFixed(2)}</span>}
                    {job.processing_seconds !== null && (
                      <span>{job.processing_seconds.toFixed(2)}s</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#a0aec0', marginTop: '0.25rem' }}>
                    {new Date(job.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
              {jobs?.jobs.length === 0 && (
                <div style={{ padding: '3rem', textAlign: 'center', color: '#a0aec0' }}>
                  No jobs found
                </div>
              )}
            </div>
          </div>

          {/* Job Detail */}
          {selectedJob && jobDetail && (
            <div style={{
              background: 'white',
              borderRadius: '0.5rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              overflow: 'hidden'
            }}>
              <div style={{
                padding: '1.5rem',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1a202c' }}>
                  Job Details
                </h2>
                <button
                  onClick={() => setSelectedJob(null)}
                  style={{
                    padding: '0.25rem 0.75rem',
                    background: '#edf2f7',
                    border: 'none',
                    borderRadius: '0.25rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    color: '#4a5568'
                  }}
                >
                  Close
                </button>
              </div>

              <div style={{ padding: '1.5rem', maxHeight: '600px', overflowY: 'auto' }}>
                {/* Summary */}
                <Section title="Summary">
                  <DetailRow label="Job ID" value={jobDetail.summary.job_id} />
                  <DetailRow label="Client Job ID" value={jobDetail.summary.client_job_id} />
                  <DetailRow label="Status" value={jobDetail.summary.status} />
                  <DetailRow label="Decision" value={jobDetail.summary.decision || 'N/A'} />
                  {jobDetail.summary.risk_score !== null && (
                    <DetailRow label="Risk Score" value={jobDetail.summary.risk_score.toFixed(3)} />
                  )}
                  {jobDetail.summary.processing_seconds !== null && (
                    <DetailRow
                      label="Processing Time"
                      value={`${jobDetail.summary.processing_seconds.toFixed(2)}s`}
                    />
                  )}
                  <DetailRow label="Created" value={new Date(jobDetail.summary.created_at).toLocaleString()} />
                </Section>

                {/* Raw Input */}
                {jobDetail.raw_input && (
                  <Section title="Raw Input">
                    <pre style={{
                      background: '#f7fafc',
                      padding: '1rem',
                      borderRadius: '0.375rem',
                      fontSize: '0.75rem',
                      overflow: 'auto',
                      color: '#2d3748'
                    }}>
                      {JSON.stringify(jobDetail.raw_input, null, 2)}
                    </pre>
                  </Section>
                )}

                {/* LLM Output */}
                {jobDetail.llm_output_markdown && (
                  <Section title="LLM Output">
                    <div
                      style={{
                        background: '#f7fafc',
                        padding: '1rem',
                        borderRadius: '0.375rem',
                        border: '1px solid #e2e8f0',
                      }}
                    >
                      <MarkdownRenderer markdown={jobDetail.llm_output_markdown} />
                    </div>
                  </Section>
                )}

                {/* LLM Metadata */}
                {jobDetail.llm_output_metadata && (
                  <Section title="Output Metadata">
                    <pre style={{
                      background: '#f7fafc',
                      padding: '1rem',
                      borderRadius: '0.375rem',
                      fontSize: '0.75rem',
                      overflow: 'auto',
                      color: '#2d3748'
                    }}>
                      {JSON.stringify(jobDetail.llm_output_metadata, null, 2)}
                    </pre>
                  </Section>
                )}

                {/* Audit Trail */}
                {jobDetail.audits.length > 0 && (
                  <Section title="Audit Trail">
                    {jobDetail.audits.map((audit) => (
                      <div
                        key={audit.id}
                        style={{
                          padding: '0.75rem',
                          background: '#f7fafc',
                          borderRadius: '0.375rem',
                          marginBottom: '0.5rem',
                          fontSize: '0.875rem'
                        }}
                      >
                        <div style={{ fontWeight: '600', color: '#2d3748' }}>{audit.action}</div>
                        <div style={{ color: '#718096', fontSize: '0.75rem' }}>
                          by {audit.actor} at {new Date(audit.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </Section>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div style={{
      background: 'white',
      padding: '1.5rem',
      borderRadius: '0.5rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      display: 'flex',
      alignItems: 'center',
      gap: '1rem'
    }}>
      <div style={{
        padding: '0.75rem',
        borderRadius: '0.5rem',
        background: `${color}15`,
        color: color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '0.875rem', color: '#718096', marginBottom: '0.25rem' }}>
          {label}
        </div>
        <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1a202c' }}>
          {value}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    succeeded: { bg: '#c6f6d5', text: '#22543d' },
    failed: { bg: '#fed7d7', text: '#742a2a' },
    pending: { bg: '#feebc8', text: '#7c2d12' },
  }
  const color = colors[status as keyof typeof colors] || { bg: '#e2e8f0', text: '#2d3748' }

  return (
    <span style={{
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: '600',
      background: color.bg,
      color: color.text
    }}>
      {status}
    </span>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: '600', color: '#2d3748', marginBottom: '0.75rem' }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', fontSize: '0.875rem' }}>
      <span style={{ color: '#718096' }}>{label}:</span>
      <span style={{ color: '#2d3748', fontWeight: '500' }}>{value}</span>
    </div>
  )
}
