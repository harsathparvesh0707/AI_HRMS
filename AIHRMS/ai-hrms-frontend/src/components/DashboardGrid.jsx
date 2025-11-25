import { motion, AnimatePresence } from 'framer-motion';
import { useState, useRef } from 'react';
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
} from '@dnd-kit/sortable'
import DashboardCard from './DashboardCard';
import CreateCardModal from './CreateCardModal';
import PinnedIconCard from './PinnedIconCard';
import DynamicUIComponent from './DynamicUIComponent';
import useStore from '../store/useStore';
import useThemeColors from '../hooks/useThemeColors';
import { ChevronDown, ChevronUp, Plus, X, Upload } from 'lucide-react';  

const DashboardGrid = ({ onNavigate }) => {
  const { 
    cards, 
    reorderCards,
    dynamicLayout,
    dynamicData,
    isGenerating,
    showDynamicUI,
    hideDynamicUI,
    userQuery
  } = useStore();

  const colors = useThemeColors();
  const [pinnedExpanded, setPinnedExpanded] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const fileInputRef = useRef(null);

  // const handleFileUpload = async (event) => {
  //   debugger
  //   const file = event.target.files[0];
  //   if (file && file.type === 'text/csv') {
  //     try {
  //       useStore.setState({ 
  //         isGenerating: true, 
  //         showDynamicUI: true,
  //         userQuery: `Uploaded CSV: ${file.name}`
  //       });
        
  //       const formData = new FormData();
  //       formData.append('file', file);
        
  //       const response = await fetch('http://172.25.247.12:8000/upload/hrms-data', {
  //         method: 'POST',
  //         body: formData,
  //       });
        
  //       if (!response.ok) {
  //         throw new Error(`HTTP error! status: ${response.status}`);
  //       }
        
  //       const result = await response.json();

  //       console.log(result);
        
  //       const layout = {
  //         layout: {
  //           type: 'responsive_grid',
  //           columns: 1,
  //           gap: '20px',
  //           components: [
  //             {
  //               type: 'data_table',
  //               title: '',
  //               dataField: 'apiResponse',
  //               style: { gridColumn: 'span 1' }
  //             }
  //           ]
  //         }
  //       };
        
  //       useStore.setState({ 
  //         dynamicLayout: layout,
  //         dynamicData: { apiResponse: result },
  //         dashboardData: { apiResponse: result },
  //         isGenerating: false
  //       });
  //     } catch (error) {
  //       console.error('Error uploading CSV:', error);
  //       alert('Error uploading CSV file: ' + error.message);
  //       useStore.setState({ 
  //         isGenerating: false
  //       });
  //     }
  //   } else {
  //     alert('Please select a CSV file');
  //   }
  //   event.target.value = ''; // Reset file input
  // };
  // console.log("grid", dynamicData);

  const parseCsvFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csv = e.target.result;
          const lines = csv.split('\n').filter(line => line.trim());
          const headers = lines[0].split(',').map(h => h.trim());
          const rows = lines.slice(1).map(line => {
            const values = line.split(',').map(v => v.trim());
            const row = {};
            headers.forEach((header, index) => {
              row[header] = values[index] || '';
            });
            return row;
          });
          resolve({ headers, rows });
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const createTableLayout = (csvData, fileName) => {
    const dataMapping = {};
    csvData.headers.forEach(header => {
      dataMapping[header] = header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    });

    return {
      layout: {
        type: 'responsive_grid',
        columns: 2,
        gap: '20px',
        components: [
          {
            type: 'header',
            title: `Uploaded Data: ${fileName}`,
            // subtitle: `${csvData.rows.length} records found`,
            style: { gridColumn: 'span 2' }
          },
          {
            type: 'data_table',
            title: '',
            dataField: 'database_results.select_employees_0.data',
            style: { gridColumn: 'span 2' }
          }
        ]
      },
      dataMapping
    };
  };

  const formatCsvData = (csvData) => {
    return {
      database_results: {
        select_employees_0: {
          data: csvData.rows
        }
      }
    };
  };

  // Filter out specific cards (add card IDs you want to hide)
  const hiddenCardIds = ['attendance', 'leave-balance', 'payroll','pending-approvals','leave-requests','team-members'];
  const visibleCards = cards.filter((card) => !hiddenCardIds.includes(card.id));
  
  const pinnedCards = visibleCards.filter((card) => card.pinned);
  const unpinnedCards = visibleCards.filter((card) => !card.pinned);

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
        {/* Dynamic UI */}
        {showDynamicUI && (
          <div className="space-y-2">
            <div className="flex items-center justify-end">
              <button 
                onClick={hideDynamicUI}
                className="p-1.5 bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {isGenerating ? (
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                <span className="ml-3 text-slate-600">Loading data...</span>
              </div>
            ) : (
              dynamicLayout && dynamicData && (
                <DynamicUIComponent layoutData={dynamicLayout} data={dynamicData} userQuery={userQuery} />
              )
            )}
          </div>
        )}
        {/* Pinned Section */}
        {!showDynamicUI && pinnedCards.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-0.5 w-0.5 bg-blue-600 rounded-full"></div>
                <h2 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                  Pinned
                </h2>
              </div>
              <button
                onClick={() => setPinnedExpanded(!pinnedExpanded)}
                className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
              >
                {pinnedExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>
            <SortableContext
              items={pinnedCards.map((c) => c.id)}
              strategy={rectSortingStrategy}
            >
              {pinnedExpanded ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  <AnimatePresence mode="popLayout">
                    {pinnedCards.map((card) => (
                      <DashboardCard key={card.id} card={card} />
                    ))}
                  </AnimatePresence>
                </div>
              ) : (
                <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
                  <AnimatePresence mode="popLayout">
                    {pinnedCards.map((card) => (
                      <PinnedIconCard key={card.id} card={card} />
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </SortableContext>
          </div>
        )}

        {/* All Cards Section */}
        {!showDynamicUI && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-0.5 bg-cyan-600 rounded-full"></div>
              <h2 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                Dashboard
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => onNavigate && onNavigate('upload')}
                className={`flex items-center gap-2 px-3 py-2 bg-gradient-to-r ${colors.gradient} text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 text-sm font-medium -mt-3`}
                title="Upload CSV File"
              >
                <Upload className="w-4 h-4" />
                
              </button>
            </div>
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

        )}
        
        {/* Empty State */}
        {!showDynamicUI && cards.length === 0 && (
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
            <button 
              onClick={() => setIsCreateModalOpen(true)}
              className={`px-4 py-2 bg-gradient-to-r ${colors.gradient} text-white rounded-lg shadow-md hover:shadow-lg transition-shadow font-medium text-sm`}
            >
              Add Your First Card
            </button>
          </motion.div>
        )}
      </div>
      
      <CreateCardModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)} 
      />

    </DndContext>
  );
};

export default DashboardGrid;
