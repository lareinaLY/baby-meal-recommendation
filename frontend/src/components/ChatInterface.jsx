/**
 * Chat Interface Component
 * Conversational AI assistant for nutrition questions
 */
import { AlertCircle, Bot, Send, User } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { recommendationAPI } from '../services/api';

export default function ChatInterface({ baby, messages, setMessages }) {
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim() || !baby) return;

        const userMessage = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        // Add user message
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);
        setError(null);

        try {
            // Convert messages to API format
            const conversationHistory = messages.map((msg) => ({
                role: msg.role,
                content: msg.content,
            }));

            // Call chat API
            const response = await recommendationAPI.chat(
                baby.id,
                userMessage.content,
                conversationHistory
            );

            // Add assistant response
            const assistantMessage = {
                role: 'assistant',
                content: response.message,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    if (!baby) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-center text-gray-500">
                    <Bot size={48} className="mx-auto mb-4 text-gray-400" />
                    <p>Select a baby to start chatting</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-white rounded-lg shadow-sm">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">
                    Chat with AI Assistant
                </h2>
                <p className="text-sm text-gray-500">
                    Ask anything about {baby.name}'s nutrition
                </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`flex gap-3 message-enter ${message.role === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                    >
                        {message.role === 'assistant' && (
                            <div className="flex-shrink-0">
                                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                                    <Bot size={18} className="text-primary-600" />
                                </div>
                            </div>
                        )}

                        <div
                            className={`max-w-[80%] rounded-lg px-4 py-3 ${message.role === 'user'
                                    ? 'bg-primary-600 text-white'
                                    : 'bg-gray-100 text-gray-900'
                                }`}
                        >
                            <p className="whitespace-pre-wrap">{message.content}</p>
                            <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-primary-200' : 'text-gray-500'
                                }`}>
                                {message.timestamp.toLocaleTimeString([], {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </div>
                        </div>

                        {message.role === 'user' && (
                            <div className="flex-shrink-0">
                                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                                    <User size={18} className="text-gray-600" />
                                </div>
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                            <Bot size={18} className="text-primary-600" />
                        </div>
                        <div className="bg-gray-100 rounded-lg px-4 py-3">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Error Message */}
            {error && (
                <div className="mx-6 mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                    <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-red-800">{error}</div>
                </div>
            )}

            {/* Input */}
            <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={`Ask about ${baby.name}'s nutrition...`}
                        disabled={loading}
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={!input.trim() || loading}
                        className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                        <Send size={20} />
                        <span className="hidden sm:inline">Send</span>
                    </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                    Press Enter to send, Shift+Enter for new line
                </p>
            </div>
        </div>
    );
}