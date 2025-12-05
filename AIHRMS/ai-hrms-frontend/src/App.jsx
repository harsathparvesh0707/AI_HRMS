import { useEffect, useRef, useState } from "react";
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { Upload, CheckCircle, X } from "lucide-react";
import Login from "./components/Login";
import Header from "./components/Header";
import DashboardGrid from "./components/DashboardGrid";
import ProjectAlert from "./components/ProjectAlert";
import EmployeeDetails from "./components/EmployeeDetails";
import NotificationsPage from "./components/NotificationsPage";

import useStore from "./store/useStore";
import useThemeColors from "./hooks/useThemeColors";

function AppContent() {
  const { theme, isAuthenticated, showDynamicUI, isGenerating } = useStore();
  const colors = useThemeColors();
  const fileInputRef = useRef(null);
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [showToast, setShowToast] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  // const [startUpload, setStartUpload] = useState(false);

  // Set current page based on dynamic UI state
  useEffect(() => {
    if (showDynamicUI) {
      setCurrentPage("dynamicUI");
    }
  }, [showDynamicUI]);



  // Function to handle no data scenario
  const handleNoDataAvailable = () => {
    setCurrentPage("upload");
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === "text/csv") {
      setSelectedFile(file);
    } else {
      alert("Please select a CSV file");
    }
    event.target.value = "";
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      useStore.setState({ isGenerating: true });

      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(
        "http://172.25.244.2:8000/upload/hrms-data",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      const responseData = await response.json();

      const tableData = responseData.all_employees || [];

      // Store uploaded data separately and update UI
      const uploadedDataStructure = {
        database_results: {
          select_employees_0: { data: tableData },
        },
      };

      // Immediate UI update
      requestAnimationFrame(() => {
        useStore.setState({
          uploadedData: uploadedDataStructure, // Store uploaded data separately
          dynamicLayout: {
            layout: {
              components: [
                {
                  type: "data_table",
                  title: `${selectedFile.name} - ${tableData.length} records`,
                  dataField: "database_results.select_employees_0.data",
                },
              ],
            },
          },
          dynamicData: uploadedDataStructure,
          showDynamicUI: true,
          isGenerating: false,
          userQuery: `Uploaded CSV: ${selectedFile.name}`,
        });

        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
        setCurrentPage("dynamicUI");
        setSelectedFile(null);
      });
    } catch (error) {
      console.error("Upload error:", error);
      alert(`Upload failed: ${error.message}`);
      useStore.setState({ isGenerating: false });
    }
  };

  useEffect(() => {
    // Apply theme to document
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
      document.body.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
      document.body.classList.remove("dark");
    }
  }, [theme]);

  useEffect(() => {
    // Navigate back to dashboard when dynamic UI is closed
    if (!showDynamicUI && currentPage === "dynamicUI") {
      setCurrentPage("dashboard");
    }
  }, [showDynamicUI, currentPage]);

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Project Alert */}
      {currentPage === "dashboard" && <ProjectAlert />}

      {/* Toast Notification */}
      {showToast && (
        <div className="fixed top-20 right-9 bg-emerald-600 text-white px-4 py-2 rounded-md shadow-sm flex items-center gap-2 z-50">
          <CheckCircle className="w-4 h-4" />
          File uploaded successfully
        </div>
      )}
      <div className="relative z-10 flex flex-col h-screen">
        <Header onNavigate={setCurrentPage} currentPage={currentPage} />
        {currentPage === "upload" ? (
          <div className="flex-1 flex items-start justify-center pt-24">
            <div className="w-full max-w-md">
              <div className="absolute top-20 left-6">
                <div className="flex items-center mb-6">
                  <button
                    onClick={() => setCurrentPage("dashboard")}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                    Back to Dashboard
                  </button>
                </div>
              </div>

              <div className="text-center mb-8">
                <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                  Upload CSV File
                </h1>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  Select a CSV file to upload and process
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
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
                      className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md font-medium transition-colors duration-200 disabled:cursor-not-allowed"
                    >
                      Choose CSV File
                    </button>
                  )}
                  {selectedFile && (
                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={selectedFile.name}
                        readOnly
                        className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      />
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                  {selectedFile && (
                    <button
                      onClick={handleFileUpload}
                      disabled={isGenerating}
                      className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md font-medium transition-colors duration-200 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <Upload className="w-5 h-5" />
                      {isGenerating ? "Uploading..." : "Upload File"}
                    </button>
                  )}
                  {isGenerating && (
                    <div className="space-y-2">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div className="bg-blue-600 h-1.5 rounded-full animate-pulse w-full"></div>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        Processing file...
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-auto p-6">
            <DashboardGrid onNavigate={setCurrentPage} />
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AppContent />} />
        <Route path="/employee/:employeeId" element={<EmployeeDetails />} />
        <Route path="/notifications" element={<NotificationsPage />} />
      </Routes>
    </Router>
  );
}

export default App;
