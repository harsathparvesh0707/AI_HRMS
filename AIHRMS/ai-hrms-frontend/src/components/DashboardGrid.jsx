import { motion, AnimatePresence } from 'framer-motion';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import DashboardCard from './DashboardCard';
import useStore from '../store/useStore';
import useThemeColors from '../hooks/useThemeColors';
import { Plus } from 'lucide-react';

const DashboardGrid = () => {
  const { cards, reorderCards } = useStore();
  const colors = useThemeColors();

  const pinnedCards = cards.filter((card) => card.pinned);
  const unpinnedCards = cards.filter((card) => !card.pinned);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = cards.findIndex((card) => card.id === active.id);
      const newIndex = cards.findIndex((card) => card.id === over?.id);

      if (oldIndex !== -1 && newIndex !== -1) {
        const newCards = arrayMove(cards, oldIndex, newIndex);
        reorderCards(newCards);
      }
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <div className="px-4 py-3 space-y-4 bg-transparent">
        {/* Pinned Section */}
        {pinnedCards.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-0.5 bg-blue-600 rounded-full"></div>
              <h2 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                Pinned
              </h2>
            </div>
            <SortableContext
              items={pinnedCards.map((c) => c.id)}
              strategy={rectSortingStrategy}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                <AnimatePresence mode="popLayout">
                  {pinnedCards.map((card) => (
                    <DashboardCard key={card.id} card={card} />
                  ))}
                </AnimatePresence>
              </div>
            </SortableContext>
          </div>
        )}

        {/* All Cards Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-0.5 bg-cyan-600 rounded-full"></div>
              <h2 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                Dashboard
              </h2>
            </div>
            <button className={`p-1.5 bg-gradient-to-r ${colors.gradient} text-white rounded-lg shadow-md hover:shadow-lg transition-shadow`}>
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <SortableContext
            items={unpinnedCards.map((c) => c.id)}
            strategy={rectSortingStrategy}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              <AnimatePresence mode="popLayout">
                {unpinnedCards.map((card) => (
                  <DashboardCard key={card.id} card={card} />
                ))}
              </AnimatePresence>
            </div>
          </SortableContext>
        </div>

        {/* Empty State */}
        {cards.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-16"
          >
            <div className={`w-16 h-16 bg-gradient-to-br ${colors.gradient} rounded-2xl flex items-center justify-center mb-4`}>
              <Plus className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
              No Cards Yet
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 text-center max-w-md mb-4">
              Ask the AI assistant to create personalized cards for your
              dashboard, or add them manually.
            </p>
            <button className={`px-4 py-2 bg-gradient-to-r ${colors.gradient} text-white rounded-lg shadow-md hover:shadow-lg transition-shadow font-medium text-sm`}>
              Add Your First Card
            </button>
          </motion.div>
        )}
      </div>
    </DndContext>
  );
};

export default DashboardGrid;
