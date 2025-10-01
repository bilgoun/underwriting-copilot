import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { dashboardApi, JobSummary, TenantOverview } from '../api/client'
import { useAuth } from '../utils/auth'
import { Activity, LogOut, Users, AlertTriangle } from 'lucide-react'
import MarkdownRenderer from '../components/MarkdownRenderer'

export default function AdminDashboard() {
  const [selectedTenant, setSelectedTenant] = useState<string>('')
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const navigate = useNavigate()
  const { logout } = useAuth()

  const { data: tenants } = useQuery<{ tenants: TenantOverview[] }>({
    queryKey: ['admin-tenants'],
    queryFn: () => dashboardApi.getAdminTenants(24),
    refetchInterval: 30000,
  })

  const { data: jobs } = useQuery<{ jobs: JobSummary[] }>({
    queryKey: ['admin-jobs', selectedTenant],
    queryFn: () => dashboardApi.getAdminJobs(50, selectedTenant || undefined),
    refetchInterval: 10000,
  })

  const { data: jobDetail } = useQuery({
    queryKey: ['admin-job-detail', selectedJob],
    queryFn: () => dashboardApi.getAdminJobDetail(selectedJob!),
    enabled: !!selectedJob,
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const totalJobs = tenants?.tenants.reduce((sum, t) => sum + t.total_jobs_24h, 0) || 0
  const avgFailureRate = tenants?.tenants.length
    ? (tenants.tenants.reduce((sum, t) => sum + t.failure_rate_24h, 0) / tenants.tenants.length).toFixed(1)
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
          Admin Dashboard
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
        {/* Global Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem'
        }}>
          <MetricCard
            icon={<Users size={24} />}
            label="Active Tenants"
            value={tenants?.tenants.length.toString() || '0'}
            color="#667eea"
          />
          <MetricCard
            icon={<Activity size={24} />}
            label="Total Jobs (24h)"
            value={totalJobs.toString()}
            color="#48bb78"
          />
          <MetricCard
            icon={<AlertTriangle size={24} />}
            label="Avg Failure Rate"
            value={`${avgFailureRate}%`}
            color="#ed8936"
          />
        </div>

        {/* Tenant Overview */}
        <div style={{
          background: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          marginBottom: '1.5rem',
          overflow: 'hidden'
        }}>
          <div style={{
            padding: '1.5rem',
            borderBottom: '1px solid #e2e8f0',
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1a202c' }}>
              Tenant Overview
            </h2>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f7fafc' }}>
                  <th style={tableHeaderStyle}>Tenant ID</th>
                  <th style={tableHeaderStyle}>Name</th>
                  <th style={tableHeaderStyle}>Jobs (24h)</th>
                  <th style={tableHeaderStyle}>Failure Rate</th>
                  <th style={tableHeaderStyle}>Action</th>
                </tr>
              </thead>
              <tbody>
                {tenants?.tenants.map((tenant) => (
                  <tr
                    key={tenant.tenant_id}
                    style={{
                      borderBottom: '1px solid #f7fafc',
                      background: selectedTenant === tenant.tenant_id ? '#edf2f7' : 'white'
                    }}
                  >
                    <td style={tableCellStyle}>{tenant.tenant_id}</td>
                    <td style={tableCellStyle}>{tenant.name}</td>
                    <td style={tableCellStyle}>{tenant.total_jobs_24h}</td>
                    <td style={tableCellStyle}>
                      <span style={{
                        color: tenant.failure_rate_24h > 10 ? '#c53030' : tenant.failure_rate_24h > 5 ? '#ed8936' : '#38a169'
                      }}>
                        {tenant.failure_rate_24h.toFixed(1)}%
                      </span>
                    </td>
                    <td style={tableCellStyle}>
                      <button
                        onClick={() => setSelectedTenant(tenant.tenant_id === selectedTenant ? '' : tenant.tenant_id)}
                        style={{
                          padding: '0.25rem 0.75rem',
                          background: selectedTenant === tenant.tenant_id ? '#667eea' : '#edf2f7',
                          color: selectedTenant === tenant.tenant_id ? 'white' : '#4a5568',
                          border: 'none',
                          borderRadius: '0.25rem',
                          cursor: 'pointer',
                          fontSize: '0.875rem',
                          fontWeight: '500'
                        }}
                      >
                        {selectedTenant === tenant.tenant_id ? 'Clear' : 'View Jobs'}
                      </button>
                    </td>
                  </tr>
                ))}
                {tenants?.tenants.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ ...tableCellStyle, textAlign: 'center', color: '#a0aec0', padding: '3rem' }}>
                      No tenants found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
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
            }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1a202c' }}>
                {selectedTenant ? `Jobs for ${tenants?.tenants.find(t => t.tenant_id === selectedTenant)?.name || 'Selected Tenant'}` : 'All Jobs'}
              </h2>
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
                    <div>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#2d3748', display: 'block' }}>
                        {job.client_job_id}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#a0aec0' }}>
                        Tenant: {job.tenant_id}
                      </span>
                    </div>
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
                  {selectedTenant ? 'No jobs found for selected tenant' : 'No jobs found'}
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
                  <DetailRow label="Tenant ID" value={jobDetail.summary.tenant_id} />
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
                  <Section title="Raw Input (Bank Submitted Data)">
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

                {/* LLM Input */}
                {jobDetail.llm_input && (
                  <Section title="LLM Input (Processed Features)">
                    <pre style={{
                      background: '#fff5f5',
                      padding: '1rem',
                      borderRadius: '0.375rem',
                      fontSize: '0.75rem',
                      overflow: 'auto',
                      color: '#2d3748',
                      border: '1px solid #feb2b2'
                    }}>
                      {JSON.stringify(jobDetail.llm_input, null, 2)}
                    </pre>
                  </Section>
                )}

                {/* LLM Output */}
                {jobDetail.llm_output_markdown && (
                  <Section title="LLM Output (Credit Memo)">
                    <div
                      style={{
                        background: '#f0fff4',
                        padding: '1rem',
                        borderRadius: '0.375rem',
                        border: '1px solid #9ae6b4',
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

const tableHeaderStyle: React.CSSProperties = {
  padding: '0.75rem 1.5rem',
  textAlign: 'left',
  fontSize: '0.75rem',
  fontWeight: '600',
  color: '#718096',
  textTransform: 'uppercase',
  letterSpacing: '0.05em'
}

const tableCellStyle: React.CSSProperties = {
  padding: '1rem 1.5rem',
  fontSize: '0.875rem',
  color: '#2d3748'
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
