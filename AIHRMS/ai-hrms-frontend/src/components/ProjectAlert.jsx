import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';
import { useState, useEffect } from 'react';

const ProjectAlert = () => {
  const [isVisible, setIsVisible] = useState(true);
  const [currentAlertIndex, setCurrentAlertIndex] = useState(0);

  // Project alerts sorted by days left (ascending)
  const projectAlerts = [
    {
      projectName: 'VVDN_MEXS',
      daysLeft: 3,
    },
    {
      projectName: 'INSU_PEGS', 
      daysLeft: 7,
    },
    {
      projectName: 'NTGU_IMDV',
      daysLeft: 12,
    }
  ];
  // Cycle through alerts every 6 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentAlertIndex((prev) => (prev + 1) % projectAlerts.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [projectAlerts.length]);

  const handleDismiss = () => {
    setIsVisible(false);
  };

  if (!isVisible) return null;
  const currentAlert = projectAlerts[currentAlertIndex];
 const styles = {
    bg: 'bg-blue-500/20',
    border: 'border-blue-300/30',
    icon: 'text-blue-600',
    text: 'text-blue-800 dark:text-blue-200'
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={currentAlertIndex}
        initial={{ opacity: 0, x: 20, scale: 0.95 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: -20, scale: 0.95 }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
        className={`fixed top-20 right-40 z-40 ${styles.bg} ${styles.border} border backdrop-blur-md rounded-lg shadow-lg max-w-xs`}
      >
        <div className="p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className={`w-4 h-4 ${styles.icon}`} />
            <div className="flex-1 min-w-0">
              <div className={`text-xs font-medium ${styles.text}`}>
                {currentAlert.projectName} ends in {currentAlert.daysLeft} days
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