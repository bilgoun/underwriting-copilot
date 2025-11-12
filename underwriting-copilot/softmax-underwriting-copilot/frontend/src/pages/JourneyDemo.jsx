import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import softmaxJourneyData from '../data/softmaxJourney'
import individualJourneySource from '../data/individualJourney'
import './JourneyDemo.css'

const stageSequence = [
  'leadConsent',
  'timeline',
  'evidence',
  'rules',
  'checklist',
  'documents',
  'cross',
  'committee',
  'rm',
  'analytics',
  'security',
]

const stageLabels = {
  leadConsent: 'Lead & Consent Vault',
  timeline: 'Orchestrator timeline',
  evidence: 'Evidence collectors',
  rules: 'Policy pre-qual + product match',
  checklist: 'Dynamic checklist',
  documents: 'Document AI ingestion',
  cross: 'Cross-check scoring',
  committee: 'Loan committee transcript',
  rm: 'RM handoff package',
  analytics: 'Analytics & observability',
  security: 'Security & immutable audit',
}

const stageDurations = {
  leadConsent: 3200,
  timeline: 3600,
  evidence: 4200,
  rules: 3200,
  checklist: 2600,
  documents: 4200,
  cross: 3600,
  committee: 3200,
  rm: 3000,
  analytics: 2600,
  security: 2600,
}

const stageLoadingStates = {
  leadConsent: {
    message: 'Chatbot lead capture & consent vault hashing…',
    caption: 'ЗМС, ТЕГ, НДШ зөвшөөрлүүдийг баталгаажуулж байна',
  },
  timeline: {
    message: 'State machine advancing orchestration…',
    caption: 'Collector ажлуудыг дараалж, SLA таймер идэвхжүүлэв',
  },
  evidence: {
    message: 'Evidence collectors fetching source data…',
    caption: 'ЗМС, LES, барьцаа бүртгэл, liquidation mirror',
  },
  rules: {
    message: 'Policy rules + product matcher running…',
    caption: 'YAML дүрэм, DSCR тооцоолол, pricing bands',
  },
  checklist: {
    message: 'Building dynamic checklist…',
    caption: 'Бодлого + бүтээгдэхүүний шаардлагыг нэгтгэж байна',
  },
  documents: {
    message: 'Document AI OCR & schema validation…',
    caption: 'Bank statements, tax, payroll, invoice parsing',
  },
  cross: {
    message: 'LLM cross-check analyst reconciling…',
    caption: 'Bank↔VAT, Payroll↔НДШ, ЗМС schedule зөрүүг шалгаж байна',
  },
  committee: {
    message: 'Loan committee review syncing…',
    caption: 'Transcript, motions, cure stack, and bridge offers',
  },
  rm: {
    message: 'Packaging RM dossier…',
    caption: 'Decision cards, DSCR math, proof links',
  },
  analytics: {
    message: 'Refreshing analytics & observability…',
    caption: 'Funnel, SLA, collector health, error heatmap',
  },
  security: {
    message: 'Sealing immutable audit trail…',
    caption: 'Hash chain + KMS envelope encryption',
  },
}

const totalDuration = stageSequence.reduce((sum, stage) => sum + stageDurations[stage], 0)

const individualJourneyDemo = buildIndividualJourneyDemo(individualJourneySource)

const journeyVariants = [
  {
    id: 'softmax',
    label: 'Softmax AI LLC',
    buttonLabel: 'Run Demo 1',
    chip: 'Softmax AI × Automated Credit Copilot',
    title: 'Softmax AI — Fully Automated RM Handoff',
    subtitle:
      'Watch the entire underwriting journey unfold automatically: chatbot lead capture, consent vault, orchestrated data collectors, policy rules, document AI, deterministic cross-checks, and the packaged RM dossier.',
    summaryLabel: 'Loan request insight',
    durationLabel: '~35 секунд',
    durationHelper: 'Automated end-to-end',
    completenessLabel: '100%',
    completenessHelper: 'All docs QA’d at 0.85+ confidence',
    journey: softmaxJourneyData,
  },
  {
    id: 'individual',
    label: 'Батзаяа · Микро бизнес',
    buttonLabel: 'Run Demo 2',
    chip: 'Micro entrepreneur × Digital Portal',
    title: 'Батзаяа — Portal-to-RM Journey',
    subtitle:
      'See how a micro business owner’s portal submission, government data fetch, and cross-checks flow into a declined-yet-coached RM package.',
    summaryLabel: 'Portal submission insight',
    durationLabel: '~28 секунд',
    durationHelper: 'Portal → gov data → RM decision',
    completenessLabel: '92%',
    completenessHelper: 'Portal, gov fetch, and bank statements synced',
    journey: individualJourneyDemo,
  },
]

const severityClass = {
  low: 'journey-alert--low',
  medium: 'journey-alert--medium',
  high: 'journey-alert--high',
}

const dateFormatter = new Intl.DateTimeFormat('mn', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
})

const currencyFormatter = new Intl.NumberFormat('mn-MN', {
  style: 'currency',
  currency: 'MNT',
  maximumFractionDigits: 0,
})

const formatPercent = (value) => `${(value * 100).toFixed(0)}%`

const formatValue = (value) => {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') {
    if (value > 1_000_000) return currencyFormatter.format(value)
    return value.toLocaleString()
  }
  return String(value)
}

const MAX_FIELD_LIST_ITEMS = 4

const formatFieldLabel = (label) =>
  label
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase())

