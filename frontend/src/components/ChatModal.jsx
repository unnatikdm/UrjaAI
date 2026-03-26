import { useState, useRef, useEffect } from 'react'
import { chatWithRecommendationAI } from '../services/api'

// Store chat histories per recommendation (keyed by action + building_id)
const chatHistoryStore = new Map()

const ChatModal = ({ isOpen, onClose, recommendation }) => {
    // Get unique key for this recommendation
    const getRecKey = () => {
        if (!recommendation) return null
        return `${recommendation.building_id || 'unknown'}-${recommendation.action?.slice(0, 50) || 'unknown'}`
    }
    
    // Get initial messages for this recommendation
    const getInitialMessages = () => {
        const key = getRecKey()
        if (key && chatHistoryStore.has(key)) {
            return chatHistoryStore.get(key)
        }
        return [
            { role: 'assistant', content: 'Hi! I can help you understand this recommendation better. Ask me things like:\n• "What if I increase temperature by 3°C?"\n• "How much will this save me?"\n• "Why is this recommended for night time?"' }
        ]
    }
    
    const [messages, setMessages] = useState(getInitialMessages())
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef(null)

    // Reset messages when recommendation changes
    useEffect(() => {
        if (isOpen && recommendation) {
            setMessages(getInitialMessages())
        }
    }, [isOpen, recommendation?.action, recommendation?.building_id])

    // Save messages to store when they change
    useEffect(() => {
        const key = getRecKey()
        if (key && messages.length > 0) {
            chatHistoryStore.set(key, messages)
        }
    }, [messages])

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async () => {
        if (!input.trim() || isLoading) return

        const userMessage = input.trim()
        setInput('')
        
        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: userMessage }])
        setIsLoading(true)

        try {
            // Build chat history for API - include all previous messages except the new one we just added
            const chatHistory = messages
                .slice(1) // Skip welcome message for API
                .map(m => ({ role: m.role, content: m.content }))

            const response = await chatWithRecommendationAI(
                recommendation,
                userMessage,
                chatHistory
            )

            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: response.response,
                sources: response.sources
            }])
        } catch (error) {
            console.error('Chat error:', error)
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: 'Sorry, I encountered an error. Please try again.' 
            }])
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-border">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="font-bold text-ink">Recommendation AI</h3>
                                <p className="text-xs text-ink-muted">Powered by RAG Pipeline</p>
                            </div>
                        </div>
                        <button 
                            onClick={onClose}
                            className="p-2 hover:bg-beige rounded-lg transition-colors"
                        >
                            <svg className="w-5 h-5 text-ink-soft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    
                    {/* Recommendation Context */}
                    <div className="mt-4 p-4 bg-beige/50 rounded-xl border border-border-subtle">
                        <p className="text-sm font-semibold text-ink">Current Recommendation:</p>
                        <p className="text-sm text-ink-soft mt-1">{recommendation?.action}</p>
                        <div className="flex gap-4 mt-2 text-xs text-ink-muted">
                            <span>⚡ {recommendation?.savings_kwh} kWh savings</span>
                            <span>💰 ₹{recommendation?.savings_cost_inr?.toFixed(0)}</span>
                            <span className={`capitalize ${
                                recommendation?.priority === 'high' ? 'text-red-600' :
                                recommendation?.priority === 'medium' ? 'text-orange-600' :
                                'text-blue-600'
                            }`}>{recommendation?.priority} priority</span>
                        </div>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.map((message, idx) => (
                        <div key={idx} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] rounded-2xl p-4 ${
                                message.role === 'user' 
                                    ? 'bg-primary text-white rounded-br-md' 
                                    : 'bg-beige/50 text-ink rounded-bl-md border border-border-subtle'
                            }`}>
                                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                                    {message.content.split('**').map((part, i) => 
                                        i % 2 === 0 ? part : <strong key={i} className="font-bold">{part}</strong>
                                    )}
                                </div>
                                {message.sources && message.sources.length > 0 && (
                                    <div className="mt-2 pt-2 border-t border-border-subtle/50">
                                        <p className="text-xs text-ink-muted">Sources: {message.sources.join(', ')}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-beige/50 rounded-2xl rounded-bl-md p-4 border border-border-subtle">
                                <div className="flex items-center gap-2 text-ink-muted">
                                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    <span className="text-xs ml-2">AI is thinking...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-6 border-t border-border">
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about this recommendation..."
                            className="flex-1 px-4 py-3 bg-beige/50 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="px-4 py-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                    <p className="text-xs text-ink-faint mt-2 text-center">
                        Press Enter to send • Shift+Enter for new line
                    </p>
                </div>
            </div>
        </div>
    )
}

export default ChatModal
