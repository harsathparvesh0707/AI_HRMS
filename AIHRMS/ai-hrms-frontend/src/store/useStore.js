import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import qwenFormatter from '../services/qwenFormatter';

const useStore = create(
  persist(
    (set, get) => ({
      // Authentication
      isAuthenticated: false,
      user: null,

      login: (userData) =>
        set({
          isAuthenticated: true,
          user: userData,
        }),

      logout: () =>
        set({
          isAuthenticated: false,
          user: null,
          messages: [
            {
              id: 1,
              role: 'assistant',
              content: "Hello! I'm your HR Assistant. How can I help you today?",
              timestamp: new Date(),
            },
          ],
        }),

      // Theme
      theme: 'light',
      colorTheme: 'blue',
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light',
        })),
      setTheme: (theme) => set({ theme }),
      setColorTheme: (colorTheme) => set({ colorTheme }),

      // Dashboard Cards - Optimized with lazy loading
      cards: [
        {
          id: 'attendance',
          title: 'My Attendance',
          type: 'attendance',
          pinned: false,
          size: 'medium',
          data: { hoursWorked: 156, totalHours: 160, percentage: 97.5 },
        },
        {
          id: 'leave-balance',
          title: 'Leave Balance',
          type: 'leave',
          pinned: false,
          size: 'medium',
          data: { available: 12, used: 8, total: 20 },
        },
        // ... other cards (consider reducing initial set for performance)
      ],

      addCard: (card) =>
        set((state) => ({
          cards: [...state.cards, { 
            ...card, 
            id: Date.now().toString(),
            createdAt: new Date().toISOString()
          }],
        })),

      removeCard: (cardId) =>
        set((state) => ({
          cards: state.cards.filter((card) => card.id !== cardId),
        })),

      updateCard: (cardId, updates) =>
        set((state) => ({
          cards: state.cards.map((card) =>
            card.id === cardId ? { ...card, ...updates } : card
          ),
        })),

      togglePin: (cardId) =>
        set((state) => ({
          cards: state.cards.map((card) =>
            card.id === cardId ? { ...card, pinned: !card.pinned } : card
          ),
        })),

      reorderCards: (newCards) => set({ cards: newCards }),

      // API Response Formatting with better error handling
      formatApiResponse: async (data, context = 'dashboard') => {
        try {
          if (!data || typeof data !== 'object') {
            console.warn('Invalid data provided to formatApiResponse');
            return data;
          }
          return await qwenFormatter.formatResponse(data, context);
        } catch (error) {
          console.error('Failed to format API response:', error);
          // Return original data as fallback
          return data;
        }
      },

      // Chat Messages with full CRUD operations
      messages: [
        {
          id: 1,
          role: 'assistant',
          content: "Hello! I'm your HR Assistant. How can I help you today?",
          timestamp: new Date(),
        },
      ],

      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            { 
              ...message, 
              id: Date.now(), 
              timestamp: new Date(),
              // Ensure message has required fields
              role: message.role || 'user',
              content: message.content || ''
            },
          ],
        })),

      updateMessage: (messageId, updates) =>
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === messageId ? { ...msg, ...updates } : msg
          ),
        })),

      deleteMessage: (messageId) =>
        set((state) => ({
          messages: state.messages.filter((msg) => msg.id !== messageId),
        })),

      clearMessages: () =>
        set({
          messages: [
            {
              id: 1,
              role: 'assistant',
              content: "Hello! I'm your HR Assistant. How can I help you today?",
              timestamp: new Date(),
            },
          ],
        }),

      // Chat state
      isChatExpanded: false,
      isTyping: false,
      toggleChat: () =>
        set((state) => ({ isChatExpanded: !state.isChatExpanded })),
      setTyping: (isTyping) => set({ isTyping }),

      // Dynamic UI with better state management
      dynamicLayout: null,
      dynamicData: null,
      isGenerating: false,
      showDynamicUI: false,
      generationError: null,
      
      generateDynamicUI: async (query) => {
        if (!query || query.trim().length === 0) {
          set({ generationError: 'Query cannot be empty' });
          return;
        }

        set({ 
          isGenerating: true, 
          showDynamicUI: true,
          generationError: null 
        });
        
        try {
          console.log('Generating UI for:', query);
          const { data, layout } = await qwenFormatter.searchAndGenerateLayout(query);
          console.log('Search result:', data);
          console.log('Generated layout:', layout);
          
          set({ 
            dynamicLayout: layout,
            dynamicData: data,
            isGenerating: false,
            generationError: null
          });
        } catch (error) {
          console.error('Dynamic UI generation failed:', error);
          
          const fallbackData = {
            data: {
              database_results: {
                select_employees_0: {
                  data: [
                    { 
                      employee_id: 1, 
                      first_name: 'John', 
                      last_name: 'Doe', 
                      email: 'john@example.com', 
                      phone: '123-456-7890', 
                      date_of_joining: '2023-01-15' 
                    },
                    { 
                      employee_id: 2, 
                      first_name: 'Jane', 
                      last_name: 'Smith', 
                      email: 'jane@example.com', 
                      phone: '123-456-7891', 
                      date_of_joining: '2023-02-20' 
                    }
                  ]
                }
              }
            }
          };
          
          const fallbackLayout = {
            layout: {
              type: 'responsive_grid',
              columns: 1,
              gap: '16px',
              components: [
                {
                  type: 'header',
                  title: 'Employee Information (Demo)',
                  subtitle: 'Fallback data due to generation error',
                  style: {
                    gridColumn: 'span 1',
                    background: 'neutral',
                    padding: '16px'
                  }
                },
                {
                  type: 'data_table',
                  title: 'Employees',
                  dataField: 'data.database_results.select_employees_0.data',
                  style: {
                    gridColumn: 'span 1'
                  }
                }
              ]
            },
            dataMapping: {
              employee_id: 'Employee ID',
              first_name: 'First Name',
              last_name: 'Last Name',
              email: 'Email',
              phone: 'Phone',
              date_of_joining: 'Join Date'
            }
          };
          
          set({ 
            dynamicLayout: fallbackLayout,
            dynamicData: fallbackData,
            isGenerating: false,
            generationError: 'Failed to generate dynamic UI. Using demo data.'
          });
        }
      },
      
      hideDynamicUI: () => set({ 
        showDynamicUI: false, 
        dynamicLayout: null, 
        dynamicData: null,
        generationError: null 
      }),

      // Utility function to reset specific parts of state
      resetState: (keys = []) => {
        if (keys.length === 0) {
          // Reset to initial state except auth
          const { isAuthenticated, user, ...initialState } = get();
          set(initialState);
        } else {
          // Reset specific keys
          const resetState = {};
          keys.forEach(key => {
            resetState[key] = get()[key]; // Get initial value
          });
          set(resetState);
        }
      }

    }),
    {
      name: 'hrms-storage',
      version: 4,
      partialize: (state) => ({
        theme: state.theme,
        colorTheme: state.colorTheme,
        cards: state.cards,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        // messages: state.messages, // Added to persist chat history
      }),
      migrate: (persistedState, version) => {
        if (version < 4) {
          return undefined;
        }
        return persistedState;
      },
    }
  )
);

export default useStore;