import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import softmaxJourney from '../data/softmaxJourney'
import './JourneyDemo.css'

const stageSequence = [
  'leadConsent',
  'timeline',
  'evidence',
  'rules',
  'checklist',
  'documents',
  'cross',
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

const formatArrayField = (value) => {
  if (!value.length) return '—'
  if (typeof value[0] === 'object') {
    return value.map((item) => Object.values(item).join(' ')).join(' / ')
  }
  return value.join(', ')
}

export default function JourneyDemo() {
  const location = useLocation()
  const intakeContext = location.state ?? null

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

  const orchestratorStates = useMemo(
    () => softmaxJourney.orchestrator.stateMachine.map((state) => ({ ...state, reachedAtDate: new Date(state.reachedAt) })),
    [],
  )

  const evidenceCards = useMemo(() => softmaxJourney.evidence.collectors, [])

  const requestAmount = intakeContext?.form?.amount ?? softmaxJourney.intent.amount
  const requestPurpose = intakeContext?.form?.fundingPurpose || softmaxJourney.intent.narrative
  const contactName = intakeContext?.form?.fullName || softmaxJourney.lead.contact.name
  const companyName = intakeContext?.form?.companyName || softmaxJourney.entity.legalName
  const contactPhone = intakeContext?.form?.phone || softmaxJourney.lead.contact.phone
  const contactEmail = intakeContext?.form?.email || softmaxJourney.lead.contact.email
  const productTitle =
    intakeContext?.productTitle || softmaxJourney.rules.productMatch.recommendedProducts[0]?.label || 'Term loan'

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

  const handleStart = () => {
    const hasRunningStage = Object.values(stageStatus).some((status) => status === 'running')
    if (!demoComplete && demoStarted && hasRunningStage) return

    setDemoComplete(false)
    setStageStatus({})
    setActiveStageIndex(-1)
    setTimelineActiveCount(0)
    setProgressPercent(0)
    setDemoStartTime(Date.now())
    setRunId((id) => id + 1)
    setDemoStarted(true)
  }

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
        <div className="journey-hero__chip">Softmax AI × Automated Credit Copilot</div>
        <div className="journey-hero__header">
          <div>
            <h1 className="journey-hero__title">Softmax AI — Fully Automated RM Handoff</h1>
            <p className="journey-hero__subtitle">
              Watch the entire underwriting journey unfold automatically: chatbot lead capture, consent vault, orchestrated data
              collectors, policy rules, document AI, deterministic cross-checks, and the packaged RM dossier.
            </p>
          </div>
          <div className="journey-hero__summary-card">
            <span className="journey-hero__summary-label">Loan request insight</span>
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
          <HeroStat label="Accuracy Score" value={`${Math.round(softmaxJourney.orchestrator.accuracyScore * 100)}%`} />
          <HeroStat label="Completeness" value="100%" helper="All docs QA’d at 0.85+ confidence" />
          <HeroStat
            label="RM contact"
            value={softmaxJourney.entity.relationshipManager.name}
            helper={`${softmaxJourney.entity.relationshipManager.phone} · ${softmaxJourney.entity.relationshipManager.email}`}
          />
          <HeroStat label="Journey length" value="~35 секунд" helper="Automated end-to-end" />
        </div>

        <div className="journey-hero__actions">
          <button
            type="button"
            className="journey-hero__cta"
            onClick={handleStart}
            disabled={!demoComplete && demoStarted && Object.values(stageStatus).some((status) => status === 'running')}
          >
            {demoComplete ? 'Replay Demo' : !demoStarted || Object.keys(stageStatus).length === 0 ? 'Start Demo' : 'Running…'}
          </button>
          <div className="journey-hero__status">
            <span>{demoComplete ? 'All steps automated — ready for RM review.' : runningStageLabel}</span>
            {!demoComplete && <small>{upcomingStageLabel}</small>}
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
                  <ListItem label="Lead ID" value={softmaxJourney.lead.leadId} />
                  <ListItem label="Channel" value="Chatbot → Portal" />
                  <ListItem label="Company" value={`${softmaxJourney.entity.legalName} / ${softmaxJourney.entity.englishName}`} />
                  <ListItem label="BRN" value={softmaxJourney.entity.brn} />
                  <ListItem label="Contact" value={`${contactName}, Санхүү хариуцсан захирал`} />
                  <ListItem label="Phone" value={contactPhone} />
                  <ListItem label="Email" value={contactEmail} />
                  <ListItem label="Suggested products" value={softmaxJourney.lead.productsSuggested.join(', ')} />
                  <ListItem label="Created" value={dateFormatter.format(new Date(softmaxJourney.lead.createdAt))} />
                </dl>
                <div className="journey-transcript">
                  <p className="journey-transcript__label">Chat transcript (excerpt)</p>
                  <ul className="journey-transcript__list">
                    {softmaxJourney.lead.chatbotTranscript.map((message) => (
                      <li key={message.id} className={`journey-transcript__item journey-transcript__item--${message.actor}`}>
                        <span>{message.content}</span>
                        <time>{dateFormatter.format(new Date(message.timestamp))}</time>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.32s' }}>
                <h3 className="journey-card__title">Consent scopes</h3>
                <p className="journey-card__lead">
                  Consent Vault logs every scope, hashes proofs, and attaches consent_id on all downstream calls.
                </p>
                <dl className="journey-list">
                  <ListItem label="Consent ID" value={softmaxJourney.consents.consentId} />
                  <ListItem label="Granted" value={dateFormatter.format(new Date(softmaxJourney.consents.grantedAt))} />
                  <ListItem label="Expires" value={dateFormatter.format(new Date(softmaxJourney.consents.expiresAt))} />
                </dl>
                <div className="journey-consents">
                  {softmaxJourney.consents.scopes.map((scope, index) => (
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
                  {softmaxJourney.orchestrator.events.map((event, index) => (
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
              {evidenceCards.map((collector, index) => (
                <article
                  className="journey-card journey-card--animate"
                  key={collector.id}
                  style={{ animationDelay: `${0.15 + index * 0.12}s` }}
                >
                  <header>
                    <span className="journey-pill journey-pill--pass">Pass</span>
                    <strong>{collector.label}</strong>
                  </header>
                  <dl className="journey-list journey-list--compact">
                    <ListItem label="Captured" value={dateFormatter.format(new Date(collector.capturedAt))} />
                    <ListItem label="Confidence" value={`${Math.round(collector.confidence * 100)}%`} />
                    <ListItem label="Checksum" value={collector.checksum.slice(0, 12)} />
                  </dl>
                  <div className="journey-evidence__fields">
                    {Object.entries(collector.parsedFields).map(([field, value]) => (
                      <div key={field}>
                        <span>{field}</span>
                        <strong>{Array.isArray(value) ? formatArrayField(value) : formatValue(value)}</strong>
                      </div>
                    ))}
                  </div>
                  <span className="journey-link">View raw proof (mock)</span>
                </article>
              ))}
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
                  {softmaxJourney.rules.policyPrequal.rules.map((rule, index) => (
                    <li
                      key={rule.id}
                      className="journey-card--animate"
                      style={{ animationDelay: `${0.26 + index * 0.08}s` }}
                    >
                      <div>
                        <strong>{rule.id}</strong>
                        <span className="journey-pill journey-pill--pass">Pass</span>
                      </div>
                      <p>{rule.evidence}</p>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.34s' }}>
                <h3 className="journey-card__title">Recommended bundle</h3>
                <ul className="journey-product-list">
                  {softmaxJourney.rules.productMatch.recommendedProducts.map((product, index) => (
                    <li
                      key={product.id}
                      className="journey-card--animate"
                      style={{ animationDelay: `${0.42 + index * 0.12}s` }}
                    >
                      <div className="journey-product-list__header">
                        <strong>{product.label}</strong>
                        <span>{currencyFormatter.format(product.limit)}</span>
                      </div>
                      <dl className="journey-list journey-list--compact">
                        <ListItem label="Pricing" value={product.pricingBand} />
                        <ListItem label="DSCR" value={product.dscr.toFixed(2)} />
                        <ListItem label="Collateral" value={product.collateral} />
                        <ListItem label="Notes" value={product.comments} />
                      </dl>
                    </li>
                  ))}
                </ul>
                <div className="journey-rejected journey-card--animate" style={{ animationDelay: '0.68s' }}>
                  <p>Rejected products</p>
                  <ul>
                    {softmaxJourney.rules.productMatch.rejectedProducts.map((entry) => (
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
                  {softmaxJourney.checklist.items.map((item, index) => (
                    <li
                      key={item.id}
                      className={`journey-checklist__item journey-card--animate ${
                        item.status === 'uploaded' ? 'journey-checklist__item--pass' : ''
                      }`}
                      style={{ animationDelay: `${0.26 + index * 0.06}s` }}
                    >
                      <div>
                        <strong>{item.label}</strong>
                        <span>{item.required ? 'Required' : 'Optional'}</span>
                      </div>
                      <span className="journey-pill journey-pill--pass">
                        {item.status === 'uploaded' ? 'Uploaded' : item.status === 'not_required' ? 'Waived' : 'Pending'}
                      </span>
                    </li>
                  ))}
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
                  {softmaxJourney.documents.uploads.map((doc, index) => (
                    <tr key={doc.id} className="journey-card--animate" style={{ animationDelay: `${0.3 + index * 0.08}s` }}>
                      <td>
                        <span>{doc.name}</span>
                        <small>{dateFormatter.format(new Date(doc.uploadedAt))}</small>
                      </td>
                      <td>{doc.class}</td>
                      <td>{doc.sizeMb.toFixed(1)} MB</td>
                      <td>{Math.round(doc.ocr.confidence * 100)}%</td>
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
                {softmaxJourney.crossChecks.results.map((item, index) => (
                  <li key={item.id} className="journey-card--animate" style={{ animationDelay: `${0.28 + index * 0.08}s` }}>
                    <div>
                      <strong>{item.label}</strong>
                      <span className="journey-pill journey-pill--pass">Pass</span>
                    </div>
                    <p>{item.detail}</p>
                    <small>Variance: {formatPercent(item.variance)}</small>
                  </li>
                ))}
              </ul>
              <footer className="journey-card__footer">
                <strong>Accuracy Score:</strong>
                <span>{Math.round(softmaxJourney.crossChecks.accuracyScore * 100)}%</span>
              </footer>
            </div>
          )}
        </section>
      )}

      {stageVisible('rm') && (
        <section ref={assignStageRef.rm} className="journey-section journey-section--animated" aria-live="polite">
          <SectionHeader title="8. RM handoff package" subtitle="Credit 360 dossier with decisions, proofs, and next steps" />
          {stageState('rm') !== 'complete' ? (
            <StageLoading stage="rm" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Decision summary</h3>
                <dl className="journey-list">
                  <ListItem label="Decision" value={softmaxJourney.rmPackage.summary.decision} />
                  <ListItem label="DSCR" value={softmaxJourney.rmPackage.summary.dscr.toFixed(2)} />
                  <ListItem
                    label="Debt capacity"
                    value={currencyFormatter.format(softmaxJourney.rmPackage.summary.debtCapacity)}
                  />
                </dl>
                <div className="journey-tags">
                  {softmaxJourney.rmPackage.summary.riskHighlights.map((note, index) => (
                    <span key={note} className="journey-tag journey-card--animate" style={{ animationDelay: `${0.3 + index * 0.06}s` }}>
                      {note}
                    </span>
                  ))}
                </div>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.32s' }}>
                <h3 className="journey-card__title">Next actions</h3>
                <ul className="journey-next-actions">
                  {softmaxJourney.rmPackage.summary.nextActions.map((task, index) => (
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
          <SectionHeader title="9. Analytics & observability" subtitle="Funnel, SLA, collector health, and exception alerts" />
          {stageState('analytics') !== 'complete' ? (
            <StageLoading stage="analytics" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.18s' }}>
                <h3 className="journey-card__title">Weekly metrics</h3>
                <ul className="journey-metrics">
                  {softmaxJourney.analytics.metrics.map((metric, index) => (
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
                    <span>Updated {dateFormatter.format(new Date(softmaxJourney.analytics.updatedAt))}</span>
                  </header>
                  <ul>
                    {softmaxJourney.analytics.funnel.map((stage) => (
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
                  {softmaxJourney.analytics.alerts.map((alert, index) => (
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
          <SectionHeader title="10. Security & immutable audit" subtitle="RBAC, mTLS, KMS, hash chained events" />
          {stageState('security') !== 'complete' ? (
            <StageLoading stage="security" />
          ) : (
            <div className="journey-grid journey-grid--two">
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.2s' }}>
                <h3 className="journey-card__title">RBAC & encryption</h3>
                <ul className="journey-rbac">
                  {softmaxJourney.security.rbacRoles.map((role, index) => (
                    <li key={role.role} className="journey-card--animate" style={{ animationDelay: `${0.28 + index * 0.08}s` }}>
                      <strong>{role.role}</strong>
                      <span>{role.permissions.join(', ')}</span>
                    </li>
                  ))}
                </ul>
                <dl className="journey-list">
                  <ListItem label="mTLS" value={softmaxJourney.security.encryption.transit} />
                  <ListItem label="Encryption at rest" value={softmaxJourney.security.encryption.atRest} />
                </dl>
              </div>
              <div className="journey-card journey-card--animate" style={{ animationDelay: '0.34s' }}>
                <h3 className="journey-card__title">Immutable audit log</h3>
                <ul className="journey-audit">
                  {softmaxJourney.auditLog.map((entry, index) => (
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
                <p className="journey-card__footnote">Merkle seal: {softmaxJourney.security.audit.lastSeal} (SHA3-256)</p>
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
