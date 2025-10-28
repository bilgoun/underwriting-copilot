import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { Loader2, SendHorizontal } from 'lucide-react'
import { chatApi } from '../api/client'
import MarkdownRenderer from './MarkdownRenderer'

type ChatRole = 'user' | 'assistant'

type UiMessage = {
  id: string
  role: ChatRole
  content: string
  state?: 'pending' | 'error'
}

const backgroundColor = '#131314'
const bubbleUser = '#343541'
const textPrimary = '#ececf1'
const accent = '#4a8ef4'
const shellWidth = 'min(780px, calc(100% - 2.5rem))'

const LoadingDots = () => (
  <span className="loan-chat-dots" role="status" aria-label="Processing response" style={{ color: accent }}>
    <span className="loan-chat-dot" />
    <span className="loan-chat-dot" />
    <span className="loan-chat-dot" />
  </span>
)

const pageStyle: CSSProperties = {
  minHeight: '100vh',
  width: '100%',
  background: backgroundColor,
  color: textPrimary,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
}

const contentShellStyle = (hasConversation: boolean): CSSProperties => ({
  flex: 1,
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: hasConversation ? 'flex-start' : 'center',
  paddingTop: hasConversation ? '6rem' : '0',
  paddingBottom: hasConversation ? '9rem' : '12rem',
  gap: hasConversation ? '1.75rem' : '2.5rem',
})

const heroHeadingStyle: CSSProperties = {
  fontSize: '2.6rem',
  fontWeight: 600,
  letterSpacing: '-0.01em',
  textAlign: 'center',
  color: textPrimary,
}

const inputWrapperStyle = (placement: 'hero' | 'chat'): CSSProperties => ({
  width: '100%',
  display: 'flex',
  justifyContent: 'center',
  padding: placement === 'chat' ? '0 1.5rem 2.5rem' : 0,
  marginTop: placement === 'hero' ? '1.5rem' : 0,
})

const inputShellStyle: CSSProperties = {
  width: shellWidth,
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
  background: '#202123',
  borderRadius: '999px',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  boxShadow: '0 18px 38px rgba(0, 0, 0, 0.35)',
  padding: '0.75rem 1rem',
}

const textareaStyle: CSSProperties = {
  flex: 1,
  border: 'none',
  resize: 'none',
  background: 'transparent',
  color: textPrimary,
  fontSize: '1rem',
  lineHeight: 1.5,
  outline: 'none',
  maxHeight: '200px',
  minHeight: '24px',
}

const sendButtonStyle = (disabled: boolean): CSSProperties => ({
  width: '38px',
  height: '38px',
  borderRadius: '50%',
  border: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: disabled ? 'rgba(255, 255, 255, 0.08)' : accent,
  color: disabled ? 'rgba(236, 236, 241, 0.4)' : '#ffffff',
  cursor: disabled ? 'not-allowed' : 'pointer',
  transition: 'background 0.2s ease, color 0.2s ease',
})

const messagesContainerStyle: CSSProperties = {
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '1.75rem',
  padding: '0 1.5rem',
}

const messageRowStyle = (role: ChatRole): CSSProperties => ({
  width: shellWidth,
  display: 'flex',
  justifyContent: role === 'assistant' ? 'flex-start' : 'flex-end',
})

const userMessageBubbleStyle: CSSProperties = {
  background: bubbleUser,
  color: textPrimary,
  borderRadius: '18px',
  padding: '1.15rem 1.35rem',
  fontSize: '1rem',
  lineHeight: 1.65,
  maxWidth: '100%',
  boxShadow: '0 16px 30px rgba(0, 0, 0, 0.35)',
  whiteSpace: 'pre-wrap',
}

const assistantMessageStyle = (state?: UiMessage['state']): CSSProperties => ({
  color: state === 'error' ? '#fca5a5' : textPrimary,
  fontSize: '1rem',
  lineHeight: 1.65,
  maxWidth: '100%',
  opacity: state === 'pending' ? 0.7 : 1,
})

export default function LoanAssistantChat() {
  const [messages, setMessages] = useState<UiMessage[]>([])
  const [draft, setDraft] = useState('')
  const [isSending, setIsSending] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const scrollAnchorRef = useRef<HTMLDivElement | null>(null)

  const hasConversation = messages.length > 0

  useEffect(() => {
    if (!textareaRef.current) return
    textareaRef.current.style.height = 'auto'
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
  }, [draft])

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async () => {
    const trimmed = draft.trim()
    if (!trimmed || isSending) return

    const history = messages
      .filter((message) => !message.state)
      .map(({ role, content }) => ({ role, content }))

    const userMessage: UiMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
    }

    const placeholderId = `assistant-${Date.now()}`
    const placeholder: UiMessage = {
      id: placeholderId,
      role: 'assistant',
      content: '',
      state: 'pending',
    }

    setMessages((prev) => [...prev, userMessage, placeholder])
    setDraft('')
    setIsSending(true)

    try {
      const { reply } = await chatApi.sendLoanAssistant([...history, { role: 'user', content: trimmed }])
      setMessages((prev) =>
        prev.map((message) =>
          message.id === placeholderId
            ? { id: placeholderId, role: 'assistant', content: reply.trim() }
            : message,
        ),
      )
    } catch (error) {
      console.error('Loan assistant error', error)
      setMessages((prev) =>
        prev.map((message) =>
          message.id === placeholderId
            ? {
                ...message,
                content: 'Уучлаарай, түр алдаа гарлаа. Дахин оролдоод үзнэ үү.',
                state: 'error',
              }
            : message,
        ),
      )
    } finally {
      setIsSending(false)
    }
  }

  const renderInput = (placement: 'hero' | 'chat') => (
    <div style={inputWrapperStyle(placement)}>
      <div style={inputShellStyle}>
        <textarea
          ref={textareaRef}
          style={textareaStyle}
          rows={1}
          placeholder="Ask anything"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              handleSubmit()
            }
          }}
        />
        <button
          type="button"
          style={sendButtonStyle(isSending || !draft.trim())}
          onClick={handleSubmit}
          disabled={isSending || !draft.trim()}
          aria-label="Send message"
        >
          {isSending ? <Loader2 size={18} /> : <SendHorizontal size={18} />}
        </button>
      </div>
    </div>
  )

  return (
    <div style={pageStyle}>
      <div style={contentShellStyle(hasConversation)}>
        {!hasConversation && (
          <>
            <h1 style={heroHeadingStyle}>Бизнесийн зээлийн талаар хүссэнээ асуугаарай</h1>
            {renderInput('hero')}
          </>
        )}

        {hasConversation && (
          <div style={messagesContainerStyle}>
            {messages.map((message) => (
              <div key={message.id} style={messageRowStyle(message.role)}>
                {message.role === 'assistant' ? (
                  <div style={assistantMessageStyle(message.state)}>
                    {message.state === 'pending' ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', minHeight: '32px' }}>
                        <LoadingDots />
                      </span>
                    ) : (
                      <MarkdownRenderer
                        markdown={message.content}
                        color={message.state === 'error' ? '#fca5a5' : textPrimary}
                      />
                    )}
                  </div>
                ) : (
                  <div style={userMessageBubbleStyle}>{message.content}</div>
                )}
              </div>
            ))}
            <div ref={scrollAnchorRef} />
          </div>
        )}
      </div>

      {hasConversation && (
        <>
          {renderInput('chat')}
        </>
      )}
    </div>
  )
}
