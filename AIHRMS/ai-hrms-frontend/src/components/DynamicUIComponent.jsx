import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

const PaginatedTable = ({ data, getFieldLabel }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [jumpToPage, setJumpToPage] = useState('');
  
  const totalPages = Math.ceil(data.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = data.slice(startIndex, endIndex);
  
  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };
  
  const handleJumpToPage = (e) => {
    e.preventDefault();
    const pageNum = parseInt(jumpToPage);
    if (pageNum >= 1 && pageNum <= totalPages) {
      setCurrentPage(pageNum);
      setJumpToPage('');
    }
  };
  
  const fields = Object.keys(data[0]);
  const displayFields = fields.filter(field => field !== 'last_name');
  
  return (
    <div className="space-y-4">
      <div className="w-full overflow-x-auto bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 max-h-[600px] overflow-y-auto">
        <table className="w-full min-w-full">
          <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-10">
            <tr>
              {displayFields.map(field => (
                <th 
                  key={field} 
                  className="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap bg-slate-50 dark:bg-slate-800/50"
                >
                  {field === 'first_name' ? 'name' : getFieldLabel(field)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {currentData.map((item, index) => (
              <tr key={startIndex + index} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                {displayFields.map(field => (
                  <td 
                    key={field} 
                    className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white"
                  >
                    {field === 'first_name' 
                      ? `${item.first_name || ''} ${item.last_name || ''}`.trim() || 'N/A'
                      : item[field] || 'N/A'
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm">
        <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
          <span>Showing {startIndex + 1} to {Math.min(endIndex, data.length)} of {data.length} results</span>
          <div className="flex items-center gap-2">
            <label>Show:</label>
            <select
              value={itemsPerPage}
              onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
              className="px-2 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          
          <form onSubmit={handleJumpToPage} className="flex items-center gap-2">
            <span className="text-sm text-slate-600 dark:text-slate-400">Page</span>
            <input
              type="number"
              min="1"
              max={totalPages}
              value={jumpToPage}
              onChange={(e) => setJumpToPage(e.target.value)}
              placeholder={currentPage.toString()}
              className="w-16 px-2 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm text-center"
            />
            <span className="text-sm text-slate-600 dark:text-slate-400">of {totalPages}</span>
          </form>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

const DynamicUIComponent = ({ layoutData, data }) => {
  console.log('=== DYNAMIC UI DEBUG ===');
  console.log('Full layoutData:', layoutData);
  console.log('Full data:', data);
  
  if (!layoutData || !data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-red-800 font-bold">No data or layout available</h3>
      </div>
    );
  }

  // Extract employee data
  let employees = data.database_results?.select_employees_0?.data || [];
  if (employees.rows && Array.isArray(employees.rows)) {
    employees = employees.rows;
  }

  const layout = layoutData.layout || layoutData;
  const components = layout.components || [];
  const dataMapping = layoutData.dataMapping || {};
  
  console.log('Extracted employees:', employees);
  console.log('Raw data structure:', data);
  console.log('Layout components:', components);

  if (employees.length === 0) {
    return (
      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-yellow-800 font-bold">No Employee Data Found</h3>
      </div>
    );
  }

  const getFieldLabel = (fieldKey) => {
    return dataMapping[fieldKey] || fieldKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getComponentData = (dataField) => {
    if (!dataField) return null;
    
    try {
      if (dataField === 'database_results.select_employees_0.data') {
        return employees;
      }
      
      if (dataField === 'database_results.select_employees_0.data[0]' && employees.length > 0) {
        return employees[0];
      }
      
      return employees;
    } catch (error) {
      console.error('Error getting component data:', error);
      return employees;
    }
  };

  const renderComponent = (component, componentData) => {
    switch (component.type) {
      case 'header':
        return (
          <div className="flex items-center justify-center mb-6">
            <div className="relative w-full max-w-2xl">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search through your data..."
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm hover:shadow-md transition-shadow"
              />
            </div>
            {component.subtitle && (
              <p className="text-gray-500 dark:text-gray-400 text-sm mt-2 text-center">
                {component.subtitle}
              </p>
            )}
          </div>
        );

      case 'profile_card':
        const singleEmp = Array.isArray(componentData) ? componentData[0] : componentData;
        if (!singleEmp || typeof singleEmp !== 'object') {
          return <div className="text-gray-500">No employee data available</div>;
        }
        
        const profileFields = Object.keys(singleEmp).filter(field => field !== 'last_name');
        
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profileFields.map((key) => (
              <div key={key} className="flex justify-between items-center py-3 px-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {key === 'first_name' ? 'name' : getFieldLabel(key)}:
                </span>
                <span className="text-gray-900 dark:text-white font-semibold">
                  {key === 'first_name' 
                    ? `${singleEmp.first_name || ''} ${singleEmp.last_name || ''}`.trim() || 'N/A'
                    : singleEmp[key] || 'N/A'
                  }
                </span>
              </div>
            ))}
          </div>
        );

      case 'data_table':
        if (!Array.isArray(componentData) || componentData.length === 0) {
          return <div className="text-gray-500">No employee data available</div>;
        }

        return <PaginatedTable data={componentData} getFieldLabel={getFieldLabel} />;

      case 'metrics_grid':
        if (Array.isArray(componentData) && componentData.length > 0) {
          const activeCount = componentData.filter(emp => emp.employee_status === 'Active').length;
          const freepoolCount = componentData.filter(emp => emp.employee_status === 'Freepool').length;
          
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {componentData.length}
                </div>
                <div className="text-sm text-blue-700 dark:text-blue-300 mt-2">Total Employees</div>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {activeCount}
                </div>
                <div className="text-sm text-green-700 dark:text-green-300 mt-2">Active</div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/20 p-6 rounded-lg text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {freepoolCount}
                </div>
                <div className="text-sm text-purple-700 dark:text-purple-300 mt-2">Freepool</div>
              </div>
            </div>
          );
        }
        return <div className="text-gray-500">No metrics data available</div>;

      default:
        return (
          <div className="text-gray-500">
            Component type "{component.type}" not implemented
          </div>
        );
    }
  };

  const getComponentStyle = (component) => {
    const baseStyle = "bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700";
    
    if (component.type === 'data_table') {
      return `${baseStyle} col-span-1 overflow-hidden`;
    }
    
    if (component.type === 'header') {
      return "col-span-1";
    }
    
    return `${baseStyle} col-span-1 p-6`;
  };

  return (
    <div className="w-full space-y-6 p-4">
      {components.map((component, index) => {
        const componentData = getComponentData(component.dataField);
        console.log(`Component ${index}:`, component);
        console.log(`Component data for ${component.dataField}:`, componentData);
        
        return (
          <div key={index} className="space-y-4">
            {component.type !== 'header' && (
              <h3 className="font-bold text-gray-900 dark:text-white text-lg">
                {component.title}
              </h3>
            )}
            <div className={getComponentStyle(component)}>
              {renderComponent(component, componentData)}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DynamicUIComponent;