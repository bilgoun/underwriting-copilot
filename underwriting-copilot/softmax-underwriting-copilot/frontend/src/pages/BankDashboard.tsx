import { useState, type CSSProperties, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { dashboardApi, JobSummary, DashboardSummary } from '../api/client'
import { useAuth } from '../utils/auth'
import { Clock, CheckCircle, Activity, LogOut, TrendingUp } from 'lucide-react'
import MarkdownRenderer from '../components/MarkdownRenderer'

const accentBlue = '#0a84ff'
const backgroundGradient = 'linear-gradient(135deg, #eef2ff 0%, #f9fbff 45%, #f5f7ff 100%)'

const glassSurface: CSSProperties = {
  background: 'rgba(255, 255, 255, 0.78)',
  borderRadius: '28px',
  border: '1px solid rgba(255, 255, 255, 0.45)',
  boxShadow: '0 30px 60px rgba(15, 23, 42, 0.12)',
  backdropFilter: 'blur(22px)',
}

const pageStyle: CSSProperties = {
  minHeight: '100vh',
  background: backgroundGradient,
  padding: '3rem 0 3.5rem',
}

const shellStyle: CSSProperties = {
  maxWidth: '1200px',
  margin: '0 auto',
  padding: '0 2.5rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '2rem',
}

const headerStyle: CSSProperties = {
  ...glassSurface,
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '2rem',
  padding: '1.9rem 2.35rem',
  flexWrap: 'wrap',
}

const infoTagStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.4rem',
  padding: '0.35rem 0.9rem',
  borderRadius: '9999px',
  background: hexToRgba(accentBlue, 0.12),
  border: `1px solid ${hexToRgba(accentBlue, 0.25)}`,
  color: accentBlue,
  fontSize: '0.75rem',
  fontWeight: 600,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
}

const headerTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '2.4rem',
  fontWeight: 700,
  letterSpacing: '-0.03em',
  color: '#0b1120',
}

const headerSubtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1rem',
  lineHeight: 1.6,
  color: 'rgba(11, 17, 32, 0.62)',
  maxWidth: '28rem',
}

const logoutButtonStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.6rem',
  padding: '0.65rem 1.45rem',
  borderRadius: '9999px',
  background: `linear-gradient(135deg, ${hexToRgba(accentBlue, 0.1)}, ${hexToRgba(accentBlue, 0.22)})`,
  border: `1px solid ${hexToRgba(accentBlue, 0.35)}`,
  color: accentBlue,
  fontSize: '0.9rem',
  fontWeight: 600,
  cursor: 'pointer',
  boxShadow: `0 14px 28px ${hexToRgba(accentBlue, 0.22)}`,
  transition: 'transform 0.2s ease, box-shadow 0.3s ease',
}

const metricsGridStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
  gap: '1.75rem',
}

const sectionHeadingStyle: CSSProperties = {
  margin: 0,
  fontSize: '1.4rem',
  fontWeight: 600,
  color: '#101828',
  letterSpacing: '-0.01em',
}

const sectionSubtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.95rem',
  lineHeight: 1.5,
  color: '#6d7289',
}

const filterGroupStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
  flexWrap: 'wrap',
}

const filterLabelStyle: CSSProperties = {
  fontSize: '0.85rem',
  fontWeight: 600,
  color: '#6d7289',
}

const filterSelectStyle: CSSProperties = {
  padding: '0.5rem 1rem',
  borderRadius: '14px',
  border: `1px solid ${hexToRgba(accentBlue, 0.25)}`,
  background: 'rgba(255, 255, 255, 0.75)',
  color: '#111b2e',
  fontSize: '0.85rem',
  fontWeight: 600,
  cursor: 'pointer',
  boxShadow: '0 12px 22px rgba(15, 23, 42, 0.08)',
  WebkitAppearance: 'none',
  appearance: 'none',
}

const emptyStateStyle: CSSProperties = {
  fontSize: '0.95rem',
  color: '#8a93ab',
  textAlign: 'center',
}

const jobColumnsBaseStyle: CSSProperties = {
  display: 'grid',
  gap: '1.75rem',
  alignItems: 'stretch',
  minHeight: 0,
}

const jobListHeaderStyle: CSSProperties = {
  padding: '1.8rem 2.25rem 1.2rem',
  borderBottom: '1px solid rgba(15, 23, 42, 0.06)',
}

const jobsScrollAreaStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
  padding: '1.5rem 2.25rem 2rem',
  maxHeight: '620px',
  overflowY: 'auto',
  minHeight: 0,
  WebkitOverflowScrolling: 'touch',
}

const jobCardBaseStyle: CSSProperties = {
  borderRadius: '20px',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  background: 'rgba(255, 255, 255, 0.72)',
  boxShadow: '0 18px 36px rgba(15, 23, 42, 0.1)',
  padding: '1.2rem 1.5rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
  cursor: 'pointer',
  transition: 'transform 0.2s ease, box-shadow 0.3s ease, background 0.3s ease',
}

const jobCardSelectedStyle: CSSProperties = {
  background: 'rgba(10, 132, 255, 0.16)',
  border: `1px solid ${hexToRgba(accentBlue, 0.35)}`,
  boxShadow: `0 24px 40px ${hexToRgba(accentBlue, 0.25)}`,
  transform: 'translateY(-4px)',
}

const jobTitleStyle: CSSProperties = {
  fontSize: '1.05rem',
  fontWeight: 700,
  letterSpacing: '-0.01em',
  color: '#0f172a',
}

const jobSubtitleStyle: CSSProperties = {
  fontSize: '0.85rem',
  color: '#6d7289',
}

const jobMetaStyle: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '0.85rem',
  fontSize: '0.82rem',
  color: '#4d576a',
}

const jobTimestampStyle: CSSProperties = {
  fontSize: '0.78rem',
  color: '#94a0b8',
}

const closeButtonStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '0.45rem 0.9rem',
  borderRadius: '9999px',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  background: 'rgba(15, 23, 42, 0.05)',
  color: '#4a5565',
  fontSize: '0.85rem',
  fontWeight: 600,
  cursor: 'pointer',
}

const codeBlockStyle: CSSProperties = {
  padding: '1.25rem',
  borderRadius: '18px',
  background: 'rgba(15, 23, 42, 0.05)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  fontSize: '0.8rem',
  overflow: 'auto',
  color: '#1b2337',
  fontFamily: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
}

const accentCodeBlockStyle: CSSProperties = {
  ...codeBlockStyle,
  background: 'linear-gradient(135deg, rgba(255, 159, 10, 0.16), rgba(255, 204, 64, 0.18))',
  border: '1px solid rgba(255, 159, 10, 0.28)',
}

const llmOutputShellStyle: CSSProperties = {
  padding: '1.25rem',
  borderRadius: '20px',
  background: 'linear-gradient(135deg, rgba(52, 199, 89, 0.16), rgba(52, 199, 89, 0.28))',
  border: '1px solid rgba(52, 199, 89, 0.3)',
  boxShadow: '0 18px 38px rgba(52, 199, 89, 0.18)',
}

const auditCardStyle: CSSProperties = {
  padding: '0.85rem 1rem',
  borderRadius: '16px',
  background: 'rgba(255, 255, 255, 0.82)',
  border: '1px solid rgba(15, 23, 42, 0.06)',
  boxShadow: '0 12px 24px rgba(15, 23, 42, 0.08)',
}

const sectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1rem',
  fontWeight: 600,
  color: '#1b2337',
}

const detailRowStyle: CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '1rem',
  padding: '0.65rem 0',
  fontSize: '0.95rem',
  borderBottom: '1px solid rgba(15, 23, 42, 0.06)',
}

const detailRowLabelStyle: CSSProperties = {
  color: '#6d7289',
}

const detailRowValueStyle: CSSProperties = {
  color: '#111b2e',
  fontWeight: 600,
}

