import { useEffect } from 'react';
import { motion } from 'framer-motion';
import Login from './components/Login';
import Header from './components/Header';
import DashboardGrid from './components/DashboardGrid';
import ChatPanel from './components/ChatPanel';
import useStore from './store/useStore';

function App() {
  const { theme, isAuthenticated } = useStore();

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.body.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.body.classList.remove('dark');
    }
  }, [theme]);

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50/20 to-pink-50/20 dark:from-slate-900 dark:via-slate-900 dark:to-slate-900 transition-colors duration-300">

      {/* Main Content */}
      <div className="relative z-10 flex flex-col h-screen">
        <Header />
        <div className="flex-1 overflow-y-auto">
          <DashboardGrid />
        </div>
        <ChatPanel />
      </div>
    </div>
  );
}

export default App;
