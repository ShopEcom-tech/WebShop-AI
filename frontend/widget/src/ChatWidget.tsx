import { useState, useRef, useEffect, FormEvent } from 'react'
import './ChatWidget.css'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

interface ChatWidgetProps {
    apiUrl?: string
    position?: 'bottom-right' | 'bottom-left'
    primaryColor?: string
    title?: string
    subtitle?: string
    placeholder?: string
}

const generateId = () => Math.random().toString(36).substring(2, 15)
const getSessionId = () => {
    let sessionId = localStorage.getItem('webshop_chat_session')
    if (!sessionId) {
        sessionId = generateId()
        localStorage.setItem('webshop_chat_session', sessionId)
    }
    return sessionId
}

export default function ChatWidget({
    apiUrl = 'http://localhost:3000/api/chat',
    position = 'bottom-right',
    primaryColor = '#a855f7',
    title = 'Assistant Web Shop',
    subtitle = 'En ligne • Répond instantanément',
    placeholder = 'Écrivez votre message...'
}: ChatWidgetProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [isTyping, setIsTyping] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100)
        }
    }, [isOpen])

    // Welcome message
    useEffect(() => {
        if (isOpen && messages.length === 0) {
            setMessages([{
                id: generateId(),
                role: 'assistant',
                content: 'Bonjour ! 👋 Je suis l\'assistant de Web Shop. Comment puis-je vous aider aujourd\'hui ?',
                timestamp: new Date()
            }])
        }
    }, [isOpen, messages.length])

    const sendMessage = async (e: FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage: Message = {
            id: generateId(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setInput('')
        setIsLoading(true)
        setIsTyping(true)

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage.content,
                    sessionId: getSessionId(),
                    language: 'fr'
                })
            })

            const data = await response.json()

            // Simulate typing delay for natural feel
            await new Promise(resolve => setTimeout(resolve, 500))

            if (data.success) {
                setMessages(prev => [...prev, {
                    id: generateId(),
                    role: 'assistant',
                    content: data.data.message,
                    timestamp: new Date()
                }])
            } else {
                throw new Error(data.error || 'Erreur inconnue')
            }
        } catch (error) {
            setMessages(prev => [...prev, {
                id: generateId(),
                role: 'assistant',
                content: 'Désolé, je rencontre un problème technique. Veuillez réessayer dans quelques instants.',
                timestamp: new Date()
            }])
        } finally {
            setIsLoading(false)
            setIsTyping(false)
        }
    }

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    }

    return (
        <div className={`chat-widget ${position}`}>
            {/* Chat Window */}
            <div className={`chat-window ${isOpen ? 'open' : ''}`}>
                {/* Header */}
                <div className="chat-header" style={{ background: `linear-gradient(135deg, ${primaryColor}, #ec4899)` }}>
                    <div className="chat-header-info">
                        <div className="chat-avatar">
                            <div className="avatar-icon">🤖</div>
                            <span className="status-dot"></span>
                        </div>
                        <div className="chat-header-text">
                            <h3>{title}</h3>
                            <p>{subtitle}</p>
                        </div>
                    </div>
                    <button className="chat-close" onClick={() => setIsOpen(false)}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 6L6 18M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Messages */}
                <div className="chat-messages">
                    {messages.map(msg => (
                        <div key={msg.id} className={`message ${msg.role}`}>
                            <div className="message-bubble">
                                <p>{msg.content}</p>
                                <span className="message-time">{formatTime(msg.timestamp)}</span>
                            </div>
                        </div>
                    ))}

                    {isTyping && (
                        <div className="message assistant">
                            <div className="message-bubble typing">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <form className="chat-input" onSubmit={sendMessage}>
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder={placeholder}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        style={{ background: `linear-gradient(135deg, ${primaryColor}, #ec4899)` }}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                        </svg>
                    </button>
                </form>

                {/* Powered by */}
                <div className="chat-powered">
                    Propulsé par <strong>WebShop-AI</strong>
                </div>
            </div>

            {/* Toggle Button */}
            <button
                className={`chat-toggle ${isOpen ? 'hidden' : ''}`}
                onClick={() => setIsOpen(true)}
                style={{ background: `linear-gradient(135deg, ${primaryColor}, #ec4899)` }}
            >
                <div className="toggle-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                    </svg>
                </div>
                <span className="toggle-pulse"></span>
            </button>
        </div>
    )
}
