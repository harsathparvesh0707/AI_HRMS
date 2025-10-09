import { useState, useEffect } from 'react';
import { useQwenFormatter } from '../hooks/useQwenFormatter';

const FormattedDataDisplay = ({ data, context = 'dashboard', children }) => {
  const [formattedData, setFormattedData] = useState(data);
  const { formatData, isFormatting, error } = useQwenFormatter();

  useEffect(() => {
    const formatResponse = async () => {
      if (data) {
        const formatted = await formatData(data, context);
        setFormattedData(formatted || data);
      }
    };

    formatResponse();
  }, [data, context, formatData]);

  if (isFormatting) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-slate-600">Formatting...</span>
      </div>
    );
  }

  if (error) {
    console.warn('Formatting error:', error);
  }

  return children ? children(formattedData) : <pre>{JSON.stringify(formattedData, null, 2)}</pre>;
};

export default FormattedDataDisplay;