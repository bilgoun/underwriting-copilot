import { useState, type CSSProperties, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { dashboardApi, JobSummary, TenantOverview } from '../api/client'
import { useAuth } from '../utils/auth'
import { Activity, LogOut, Users, AlertTriangle } from 'lucide-react'
import MarkdownRenderer from '../components/MarkdownRenderer'

const accentBlue = '#0a84ff'
const backgroundGradient = 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 50%, #f0f4f8 100%)'

const glassSurface: CSSProperties = {
  background: 'rgba(255, 255, 255, 0.95)',
  borderRadius: '24px',
  border: '1px solid rgba(0, 0, 0, 0.06)',
  boxShadow: '0 10px 40px rgba(0, 0, 0, 0.08), 0 0 1px rgba(0, 0, 0, 0.04) inset',
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
  color: 'rgba(0, 0, 0, 0.9)',
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
  color: 'rgba(0, 0, 0, 0.9)',
  letterSpacing: '-0.01em',
}

const sectionSubtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.95rem',
  lineHeight: 1.5,
  color: 'rgba(0, 0, 0, 0.5)',
}

const selectionBadgeStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.45rem',
  padding: '0.5rem 0.9rem',
  borderRadius: '9999px',
  background: hexToRgba(accentBlue, 0.15),
  border: `1px solid ${hexToRgba(accentBlue, 0.3)}`,
  color: accentBlue,
  fontSize: '0.85rem',
  fontWeight: 600,
  whiteSpace: 'nowrap',
}

const selectionBadgeDotStyle: CSSProperties = {
  width: '0.45rem',
  height: '0.45rem',
  borderRadius: '9999px',
  background: accentBlue,
}

const overviewTableWrapperStyle: CSSProperties = {
  overflowX: 'auto',
}

const overviewTableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'separate',
  borderSpacing: '0 14px',
}

const tableHeaderStyle: CSSProperties = {
  padding: '0.75rem 1.3rem',
  textAlign: 'left',
  fontSize: '0.75rem',
  fontWeight: 700,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: 'rgba(0, 0, 0, 0.5)',
}

const tableCellStyle: CSSProperties = {
  padding: '1rem 1.3rem',
  fontSize: '0.95rem',
  color: 'rgba(0, 0, 0, 0.85)',
  fontWeight: 500,
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
  background: 'rgba(255, 255, 255, 0.7)',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
  padding: '1.2rem 1.5rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
  cursor: 'pointer',
  transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease, background 0.3s ease, border 0.3s ease',
}

const jobCardSelectedStyle: CSSProperties = {
  background: 'rgba(10, 132, 255, 0.08)',
  border: `1px solid ${hexToRgba(accentBlue, 0.3)}`,
  boxShadow: `0 8px 24px ${hexToRgba(accentBlue, 0.2)}`,
  transform: 'translateY(-2px)',
}

const jobTitleStyle: CSSProperties = {
  fontSize: '1.05rem',
  fontWeight: 700,
  letterSpacing: '-0.01em',
  color: 'rgba(0, 0, 0, 0.9)',
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
  color: 'rgba(0, 0, 0, 0.45)',
}

const codeBlockStyle: CSSProperties = {
  padding: '1.25rem',
  borderRadius: '12px',
  background: 'rgba(0, 0, 0, 0.04)',
  border: '1px solid rgba(0, 0, 0, 0.1)',
  fontSize: '0.8rem',
  overflow: 'auto',
  color: 'rgba(0, 0, 0, 0.85)',
  fontFamily: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
}

const accentCodeBlockStyle: CSSProperties = {
  ...codeBlockStyle,
  background: 'rgba(255, 159, 10, 0.06)',
  border: '1px solid rgba(255, 159, 10, 0.2)',
}

const llmOutputShellStyle: CSSProperties = {
  padding: '1.25rem',
  borderRadius: '16px',
  background: 'rgba(52, 199, 89, 0.06)',
  border: '1px solid rgba(52, 199, 89, 0.2)',
  boxShadow: '0 4px 12px rgba(52, 199, 89, 0.08)',
}

const sectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1rem',
  fontWeight: 600,
  color: 'rgba(0, 0, 0, 0.85)',
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
  color: 'rgba(0, 0, 0, 0.85)',
  fontWeight: 600,
}

const statusPalette: Record<string, { base: string; text: string }> = {
  succeeded: { base: '#34c759', text: '#0b5d1e' },
  failed: { base: '#ff375f', text: '#991b1b' },
  pending: { base: '#ff9f0a', text: '#78350f' },
  default: { base: '#8e8e93', text: '#374151' },
}