const renderEvidenceValue = (value, depth = 0) => {
  if (value == null) {
    return <span className="journey-field__text">—</span>
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="journey-field__text">—</span>
    }

    const displayItems = value.slice(0, MAX_FIELD_LIST_ITEMS)
    const hasMore = value.length > displayItems.length

    return (
      <ul className="journey-field__list" data-depth={depth}>
        {displayItems.map((entry, index) => (
          <li key={`${index}-${typeof entry}`}>
            {typeof entry === 'object' && entry !== null ? (
              <div className="journey-field__nested">
                {Object.entries(entry).map(([childKey, childValue]) => (
                  <div key={childKey} className="journey-field__nested-row">
                    <small>{formatFieldLabel(childKey)}</small>
                    <div className="journey-field__nested-value">{renderEvidenceValue(childValue, depth + 1)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <span className="journey-field__text">{formatValue(entry)}</span>
            )}
          </li>
        ))}
        {hasMore ? <small className="journey-field__more">+{value.length - displayItems.length} more entries</small> : null}
      </ul>
    )
  }

  if (typeof value === 'object') {
    return (
      <div className="journey-field__grid" data-depth={depth}>
        {Object.entries(value).map(([key, childValue]) => (
          <div key={key} className="journey-field__grid-item">
            <small>{formatFieldLabel(key)}</small>
            <div className="journey-field__nested-value">{renderEvidenceValue(childValue, depth + 1)}</div>
          </div>
        ))}
      </div>
    )
  }

  return <span className="journey-field__text">{formatValue(value)}</span>
}

export default function JourneyDemo() {
  const location = useLocation()
  const intakeContext = location.state ?? null

  const [activeVariant, setActiveVariant] = useState(journeyVariants[0].id)
  const [demoStarted, setDemoStarted] = useState(false)
  const [demoComplete, setDemoComplete] = useState(false)
  const [runId, setRunId] = useState(0)
  const [stageStatus, setStageStatus] = useState({})
  const [activeStageIndex, setActiveStageIndex] = useState(-1)
  const [progressPercent, setProgressPercent] = useState(0)
  const [timelineActiveCount, setTimelineActiveCount] = useState(0)
  const [demoStartTime, setDemoStartTime] = useState(null)

  const stickyRef = useRef(null)
  const stageRefs = useRef({})
  const scrollAnimationRef = useRef(null)

  const journeyOption = journeyVariants.find((variant) => variant.id === activeVariant) ?? journeyVariants[0]
  const journey = journeyOption.journey
  const committeeMeeting = journey.loanCommittee ?? null
  const committeeRecordedAt =
    committeeMeeting?.recordedAt != null ? dateFormatter.format(new Date(committeeMeeting.recordedAt)) : null
  const committeePanelLabel = committeeMeeting?.panel?.length
    ? committeeMeeting.panel
        .map((member) => (member.role ? `${member.name} (${member.role})` : member.name))
        .join(', ')
    : null

  const orchestratorStates = useMemo(
    () =>
      journey.orchestrator?.stateMachine?.map((state) => ({
        ...state,
        reachedAtDate: new Date(state.reachedAt),
      })) ?? [],
    [journey],
  )

  const evidenceCards = useMemo(() => journey.evidence?.collectors ?? [], [journey])

  const requestAmount = intakeContext?.form?.amount ?? journey.intent?.amount ?? 0
  const requestPurpose = intakeContext?.form?.fundingPurpose || journey.intent?.narrative || '—'
  const contactName =
    intakeContext?.form?.fullName ||
    journey.lead?.contact?.name ||
    journey.entity?.fullName ||
    journey.entity?.legalName ||
    '—'
  const companyName =
    intakeContext?.form?.companyName || journey.entity?.legalName || journey.entity?.fullName || journey.entity?.type || '—'
  const contactPhone =
    intakeContext?.form?.phone || journey.lead?.contact?.phone || journey.entity?.relationshipManager?.phone || '—'
  const contactEmail =
    intakeContext?.form?.email || journey.lead?.contact?.email || journey.entity?.relationshipManager?.email || '—'
  const productTitle =
    intakeContext?.productTitle || journey.rules?.productMatch?.recommendedProducts?.[0]?.label || 'Term loan'

  const currentStageKey = activeStageIndex >= 0 ? stageSequence[activeStageIndex] : null
  const upcomingStageKey =
    demoComplete || activeStageIndex === -1
      ? !demoComplete && demoStarted
        ? stageSequence[0]
        : null
      : activeStageIndex + 1 < stageSequence.length
        ? stageSequence[activeStageIndex + 1]
        : null

  const assignStageRef = useMemo(() => {
    const handlers = {}
    stageSequence.forEach((stage) => {
      handlers[stage] = (node) => {
        if (node) {
          stageRefs.current[stage] = node
        } else {
          delete stageRefs.current[stage]
        }
      }
    })
    return handlers
  }, [])

  const cancelScrollAnimation = useCallback(() => {
    if (scrollAnimationRef.current != null) {
      cancelAnimationFrame(scrollAnimationRef.current)
      scrollAnimationRef.current = null
    }
  }, [])

  const animateScrollTo = useCallback(
    (targetY, duration = 1500) => {
      cancelScrollAnimation()
      const startY = window.scrollY
      const distance = targetY - startY
      const startTime = performance.now()

      const easeInOutQuad = (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t)

      const step = (now) => {
        const elapsed = now - startTime
        const progress = Math.min(elapsed / duration, 1)
        const eased = easeInOutQuad(progress)
        window.scrollTo(0, startY + distance * eased)

        if (progress < 1) {
          scrollAnimationRef.current = requestAnimationFrame(step)
        } else {
          scrollAnimationRef.current = null
        }
      }

      scrollAnimationRef.current = requestAnimationFrame(step)
    },
    [cancelScrollAnimation],
  )

  const scrollToStage = useCallback(
    (stage) => {
      const node = stageRefs.current[stage]
      if (!node) return
      const headerHeight = stickyRef.current?.offsetHeight ?? 0
      const rect = node.getBoundingClientRect()
      const targetY = window.scrollY + rect.top - (headerHeight + 24)
      animateScrollTo(targetY, 1500)
    },
    [animateScrollTo],
  )

  useEffect(
    () => () => {
      cancelScrollAnimation()
    },
    [cancelScrollAnimation],
  )

  const handleStart = useCallback(
    (variantId) => {
      const hasRunningStage = Object.values(stageStatus).some((status) => status === 'running')
      if (!demoComplete && demoStarted && hasRunningStage) return

      setActiveVariant(variantId)
      setDemoComplete(false)
      setStageStatus({})
      setActiveStageIndex(-1)
      setTimelineActiveCount(0)
      setProgressPercent(0)
      setDemoStartTime(Date.now())
      setRunId((id) => id + 1)
      setDemoStarted(true)
    },
    [demoComplete, demoStarted, stageStatus],
  )

  useEffect(() => {
    if (!demoStarted || demoStartTime == null) return

    let frameId

    const tick = () => {
      const elapsed = Date.now() - demoStartTime
      const ratio = Math.min(elapsed / totalDuration, 1)
      setProgressPercent(Math.round(ratio * 100))

      if (ratio < 1 && !demoComplete) {
        frameId = window.requestAnimationFrame(tick)
      } else {
        setProgressPercent(100)
      }
    }

    frameId = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(frameId)
  }, [demoStarted, demoStartTime, demoComplete])

  useEffect(() => {
    if (demoComplete) {
      setProgressPercent(100)
    }
  }, [demoComplete])

  useEffect(() => {
    if (!demoStarted) {
      setProgressPercent(0)
    }
  }, [demoStarted])

  useEffect(() => {
    if (!demoStarted) return

    let cancelled = false
    const currentRunId = runId

    const run = async () => {
      for (let index = 0; index < stageSequence.length; index += 1) {
        if (cancelled) return

        const stage = stageSequence[index]
        setStageStatus((prev) => ({ ...prev, [stage]: 'running' }))
        setActiveStageIndex(index)

        window.requestAnimationFrame(() => {
          if (!cancelled && runId === currentRunId) {
            scrollToStage(stage)
          }
        })

        const duration = stageDurations[stage]
        const startedAt = performance.now()

        while (!cancelled && runId === currentRunId && performance.now() - startedAt < duration) {
          await new Promise((resolve) => setTimeout(resolve, 60))
        }

        if (cancelled || runId !== currentRunId) return

        setStageStatus((prev) => ({ ...prev, [stage]: 'complete' }))
      }

      if (!cancelled && runId === currentRunId) {
        setDemoComplete(true)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [demoStarted, runId, scrollToStage])

  useEffect(() => {
    if (stageStatus.timeline !== 'running') return

    setTimelineActiveCount(0)
    let cancelled = false
    const timers = orchestratorStates.map((_, index) =>
      setTimeout(() => {
        if (!cancelled) setTimelineActiveCount(index + 1)
      }, index * 360),
    )

    return () => {
      cancelled = true
      timers.forEach(clearTimeout)
    }
  }, [stageStatus.timeline, orchestratorStates, runId])

  useEffect(() => {
    if (stageStatus.timeline === 'complete') {
      setTimelineActiveCount(orchestratorStates.length)
    }
  }, [stageStatus.timeline, orchestratorStates.length])

  const hasRunningStage = Object.values(stageStatus).some((status) => status === 'running')
  const isDemoRunning = demoStarted && !demoComplete && hasRunningStage

  const stageState = (stage) => stageStatus[stage]
  const stageVisible = (stage) => Boolean(stageStatus[stage])
  const runningStageLabel =
    currentStageKey && stageState(currentStageKey)
      ? `${stageState(currentStageKey) === 'complete' ? 'Completed' : 'Running'}: ${stageLabels[currentStageKey]}`
      : demoStarted
        ? 'Initializing orchestration…'
        : 'Demo idle'
  const upcomingStageLabel =
    upcomingStageKey && !demoComplete ? `Next: ${stageLabels[upcomingStageKey]}` : demoComplete ? 'All stages complete' : ''

  return (
    <div className="journey-page">
      <div className="journey-progress-sticky" ref={stickyRef}>
        <div className="journey-progress-sticky__header">
          <div>
            <span>{demoComplete ? 'RM handoff package ready' : runningStageLabel}</span>
            <small>{upcomingStageLabel}</small>
          </div>
          <strong className="journey-progress-sticky__percent">{progressPercent}%</strong>
        </div>
        <div
          className="journey-progress journey-progress--sticky"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progressPercent}
        >
          <div className="journey-progress__bar" style={{ width: `${progressPercent}%` }} />
        </div>
      </div>

      <header className="journey-hero">
        <div className="journey-hero__chip">{journeyOption.chip}</div>
        <div className="journey-hero__header">
          <div>
            <h1 className="journey-hero__title">{journeyOption.title}</h1>
            <p className="journey-hero__subtitle">{journeyOption.subtitle}</p>
          </div>
          <div className="journey-hero__summary-card">
            <span className="journey-hero__summary-label">{journeyOption.summaryLabel}</span>
            <strong className="journey-hero__summary-value">{currencyFormatter.format(requestAmount)}</strong>
            <p className="journey-hero__summary-meta">
              {requestPurpose}
              <br />
              Product path: {productTitle}
            </p>
            <dl className="journey-hero__summary-details">
              <dt>Company</dt>
              <dd>{companyName}</dd>
              <dt>Contact</dt>
              <dd>
                {contactName} · {contactPhone}
              </dd>
              <dt>Email</dt>
              <dd>{contactEmail}</dd>
            </dl>
          </div>
        </div>

        <div className="journey-hero__grid">
          <HeroStat
            label="Accuracy Score"
            value={
              journey.orchestrator?.accuracyScore != null
                ? `${Math.round(journey.orchestrator.accuracyScore * 100)}%`
                : '—'
            }
          />
          <HeroStat label="Completeness" value={journeyOption.completenessLabel} helper={journeyOption.completenessHelper} />
          <HeroStat
            label="RM contact"
            value={journey.entity?.relationshipManager?.name ?? '—'}
            helper={
              journey.entity?.relationshipManager
                ? `${journey.entity.relationshipManager.phone} · ${journey.entity.relationshipManager.email}`
                : ''
            }
          />
          <HeroStat label="Journey length" value={journeyOption.durationLabel} helper={journeyOption.durationHelper} />
        </div>

        <div className="journey-hero__actions">
          <div className="journey-hero__cta-group">
            {journeyVariants.map((variant) => {
              const isVariantActive = variant.id === activeVariant
              const label =
                isVariantActive && demoComplete ? 'Replay Demo' : variant.buttonLabel
              return (
                <button
                  key={variant.id}
                  type="button"
                  className={`journey-hero__cta${isVariantActive ? ' journey-hero__cta--active' : ''}`}
                  onClick={() => handleStart(variant.id)}
                  disabled={isDemoRunning && variant.id !== activeVariant}
                >
                  {isVariantActive && isDemoRunning ? 'Running…' : label}
                </button>
              )
            })}
          </div>
          <div className="journey-hero__status">
            <span>
              {demoComplete
                ? `${journeyOption.label} automation complete — ready for RM review.`
                : runningStageLabel}
            </span>
            {!demoComplete && (
              <small>{upcomingStageLabel || `Select Run Demo 1 or 2 to view different loan journeys.`}</small>
            )}
          </div>
        </div>
      </header>

      {stageVisible('leadConsent') && (
        <section ref={assignStageRef.leadConsent} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="1. Lead & Consent Vault" subtitle="Chatbot → portal → consent-secured downstream calls" />
          {stageState('leadConsent') !== 'complete' ? (
            <StageLoading stage="leadConsent" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.15s' }}>
                <h3 className="journey-card__title">Lead snapshot</h3>
                <dl className="journey-list">
                  <ListItem label="Lead ID" value={journey.lead?.leadId ?? '—'} />
                  <ListItem label="Channel" value={journey.lead?.channel ?? 'Portal'} />
                  <ListItem
                    label={journey.entity?.legalName ? 'Company' : 'Borrower'}
                    value={
                      journey.entity?.legalName && journey.entity?.englishName
                        ? `${journey.entity.legalName} / ${journey.entity.englishName}`
                        : journey.entity?.legalName || journey.entity?.fullName || '—'
                    }
                  />
                  {journey.entity?.brn ? (
                    <ListItem label="BRN" value={journey.entity.brn} />
                  ) : (
                    <ListItem
                      label="Иргэний РД"
                      value={journey.entity?.nationalIdFromPortal || journey.entity?.nationalIdFromHUR || '—'}
                    />
                  )}
                  <ListItem
                    label="Contact"
                    value={`${contactName}${journey.lead?.contact?.title ? `, ${journey.lead.contact.title}` : ''}`}
                  />
                  <ListItem label="Phone" value={contactPhone} />
                  <ListItem label="Email" value={contactEmail} />
                  <ListItem
                    label="Suggested products"
                    value={
                      journey.lead?.productsSuggested?.length ? journey.lead.productsSuggested.join(', ') : '—'
                    }
                  />
                  <ListItem
                    label="Created"
                    value={
                      journey.lead?.createdAt ? dateFormatter.format(new Date(journey.lead.createdAt)) : '—'
                    }
                  />
                </dl>
                {(journey.lead?.chatbotTranscript ?? []).length > 0 && (
                  <div className="journey-transcript">
                    <p className="journey-transcript__label">Chat transcript (excerpt)</p>
                    <ul className="journey-transcript__list">
                      {journey.lead?.chatbotTranscript?.map((message) => (
                        <li
                          key={message.id}
                          className={`journey-transcript__item journey-transcript__item--${message.actor}`}
                        >
                          <span>{message.content}</span>
                          <time>{dateFormatter.format(new Date(message.timestamp))}</time>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.32s' }}>
                <h3 className="journey-card__title">Consent scopes</h3>
                <p className="journey-card__lead">
                  Consent Vault logs every scope, hashes proofs, and attaches consent_id on all downstream calls.
                </p>
                <dl className="journey-list">
                  <ListItem label="Consent ID" value={journey.consents?.consentId ?? '—'} />
                  <ListItem
                    label="Granted"
                    value={
                      journey.consents?.grantedAt
                        ? dateFormatter.format(new Date(journey.consents.grantedAt))
                        : '—'
                    }
                  />
                  <ListItem
                    label="Expires"
                    value={
                      journey.consents?.expiresAt
                        ? dateFormatter.format(new Date(journey.consents.expiresAt))
                        : '—'
                    }
                  />
                </dl>
                <div className="journey-consents">
                  {(journey.consents?.scopes ?? []).map((scope, index) => (
                    <article
                      className="journey-consent journey-card--animate"
                      key={scope.scope}
                      style={{ animationDelay: `${0.4 + index * 0.08}s` }}
                    >
                      <header>
                        <span>{scope.label}</span>
                        <strong>{scope.status === 'granted' ? 'Granted' : scope.status}</strong>
                      </header>
                      <p>{scope.scope}</p>
                      <span className="journey-link">Proof artifact (mock)</span>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {stageVisible('timeline') && (
        <section ref={assignStageRef.timeline} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="2. Orchestrator timeline" subtitle="State machine, events, and SLA tracking" />
          {stageState('timeline') !== 'complete' ? (
            <StageLoading stage="timeline" />
          ) : (
            <div className="journey-card journey-card--animate" style={{ animationDelay: '0.15s' }}>
              <div className="journey-timeline">
                {orchestratorStates.map((state, index) => {
                  const isActive = index < timelineActiveCount
                  const isCurrent = index === timelineActiveCount - 1 && stageState('timeline') === 'running'
                  return (
                    <div
                      key={state.id}
                      className={`journey-timeline__item ${isActive ? 'journey-timeline__item--active' : ''} ${
                        isCurrent ? 'journey-timeline__item--current' : ''
                      }`}
                      style={{ transitionDelay: `${index * 0.08}s` }}
                    >
                      <div
                        className={`journey-timeline__dot ${isActive ? 'journey-timeline__dot--complete' : ''} ${
                          isCurrent ? 'journey-timeline__dot--current' : ''
                        }`}
                      >
                        <span>{index + 1}</span>
                      </div>
                      <div className="journey-timeline__content">
                        <h4>{state.label}</h4>
                        <p>{dateFormatter.format(state.reachedAtDate)}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="journey-events">
                <h4>Key events</h4>
                <ul>
                  {(journey.orchestrator?.events ?? []).map((event, index) => (
                    <li
                      key={`${event.type}-${event.at}`}
                      className="journey-events__item journey-card--animate"
                      style={{ animationDelay: `${0.2 + index * 0.08}s` }}
                    >
                      <div>
                        <span>{event.type}</span>
                        <time>{dateFormatter.format(new Date(event.at))}</time>
                      </div>
                      <p>{event.detail}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      )}

      {stageVisible('evidence') && (
        <section ref={assignStageRef.evidence} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="3. Evidence collectors" subtitle="API + mirror + headless RPA with proof artifacts" />
          {stageState('evidence') !== 'complete' ? (
            <StageLoading stage="evidence" />
          ) : (
            <div className="journey-grid journey-grid--three">
              {evidenceCards.map((collector, index) => {
                const status = collector.status ?? 'passed'
                const pillClass =
                  status === 'failed'
                    ? 'journey-pill--fail'
                    : status === 'pending'
                      ? 'journey-pill--warn'
                      : 'journey-pill--pass'
                const pillLabel =
                  status === 'passed'
                    ? 'Pass'
                    : status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')
                const fieldEntries = Object.entries(collector.parsedFields ?? {})
                return (
                  <article
                    className="journey-card journey-card--animate"
                    key={collector.id}
                    style={{ animationDelay: `${0.15 + index * 0.12}s` }}
                  >
                    <header>
                      <span className={`journey-pill ${pillClass}`}>{pillLabel}</span>
                      <strong>{collector.label}</strong>
                    </header>
                    <dl className="journey-list journey-list--compact">
                      <ListItem
                        label="Captured"
                        value={collector.capturedAt ? dateFormatter.format(new Date(collector.capturedAt)) : '—'}
                      />
                      <ListItem
                        label="Confidence"
                        value={collector.confidence != null ? `${Math.round(collector.confidence * 100)}%` : '—'}
                      />
                      <ListItem label="Checksum" value={collector.checksum ? collector.checksum.slice(0, 12) : '—'} />
                    </dl>
                    <div className="journey-evidence__fields">
                      {fieldEntries.length ? (
                        fieldEntries.map(([field, value]) => (
                          <div className="journey-evidence__field" key={field}>
                            <span className="journey-evidence__field-label">{formatFieldLabel(field)}</span>
                            <div className="journey-evidence__field-value">{renderEvidenceValue(value)}</div>
                          </div>
                        ))
                      ) : (
                        <span className="journey-evidence__empty">No structured fields returned</span>
                      )}
                    </div>
                    {collector.rawProof?.uri ? <span className="journey-link">View raw proof (mock)</span> : null}
                  </article>
                )
              })}
            </div>
          )}
        </section>
      )}

      {stageVisible('rules') && (
        <section ref={assignStageRef.rules} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="4. Policy pre-qualification & product matching" subtitle="Rules engine with explainable traces" />
          {stageState('rules') !== 'complete' ? (
            <StageLoading stage="rules" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Policy rules</h3>
                <ul className="journey-rule-list">
                  {(journey.rules?.policyPrequal?.rules ?? []).map((rule, index) => {
                    const status = rule.status ?? 'pass'
                    const pillClass =
                      status === 'fail'
                        ? 'journey-pill--fail'
                        : status === 'warn'
                          ? 'journey-pill--warn'
                          : 'journey-pill--pass'
                    const pillLabel =
                      status === 'pass' ? 'Pass' : status === 'fail' ? 'Fail' : status === 'warn' ? 'Warn' : status
                    return (
                      <li
                        key={rule.id}
                        className="journey-card--animate"
                        style={{ animationDelay: `${0.26 + index * 0.08}s` }}
                      >
                        <div>
                          <strong>{rule.id}</strong>
                          <span className={`journey-pill ${pillClass}`}>{pillLabel}</span>
                        </div>
                        <p>{rule.evidence}</p>
                      </li>
                    )
                  })}
                </ul>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.34s' }}>
                <h3 className="journey-card__title">Recommended bundle</h3>
                <ul className="journey-product-list">
                  {(journey.rules?.productMatch?.recommendedProducts ?? []).map((product, index) => (
                    <li
                      key={product.id}
                      className="journey-card journey-card--animate"
                      style={{ animationDelay: `${0.42 + index * 0.12}s` }}
                    >
                      <div className="journey-product-list__header">
                        <strong>{product.label}</strong>
                        {product.limit != null && <span>{currencyFormatter.format(product.limit)}</span>}
                      </div>
                      <dl className="journey-list journey-list--compact">
                        {product.pricingBand && <ListItem label="Pricing" value={product.pricingBand} />}
                        {product.dscr != null && <ListItem label="DSCR" value={product.dscr.toFixed(2)} />}
                        {product.paymentCap != null && (
                          <ListItem label="Payment cap" value={currencyFormatter.format(product.paymentCap)} />
                        )}
                        {product.collateral && <ListItem label="Collateral" value={product.collateral} />}
                        {product.comments && <ListItem label="Notes" value={product.comments} />}
                      </dl>
                    </li>
                  ))}
                </ul>
                <div className="journey-rejected journey-card--animate" style={{ animationDelay: '0.68s' }}>
                  <p>Rejected products</p>
                  <ul>
                    {(journey.rules?.productMatch?.rejectedProducts ?? []).map((entry) => (
                      <li key={entry.id}>
                        <span>{entry.id}</span>
                        <p>{entry.reason}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {stageVisible('checklist') && (
        <section ref={assignStageRef.checklist} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="5. Dynamic checklist" subtitle="Auto-generated requirements by policy + product" />
          {stageState('checklist') !== 'complete' ? (
            <StageLoading stage="checklist" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Checklist status</h3>
                <ul className="journey-checklist">
                  {(journey.checklist?.items ?? []).map((item, index) => {
                    const status = item.status ?? 'pending'
                    const itemClass =
                      status === 'uploaded' || status === 'not_required' ? 'journey-checklist__item--pass' : ''
                    let pillClass = 'journey-pill--pass'
                    if (status === 'pending') pillClass = 'journey-pill--warn'
                    if (status === 'rejected') pillClass = 'journey-pill--fail'
                    const pillLabel =
                      status === 'uploaded'
                        ? 'Uploaded'
                        : status === 'not_required'
                          ? 'Waived'
                          : status === 'synced'
                            ? 'Synced'
                            : status === 'rejected'
                              ? 'Rejected'
                              : 'Pending'
                    return (
                      <li
                        key={item.id}
                        className={`journey-checklist__item journey-card--animate ${itemClass}`}
                        style={{ animationDelay: `${0.26 + index * 0.06}s` }}
                      >
                        <div>
                          <strong>{item.label}</strong>
                          <span>{item.required ? 'Required' : 'Optional'}</span>
                        </div>
                        <span className={`journey-pill ${pillClass}`}>{pillLabel}</span>
                      </li>
                    )
                  })}
                </ul>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.34s' }}>
                <h3 className="journey-card__title">Upload guardrails</h3>
                <ul className="journey-next-actions">
                  <li>Virus scan, size/type check, SHA-256 hashing, duplicate detection</li>
                  <li>Classification model routes docs into registration, tax, payroll, invoices, statements</li>
                  <li>Portal gives instant feedback on missing or low-confidence fields</li>
                  <li>Attended console handles CAPTCHA / selector drift escalations</li>
                </ul>
              </div>
            </div>
          )}
        </section>
      )}

      {stageVisible('documents') && (
        <section ref={assignStageRef.documents} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="6. Document AI ingestion" subtitle="Classification → OCR extraction → structured schema" />
          {stageState('documents') !== 'complete' ? (
            <StageLoading stage="documents" />
          ) : (
            <div className="journey-card journey-card--animate" style={{ animationDelay: '0.2s' }}>
              <table className="journey-table">
                <thead>
                  <tr>
                    <th>Файл</th>
                    <th>Класс</th>
                    <th>Хэмжээ</th>
                    <th>OCR итгэл</th>
                  </tr>
                </thead>
                <tbody>
                  {(journey.documents?.uploads ?? []).map((doc, index) => (
                    <tr key={doc.id} className="journey-card--animate" style={{ animationDelay: `${0.3 + index * 0.08}s` }}>
                      <td>
                        <span>{doc.name}</span>
                        {doc.uploadedAt && <small>{dateFormatter.format(new Date(doc.uploadedAt))}</small>}
                      </td>
                      <td>{doc.class}</td>
                      <td>{doc.sizeMb != null ? `${doc.sizeMb.toFixed(1)} MB` : '—'}</td>
                      <td>
                        {doc.ocr?.confidence != null ? `${Math.round(doc.ocr.confidence * 100)}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {stageVisible('cross') && (
        <section ref={assignStageRef.cross} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="7. Cross-checks & scoring" subtitle="Deterministic reconciliations with tolerances" />
          {stageState('cross') !== 'complete' ? (
            <StageLoading stage="cross" />
          ) : (
            <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
              <ul className="journey-crosschecks">
                {(journey.crossChecks?.results ?? []).map((item, index) => {
                  const status = item.status ?? 'pass'
                  const pillClass =
                    status === 'fail'
                      ? 'journey-pill--fail'
                      : status === 'warn' || status === 'unverified'
                        ? 'journey-pill--warn'
                        : 'journey-pill--pass'
                  const pillLabel =
                    status === 'pass'
                      ? 'Pass'
                      : status === 'fail'
                        ? 'Fail'
                        : status === 'warn'
                          ? 'Warn'
                          : status === 'unverified'
                            ? 'Review'
                            : status
                  return (
                    <li
                      key={item.id}
                      className="journey-card--animate"
                      style={{ animationDelay: `${0.28 + index * 0.08}s` }}
                    >
                      <div>
                        <strong>{item.label}</strong>
                        <span className={`journey-pill ${pillClass}`}>{pillLabel}</span>
                      </div>
                      <p>{item.detail}</p>
                      {item.variance != null && <small>Variance: {formatPercent(item.variance)}</small>}
                    </li>
                  )
                })}
              </ul>
              <footer className="journey-card__footer">
                <strong>Accuracy Score:</strong>
                <span>
                  {journey.crossChecks?.accuracyScore != null
                    ? `${Math.round(journey.crossChecks.accuracyScore * 100)}%`
                    : '—'}
                </span>
              </footer>
            </div>
          )}
        </section>
      )}

      {stageVisible('committee') && (
        <section ref={assignStageRef.committee} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="8. Loan committee transcript" subtitle="Panel deliberations, motions, and cure stack tracking" />
          {stageState('committee') !== 'complete' ? (
            <StageLoading stage="committee" />
          ) : committeeMeeting ? (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Discussion highlights</h3>
                <p className="journey-card__lead">
                  {[
                    committeeMeeting.moderator ? `Moderator: ${committeeMeeting.moderator}` : null,
                    committeeRecordedAt ? `Recorded ${committeeRecordedAt}` : null,
                    committeePanelLabel ? `Panel: ${committeePanelLabel}` : null,
                  ]
                    .filter(Boolean)
                    .join(' · ') || '—'}
                </p>
                <ul className="journey-transcript">
                  {(committeeMeeting.transcript ?? []).map((entry, index) => (
                    <li
                      key={`${entry.speaker}-${index}`}
                      className="journey-transcript__item journey-card--animate"
                      style={{ animationDelay: `${0.26 + index * 0.06}s` }}
                    >
                      <div className="journey-transcript__header">
                        <strong className="journey-transcript__speaker">{entry.speaker}</strong>
                        {entry.focus ? <span className="journey-transcript__focus">{entry.focus}</span> : null}
                      </div>
                      <p className="journey-transcript__content">{entry.content}</p>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.32s' }}>
                <h3 className="journey-card__title">Motions & votes</h3>
                <div className="journey-motions">
                  {(committeeMeeting.motions ?? []).map((motion, index) => (
                    <article
                      key={motion.id ?? `${motion.title}-${index}`}
                      className="journey-motion journey-card--animate"
                      style={{ animationDelay: `${0.4 + index * 0.08}s` }}
                    >
                      <header className="journey-motion__header">
                        <strong className="journey-motion__title">{motion.title}</strong>
                        <span className="journey-motion__result">{motion.result ?? '—'}</span>
                      </header>
                      <p className="journey-motion__proposal">{motion.proposal}</p>
                      {motion.rationale ? <p className="journey-motion__meta">{motion.rationale}</p> : null}
                      {motion.conditions?.length ? (
                        <ul className="journey-motion__conditions">
                          {motion.conditions.map((condition) => (
                            <li key={condition}>{condition}</li>
                          ))}
                        </ul>
                      ) : null}
                    </article>
                  ))}
                </div>
                {committeeMeeting.followUps?.length ? (
                  <div className="journey-committee-meta">
                    <strong>Follow-ups</strong>
                    <ul>
                      {committeeMeeting.followUps.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="journey-card journey-card--animate" style={{ animationDelay: '0.2s' }}>
              <h3 className="journey-card__title">No committee review required</h3>
              <p className="journey-card__lead">This scenario bypassed a formal loan committee.</p>
            </div>
          )}
        </section>
      )}

      {stageVisible('rm') && (
        <section ref={assignStageRef.rm} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="9. RM handoff package" subtitle="Credit 360 dossier with decisions, proofs, and next steps" />
          {stageState('rm') !== 'complete' ? (
            <StageLoading stage="rm" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Decision summary</h3>
                <dl className="journey-list">
                  <ListItem label="Decision" value={journey.rmPackage?.summary?.decision ?? '—'} />
                  <ListItem
                    label="DSCR"
                    value={
                      journey.rmPackage?.summary?.dscr != null
                        ? journey.rmPackage.summary.dscr.toFixed(2)
                        : '—'
                    }
                  />
                  <ListItem
                    label="Debt capacity"
                    value={
                      journey.rmPackage?.summary?.debtCapacity != null
                        ? currencyFormatter.format(journey.rmPackage.summary.debtCapacity)
                        : '—'
                    }
                  />
                </dl>
                <div className="journey-tags">
                  {(journey.rmPackage?.summary?.riskHighlights ?? []).map((note, index) => (
                    <span key={note} className="journey-tag journey-card--animate" style={{ animationDelay: `${0.3 + index * 0.06}s` }}>
                      {note}
                    </span>
                  ))}
                </div>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.32s' }}>
                <h3 className="journey-card__title">Next actions</h3>
                <ul className="journey-next-actions">
                  {(journey.rmPackage?.summary?.nextActions ?? []).map((task, index) => (
                    <li key={task} className="journey-card--animate" style={{ animationDelay: `${0.4 + index * 0.08}s` }}>
                      {task}
                    </li>
                  ))}
                </ul>
                <div className="journey-links">
                  <span className="journey-link">Download dossier (PDF mock)</span>
                  <span className="journey-link">Download dossier (JSON mock)</span>
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {stageVisible('analytics') && (
        <section ref={assignStageRef.analytics} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="10. Analytics & observability" subtitle="Funnel, SLA, collector health, and exception alerts" />
          {stageState('analytics') !== 'complete' ? (
            <StageLoading stage="analytics" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Weekly metrics</h3>
                <ul className="journey-metrics">
                  {(journey.analytics?.metrics ?? []).map((metric, index) => (
                    <li key={metric.id} className="journey-card--animate" style={{ animationDelay: `${0.28 + index * 0.08}s` }}>
                      <div>
                        <strong>{metric.label}</strong>
                        <p>{metric.value}</p>
                      </div>
                      <span>{metric.delta}</span>
                    </li>
                  ))}
                </ul>
                <div className="journey-funnel journey-card--animate" style={{ animationDelay: '0.5s' }}>
                  <header>
                    <strong>Funnel snapshot</strong>
                    <span>
                      Updated{' '}
                      {journey.analytics?.updatedAt ? dateFormatter.format(new Date(journey.analytics.updatedAt)) : '—'}
                    </span>
                  </header>
                  <ul>
                    {(journey.analytics?.funnel ?? []).map((stage) => (
                      <li key={stage.stage}>
                        <span>{stage.stage}</span>
                        <strong>{stage.count}</strong>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.32s' }}>
                <h3 className="journey-card__title">Alerts & resilience</h3>
                <ul className="journey-alerts">
                  {(journey.analytics?.alerts ?? []).map((alert, index) => (
                    <li
                      key={alert.id}
                      className={`journey-alert journey-card--animate ${severityClass[alert.severity] || ''}`}
                      style={{ animationDelay: `${0.4 + index * 0.08}s` }}
                    >
                      <div>
                        <strong>{alert.message}</strong>
                        <span>{alert.severity.toUpperCase()}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      )}

      {stageVisible('security') && (
        <section ref={assignStageRef.security} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="11. Security & immutable audit" subtitle="RBAC, mTLS, KMS, hash chained events" />
          {stageState('security') !== 'complete' ? (
            <StageLoading stage="security" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.2s' }}>
                <h3 className="journey-card__title">RBAC & encryption</h3>
                <ul className="journey-rbac">
                  {(journey.security?.rbacRoles ?? []).map((role, index) => (
                    <li key={role.role} className="journey-card--animate" style={{ animationDelay: `${0.28 + index * 0.08}s` }}>
                      <strong>{role.role}</strong>
                      <span>{role.permissions.join(', ')}</span>
                    </li>
                  ))}
                </ul>
                <dl className="journey-list">
                  <ListItem label="mTLS" value={journey.security?.encryption?.transit ?? '—'} />
                  <ListItem label="Encryption at rest" value={journey.security?.encryption?.atRest ?? '—'} />
                </dl>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.34s' }}>
                <h3 className="journey-card__title">Immutable audit log</h3>
                <ul className="journey-audit">
                  {(journey.auditLog ?? []).map((entry, index) => (
                    <li key={entry.id} className="journey-card--animate" style={{ animationDelay: `${0.42 + index * 0.08}s` }}>
                      <div>
                        <strong>{entry.action}</strong>
                        <span>{entry.actor}</span>
                      </div>
                      <time>{dateFormatter.format(new Date(entry.at))}</time>
                      <code>{entry.hash.slice(0, 24)}…</code>
                    </li>
                  ))}
                </ul>
                <p className="journey-card__footnote">
                  Merkle seal: {journey.security?.audit?.lastSeal ?? '—'} (SHA3-256)
                </p>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  )
}

function SectionHeader({ title, subtitle }) {
  return (
    <header className="journey-section__header">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </header>
  )
}

function HeroStat({ label, value, helper }) {
  return (
    <div className="journey-hero__stat">
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <small>{helper}</small> : null}
    </div>
  )
}

function ListItem({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

function StageLoading({ stage }) {
  const loading = stageLoadingStates[stage] ?? { message: 'Processing…', caption: '' }
  return (
    <div className="journey-loading">
      <span className="journey-spinner" />
      <div className="journey-loading__copy">
        <strong>{loading.message}</strong>
        {loading.caption ? <span>{loading.caption}</span> : null}
      </div>
      <span className="journey-loading__dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
    </div>
  )
}

function buildIndividualJourneyDemo(source) {
  const submittedAt = source.loanApplication.submittedAt
  const borrower = source.loanApplication.primaryBorrower
  const shiftBy = (minutes) => addMinutesToIso(submittedAt, minutes)

  const lead = {
    leadId: 'lead-individual-20250704-001',
    channel: source.loanApplication.source === 'portal_submission' ? 'Portal' : 'Branch',
    createdAt: submittedAt,
    contact: {
      name: `${borrower.name}`,
      title: 'Micro business owner',
      phone: borrower.phone,
      email: borrower.email,
    },
    productsSuggested: ['Micro 36m', 'Pension-backed top-up'],
    chatbotTranscript: [
      {
        id: 'ind-msg-1',
        actor: 'assistant',
        content: 'Сайн байна уу? Таны санхүүжилтийн зорилго, дүн, хугацааг оруулна уу.',
        timestamp: submittedAt,
      },
      {
        id: 'ind-msg-2',
        actor: 'user',
        content: 'Орон сууцны үлдэгдэл ₮101сая, 36 сар. Хувиараа оёдол хийдэг.',
        timestamp: shiftBy(2),
      },
      {
        id: 'ind-msg-3',
        actor: 'assistant',
        content: 'Баталгаажсан зөвшөөрөл өгснөөр төрийн мэдээллийн сангаас шалгана.',
        timestamp: shiftBy(3),
      },
    ],
  }

  const consentScopes = source.governmentData.items.map((item, index) => ({
    scope: item.id,
    label: item.name,
    status: item.status === 'parsed' ? 'granted' : item.status,
    proof: `/mock/consent/${item.id}.pdf`,
    capturedAt: shiftBy(5 + index),
  }))

  const consents = {
    consentId: 'consent-individual-20250704-001',
    grantedAt: shiftBy(4),
    expiresAt: addMinutesToIso(submittedAt, 60 * 24 * 90),
    scopes: consentScopes,
  }

  const stateMachine = [
    { id: 'PORTAL_SUBMITTED', label: 'Portal submission received', reachedAt: submittedAt, status: 'complete' },
    { id: 'CONSENT_HASHED', label: 'Citizen consent hashed', reachedAt: shiftBy(4), status: 'complete' },
    { id: 'GOV_DATA', label: 'Gov data fetched', reachedAt: shiftBy(8), status: 'complete' },
    { id: 'DOCS_SYNC', label: 'Portal docs ingested', reachedAt: shiftBy(24), status: 'complete' },
    { id: 'CROSSCHECK', label: 'Cross-checks executed', reachedAt: shiftBy(62), status: 'complete' },
    { id: 'RM_HANDOFF', label: 'Decline + coaching tips', reachedAt: source.rmPackage.generatedAt, status: 'complete' },
  ]

  const orchestrator = {
    accuracyScore: source.crossChecks.accuracyScore,
    completenessScore: 0.92,
    currentState: 'RM_HANDOFF',
    startedAt: submittedAt,
    completedAt: source.rmPackage.generatedAt,
    stateMachine,
    events: [
      {
        type: 'portal.submitted',
        at: submittedAt,
        actor: 'portal',
        detail: 'Батзаяа портал дээр хүсэлтээ ирүүлэв.',
      },
      {
        type: 'consent.captured',
        at: shiftBy(4),
        actor: 'consent-vault',
        detail: 'Иргэний лавлагааны зөвшөөрөл хэшлэгдэв.',
      },
      {
        type: 'collector.gov',
        at: shiftBy(8),
        actor: 'collector.gov',
        detail: 'Эд хөрөнгө, хаяг, гэрлэлтийн мэдээлэл татав.',
      },
      {
        type: 'document.uploaded',
        at: shiftBy(24),
        actor: 'portal',
        detail: 'Хоёр банкны хуулга, түрээсийн гэрээ OCR-д орлоо.',
      },
      {
        type: 'crosscheck.run',
        at: shiftBy(62),
        actor: 'crosscheck-service',
        detail: 'Portal vs gov vs банкны мэдээллийг тулгав.',
      },
      {
        type: 'rm.package',
        at: source.rmPackage.generatedAt,
        actor: 'packager',
        detail: 'Decline шийдвэртэй RM багц үүсэв.',
      },
    ],
  }

  const evidenceCollectors = [
    ...source.governmentData.items.map((item, index) => ({
      id: item.id,
      label: item.name,
      confidence: item.confidence ?? 0.95,
      capturedAt: shiftBy(6 + index),
      status: item.status === 'parsed' ? 'passed' : item.status,
      checksum: `${item.id}-gov-hash`,
      parsedFields: item.parsedFields,
      rawProof: { type: 'json', uri: `/mock/evidence/${item.id}.json` },
    })),
    ...source.submittedData.items.map((item, index) => ({
      id: item.id,
      label: item.name,
      confidence: item.confidence ?? 0.9,
      capturedAt: shiftBy(20 + index * 3),
      status: item.status ?? 'verified',
      checksum: `${item.id}-portal-hash`,
      parsedFields: item.claimedFields ?? item.parsedFields ?? item.verification ?? {},
      rawProof: { type: 'pdf', uri: `/mock/portal/${item.id}.pdf` },
    })),
  ]

  const checklist = {
    assignedAt: shiftBy(12),
    items: [
      { id: 'portal-form', label: 'Portal digitized form', required: true, status: 'uploaded' },
      { id: 'gov-fetch', label: 'Gov registry snapshot', required: true, status: 'synced' },
      { id: 'bank-statements', label: '2 банкны хуулга (6 сар)', required: true, status: 'uploaded' },
      { id: 'rent-contract', label: 'Түрээсийн гэрээ OCR', required: true, status: 'uploaded' },
      { id: 'inventory', label: 'Бараа материалын формууд', required: false, status: 'pending' },
      { id: 'co-borrower', label: 'Хамтран зээлдэгчийн мэдээлэл', required: true, status: 'pending' },
    ],
  }

  const uploads = source.submittedData.items.map((item, index) => ({
    id: item.id,
    name: item.name,
    class: inferDocClass(item.id),
    sizeMb: Number((0.8 + index * 0.25).toFixed(1)),
    uploadedAt: shiftBy(20 + index * 3),
    ocr: { confidence: item.ocr?.confidence ?? item.confidence ?? 0.88 },
  }))

  const crossChecks = {
    ...source.crossChecks,
    results: source.crossChecks.results.map((item, index) => ({
      ...item,
      variance: item.variance ?? [0.28, 0.41, 0.33, 0.37, 0.22, 0.05, 0.01, 0][index] ?? 0.2,
    })),
  }

  const analytics = {
    updatedAt: source.rmPackage.generatedAt,
    funnel: [
      { stage: 'Portal', count: 32 },
      { stage: 'Consent', count: 28 },
      { stage: 'Gov Sync', count: 26 },
      { stage: 'Docs Complete', count: 14 },
      { stage: 'RM Handoff', count: 6 },
    ],
    metrics: [
      { id: 'turnaround', label: 'Portal → RM turnaround', value: '29 мин', delta: '+12%' },
      { id: 'gov-hit', label: 'Gov fetch success', value: '100%', delta: '+3%' },
      { id: 'doc-confidence', label: 'OCR ≥0.85 confidence', value: '87%', delta: '-4%' },
      { id: 'manual-review', label: 'Manual review rate', value: '18%', delta: '+5%' },
    ],
    alerts: [
      {
        id: 'income-gap',
        severity: 'high',
        message: 'Portal орлогын мэдүүлэг gov/банк баталгаанаас 25x өндөр байна.',
        openedAt: shiftBy(70),
      },
      {
        id: 'statement-delay',
        severity: 'medium',
        message: 'ХААН банкны хуулга татах Playwright 2 минут удаашрав.',
        openedAt: shiftBy(26),
      },
    ],
  }

  const auditLog = [
    {
      id: 'audit-ind-001',
      at: submittedAt,
      actor: 'portal',
      action: 'Portal submission stored',
      hash: 'batzayaa-portal-001-hash',
    },
    {
      id: 'audit-ind-002',
      at: shiftBy(4),
      actor: 'consent-vault',
      action: 'Citizen consent hashed',
      hash: 'batzayaa-consent-002-hash',
    },
    {
      id: 'audit-ind-003',
      at: shiftBy(20),
      actor: 'document-service',
      action: 'Bank statement OCR complete',
      hash: 'batzayaa-doc-003-hash',
    },
    {
      id: 'audit-ind-004',
      at: source.rmPackage.generatedAt,
      actor: 'packager',
      action: 'RM package generated',
      hash: 'batzayaa-rm-004-hash',
    },
  ]

  return {
    ...source,
    lead,
    consents,
    orchestrator,
    evidence: { collectors: evidenceCollectors },
    checklist,
    documents: { uploads },
    crossChecks,
    analytics,
    auditLog,
  }
}

function addMinutesToIso(isoString, minutes) {
  const base = new Date(isoString)
  if (Number.isNaN(base.getTime())) return isoString
  base.setMinutes(base.getMinutes() + minutes)
  return base.toISOString()
}

function inferDocClass(id) {
  if (id.includes('bank')) return 'bank_statement'
  if (id.includes('rent')) return 'contract'
  if (id.includes('img')) return 'photo'
  if (id.includes('inv')) return 'inventory'
  if (id.includes('meta')) return 'certificate'
  if (id.includes('app')) return 'application'
  return 'document'
}
