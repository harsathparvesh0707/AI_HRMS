import React from 'react';

const DynamicUIComponent = ({ layoutData, data }) => {
  if (!layoutData || !data) {
    return <div className="p-4 text-red-500">No data or layout available</div>;
  }

  const employees = data.database_results?.select_employees_0?.data || [];
  const layout = layoutData.layout || layoutData;
  const components = layout.components || [];

  const getGridColsClass = (columns) => {
    switch (columns) {
      case 1: return 'grid-cols-1';
      case 2: return 'grid-cols-1 md:grid-cols-2';
      case 3: return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
      case 4: return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      default: return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
    }
  };

  return (
    <div className={`grid ${getGridColsClass(layout.columns)} gap-6`}>
      {components.map((component, index) => (
        <div key={index} className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
          <h3 className="font-bold mb-2 text-slate-900 dark:text-white">{component.title}</h3>
          {employees.map((emp, empIdx) => (
            <div key={empIdx} className="mb-2 p-2 border-b border-slate-200 dark:border-slate-600">
              {Object.entries(emp).map(([key, value]) => (
                <div key={key} className="text-slate-700 dark:text-slate-300">
                  <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: </strong>
                  {value || 'N/A'}
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default DynamicUIComponent;