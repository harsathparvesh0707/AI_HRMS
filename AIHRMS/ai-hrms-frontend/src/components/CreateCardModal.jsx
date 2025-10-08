import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus } from 'lucide-react';
import useStore from '../store/useStore';
import useThemeColors from '../hooks/useThemeColors';

const CreateCardModal = ({ isOpen, onClose }) => {
  const { addCard } = useStore();
  const colors = useThemeColors();
  const [formData, setFormData] = useState({
    title: '',
    type: 'chart',
    size: 'medium',
  });

  const cardTypes = [
    { value: 'attendance', label: 'Attendance' },
    { value: 'leave', label: 'Leave Balance' },
    { value: 'chart', label: 'Chart' },
    { value: 'announcements', label: 'Announcements' },
    { value: 'recruitment', label: 'Recruitment' },
    { value: 'payroll', label: 'Payroll' },
    { value: 'team', label: 'Team Members' },
    { value: 'approvals', label: 'Approvals' },
    { value: 'department', label: 'Department' },
    { value: 'training', label: 'Training' },
    { value: 'stats', label: 'Statistics' },
    { value: 'holidays', label: 'Holidays' },
  ];

  const cardSizes = [
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium' },
    { value: 'wide', label: 'Wide' },
    { value: 'tall', label: 'Tall' },
    { value: 'large', label: 'Large' },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    const newCard = {
      title: formData.title,
      type: formData.type,
      size: formData.size,
      pinned: false,
      data: getDefaultData(formData.type),
    };

    addCard(newCard);
    setFormData({ title: '', type: 'chart', size: 'medium' });
    onClose();
  };

  const getDefaultData = (type) => {
    switch (type) {
      case 'attendance':
        return { hoursWorked: 40, totalHours: 40, percentage: 100 };
      case 'leave':
        return { available: 15, used: 5, total: 20 };
      case 'chart':
        return {
          series: [
            { month: 'Jan', value: 65 },
            { month: 'Feb', value: 78 },
            { month: 'Mar', value: 82 },
          ],
        };
      case 'announcements':
        return {
          items: [
            { id: 1, text: 'Welcome to your new card!', date: new Date().toISOString() },
          ],
        };
      default:
        return {};
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50"
            onClick={onClose}
          />
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl p-6 w-full max-w-md mx-4"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Create New Card
              </h2>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Card Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter card title..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Card Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {cardTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Card Size
                </label>
                <select
                  value={formData.size}
                  onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {cardSizes.map((size) => (
                    <option key={size.value} value={size.value}>
                      {size.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`flex-1 px-4 py-2 bg-gradient-to-r ${colors.gradient} text-white rounded-lg hover:shadow-lg transition-all font-medium`}
                >
                  Create Card
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default CreateCardModal;