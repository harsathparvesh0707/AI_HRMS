import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';
import { useState, useEffect } from 'react';

const ProjectAlert = () => {
  const [isVisible, setIsVisible] = useState(true);
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    // Mock alert data - using one of the project names
    const projectNames = ['VVDN_MEXS', 'INSU_PEGS', 'NTGU_IMDV', 'CRCU_BLUP', 'VIMU_GSUP'];
    const randomProject = projectNames[Math.floor(Math.random() * projectNames.length)];
    const randomDays = Math.floor(Math.random() * 15) + 2; // 1-15 days

    setAlert({
      projectName: randomProject,
      daysLeft: randomDays,
      // type: randomDays <= 5 ? 'critical' : randomDays <= 10 ? 'warning' : 'info'
    });
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
  };

  if (!alert || !isVisible) return null;

  const styles = {
    bg: 'bg-blue-500/20',
    border: 'border-blue-300/30',
    icon: 'text-blue-600',
    text: 'text-blue-800 dark:text-blue-200'
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.9 }}
        transition={{ duration: 0.3, type: "spring" }}
        className={`fixed top-20 right-40 z-40 ${styles.bg} ${styles.border} border backdrop-blur-md rounded-lg shadow-lg max-w-xs`}
      >
        <div className="p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className={`w-4 h-4 ${styles.icon}`} />
            <div className="flex-1 min-w-0">
              <div className={`text-xs font-medium ${styles.text}`}>
                {alert.projectName} ends in {alert.daysLeft} days
              </div>
            </div>
            <button
              onClick={handleDismiss}
              className={`p-1 rounded hover:bg-white/20 transition-colors ${styles.text} opacity-70 hover:opacity-100`}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ProjectAlert;