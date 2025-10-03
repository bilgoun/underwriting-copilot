import { useState, type CSSProperties, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { dashboardApi, JobSummary, DashboardSummary } from '../api/client'
import { useAuth } from '../utils/auth'
import { Clock, CheckCircle, Activity, LogOut, TrendingUp } from 'lucide-react'
import MarkdownRenderer from '../components/MarkdownRenderer'

const accentBlue = '#0a84ff'
const backgroundGradient = 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 50%, #f0f4f8 100%)'

const glassSurface: CSSProperties = {
  background: 'rgba(255, 255, 255, 0.95)',
  borderRadius: '24px',
  border: '1px solid rgba(0, 0, 0, 0.06)',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08), 0 0 1px rgba(0, 0, 0, 0.04) inset',
  backdropFilter: 'blur(40px) saturate(180%)',
}

const pageStyle: CSSProperties = {
  minHeight: '100vh',
  background: backgroundGradient,
  padding: '3rem 0 3.5rem',
  position: 'relative',
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
  background: 'linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
}

const headerSubtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1rem',
  lineHeight: 1.6,
  color: 'rgba(0, 0, 0, 0.5)',
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
  color: 'rgba(0, 0, 0, 0.95)',
  letterSpacing: '-0.01em',
}

const sectionSubtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.95rem',
  lineHeight: 1.5,
  color: 'rgba(0, 0, 0, 0.5)',
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
  color: 'rgba(0, 0, 0, 0.6)',
}

const filterSelectStyle: CSSProperties = {
  padding: '0.5rem 1rem',
  borderRadius: '12px',
  border: `1px solid rgba(0, 0, 0, 0.15)`,
  background: 'rgba(0, 0, 0, 0.05)',
  color: 'rgba(0, 0, 0, 0.9)',
  fontSize: '0.85rem',
  fontWeight: 600,
  cursor: 'pointer',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
  WebkitAppearance: 'none',
  appearance: 'none',
}

const emptyStateStyle: CSSProperties = {
  fontSize: '0.95rem',
  color: 'rgba(0, 0, 0, 0.4)',
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
  borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
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
  borderRadius: '16px',
  border: '1px solid rgba(0, 0, 0, 0.1)',
  background: 'rgba(0, 0, 0, 0.04)',
  boxShadow: '0 8px 16px rgba(0, 0, 0, 0.2)',
  padding: '1.2rem 1.5rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
  cursor: 'pointer',
  transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease, background 0.3s ease, border 0.3s ease',
}

const jobCardSelectedStyle: CSSProperties = {
  background: 'rgba(10, 132, 255, 0.1)',
  border: `1px solid ${hexToRgba(accentBlue, 0.4)}`,
  boxShadow: `0 12px 32px ${hexToRgba(accentBlue, 0.3)}`,
  transform: 'translateY(-2px)',
}

const jobTitleStyle: CSSProperties = {
  fontSize: '1.05rem',
  fontWeight: 700,
  letterSpacing: '-0.01em',
  color: 'rgba(0, 0, 0, 0.95)',
}

const jobSubtitleStyle: CSSProperties = {
  fontSize: '0.85rem',
  color: 'rgba(0, 0, 0, 0.5)',
}

const jobMetaStyle: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '0.85rem',
  fontSize: '0.82rem',
  color: 'rgba(0, 0, 0, 0.6)',
}

const jobTimestampStyle: CSSProperties = {
  fontSize: '0.78rem',
  color: 'rgba(0, 0, 0, 0.4)',
}

const closeButtonStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '0.45rem 0.9rem',
  borderRadius: '9999px',
  border: '1px solid rgba(0, 0, 0, 0.15)',
  background: 'rgba(0, 0, 0, 0.05)',
  color: 'rgba(0, 0, 0, 0.7)',
  fontSize: '0.85rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.2s ease',
}

const codeBlockStyle: CSSProperties = {
  padding: '1.25rem',
  borderRadius: '12px',
  background: 'rgba(0, 0, 0, 0.03)',
  border: '1px solid rgba(0, 0, 0, 0.1)',
  fontSize: '0.8rem',
  overflow: 'auto',
  color: 'rgba(0, 0, 0, 0.85)',
  fontFamily: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
}


const llmOutputShellStyle: CSSProperties = {
  padding: '1.25rem',
  borderRadius: '16px',
  background: 'rgba(52, 199, 89, 0.08)',
  border: '1px solid rgba(52, 199, 89, 0.2)',
  boxShadow: '0 8px 16px rgba(52, 199, 89, 0.1)',
}

const sectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1rem',
  fontWeight: 600,
  color: 'rgba(0, 0, 0, 0.9)',
}

const detailRowStyle: CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '1rem',
  padding: '0.65rem 0',
  fontSize: '0.95rem',
  borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
}

const detailRowLabelStyle: CSSProperties = {
  color: 'rgba(0, 0, 0, 0.5)',
}

const detailRowValueStyle: CSSProperties = {
  color: 'rgba(0, 0, 0, 0.9)',
  fontWeight: 600,
}

const tabContainerStyle: CSSProperties = {
  display: 'flex',
  gap: '0.5rem',
  borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
  padding: '0 2rem',
  marginBottom: '1.5rem',
}

const getTabStyle = (isActive: boolean): CSSProperties => ({
  padding: '1rem 1.5rem',
  background: 'transparent',
  border: 'none',
  borderBottom: isActive ? `2px solid ${accentBlue}` : '2px solid transparent',
  color: isActive ? accentBlue : 'rgba(0, 0, 0, 0.6)',
  fontWeight: isActive ? 600 : 500,
  fontSize: '0.95rem',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  marginBottom: '-1px',
})

const tabContentStyle: CSSProperties = {
  padding: '0 2rem 2rem 2rem',
}

const statusPalette: Record<string, { base: string; text: string }> = {
  succeeded: { base: '#34c759', text: '#0b5d1e' },
  failed: { base: '#ff375f', text: '#991b1b' },
  pending: { base: '#ff9f0a', text: '#78350f' },
  default: { base: '#8e8e93', text: '#4b5563' },
}

export default function BankDashboard() {
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'raw_input' | 'llm_output'>('raw_input')
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
                {/* Summary Section - Always visible */}
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

                {/* Tab Navigation */}
                <div style={tabContainerStyle}>
                  <button
                    style={getTabStyle(activeTab === 'raw_input')}
                    onClick={() => setActiveTab('raw_input')}
                  >
                    Raw Input
                  </button>
                  <button
                    style={getTabStyle(activeTab === 'llm_output')}
                    onClick={() => setActiveTab('llm_output')}
                  >
                    LLM Output
                  </button>
                </div>

                {/* Tab Content */}
                <div style={tabContentStyle}>
                  {activeTab === 'raw_input' && jobDetail.raw_input && (
                    <pre style={codeBlockStyle}>
                      {JSON.stringify(jobDetail.raw_input, null, 2)}
                    </pre>
                  )}

                  {activeTab === 'llm_output' && jobDetail.llm_output_markdown && (
                    <div style={llmOutputShellStyle}>
                      <MarkdownRenderer markdown={jobDetail.llm_output_markdown} />
                    </div>
                  )}
                </div>
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
