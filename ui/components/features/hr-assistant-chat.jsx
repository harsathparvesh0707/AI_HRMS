import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, MessageCircle } from 'lucide-react';
import { processHRQuery } from '@/lib/hr-assistant';
import { Button } from '../ui/button';

export default function HRAssistantChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content: "Hello! I'm your HR Assistant. I can help you with employee information, project details, leave balances, skills analysis, and department insights. What would you like to know?",
      isBot: true
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now(),
      content: input,
      isBot: false
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    setTimeout(async () => {
      try {
        const result = await processHRQuery(input);
        
        const botMessage = {
          id: Date.now() + 1,
          content: result.response,
          isBot: true
        };

        setMessages(prev => [...prev, botMessage]);
      } catch (error) {
        const errorMessage = {
          id: Date.now() + 1,
          content: "Sorry, I encountered an error. Please try again.",
          isBot: true
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }, 500);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed top-3 left-2 w-[95%] h-[97%] flex flex-col rounded-2xl shadow-2xl bg-background overflow-hidden z-50" data-chat-window>
      <div className="flex items-center justify-between gap-2 p-4 border-b bg-indigo-500   text-primary-foreground">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5" />
          <h3 className="font-semibold">HR Assistant</h3>
        </div>
        {/* {isMobile && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-primary-foreground hover:bg-indigo-500"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close chat</span>
          </Button>
        )} */}
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-2 ${message.isBot ? 'justify-start' : 'justify-end'}`}>
            {message.isBot && (
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3 h-3 text-blue-600" />
              </div>
            )}
            
            <div className={`max-w-[80%] p-2 rounded-lg text-sm ${
              message.isBot ? 'bg-gray-100 text-gray-800' : 'bg-blue-600 text-white'
            }`}>
              {message.content}
            </div>

            {!message.isBot && (
              <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                <User className="w-3 h-3 text-white" />
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-2 justify-start">
            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
              <Bot className="w-3 h-3 text-blue-600" />
            </div>
            <div className="bg-gray-100 p-2 rounded-lg">
              <div className="flex gap-1">
                <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about employees, projects, skills..."
            className="flex-1 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50 text-sm"
          >
            <Send className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}
