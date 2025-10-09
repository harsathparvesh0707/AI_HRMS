import { useState, useCallback } from 'react';
import qwenFormatter from '../services/qwenFormatter';

export const useQwenFormatter = () => {
  const [isFormatting, setIsFormatting] = useState(false);
  const [error, setError] = useState(null);

  const formatData = useCallback(async (jsonData, context = 'dashboard') => {
    setIsFormatting(true);
    setError(null);
    
    try {
      const formattedData = await qwenFormatter.formatResponse(jsonData, context);
      return formattedData;
    } catch (err) {
      setError(err.message);
      return jsonData; // Return original data on error
    } finally {
      setIsFormatting(false);
    }
  }, []);

  return {
    formatData,
    isFormatting,
    error,
  };
};