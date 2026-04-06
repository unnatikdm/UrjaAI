import { useState, useRef, useEffect, useCallback } from 'react'
import { chatWithConcierge, getConciergePrompts } from '../services/api'

// Global conversation history that persists across pages
const globalConversationStore = {
    messages: [
        {
            role: 'assistant',
            content: '👋 Hi! I\'m Urja Concierge, your AI energy assistant. Ask me anything about your campus:\n• "How much CO₂ did the Library save today?"\n• "Why is Admin Block at Critical status?"\n• "Give me a 30-second summary of the week"',
            timestamp: Date.now()
        }
    ],
    unreadCount: 0
}

const UrjaConcierge = () => {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState(globalConversationStore.messages)
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [actionablePrompts, setActionablePrompts] = useState([])
    const [unreadCount, setUnreadCount] = useState(globalConversationStore.unreadCount)
    const [hasMinimized, setHasMinimized] = useState(false)
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    // Sync with global store
    useEffect(() => {
        globalConversationStore.messages = messages
        if (!isOpen) {
            globalConversationStore.unreadCount = messages.filter(m =>
                m.role === 'assistant' && m.timestamp > (globalConversationStore.lastOpened || 0)
            ).length
            setUnreadCount(globalConversationStore.unreadCount)
        }
    }, [messages, isOpen])

    // Fetch actionable prompts when opening
    useEffect(() => {
        if (isOpen) {
            fetchActionablePrompts()
            globalConversationStore.lastOpened = Date.now()
            setUnreadCount(0)
            setTimeout(() => inputRef.current?.focus(), 100)
        }
    }, [isOpen])

    const fetchActionablePrompts = async () => {
        try {
            const prompts = await getConciergePrompts()
            setActionablePrompts(prompts.slice(0, 3)) // Max 3 prompts
        } catch (e) {
            // Fallback prompts if API fails
            setActionablePrompts([
                { type: 'alert', text: '🔴 High consumption detected in Hall A. Suggest a Class Consolidation plan?', action: 'consolidate_hall_a' },
                { type: 'suggestion', text: '💡 Library AC could be optimized. View recommendation?', action: 'optimize_library' },
                { type: 'info', text: '🌤️ Hot weather tomorrow. Pre-cool buildings tonight?', action: 'precool_campus' }
            ])
        }
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        if (isOpen) scrollToBottom()
    }, [messages, isOpen])

    const handleSend = useCallback(async (text = input) => {
        if (!text.trim() || isLoading) return

        const userMessage = text.trim()
        setInput('')

        // Add user message
        setMessages(prev => [...prev, {
            role: 'user',
            content: userMessage,
            timestamp: Date.now()
        }])
        setIsLoading(true)

        try {
            // Get recent context (last 10 messages)
            const recentContext = messages.slice(-10).map(m => ({
                role: m.role,
                content: m.content
            }))

            const response = await chatWithConcierge(userMessage, recentContext)

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.response,
                actionablePrompt: response.suggested_action || null,
                sources: response.sources || [],
                timestamp: Date.now()
            }])

            // If there's a suggested action, refresh prompts
            if (response.suggested_action) {
                fetchActionablePrompts()
            }
        } catch (error) {
            console.error('Concierge error:', error)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '⚠️ I\'m having trouble connecting to the energy brain. Let me try again...',
                isError: true,
                timestamp: Date.now()
            }])
        } finally {
            setIsLoading(false)
        }
    }, [input, isLoading, messages])

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    const handlePromptClick = (prompt) => {
        handleSend(prompt.text)
    }

    const handleQuickAction = (action) => {
        const actionMessages = {
            consolidate_hall_a: 'Can you create a Class Consolidation plan for Hall A?',
            optimize_library: 'What optimization do you suggest for Library AC?',
            precool_campus: 'Should we pre-cool buildings tonight for tomorrow\'s heat?'
        }
        handleSend(actionMessages[action] || 'Tell me more about this.')
    }

    const toggleChat = () => {
        setIsOpen(!isOpen)
        setHasMinimized(true)
    }

    // Format message with markdown-like styling
    const formatMessage = (content) => {
        return content.split('**').map((part, i) =>
            i % 2 === 0 ? part : <strong key={i} className="font-semibold text-emerald-700">{part}</strong>
        )
    }

    return (
        <>
            {/* Floating Chat Bubble */}
            <button
                onClick={toggleChat}
                className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center transition-all duration-300 hover:scale-110 active:scale-95 ${
                    isOpen
                        ? 'bg-emerald-600 rotate-90'
                        : 'bg-gradient-to-br from-emerald-500 to-teal-600 hover:shadow-emerald-500/30'
                }`}
                aria-label={isOpen ? 'Close chat' : 'Open Urja Concierge'}
            >
                {isOpen ? (
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                ) : (
                    <>
                        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        {unreadCount > 0 && (
                            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
                                {unreadCount}
                            </span>
                        )}
                    </>
                )}
            </button>

            {/* Glassmorphic Chat Window */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 z-50 w-[400px] max-w-[calc(100vw-3rem)] animate-fadeIn">
                    {/* Glassmorphic Container */}
                    <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/50 overflow-hidden">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-emerald-500/90 to-teal-600/90 backdrop-blur-sm p-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 className="font-bold text-white">Urja Concierge</h3>
                                    <p className="text-xs text-emerald-100">Your AI Energy Assistant</p>
                                </div>
                                <div className="ml-auto flex items-center gap-2">
                                    <span className="w-2 h-2 bg-emerald-300 rounded-full animate-pulse" />
                                    <span className="text-xs text-emerald-100">Online</span>
                                </div>
                            </div>
                        </div>

                        {/* Actionable Prompts */}
                        {actionablePrompts.length > 0 && (
                            <div className="px-4 py-3 bg-emerald-50/50 border-b border-emerald-100">
                                <p className="text-xs font-semibold text-emerald-700 mb-2">🎯 Suggested Actions</p>
                                <div className="space-y-2">
                                    {actionablePrompts.map((prompt, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => handleQuickAction(prompt.action)}
                                            className="w-full text-left p-2.5 bg-white/70 hover:bg-emerald-100/50 rounded-xl text-sm text-emerald-800 transition-all duration-200 border border-emerald-100/50 hover:border-emerald-200 flex items-start gap-2 group"
                                        >
                                            <span className="text-lg">{prompt.text.match(/^[🟢🔴💡🌤️⚡💰🌱🎯]/)?.[0] || '💡'}</span>
                                            <span className="flex-1">{prompt.text.replace(/^[🟢🔴💡🌤️⚡💰🌱🎯]\s*/, '')}</span>
                                            <svg className="w-4 h-4 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Messages */}
                        <div className="h-80 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-emerald-50/20 to-transparent">
                            {messages.map((message, idx) => (
                                <div key={idx} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[85%] rounded-2xl p-3.5 ${
                                        message.role === 'user'
                                            ? 'bg-emerald-600 text-white rounded-br-md shadow-md'
                                            : message.isError
                                                ? 'bg-red-50 text-red-700 rounded-bl-md border border-red-100'
                                                : 'bg-white/90 text-slate-700 rounded-bl-md shadow-sm border border-emerald-100/50 backdrop-blur-sm'
                                    }`}>
                                        {/* Avatar for assistant */}
                                        {message.role === 'assistant' && !message.isError && (
                                            <div className="flex items-center gap-2 mb-1.5">
                                                <div className="w-5 h-5 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center">
                                                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                    </svg>
                                                </div>
                                                <span className="text-xs font-medium text-emerald-600">Urja</span>
                                            </div>
                                        )}
                                        <div className="text-sm leading-relaxed whitespace-pre-wrap">
                                            {formatMessage(message.content)}
                                        </div>
                                        {/* Actionable prompt from response */}
                                        {message.actionablePrompt && (
                                            <button
                                                onClick={() => handleSend(`Yes, let's do that.`)}
                                                className="mt-2 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-700 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5"
                                            >
                                                <span>{message.actionablePrompt.label}</span>
                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                            </button>
                                        )}
                                        {/* Sources */}
                                        {message.sources && message.sources.length > 0 && (
                                            <div className="mt-2 pt-2 border-t border-emerald-100/50">
                                                <p className="text-[10px] text-emerald-600/70">
                                                    Sources: {message.sources.join(', ')}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-white/90 rounded-2xl rounded-bl-md p-4 border border-emerald-100/50 backdrop-blur-sm">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <div className="w-2 h-2 bg-emerald-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                            <span className="text-xs text-emerald-600 ml-1">Analyzing energy data...</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <div className="p-4 bg-white/90 backdrop-blur-sm border-t border-emerald-100">
                            <div className="flex gap-2">
                                <input
                                    ref={inputRef}
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Ask about CO₂, alerts, summaries..."
                                    className="flex-1 px-4 py-3 bg-emerald-50/50 border border-emerald-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-300 placeholder:text-emerald-400/60 transition-all"
                                    disabled={isLoading}
                                />
                                <button
                                    onClick={() => handleSend()}
                                    disabled={isLoading || !input.trim()}
                                    className="px-4 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl hover:from-emerald-600 hover:to-teal-700 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                </button>
                            </div>
                            <p className="text-[10px] text-emerald-500/60 mt-2 text-center">
                                Press Enter to send • Powered by RAG + LLM
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

export default UrjaConcierge
