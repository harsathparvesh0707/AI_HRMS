import React, { useState } from 'react';
import { User, ChevronDown, ChevronUp } from 'lucide-react';
import useStore from '../store/useStore';



// =================== EMPLOYEE CARD COMPONENT ===================
const EmployeeCard = ({ employee }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!employee) return null;

  const {
    employee_id,
    display_name,
    first_name,
    last_name,
    designation,
    tech_group,
    emp_location,
    rm_name,
    rm_id,
    employee_department,
    total_exp,
    vvdn_exp,
    deployment,
    email,
    phone,
    date_of_joining,
    employee_status
  } = employee;

  const fullName = display_name || `${first_name || ''} ${last_name || ''}`.trim();

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      {/* Main Card Content */}
      <div className="p-4">
        <div className="flex items-center gap-4">
          {/* User Icon */}
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          
          {/* Employee Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white truncate">
                {fullName}
              </h3>
              <span className="text-sm text-slate-500 dark:text-slate-400">•</span>
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                {employee_id}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <p className="text-slate-600 dark:text-slate-400">
                <span className="font-medium">Designation:</span> {designation || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                <span className="font-medium">Tech Group:</span> {tech_group || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                <span className="font-medium">Location:</span> {emp_location || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                <span className="font-medium">RM:</span> {rm_name ? `${rm_name} (${rm_id})` : 'N/A'}
              </p>
            </div>
          </div>
          
          {/* Expand Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-slate-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-500" />
            )}
          </button>
        </div>
      </div>
      
      {/* Accordion Content */}
      {isExpanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-4 bg-slate-50 dark:bg-slate-800/50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Contact Information</h4>
              <p className="text-slate-600 dark:text-slate-400 mb-1">
                <span className="font-medium">Email:</span> {email || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400 mb-1">
                <span className="font-medium">Phone:</span> {phone || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                <span className="font-medium">Department:</span> {employee_department || 'N/A'}
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Employment Details</h4>
              <p className="text-slate-600 dark:text-slate-400 mb-1">
                <span className="font-medium">Join Date:</span> {date_of_joining || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400 mb-1">
                <span className="font-medium">Total Experience:</span> {total_exp || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400 mb-1">
                <span className="font-medium">VVDN Experience:</span> {vvdn_exp || 'N/A'}
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                <span className="font-medium">Status:</span> 
                <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                  employee_status?.toLowerCase() === 'active' || deployment?.toLowerCase() === 'billable'
                    ? 'bg-green-100 text-green-700'
                    : employee_status?.toLowerCase() === 'inactive' || deployment?.toLowerCase() === 'free'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-blue-100 text-blue-700'
                }`}>
                  {employee_status || deployment || 'N/A'}
                </span>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// =================== REQUIREMENT CARD COMPONENT ===================
const RequirementCard = ({ employee }) => {
  if (!employee) return null;

  const {
    display_name,
    designation,
    employee_id,
    employee_department,
    emp_location,
    tech_group,
    total_exp,
    vvdn_exp,
    deployment,
    score,
    skill_set,
    reason
  } = employee;

  // Get card colors based on score (green to red gradient)
  const getCardColors = () => {
    if (score >= 70) {
      return {
        border: 'border-green-500',
        bg: 'bg-green-50 dark:bg-green-900/20',
        scoreColor: 'text-green-600 dark:text-green-400'
      };
    } else if (score >= 50) {
      return {
        border: 'border-yellow-500', 
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        scoreColor: 'text-yellow-600 dark:text-yellow-400'
      };
    } else {
      return {
        border: 'border-red-500',
        bg: 'bg-red-50 dark:bg-red-900/20', 
        scoreColor: 'text-red-600 dark:text-red-400'
      };
    }
  };

  const colors = getCardColors();

  return (
    <div className={`p-6 ${colors.bg} border-2 ${colors.border} rounded-xl shadow-md hover:shadow-lg transition-all duration-200`}>
      <div className="flex items-center justify-between">
        {/* Left Section - Employee Info */}
        <div className="flex-1 pr-6">
          <div className="mb-3">
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                {display_name}
              </h2>
              <span
                className={`px-3 py-1 text-sm font-medium rounded-full ${
                  deployment?.toLowerCase() === 'billable'
                    ? 'bg-green-100 text-green-700'
                    : deployment?.toLowerCase() === 'free'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {deployment || 'N/A'}
              </span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {employee_id} • {designation}
            </p>
          </div>
          
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm mb-4">
            <div>
              <span className="text-slate-500 dark:text-slate-400">Department:</span>
              <p className="font-medium text-slate-700 dark:text-slate-300">{employee_department}</p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Tech Group:</span>
              <p className="font-medium text-slate-700 dark:text-slate-300">{tech_group}</p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Location:</span>
              <p className="font-medium text-slate-700 dark:text-slate-300">{emp_location}</p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Experience:</span>
              <p className="font-medium text-slate-700 dark:text-slate-300">{total_exp} (VVDN: {vvdn_exp})</p>
            </div>
          </div>

          {skill_set && (
            <div className="mb-4">
              <span className="text-slate-500 dark:text-slate-400 text-sm">Skills:</span>
              <div className="flex flex-wrap gap-2 mt-1">
                {skill_set.split(',').map((skill, skillIndex) => (
                  <span key={skillIndex} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded-full">
                    {skill.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {reason && (
            <div>
              <span className="text-slate-500 dark:text-slate-400 text-sm">Why this match:</span>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 bg-white/50 dark:bg-slate-800/50 p-3 rounded-lg">
                {reason}
              </p>
            </div>
          )}
        </div>
        
        {/* Center Right - Score */}
        <div className="text-center">
          <div className={`text-5xl font-bold ${colors.scoreColor} mb-1`}>
            {score || 0}%
          </div>
          <div className="text-sm font-semibold text-slate-600 dark:text-slate-400">
            MATCH
          </div>
        </div>
      </div>
    </div>
  );
};

// =================== MAIN COMPONENT ===================
const DynamicUIComponent = ({ layoutData }) => {
  const { dynamicData, userQuery } = useStore();
  
  if (!layoutData || !dynamicData) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-red-800 font-bold">No data or layout available</h3>
      </div>
    );
  }

  // Check if this is a project requirement query
  const projectKeywords = [
    'angular developer',
    'frontend developer', 
    'need an angular',
    'for my project',
    'project requirement'
  ];
  const isProjectQuery = projectKeywords.some(keyword => 
    userQuery?.toLowerCase().includes(keyword.toLowerCase())
  );

  // Extract employees from dynamicData
  let employees = [];
  
  if (dynamicData?.data?.database_results?.select_employees_0?.data) {
    employees = dynamicData.data.database_results.select_employees_0.data;
  } else if (dynamicData?.database_results?.select_employees_0?.data) {
    employees = dynamicData.database_results.select_employees_0.data;
  } else if (dynamicData?.results?.unified_results) {
    employees = dynamicData.results.unified_results;
  } else if (Array.isArray(dynamicData)) {
    employees = dynamicData;
  }

  if (employees?.rows && Array.isArray(employees.rows)) {
    employees = employees.rows;
  }

  console.log('DynamicUI Debug:', { employees, isProjectQuery, userQuery });

  if (!employees || employees.length === 0) {
    return (
      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-yellow-800 font-bold">No Employee Data Found</h3>
      </div>
    );
  }

  const getFieldLabel = (fieldKey) =>
    fieldKey.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

  // If project requirement query → use RequirementCard (mock data has scores)
  if (isProjectQuery && Array.isArray(employees)) {
    const sortedEmployees = [...employees].sort((a, b) => (b.score || 0) - (a.score || 0));
    
    return (
      <div className="space-y-6 p-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <h2 className="text-xl font-bold text-blue-600 dark:text-blue-400 text-center">
            Project Requirement Matches
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center mt-1">
            {sortedEmployees.length} candidates found, sorted by match score
          </p>
        </div>
        
        <div className="space-y-4">
          {sortedEmployees.map((emp, index) => (
            <RequirementCard key={index} employee={emp} />
          ))}
        </div>
      </div>
    );
  }
  
  // Else → use EmployeeCard list for search API results
  return (
    <div className="space-y-6 p-6">
      <div className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
        <h2 className="text-xl font-bold text-slate-600 dark:text-slate-400 text-center">
          Employee Search Results
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center mt-1">
          {employees.length} employees found
        </p>
      </div>
      
      <div className="space-y-3">
        {employees.map((emp, index) => (
          <EmployeeCard key={index} employee={emp} />
        ))}
      </div>
    </div>
  );
};

export default DynamicUIComponent;
