/*
 * ChatPanel Component - REPLACED WITH GLOBAL SEARCH IN HEADER
 * 
 * Previous Functionality:
 * - Floating chat button with AI assistant interface
 * - Real-time messaging with LLM integration
 * - Quick action buttons for common HR queries
 * - Dynamic UI generation based on user queries
 * - Message history and typing indicators
 * - Voice input capability (Mic button)
 * - Expandable/collapsible chat interface
 * 
 * Key Features Moved to Header Search:
 * - generateDynamicUI() function calls
 * - Query processing and LLM integration
 * - Real-time search with loading states
 * - Direct UI generation without chat interface
 * 
 * Quick Actions Previously Available:
 * - "Show my leave balance" (Calendar icon)
 * - "Show team performance" (TrendingUp icon) 
 * - "Generate monthly report" (FileText icon)
 * 
 * This component is now commented out and replaced with a global search
 * bar in the Header component that provides the same LLM functionality
 * without the conversational interface.
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Mic,
  RotateCcw,
  Sparkles,
  Calendar,
  TrendingUp,
  FileText,
  X,
} from 'lucide-react';
import useStore from '../store/useStore';
import useThemeColors from '../hooks/useThemeColors';

const QuickAction = ({ icon: Icon, label, onClick, colors }) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    className="flex items-center gap-1.5 px-2 py-1.5 bg-gradient-to-r from-purple-600/10 to-pink-600/10 hover:from-purple-600/20 hover:to-pink-600/20 rounded-lg border border-purple-200 dark:border-purple-800 transition-colors text-xs"
  >
    <Icon className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
    <span className="text-gray-700 dark:text-gray-300">{label}</span>
  </motion.button>
);

// COMPONENT COMMENTED OUT - FUNCTIONALITY MOVED TO HEADER SEARCH
const ChatPanel = () => {
  const {
    messages,
    addMessage,
    clearMessages,
    isChatExpanded,
    toggleChat,
    isTyping,
    setTyping,
    generateDynamicUI,
  } = useStore();
  const colors = useThemeColors();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputValue,
    };
    
    const queryToSend = inputValue;
    console.log('ChatPanel: Sending message:', queryToSend);
    addMessage(userMessage);
    setInputValue('');
    setTyping(true);

    // Generate dynamic UI
    try {
      console.log('ChatPanel: Calling generateDynamicUI with:', queryToSend);
      await generateDynamicUI(queryToSend);
      console.log('ChatPanel: generateDynamicUI completed');
      
      // Add dynamic success response based on query
      const getResponseMessage = (query) => {
        const q = query.toLowerCase();
        if (q.includes('show all') || q.includes('list all')) {
          return 'Here are all the employees in the system. The complete list is displayed above.';
        }
        if (q.includes('find') || q.includes('search')) {
          return 'I found the employee(s) matching your search criteria. Results are shown above.';
        }
        if (q.includes('employee') && q.includes('details')) {
          return 'Here are the detailed employee records you requested.';
        }
        if (q.includes('active') || q.includes('status')) {
          return 'I\'ve retrieved the employee status information you requested.';
        }
        return `I've processed your request: "${query}". The results are displayed above.`;
      };
      
      addMessage({
        role: 'assistant',
        content: getResponseMessage(queryToSend),
      });
    } catch (error) {
      console.error('ChatPanel: Error in handleSend:', error);
      addMessage({
        role: 'assistant',
        content: 'Sorry, I couldn\'t process your request. Please try again.',
      });
    } finally {
      setTyping(false);
    }
  };

  const handleQuickAction = (action) => {
    setInputValue(action);
    inputRef.current?.focus();
  };

  return (
    <>
      {/* Floating Chat Button */}
      <AnimatePresence>
        {!isChatExpanded && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={toggleChat}
            className={`fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-r ${colors.gradient} rounded-full shadow-2xl flex items-center justify-center hover:shadow-lg transition-all`}
          >
            <Sparkles className="w-6 h-6 text-white" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Popup */}
      <AnimatePresence>
        {isChatExpanded && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={toggleChat}
              className="fixed inset-0 bg-black/10 z-40"
            />

            {/* Chat Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed bottom-6 right-6 z-50 w-80 h-[480px] bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 flex flex-col overflow-hidden"
            >
              {/* Header */}
              <div className={`flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r ${colors.gradient}`}>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-white" />
                  <h2 className="text-sm font-semibold text-white">HR Assistant</h2>
                </div>
                <div className="flex items-center gap-1.5">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={clearMessages}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <RotateCcw className="w-4 h-4 text-white" />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={toggleChat}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-white" />
                  </motion.button>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="px-3 py-2.5 border-b border-slate-200 dark:border-slate-700 space-y-1.5">
                <p className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                  Quick Actions
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <QuickAction
                    icon={Calendar}
                    label="Leaves"
                    onClick={() => handleQuickAction('Show my leave balance')}
                  />
                  <QuickAction
                    icon={TrendingUp}
                    label="Performance"
                    onClick={() => handleQuickAction('Show team performance')}
                  />
                  <QuickAction
                    icon={FileText}
                    label="Reports"
                    onClick={() => handleQuickAction('Generate monthly report')}
                  />
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-3 py-2.5 space-y-2.5 scrollbar-hide">
                <AnimatePresence>
                  {messages.map((message, index) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`flex ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[85%] rounded-xl px-3 py-1.5 ${
                          message.role === 'user'
                            ? `bg-gradient-to-r ${colors.gradient} text-white`
                            : 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white'
                        }`}
                      >
                        {message.role === 'assistant' && (
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <Sparkles className="w-3 h-3 text-purple-600 dark:text-purple-400" />
                            <span className="text-[10px] font-semibold text-purple-600 dark:text-purple-400">
                              AI Assistant
                            </span>
                          </div>
                        )}
                        <p className="text-xs leading-relaxed">{message.content}</p>
                        <p
                          className={`text-[10px] mt-0.5 ${
                            message.role === 'user'
                              ? 'text-white/70'
                              : 'text-slate-500 dark:text-slate-400'
                          }`}
                        >
                          {new Date(message.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* Typing Indicator */}
                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <div className="bg-slate-100 dark:bg-slate-700 rounded-xl px-3 py-2">
                      <div className="flex gap-1">
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{
                            repeat: Infinity,
                            duration: 0.6,
                            delay: 0,
                          }}
                          className="w-1.5 h-1.5 bg-slate-400 rounded-full"
                        />
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{
                            repeat: Infinity,
                            duration: 0.6,
                            delay: 0.2,
                          }}
                          className="w-1.5 h-1.5 bg-slate-400 rounded-full"
                        />
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{
                            repeat: Infinity,
                            duration: 0.6,
                            delay: 0.4,
                          }}
                          className="w-1.5 h-1.5 bg-slate-400 rounded-full"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="px-3 py-2.5 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-1.5">
                  <div className="flex-1 relative">
                    <input
                      ref={inputRef}
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                      placeholder="Type your message..."
                      className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 text-xs"
                    />
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                  >
                    <Mic className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSend}
                    disabled={!inputValue.trim()}
                    className={`p-2 bg-gradient-to-r ${colors.gradient} rounded-lg disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-shadow`}
                  >
                    <Send className="w-4 h-4 text-white" />
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

// export default ChatPanel; // COMMENTED OUT - REPLACED WITH GLOBAL SEARCH
export default ChatPanel;
