import { useEffect, useRef, useState } from 'react';
import { Upload, CheckCircle, X } from 'lucide-react';
import Login from './components/Login';
import Header from './components/Header';
import DashboardGrid from './components/DashboardGrid';

import useStore from './store/useStore';
import useThemeColors from './hooks/useThemeColors';

function App() {
  const { theme, isAuthenticated, showDynamicUI, isGenerating } = useStore();
  const colors = useThemeColors();
  const fileInputRef = useRef(null);
  const [currentPage, setCurrentPage] = useState('upload');
  const [showToast, setShowToast] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'text/csv') {
      setSelectedFile(file);
    } else {
      alert('Please select a CSV file');
    }
    event.target.value = '';
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;
    
    try {
      useStore.setState({ 
        isGenerating: true, 
        showDynamicUI: true,
        userQuery: `Uploaded CSV: ${selectedFile.name}`
      });

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://172.25.247.12:8000/upload/hrms-data', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const responseData = await response.json();
      
      let tableData = [];
      if (responseData.data && Array.isArray(responseData.data)) {
        tableData = responseData.data;
      } else if (Array.isArray(responseData)) {
        tableData = responseData;
      }
      
      const layout = {
        layout: {
          components: [{
            type: 'data_table',
            title: `${selectedFile.name} - ${tableData.length} records`,
            dataField: 'database_results.select_employees_0.data'
          }]
        }
      };
      
      const data = {
        database_results: {
          select_employees_0: {
            data: tableData
          }
        }
      };
      
      useStore.setState({ 
        dynamicLayout: layout,
        dynamicData: data,
        isGenerating: false
      });
      
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
      setCurrentPage('dashboard');
      setSelectedFile(null);
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Upload failed: ${error.message}`);
      useStore.setState({ 
        isGenerating: false
      });
    }
  };

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

  useEffect(() => {
    // Navigate back to upload page when dynamic UI is closed
    if (!showDynamicUI && currentPage === 'dashboard') {
      setCurrentPage('upload');
    }
  }, [showDynamicUI, currentPage]);

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50/20 to-pink-50/20 dark:from-slate-900 dark:via-slate-900 dark:to-slate-900 transition-colors duration-300">
      {/* Toast Notification */}
      {showToast && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <CheckCircle className="w-5 h-5" />
          File uploaded successfully!
        </div>
      )}
      <div className="relative z-10 flex flex-col h-screen">
        <Header />
        {currentPage === 'upload' ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8 border border-slate-200 dark:border-slate-700">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div className="space-y-4">
                {!selectedFile && (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isGenerating}
                    className={`w-full px-6 py-3 bg-gradient-to-r ${colors.gradient} text-white rounded-lg hover:shadow-lg transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                      Upload CSV File
                  </button>
                )}
                {selectedFile && (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={selectedFile.name}
                      readOnly
                      className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white"
                    />
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                {selectedFile && (
                  <button
                    onClick={handleFileUpload}
                    disabled={isGenerating}
                    className={`flex items-center justify-center gap-3 w-full px-6 py-3 bg-gradient-to-r ${colors.gradient} text-white rounded-lg hover:shadow-lg transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <Upload className="w-5 h-5" />
                    {isGenerating ? 'Uploading...' : 'Upload File'}
                  </button>
                )}
                {isGenerating && (
                  <div className="w-full">
                    <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                      <div className={`bg-gradient-to-r ${colors.gradient} h-2 rounded-full animate-pulse`}></div>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 text-center">Processing your file...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-auto">
            <DashboardGrid />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
