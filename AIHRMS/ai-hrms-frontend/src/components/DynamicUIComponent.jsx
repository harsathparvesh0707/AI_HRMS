import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import useStore from '../store/useStore';

const PaginatedTable = ({ data, getFieldLabel }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [jumpToPage, setJumpToPage] = useState('');
  const [expandedSkills, setExpandedSkills] = useState(new Set());
  
  const toggleSkillExpansion = (rowIndex) => {
    const newExpanded = new Set(expandedSkills);
    if (newExpanded.has(rowIndex)) {
      newExpanded.delete(rowIndex);
    } else {
      newExpanded.add(rowIndex);
    }
    setExpandedSkills(newExpanded);
  };
  
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
  
  // Flatten projects data to show all projects and customers
  const flattenedData = data.map(item => {
    const flattened = { ...item };
    if (item.projects && Array.isArray(item.projects) && item.projects.length > 0) {
      flattened.project = item.projects.map(p => p.project_name);
      flattened.customer = item.projects.map(p => p.customer);
      delete flattened.projects;
    } else if (item.project && item.customer) {
      // Handle direct project/customer fields from search results
      // project field already exists, no need to map
      // customer field already exists, no need to map
    }
    return flattened;
  });
  console.log("zxcvb",flattenedData);
  
  const fields = Object.keys(flattenedData[0]);
  const filteredFields = fields.filter(field => 
    field !== 'last_name' && 
    field !== 'is_free_pool' && 
    field !== 'is_billable' &&
    field !== 'type' &&
    field !== 'score' &&
    field !== 'source' &&
    field !== 'parsed_experience' &&
    field !== 'project_name' &&
    field !== 'project_department' &&
    field !== 'project_industry' &&
    field !== 'joined_date'
  );
  
  // Reorder columns: customer after project, project_count after customer, skill_set at end
  const otherFields = filteredFields.filter(field => 
    field !== 'skill_set' && field !== 'project_count' && field !== 'customer'
  );
  
  const displayFields = [];
  
  // Add all fields except customer, project_count, and skill_set
  otherFields.forEach(field => {
    displayFields.push(field);
    if (field === 'project') {
      // Add customer and project_count after project
      if (filteredFields.includes('customer')) displayFields.push('customer');
      if (filteredFields.includes('project_count')) displayFields.push('project_count');
    }
  });
  
  // Add skill_set at the end
  if (filteredFields.includes('skill_set')) {
    displayFields.push('skill_set');
  }
  
  return (
    <div className="space-y-4">
      <div className="w-full overflow-x-auto bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 max-h-[600px] overflow-y-auto">
        <table className="w-full min-w-full">
          <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-10">
            <tr>
              {displayFields.map(field => (
                <th 
                  key={field} 
                  className={`px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap bg-slate-50 dark:bg-slate-800/50 ${
                    field === 'skill_set' ? 'w-80' : ''
                  }`}
                >
                  {field === 'first_name' ? 'name' : getFieldLabel(field)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {flattenedData.slice(startIndex, endIndex).map((item, index) => (
              <tr key={startIndex + index} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                {displayFields.map(field => (
                  <td 
                    key={field} 
                    className={`px-6 py-4 text-sm text-slate-900 dark:text-white ${
                      field === 'skill_set' ? 'w-80' : 'whitespace-nowrap'
                    }`}
                  >
                    {field === 'first_name' 
                      ? `${item.first_name || ''} ${item.last_name || ''}`.trim() || 'N/A'
                      : field === 'skill_set' && item[field]
                        ? (
                            <div className="max-w-80">
                              <div className={expandedSkills.has(startIndex + index) ? '' : 'line-clamp-2'}>
                                {item[field]}
                              </div>
                              {item[field] && typeof item[field] === 'string' && item[field].length > 50 && (
                                <button
                                  onClick={() => toggleSkillExpansion(startIndex + index)}
                                  className="text-blue-600 hover:text-blue-800 text-xs mt-1"
                                >
                                  {expandedSkills.has(startIndex + index) ? 'Show Less' : 'Show More'}
                                </button>
                              )}
                            </div>
                          )
                      : Array.isArray(item[field])
                        ? item[field].map((value, idx) => (
                            <div key={idx}>{value}</div>
                          ))
                        : typeof item[field] === 'object' && item[field] !== null
                          ? JSON.stringify(item[field])
                          : item[field] || 'N/A'
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Advanced Pagination Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm">
        <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
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
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            Previous
          </button>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

const DynamicUIComponent = ({ layoutData }) => {
  const { dynamicData } = useStore();
  
  // console.log('=== DYNAMIC UI DEBUG ===');
  // console.log('Full layoutData:', layoutData);
  // console.log('Full dynamicData:', dynamicData);
  
  if (!layoutData || !dynamicData) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-red-800 font-bold">No data or layout available</h3>
      </div>
    );
  }

  // Extract employee data from various API response formats
  let employees = [];
  console.log("asdfgghjk",dynamicData);
  
  // Handle different API response structures
  if (dynamicData?.results?.unified_results) {
    employees = dynamicData.results.unified_results
  } else if (dynamicData?.database_results?.select_employees_0?.data) {
    employees = dynamicData.database_results.select_employees_0.data
  }
  
  // Handle nested rows structure
  if (employees.rows && Array.isArray(employees.rows)) {
    employees = employees.rows;
  }


  const layout = layoutData.layout || layoutData;
  const components = layout.components || [];
  const dataMapping = layoutData.dataMapping || {};
  
  // console.log('Extracted employees:', employees);
  // console.log('Raw data structure:', dynamicData);
  // console.log('Layout components:', components);

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
    if (!dataField) return employees;
    
    try {
      // Handle different dataField patterns
      if (dataField === 'database_results.select_employees_0.data' || 
          dataField === 'apiResponse' || 
          dataField === 'data' || 
          dataField === 'results') {
        return employees;
      }
      
      if (dataField.includes('[0]') && employees.length > 0) {
        return employees[0];
      }
      
      return employees;
    } catch (error) {
      console.error('Error getting component data:', error);
      return employees;
    }
  };



  const renderComponent = (component, componentData) => {
    
    // Handle LLM-generated components with actual data mapping
    if (component.type === 'llm_generated') {
      // Get actual employee data
      const actualEmployees = employees || [];
      // console.log('LLM component - actual employees:', actualEmployees);
      // console.log('Component details:', component);
      
      if (component.componentType === 'table' && actualEmployees.length > 0) {
        const fields = Object.keys(actualEmployees[0]).filter(field => field !== 'last_name');
        
        return (
          <div className="w-full overflow-x-auto">
            <table className="w-full min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  {fields.map(field => (
                    <th key={field} className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      {field === 'first_name' ? 'name' : getFieldLabel(field)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {actualEmployees.map((emp, index) => (
                  <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    {fields.map(field => (
                      <td key={field} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {field === 'first_name' 
                          ? `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || 'N/A'
                          : emp[field] || 'N/A'
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      
      if (component.componentType === 'card' && actualEmployees.length > 0) {
        const emp = actualEmployees[0];
        const empFields = Object.keys(emp).filter(field => field !== 'last_name');
        
        return (
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-3">
            {empFields.map((key) => (
              <div key={key} className="flex justify-between items-center">
                <span className="font-medium text-gray-600 dark:text-gray-400 text-sm">
                  {key === 'first_name' ? 'name' : getFieldLabel(key)}:
                </span>
                <span className="text-gray-900 dark:text-white font-semibold text-sm">
                  {key === 'first_name' 
                    ? `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || 'N/A'
                    : emp[key] || 'N/A'
                  }
                </span>
              </div>
            ))}
          </div>
        );
      }
      
      return <div className="text-gray-500">No employee data available</div>;
    }
    
    // Auto-decide format: card for single employee, table for multiple
    const isMultipleEmployees = Array.isArray(componentData) && componentData.length > 1;
    const isSingleEmployee = (Array.isArray(componentData) && componentData.length === 1) || 
                            (!Array.isArray(componentData) && componentData && typeof componentData === 'object');
    
    switch (component.type) {
      case 'header':
        return (
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-center">
              {component.title}
            </h2>
            {component.subtitle && (
              <p className="text-gray-500 dark:text-gray-400 text-sm mt-2 text-center">
                {component.subtitle}
              </p>
            )}
          </div>
        );

      case 'profile_card':
        // Card format only for single employee details
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

        // Active/freepool employees now use table format (handled by LLM)

        // Table format with pagination
        return <PaginatedTable data={componentData} getFieldLabel={getFieldLabel} />;

      case 'card_grid':
        if (!Array.isArray(componentData) || componentData.length === 0) {
          return <div className="text-gray-500">No employee data available</div>;
        }

        // Always use 2-column grid for card display
        return (
          <div className="grid grid-cols-2 gap-6">
            {componentData.map((emp, index) => {
              const empFields = Object.keys(emp).filter(field => field !== 'last_name');
              return (
                <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-3">
                  {empFields.map((key) => (
                    <div key={key} className="flex justify-between items-center">
                      <span className="font-medium text-gray-600 dark:text-gray-400 text-sm">
                        {key === 'first_name' ? 'name' : getFieldLabel(key)}:
                      </span>
                      <span className="text-gray-900 dark:text-white font-semibold text-sm">
                        {key === 'first_name' 
                          ? `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || 'N/A'
                          : emp[key] || 'N/A'
                        }
                      </span>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        );

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
    
    // For data tables, add extra padding and ensure full width
    if (component.type === 'data_table') {
      return `${baseStyle} col-span-1 overflow-hidden`;
    }
    
    // For headers, no card styling
    if (component.type === 'header') {
      return "col-span-1";
    }
    
    // For other components
    return `${baseStyle} col-span-1 p-6`;
  };

  return (
    <div className="w-full space-y-6 p-4">
      {components.map((component, index) => {
        const componentData = getComponentData(component.dataField);
        // console.log(`Component ${index}:`, component);
        // console.log(`Component data for ${component.dataField}:`, componentData);
        
        // Skip rendering header components
        if (component.type === 'header') {
          return null;
        }
        
        return (
          <div key={index} className="space-y-4">
            {/* Show title outside the card/table for all non-header components */}
            {component.type !== 'header' && component.type !== 'llm_generated' && (
              <h3 className="font-bold text-gray-900 dark:text-white text-lg">
                {component.title}
              </h3>
            )}
            {/* Show LLM-generated title */}
            {component.type === 'llm_generated' && (
              <h3 className="font-bold text-gray-900 dark:text-white text-lg">
                {component.title}
              </h3>
            )}
            <div className={component.type === 'llm_generated' ? 'bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4' : getComponentStyle(component)}>
              {renderComponent(component, componentData)}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DynamicUIComponent;