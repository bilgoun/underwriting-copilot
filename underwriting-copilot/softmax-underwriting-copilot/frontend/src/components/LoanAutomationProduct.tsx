import { type CSSProperties, type ReactNode } from 'react'
import {
  MessageCircle,
  Bot,
  CheckCircle,
  FileText,
  ShieldCheck,
  Database,
  GitBranch,
  Building2,
  ArrowDown,
  ExternalLink,
} from 'lucide-react'

const accentBlue = '#0a84ff'
const accentGreen = '#34c759'
const accentPurple = '#5856d6'

const containerStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '2.5rem',
  padding: '2.75rem',
  borderRadius: '28px',
  background: 'linear-gradient(135deg, rgba(10, 132, 255, 0.14), rgba(10, 132, 255, 0.04))',
  border: `1px solid ${hexToRgba(accentBlue, 0.2)}`,
  boxShadow: `0 28px 60px ${hexToRgba(accentBlue, 0.18)}`,
}

const headerShellStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1.25rem',
}

const infoTagStyle: CSSProperties = {
  alignSelf: 'flex-start',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.5rem',
  padding: '0.45rem 0.9rem',
  borderRadius: '9999px',
  background: hexToRgba(accentBlue, 0.15),
  border: `1px solid ${hexToRgba(accentBlue, 0.35)}`,
  color: accentBlue,
  fontSize: '0.78rem',
  letterSpacing: '0.08em',
  fontWeight: 600,
  textTransform: 'uppercase',
}

const titleStyle: CSSProperties = {
  margin: 0,
  fontSize: '2.15rem',
  fontWeight: 700,
  letterSpacing: '-0.02em',
  color: 'rgba(0, 0, 0, 0.95)',
}

const subtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1.05rem',
  lineHeight: 1.6,
  color: 'rgba(0, 0, 0, 0.6)',
  maxWidth: '48rem',
}

const phaseStackStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1.65rem',
}

const connectorStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '0.65rem',
  color: hexToRgba(accentBlue, 0.65),
  fontSize: '0.82rem',
  fontWeight: 600,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
}

const phaseCardStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1.25rem',
  padding: '2.25rem',
  borderRadius: '24px',
  background: 'rgba(255, 255, 255, 0.92)',
  border: '1px solid rgba(0, 0, 0, 0.08)',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08)',
  backdropFilter: 'blur(24px)',
}

const phaseHeaderStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: '1.25rem',
}

const phaseIconStyle: CSSProperties = {
  width: '3.4rem',
  height: '3.4rem',
  borderRadius: '18px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: hexToRgba(accentBlue, 0.12),
  border: `1px solid ${hexToRgba(accentBlue, 0.25)}`,
  color: accentBlue,
  boxShadow: `0 16px 32px ${hexToRgba(accentBlue, 0.2)}`,
}

const phaseIdStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  padding: '0.3rem 0.85rem',
  borderRadius: '9999px',
  background: hexToRgba(accentPurple, 0.12),
  border: `1px solid ${hexToRgba(accentPurple, 0.25)}`,
  color: accentPurple,
  fontSize: '0.75rem',
  fontWeight: 600,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
}

const phaseTitleStyle: CSSProperties = {
  margin: '0.35rem 0 0 0',
  fontSize: '1.4rem',
  fontWeight: 700,
  color: 'rgba(0, 0, 0, 0.92)',
  letterSpacing: '-0.01em',
}

const phaseDescriptionStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.98rem',
  lineHeight: 1.65,
  color: 'rgba(0, 0, 0, 0.58)',
}

const highlightsGridStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: '1.1rem',
}

const highlightCardStyle: CSSProperties = {
  display: 'flex',
  gap: '0.8rem',
  padding: '0.95rem 1.05rem',
  borderRadius: '16px',
  background: 'rgba(0, 0, 0, 0.04)',
  border: '1px solid rgba(0, 0, 0, 0.07)',
}

const highlightTextStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '0.25rem',
}

const highlightLabelStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.9rem',
  fontWeight: 600,
  color: 'rgba(0, 0, 0, 0.78)',
}

const highlightDetailStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.85rem',
  color: 'rgba(0, 0, 0, 0.55)',
  lineHeight: 1.45,
}

const footerTagStyle: CSSProperties = {
  alignSelf: 'flex-start',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.5rem',
  padding: '0.4rem 0.85rem',
  borderRadius: '9999px',
  background: hexToRgba(accentGreen, 0.14),
  border: `1px solid ${hexToRgba(accentGreen, 0.3)}`,
  color: accentGreen,
  fontSize: '0.8rem',
  fontWeight: 600,
}

const integrationsCardStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1.5rem',
  padding: '2.1rem',
  borderRadius: '22px',
  background: 'rgba(11, 17, 32, 0.92)',
  color: 'rgba(255, 255, 255, 0.92)',
  border: `1px solid ${hexToRgba('#ffffff', 0.12)}`,
  boxShadow: '0 28px 60px rgba(11, 17, 32, 0.45)',
}

const integrationsTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '1.3rem',
  fontWeight: 600,
  letterSpacing: '-0.01em',
}

const integrationsSubtitleStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.95rem',
  color: 'rgba(255, 255, 255, 0.65)',
  lineHeight: 1.55,
}

const integrationsGridStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: '1.1rem',
}

const integrationPillStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '0.3rem',
  padding: '0.85rem 1rem',
  borderRadius: '14px',
  background: 'rgba(255, 255, 255, 0.08)',
  border: '1px solid rgba(255, 255, 255, 0.12)',
}

const integrationLabelStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.6rem',
  fontSize: '0.85rem',
  fontWeight: 600,
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
  color: 'rgba(255, 255, 255, 0.78)',
}

const integrationDescriptionStyle: CSSProperties = {
  margin: 0,
  fontSize: '0.85rem',
  lineHeight: 1.45,
  color: 'rgba(255, 255, 255, 0.68)',
}

type PhaseHighlight = {
  label: string
  detail: string
}

type Phase = {
  id: string
  title: string
  description: string
  highlights: PhaseHighlight[]
  completionText: string
  icon: ReactNode
}

const phases: Phase[] = [
  {
    id: 'Phase 1',
    title: 'Intake & Product Guidance',
    description:
      'An LLM-powered virtual officer captures borrower intent, nuances, and constraints before surfacing the most viable lending paths.',
    icon: <MessageCircle size={28} />,
    completionText: 'Borrower is prepped with tailored package + submission kit.',
    highlights: [
      {
        label: 'Conversational discovery',
        detail: 'Dynamic dialog uncovers loan purpose, collateral, cash flow, and timing sensitivities.',
      },
      {
        label: 'Curated product trio',
        detail: 'Assistant compares policies and recommends three matching products with eligibility rules.',
      },
      {
        label: 'Click-through readiness',
        detail: 'Borrower jumps to KYC/KYB portal, confirms checklist requirements, then downloads submission kit.',
      },
    ],
  },
  {
    id: 'Phase 2',
    title: 'Document Intake & Verification',
    description:
      'Every file is triaged automatically, validated for authenticity, and scored against a rules-based completeness matrix.',
    icon: <FileText size={28} />,
    completionText: 'Document vault is clean, trusted, and audit-ready.',
    highlights: [
      {
        label: 'Source provenance',
        detail: 'Detects notarized, original, or government-issued sources before accepting each asset.',
      },
      {
        label: 'Tamper & mismatch scan',
        detail: 'Image forensics and data diffing flag altered signatures, seals, or inconsistent values.',
      },
      {
        label: 'LLM quality review',
        detail: 'Large language model interprets narrative docs, validates answers, and summarizes red flags.',
      },
    ],
  },
  {
    id: 'Phase 3',
    title: 'System Cross-Check & Credit Memo',
    description:
      'Verified data flows into third-party verifications, then the LLM assembles a decision-grade memo for human sign-off.',
    icon: <ShieldCheck size={28} />,
    completionText: 'Risk team receives an explainable, LLM-authored credit memo.',
    highlights: [
      {
        label: 'Multi-source API checks',
        detail: 'Credit bureaus, collateral registries, internal ledgers, and legal entity data are reconciled.',
      },
      {
        label: 'Exception tracking',
        detail: 'Rule engine raises outstanding gaps, duplicate submissions, or conflicting disclosures.',
      },
      {
        label: 'Credit memo drafting',
        detail: 'LLM composes structured memo with exposure summary, mitigants, and next-step guidance.',
      },
    ],
  },
]

