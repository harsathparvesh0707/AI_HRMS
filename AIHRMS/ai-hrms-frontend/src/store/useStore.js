import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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
      colorTheme: 'blue', // blue, indigo, green, red, slate, orange
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light',
        })),
      setTheme: (theme) => set({ theme }),
      setColorTheme: (colorTheme) => set({ colorTheme }),

      // Dashboard Cards
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
        {
          id: 'team-performance',
          title: 'Team Performance',
          type: 'chart',
          pinned: false,
          size: 'wide',
          data: {
            series: [
              { month: 'Jan', value: 85 },
              { month: 'Feb', value: 88 },
              { month: 'Mar', value: 92 },
              { month: 'Apr', value: 90 },
              { month: 'May', value: 95 },
            ],
          },
        },
        {
          id: 'announcements',
          title: 'Announcements',
          type: 'announcements',
          pinned: false,
          size: 'tall',
          data: {
            items: [
              {
                id: 1,
                text: 'Company-wide meeting scheduled for next Monday',
                date: '2025-10-10',
              },
              {
                id: 2,
                text: 'New health insurance policy updates available',
                date: '2025-10-08',
              },
              {
                id: 3,
                text: 'Q4 performance reviews starting next week',
                date: '2025-10-07',
              },
            ],
          },
        },
        {
          id: 'recruitment',
          title: 'Recruitment Pipeline',
          type: 'recruitment',
          pinned: false,
          size: 'wide',
          data: {
            stages: [
              { name: 'Applied', count: 45 },
              { name: 'Screening', count: 28 },
              { name: 'Interview', count: 12 },
              { name: 'Offer', count: 5 },
            ],
            total: 90,
          },
        },
        {
          id: 'payroll',
          title: 'Payroll Summary',
          type: 'payroll',
          pinned: false,
          size: 'medium',
          data: {
            current: '$125,450',
            previous: '$118,200',
            change: 6.1,
            employees: 45,
          },
        },
        {
          id: 'team-members',
          title: 'Team Members',
          type: 'team',
          pinned: false,
          size: 'tall',
          data: {
            members: [
              { id: 1, name: 'Sarah Johnson', role: 'Senior Developer', status: 'active', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah' },
              { id: 2, name: 'Mike Chen', role: 'Product Manager', status: 'active', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike' },
              { id: 3, name: 'Emily Davis', role: 'UX Designer', status: 'leave', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily' },
              { id: 4, name: 'Alex Kumar', role: 'Backend Developer', status: 'active', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex' },
              { id: 5, name: 'Lisa Wang', role: 'QA Engineer', status: 'active', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Lisa' },
            ],
          },
        },
        {
          id: 'pending-approvals',
          title: 'Pending Approvals',
          type: 'approvals',
          pinned: false,
          size: 'medium',
          data: {
            items: [
              { type: 'Leave', count: 8 },
              { type: 'Expense', count: 12 },
              { type: 'Timesheet', count: 5 },
            ],
            total: 25,
          },
        },
        {
          id: 'department-overview',
          title: 'Department Overview',
          type: 'department',
          pinned: false,
          size: 'wide',
          data: {
            departments: [
              { name: 'Engineering', count: 45, color: '#3b82f6' },
              { name: 'Sales', count: 28, color: '#10b981' },
              { name: 'Marketing', count: 18, color: '#f59e0b' },
              { name: 'HR', count: 12, color: '#8b5cf6' },
              { name: 'Finance', count: 15, color: '#ec4899' },
            ],
            total: 118,
          },
        },
        {
          id: 'training',
          title: 'Training & Development',
          type: 'training',
          pinned: false,
          size: 'medium',
          data: {
            completed: 24,
            ongoing: 8,
            upcoming: 5,
            completionRate: 75,
          },
        },
        {
          id: 'quick-stats',
          title: 'Quick Stats',
          type: 'stats',
          pinned: false,
          size: 'wide',
          data: {
            metrics: [
              { label: 'Total Employees', value: '118', change: '+5', trend: 'up' },
              { label: 'Avg Tenure', value: '3.2 yrs', change: '+0.3', trend: 'up' },
              { label: 'Turnover Rate', value: '8.5%', change: '-2.1', trend: 'down' },
              { label: 'Open Positions', value: '12', change: '+3', trend: 'up' },
            ],
          },
        },
        {
          id: 'upcoming-holidays',
          title: 'Upcoming Holidays',
          type: 'holidays',
          pinned: false,
          size: 'medium',
          data: {
            holidays: [
              { name: 'Veterans Day', date: '2025-11-11' },
              { name: 'Thanksgiving', date: '2025-11-27' },
              { name: 'Christmas', date: '2025-12-25' },
            ],
          },
        },
        {
          id: 'employee-list',
          title: 'Employee Directory',
          type: 'employee-list',
          pinned: false,
          size: 'large',
          data: {
            employees: [
              { id: 1, name: 'Sarah Johnson', department: 'Engineering', position: 'Senior Developer', email: 'sarah.j@company.com', status: 'Active', joinDate: '2022-01-15' },
              { id: 2, name: 'Mike Chen', department: 'Product', position: 'Product Manager', email: 'mike.c@company.com', status: 'Active', joinDate: '2021-06-20' },
              { id: 3, name: 'Emily Davis', department: 'Design', position: 'UX Designer', email: 'emily.d@company.com', status: 'On Leave', joinDate: '2022-03-10' },
              { id: 4, name: 'Alex Kumar', department: 'Engineering', position: 'Backend Developer', email: 'alex.k@company.com', status: 'Active', joinDate: '2023-02-01' },
              { id: 5, name: 'Lisa Wang', department: 'QA', position: 'QA Engineer', email: 'lisa.w@company.com', status: 'Active', joinDate: '2022-08-15' },
              { id: 6, name: 'James Wilson', department: 'Sales', position: 'Sales Manager', email: 'james.w@company.com', status: 'Active', joinDate: '2020-11-05' },
              { id: 7, name: 'Maria Garcia', department: 'Marketing', position: 'Marketing Lead', email: 'maria.g@company.com', status: 'Active', joinDate: '2021-09-12' },
              { id: 8, name: 'David Brown', department: 'Engineering', position: 'Frontend Developer', email: 'david.b@company.com', status: 'Active', joinDate: '2023-01-20' },
            ],
            filters: ['All', 'Engineering', 'Sales', 'Marketing', 'Active', 'On Leave'],
          },
        },
        {
          id: 'leave-requests',
          title: 'Recent Leave Requests',
          type: 'leave-requests',
          pinned: false,
          size: 'wide',
          data: {
            requests: [
              { id: 1, employee: 'Sarah Johnson', type: 'Annual Leave', from: '2025-10-15', to: '2025-10-18', days: 4, status: 'Pending' },
              { id: 2, employee: 'Mike Chen', type: 'Sick Leave', from: '2025-10-12', to: '2025-10-13', days: 2, status: 'Approved' },
              { id: 3, employee: 'Emily Davis', type: 'Personal Leave', from: '2025-10-20', to: '2025-10-22', days: 3, status: 'Pending' },
              { id: 4, employee: 'Alex Kumar', type: 'Annual Leave', from: '2025-11-01', to: '2025-11-05', days: 5, status: 'Approved' },
            ],
          },
        },
        {
          id: 'performance-reviews',
          title: 'Performance Reviews',
          type: 'performance-list',
          pinned: false,
          size: 'wide',
          data: {
            reviews: [
              { id: 1, employee: 'Sarah Johnson', reviewer: 'John Doe', score: 4.5, status: 'Completed', date: '2025-09-15' },
              { id: 2, employee: 'Mike Chen', reviewer: 'Jane Smith', score: 4.8, status: 'Completed', date: '2025-09-20' },
              { id: 3, employee: 'Emily Davis', reviewer: 'John Doe', score: 4.2, status: 'In Progress', date: '2025-10-01' },
              { id: 4, employee: 'Alex Kumar', reviewer: 'Jane Smith', score: null, status: 'Pending', date: '2025-10-15' },
            ],
          },
        },
      ],

      addCard: (card) =>
        set((state) => ({
          cards: [...state.cards, { ...card, id: Date.now().toString() }],
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

      // Chat Messages
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
            { ...message, id: Date.now(), timestamp: new Date() },
          ],
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
    }),
    {
      name: 'hrms-storage',
      version: 4, // Increment this to reset localStorage
      partialize: (state) => ({
        theme: state.theme,
        colorTheme: state.colorTheme,
        cards: state.cards,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      migrate: (persistedState, version) => {
        // If version is less than 4, reset the state
        if (version < 4) {
          return undefined; // This will cause the store to use initial state
        }
        return persistedState;
      },
    }
  )
);

export default useStore;