const statusPalette: Record<string, { base: string; text: string }> = {
  succeeded: { base: '#34c759', text: '#0b3d17' },
  failed: { base: '#ff375f', text: '#671226' },
  pending: { base: '#ff9f0a', text: '#6c3a00' },
  default: { base: '#8e8e93', text: '#1f2937' },
}

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

  const handleFilterChange = (value: string) => {
    setStatusFilter(value)
    setSelectedJob(null)
  }

  const successRate = summary
    ? summary.total_jobs > 0
      ? ((summary.succeeded_jobs / summary.total_jobs) * 100).toFixed(1)
      : '0.0'
    : '0.0'

  return (
    <div style={pageStyle}>
      <div style={shellStyle}>
        <header style={headerStyle}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <span style={infoTagStyle}>Partner Console</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <h1 style={headerTitleStyle}>Bank Dashboard</h1>
              <p style={headerSubtitleStyle}>
                Keep underwriting progress close at hand and move quickly on borrower needs.
              </p>
            </div>
          </div>

          <button onClick={handleLogout} style={logoutButtonStyle}>
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </header>

        <section>
          <div style={metricsGridStyle}>
            <MetricCard
              icon={<Activity size={28} />}
              label="Total Jobs (24h)"
              value={summary?.total_jobs?.toString() || '0'}
              color={accentBlue}
            />
            <MetricCard
              icon={<CheckCircle size={28} />}
              label="Success Rate"
              value={`${successRate}%`}
              color="#34c759"
            />
            <MetricCard
              icon={<Clock size={28} />}
              label="Avg Processing Time"
              value={
                summary?.average_processing_seconds
                  ? `${summary.average_processing_seconds.toFixed(2)}s`
                  : 'N/A'
              }
              color="#ff9f0a"
            />
            <MetricCard
              icon={<TrendingUp size={28} />}
              label="Succeeded Jobs"
              value={summary?.succeeded_jobs?.toString() || '0'}
              color="#5856d6"
            />
          </div>
        </section>

        <section
          style={{
            ...jobColumnsBaseStyle,
            gridTemplateColumns: selectedJob
              ? 'minmax(0, 1fr) minmax(0, 1fr)'
              : 'minmax(0, 1fr)',
          }}
        >
          <div
            style={{
              ...glassSurface,
              padding: 0,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              minHeight: 0,
            }}
          >
            <div style={{ ...jobListHeaderStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <h2 style={sectionHeadingStyle}>Recent Jobs</h2>
                <p style={sectionSubtitleStyle}>
                  Filter by status and open a job to review the generated memo and audit trail.
                </p>
              </div>
              <div style={filterGroupStyle}>
                <span style={filterLabelStyle}>Status</span>
                <select
                  value={statusFilter}
                  onChange={(event) => handleFilterChange(event.target.value)}
                  style={filterSelectStyle}
                >
                  <option value="">All statuses</option>
                  <option value="succeeded">Succeeded</option>
                  <option value="failed">Failed</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            </div>

            <div style={jobsScrollAreaStyle}>
              {jobs?.jobs.length ? (
                jobs.jobs.map((job) => {
                  const isSelected = job.job_id === selectedJob
                  return (
                    <div
                      key={job.job_id}
                      onClick={() => setSelectedJob(job.job_id)}
                      style={getJobCardStyle(isSelected)}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          gap: '1.25rem',
                          flexWrap: 'wrap',
                        }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          <span style={jobTitleStyle}>{job.client_job_id}</span>
                          <span style={jobSubtitleStyle}>Internal ID • {job.job_id}</span>
                        </div>
                        <StatusBadge status={job.status} />
                      </div>

                      <div style={jobMetaStyle}>
                        <span>Decision: {job.decision || 'Pending'}</span>
                        {job.risk_score !== null && (
                          <span>Risk score {job.risk_score.toFixed(2)}</span>
                        )}
                        {job.processing_seconds !== null && (
                          <span>{job.processing_seconds.toFixed(2)}s</span>
                        )}
                      </div>

                      <div style={jobTimestampStyle}>
                        {new Date(job.created_at).toLocaleString()}
                      </div>
                    </div>
                  )
                })
              ) : (
                <div style={emptyStateStyle}>
                  {jobs ? 'No jobs found. Adjust your filters to try again.' : 'Loading recent jobs…'}
                </div>
              )}
            </div>
          </div>

          {selectedJob && jobDetail && (
            <div
              style={{
                ...glassSurface,
                padding: '2rem 2.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.75rem',
                minHeight: 0,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '1rem',
                  flexWrap: 'wrap',
                }}
              >
                <h2 style={sectionHeadingStyle}>Job details</h2>
                <button onClick={() => setSelectedJob(null)} style={closeButtonStyle}>
                  Close
                </button>
              </div>

              <div style={{ ...jobsScrollAreaStyle, padding: 0 }}>
                <Section title="Summary">
                  <DetailRow label="Job ID" value={jobDetail.summary.job_id} />
                  <DetailRow label="Client Job ID" value={jobDetail.summary.client_job_id} />
                  <DetailRow label="Status" value={jobDetail.summary.status} />
                  <DetailRow label="Decision" value={jobDetail.summary.decision || 'N/A'} />
                  {jobDetail.summary.risk_score !== null && (
                    <DetailRow
                      label="Risk Score"
                      value={jobDetail.summary.risk_score.toFixed(3)}
                    />
                  )}
                  {jobDetail.summary.processing_seconds !== null && (
                    <DetailRow
                      label="Processing Time"
                      value={`${jobDetail.summary.processing_seconds.toFixed(2)}s`}
                    />
                  )}
                  <DetailRow
                    label="Created"
                    value={new Date(jobDetail.summary.created_at).toLocaleString()}
                  />
                </Section>

                {jobDetail.raw_input && (
                  <Section title="Raw Input">
                    <pre style={codeBlockStyle}>
                      {JSON.stringify(jobDetail.raw_input, null, 2)}
                    </pre>
                  </Section>
                )}

                {jobDetail.llm_output_markdown && (
                  <Section title="LLM Output">
                    <div style={llmOutputShellStyle}>
                      <MarkdownRenderer markdown={jobDetail.llm_output_markdown} />
                    </div>
                  </Section>
                )}

                {jobDetail.llm_output_metadata && (
                  <Section title="Output Metadata">
                    <pre style={codeBlockStyle}>
                      {JSON.stringify(jobDetail.llm_output_metadata, null, 2)}
                    </pre>
                  </Section>
                )}

                {jobDetail.audits.length > 0 && (
                  <Section title="Audit Trail">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {jobDetail.audits.map((audit) => (
                        <div key={audit.id} style={auditCardStyle}>
                          <div style={{ fontWeight: 600, color: '#1b2337' }}>{audit.action}</div>
                          <div style={{ fontSize: '0.8rem', color: '#6b7285' }}>
                            by {audit.actor} at {new Date(audit.created_at).toLocaleString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Section>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, color }: { icon: ReactNode; label: string; value: string; color: string }) {
  const gradientStart = hexToRgba(color, 0.18)
  const gradientEnd = hexToRgba(color, 0.34)
  return (
    <div
      style={{
        ...glassSurface,
        background: `linear-gradient(135deg, ${gradientStart}, ${gradientEnd})`,
        border: `1px solid ${hexToRgba(color, 0.35)}`,
        display: 'grid',
        gridTemplateColumns: 'auto 1fr',
        alignItems: 'center',
        gap: '1.4rem',
        padding: '1.9rem',
        color: '#0b1120',
        boxShadow: `0 28px 45px ${hexToRgba(color, 0.25)}`,
      }}
    >
      <div
        style={{
          width: '3.4rem',
          height: '3.4rem',
          borderRadius: '9999px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(255, 255, 255, 0.35)',
          border: `1px solid ${hexToRgba(color, 0.45)}`,
          color,
          boxShadow: `0 16px 28px ${hexToRgba(color, 0.3)}`,
        }}
      >
        {icon}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        <span
          style={{
            fontSize: '0.8rem',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: 'rgba(11, 17, 32, 0.65)',
            fontWeight: 600,
          }}
        >
          {label}
        </span>
        <span style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em' }}>{value}</span>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const palette = statusPalette[status] || statusPalette.default
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.35rem 0.75rem',
        borderRadius: '9999px',
        fontSize: '0.8rem',
        fontWeight: 600,
        textTransform: 'capitalize',
        background: `linear-gradient(135deg, ${hexToRgba(palette.base, 0.22)}, ${hexToRgba(palette.base, 0.35)})`,
        color: palette.text,
        border: `1px solid ${hexToRgba(palette.base, 0.4)}`,
        boxShadow: `0 12px 24px ${hexToRgba(palette.base, 0.24)}`,
      }}
    >
      <span
        style={{
          width: '0.5rem',
          height: '0.5rem',
          borderRadius: '9999px',
          background: hexToRgba(palette.base, 0.8),
        }}
      />
      {status}
    </span>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <h3 style={sectionTitleStyle}>{title}</h3>
      {children}
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={detailRowStyle}>
      <span style={detailRowLabelStyle}>{label}</span>
      <span style={detailRowValueStyle}>{value}</span>
    </div>
  )
}

function getJobCardStyle(isSelected: boolean): CSSProperties {
  return {
    ...jobCardBaseStyle,
    ...(isSelected ? jobCardSelectedStyle : {}),
  }
}

function hexToRgba(hex: string, alpha: number): string {
  const parsed = hex.replace('#', '')
  const bigint = parseInt(parsed.length === 3 ? parsed.repeat(2) : parsed, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