const integrations = [
  {
    label: 'Credit Bureaus',
    description: 'Equifax-style pull for score bands, delinquencies, and tradeline verification.',
    icon: <Database size={16} />,
  },
  {
    label: 'Collateral Intelligence',
    description: 'Land, vehicle, or equipment registries confirm asset ownership and encumbrances.',
    icon: <GitBranch size={16} />,
  },
  {
    label: 'Internal Systems',
    description: 'Legacy core banking, risk limits, and watchlists reconcile borrower exposure.',
    icon: <Building2 size={16} />,
  },
  {
    label: 'Entity & Legal',
    description: 'Business registries, UBO databases, and sanctions lists validate organizational data.',
    icon: <ShieldCheck size={16} />,
  },
]

export default function LoanAutomationProduct() {
  return (
    <section style={containerStyle}>
      <div style={headerShellStyle}>
        <span style={infoTagStyle}>
          <Bot size={16} />
          Automation Blueprint
        </span>
        <h2 style={titleStyle}>Underwriting Co-Pilot: End-to-end origination automation</h2>
        <p style={subtitleStyle}>
          A three-phase orchestration that blends rule-based rigor with large language models to bring
          borrowers from the first conversation to a lender-ready credit memo—all without leaving the
          digital channel.
        </p>
      </div>

      <div style={phaseStackStyle}>
        {phases.map((phase, index) => (
          <div key={phase.id} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
            <PhaseCard {...phase} />
            {index < phases.length - 1 && (
              <div style={connectorStyle}>
                <span>Progresses To</span>
                <ArrowDown size={18} />
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={integrationsCardStyle}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <h3 style={integrationsTitleStyle}>Verification Fabric</h3>
          <p style={integrationsSubtitleStyle}>
            API-first checks underpin the automation. Each connection feeds the knowledge graph that the
            LLM uses to justify recommendations and flag anomalies.
          </p>
        </div>

        <div style={integrationsGridStyle}>
          {integrations.map((integration) => (
            <div key={integration.label} style={integrationPillStyle}>
              <div style={integrationLabelStyle}>
                {integration.icon}
                {integration.label}
              </div>
              <p style={integrationDescriptionStyle}>{integration.description}</p>
            </div>
          ))}
        </div>

        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.72)' }}>
          <ExternalLink size={16} />
          Extend with internal APIs or partner data rooms.
        </span>
      </div>
    </section>
  )
}

function PhaseCard({ id, title, description, highlights, completionText, icon }: Phase) {
  return (
    <article style={phaseCardStyle}>
      <header style={phaseHeaderStyle}>
        <div style={phaseIconStyle}>{icon}</div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={phaseIdStyle}>{id}</span>
          <h3 style={phaseTitleStyle}>{title}</h3>
        </div>
      </header>

      <p style={phaseDescriptionStyle}>{description}</p>

      <div style={highlightsGridStyle}>
        {highlights.map((highlight) => (
          <div key={highlight.label} style={highlightCardStyle}>
            <CheckCircle size={18} color={accentBlue} />
            <div style={highlightTextStyle}>
              <h4 style={highlightLabelStyle}>{highlight.label}</h4>
              <p style={highlightDetailStyle}>{highlight.detail}</p>
            </div>
          </div>
        ))}
      </div>

      <span style={footerTagStyle}>{completionText}</span>
    </article>
  )
}

function hexToRgba(hex: string, alpha: number): string {
  const parsed = hex.replace('#', '')
  const bigint = parseInt(parsed.length === 3 ? parsed.repeat(2) : parsed, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