const modalOverlayStyle: CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(0, 0, 0, 0.5)',
  backdropFilter: 'blur(8px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: '2rem',
}

const modalContentStyle: CSSProperties = {
  background: 'rgba(255, 255, 255, 0.98)',
  borderRadius: '24px',
  border: '1px solid rgba(0, 0, 0, 0.1)',
  boxShadow: '0 30px 80px rgba(0, 0, 0, 0.25)',
  maxWidth: '1400px',
  width: '100%',
  maxHeight: '90vh',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}

const modalHeaderStyle: CSSProperties = {
  padding: '1.5rem 2rem',
  borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
}

const modalBodyStyle: CSSProperties = {
  padding: '2rem',
  overflowY: 'auto',
  flex: 1,
}

const modalCloseButtonStyle: CSSProperties = {
  width: '32px',
  height: '32px',
  borderRadius: '50%',
  border: '1px solid rgba(0, 0, 0, 0.15)',
  background: 'rgba(0, 0, 0, 0.04)',
  color: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  fontSize: '1.25rem',
  fontWeight: 400,
}

const threeColumnGridStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: '1.5rem',
  marginBottom: '2rem',
}

const columnStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
}

const columnTitleStyle: CSSProperties = {
  fontSize: '0.9rem',
  fontWeight: 600,
  color: 'rgba(0, 0, 0, 0.7)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
}

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

  const activeTenantCount = tenants?.tenants.length ?? 0
  const totalJobs = tenants?.tenants.reduce((sum, tenant) => sum + tenant.total_jobs_24h, 0) ?? 0
  const avgFailureRate = tenants?.tenants.length
    ? (
        tenants.tenants.reduce((sum, tenant) => sum + tenant.failure_rate_24h, 0) /
        tenants.tenants.length
      ).toFixed(1)
    : '0.0'

  const selectedTenantName = selectedTenant
    ? tenants?.tenants.find((tenant) => tenant.tenant_id === selectedTenant)?.name
    : undefined

  return (
    <div style={pageStyle}>
      <div style={shellStyle}>
        <header style={headerStyle}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <span style={infoTagStyle}>Operations Control</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <h1 style={headerTitleStyle}>Admin Dashboard</h1>
              <p style={headerSubtitleStyle}>
                Monitor tenant performance and underwriting health in real time.
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
              icon={<Users size={28} />}
              label="Active Tenants"
              value={activeTenantCount.toString()}
              color={accentBlue}
            />
            <MetricCard
              icon={<Activity size={28} />}
              label="Total Jobs (24h)"
              value={totalJobs.toString()}
              color="#34c759"
            />
            <MetricCard
              icon={<AlertTriangle size={28} />}
              label="Avg Failure Rate"
              value={`${avgFailureRate}%`}
              color="#ff375f"
            />
          </div>
        </section>

        <section
          style={{
            ...glassSurface,
            padding: '2.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.75rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '1.5rem',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <h2 style={sectionHeadingStyle}>Tenant Overview</h2>
              <p style={sectionSubtitleStyle}>
                {selectedTenantName
                  ? `Focusing on ${selectedTenantName} — tap clear to return to all tenants.`
                  : 'Review tenant activity and identify where attention is needed most.'}
              </p>
            </div>
            {selectedTenantName && (
              <div style={selectionBadgeStyle}>
                <span style={selectionBadgeDotStyle} />
                Viewing {selectedTenantName}
              </div>
            )}
          </div>

          <div style={overviewTableWrapperStyle}>
            <table style={overviewTableStyle}>
              <thead>
                <tr>
                  <th style={tableHeaderStyle}>Tenant ID</th>
                  <th style={tableHeaderStyle}>Name</th>
                  <th style={tableHeaderStyle}>Jobs (24h)</th>
                  <th style={tableHeaderStyle}>Failure Rate</th>
                  <th style={tableHeaderStyle}>Action</th>
                </tr>
              </thead>
              <tbody>
                {tenants?.tenants.length ? (
                  tenants.tenants.map((tenant) => {
                    const isActive = tenant.tenant_id === selectedTenant
                    return (
                      <tr key={tenant.tenant_id} style={getTenantRowStyle(isActive)}>
                        <td
                          style={{
                            ...tableCellStyle,
                            borderTopLeftRadius: '18px',
                            borderBottomLeftRadius: '18px',
                          }}
                        >
                          {tenant.tenant_id}
                        </td>
                        <td style={tableCellStyle}>{tenant.name}</td>
                        <td style={tableCellStyle}>{tenant.total_jobs_24h}</td>
                        <td style={tableCellStyle}>
                          <span
                            style={{
                              fontWeight: 600,
                              color:
                                tenant.failure_rate_24h > 10
                                  ? '#ff375f'
                                  : tenant.failure_rate_24h > 5
                                  ? '#ff9f0a'
                                  : '#34c759',
                            }}
                          >
                            {tenant.failure_rate_24h.toFixed(1)}%
                          </span>
                        </td>
                        <td
                          style={{
                            ...tableCellStyle,
                            borderTopRightRadius: '18px',
                            borderBottomRightRadius: '18px',
                          }}
                        >
                          <button
                            onClick={() => {
                              const nextTenant =
                                tenant.tenant_id === selectedTenant ? '' : tenant.tenant_id
                              setSelectedTenant(nextTenant)
                              if (nextTenant !== selectedTenant) {
                                setSelectedJob(null)
                              }
                            }}
                            style={getTenantActionStyle(isActive)}
                          >
                            {isActive ? 'Clear focus' : 'View jobs'}
                          </button>
                        </td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan={5} style={{ ...tableCellStyle, padding: '3rem 1rem' }}>
                      <div style={emptyStateStyle}>
                        {tenants ? 'No tenants found' : 'Loading tenant data…'}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section style={jobColumnsBaseStyle}>
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
            <div style={jobListHeaderStyle}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <h2 style={sectionHeadingStyle}>
                  {selectedTenantName ? `${selectedTenantName} Jobs` : 'All Jobs'}
                </h2>
                <p style={sectionSubtitleStyle}>
                  Tap a job to inspect details, memos, and audit history.
                </p>
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
                          <span style={jobSubtitleStyle}>Tenant • {job.tenant_id}</span>
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
                  {selectedTenantName
                    ? 'No jobs for this tenant yet.'
                    : jobs
                    ? 'No jobs found.'
                    : 'Loading recent jobs…'}
                </div>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Modal Dialog */}
      {selectedJob && jobDetail && (
        <div style={modalOverlayStyle} onClick={() => setSelectedJob(null)}>
          <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
            <div style={modalHeaderStyle}>
              <h2 style={sectionHeadingStyle}>Job Details</h2>
              <button onClick={() => setSelectedJob(null)} style={modalCloseButtonStyle}>
                ×
              </button>
            </div>

            <div style={modalBodyStyle}>
              {/* Three Column Grid */}
              <div style={threeColumnGridStyle}>
                {/* Raw Input Column */}
                <div style={columnStyle}>
                  <div style={columnTitleStyle}>Raw Input</div>
                  <pre style={codeBlockStyle}>
                    {JSON.stringify(jobDetail.raw_input, null, 2)}
                  </pre>
                </div>

                {/* LLM Input Column */}
                <div style={columnStyle}>
                  <div style={columnTitleStyle}>LLM Input</div>
                  <pre style={accentCodeBlockStyle}>
                    {JSON.stringify(jobDetail.llm_input, null, 2)}
                  </pre>
                </div>

                {/* LLM Output Column */}
                <div style={columnStyle}>
                  <div style={columnTitleStyle}>LLM Output</div>
                  {jobDetail.llm_output_markdown && (
                    <div style={llmOutputShellStyle}>
                      <MarkdownRenderer markdown={jobDetail.llm_output_markdown} />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
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

function getTenantRowStyle(isSelected: boolean): CSSProperties {
  return {
    background: isSelected ? hexToRgba(accentBlue, 0.1) : 'rgba(0, 0, 0, 0.04)',
    border: `1px solid ${isSelected ? hexToRgba(accentBlue, 0.3) : 'rgba(0, 0, 0, 0.08)'}`,
    boxShadow: isSelected
      ? `0 8px 24px ${hexToRgba(accentBlue, 0.25)}`
      : '0 4px 12px rgba(0, 0, 0, 0.2)',
    transform: isSelected ? 'translateY(-1px)' : 'translateY(0)',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
  }
}

function getTenantActionStyle(isActive: boolean): CSSProperties {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    padding: '0.5rem 0.95rem',
    borderRadius: '9999px',
    background: isActive
      ? `linear-gradient(135deg, ${hexToRgba(accentBlue, 0.15)}, ${hexToRgba(accentBlue, 0.25)})`
      : 'rgba(0, 0, 0, 0.05)',
    border: isActive
      ? `1px solid ${hexToRgba(accentBlue, 0.4)}`
      : '1px solid rgba(0, 0, 0, 0.1)',
    color: isActive ? accentBlue : 'rgba(0, 0, 0, 0.7)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
  }
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
