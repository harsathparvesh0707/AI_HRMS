import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import useThemeColors from '../hooks/useThemeColors';

const DynamicTable = ({ data, isLoading }) => {
  const colors = useThemeColors();
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  useEffect(() => {
    console.log('DynamicTable received data:', data);
    
    if (data && Array.isArray(data) && data.length > 0) {
      const cols = Object.keys(data[0]);
      setColumns(cols);
      setRows(data);
    } else if (data && typeof data === 'object' && !Array.isArray(data)) {
      // Handle single object or nested data
      if (data.data && Array.isArray(data.data)) {
        const cols = Object.keys(data.data[0]);
        setColumns(cols);
        setRows(data.data);
      } else {
        const cols = Object.keys(data);
        setColumns(cols);
        setRows([data]);
      }
    }
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-slate-600">Loading data...</span>
      </div>
    );
  }

  if (!data || (Array.isArray(data) && data.length === 0) || (!Array.isArray(data) && Object.keys(data).length === 0)) {
    return (
      <div className="text-center p-8 text-slate-500">
        No data available
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden"
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className={`bg-gradient-to-r ${colors.gradient} text-white`}>
            <tr>
              {columns.map((col) => (
                <th key={col} className="px-4 py-3 text-left text-sm font-semibold">
                  {col.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {rows.map((row, index) => (
              <tr key={index} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                {columns.map((col) => (
                  <td key={col} className="px-4 py-3 text-sm text-slate-900 dark:text-slate-100">
                    {row[col]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
};

export default DynamicTable;