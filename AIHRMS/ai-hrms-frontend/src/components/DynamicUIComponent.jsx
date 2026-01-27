import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, ChevronDown, ChevronUp } from 'lucide-react';
import useStore from '../store/useStore';
import { em } from 'framer-motion/client';



// =================== EMPLOYEE CARD COMPONENT ===================
const EmployeeCard = ({ employee, index }) => {
  const navigate = useNavigate();
  
  const handleCardClick = () => {
    navigate(`/employee/${index}`);
  };
  
  if (!employee) return null;

  const {
    employee_id,
    display_name,
    first_name,
    last_name,
    designation,
    tech_group,
    emp_location
  } = employee;

  const fullName = display_name || `${first_name || ''} ${last_name || ''}`.trim();

  return (
    <div 
      onClick={handleCardClick}
      className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer p-4"
    >
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
          <User className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        
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
          
          <div className="flex flex-wrap gap-4 text-sm text-slate-600 dark:text-slate-400">
            <span>{designation || 'N/A'}</span>
            <span>•</span>
            <span>{tech_group || 'N/A'}</span>
            <span>•</span>
            <span>{emp_location || 'N/A'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// =================== REQUIREMENT CARD COMPONENT ===================
const RequirementCard = ({ employee, index }) => {
  const navigate = useNavigate();
  const [showAllSkills, setShowAllSkills] = useState(false);
  const [showReason, setShowReason] = useState(false);
  
  const handleCardClick = (e) => {
    if (e.target.closest('button')) return;
    navigate(`/employee/${index}`);
  };
  
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
    ai_score,
    skill_set,
    ai_reason
  } = employee;

  // Get card colors based on score (green to red gradient)
  const getCardColors = () => {
    if (ai_score >= 70) {
      return {
        border: 'border-green-500',
        bg: 'bg-green-50 dark:bg-green-900/20',
        scoreColor: 'text-green-600 dark:text-green-400'
      };
    } else if (ai_score >= 50) {
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
    <div 
      onClick={handleCardClick}
      className={`p-4 ${colors.bg} border-2 ${colors.border} rounded-lg shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer`}
    >
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3">
        {/* Left Section - Employee Info */}
        <div className="flex-1 lg:pr-6">
          <div className="mb-2">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                {display_name}
              </h2>
              <span className="text-sm font-semibold text-slate-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded-full border border-blue-200 dark:border-blue-800">
                {designation}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
             <i className="fa-regular fa-id-card"></i> {employee_id} &nbsp; <i className="fa-solid fa-building"></i> {employee_department} &nbsp; <i className="fa-solid fa-location-dot"></i> {emp_location} &nbsp; <i className="fa-solid fa-laptop-code"></i> {tech_group} &nbsp; <i className="fa-solid fa-business-time"></i>  {total_exp}
            </p>
          </div>
          
          {/* <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm mb-4"> */}
            {/* <div> */}
              {/* <span className="text-slate-500 dark:text-slate-400">Department:</span> */}
              {/* <p className="font-medium text-slate-700 dark:text-slate-300">{employee_department}</p> */}
            {/* </div> */}
            {/* <div> */}
              {/* <span className="text-slate-500 dark:text-slate-400">Tech Group:</span> */}
              {/* <p className="font-medium text-slate-700 dark:text-slate-300">{tech_group}</p> */}
            {/* </div> */}
            {/* <div> */}
              {/* <span className="text-slate-500 dark:text-slate-400">Location:</span> */}
              {/* <p className="font-medium text-slate-700 dark:text-slate-300">{emp_location}</p> */}
            {/* </div> */}
            {/* <div> */}
              {/* <span className="text-slate-500 dark:text-slate-400">Experience:</span> */}
              {/* <p className="font-medium text-slate-700 dark:text-slate-300">{total_exp} (VVDN: {vvdn_exp})</p> */}
            {/* </div> */}
          {/* </div> */}

          {skill_set && (
            <div className="mb-2">
              <span className="text-slate-500 dark:text-slate-400 text-xs">Skills:</span>
              <div className="flex flex-wrap gap-1.5 mt-0.5">
                {skill_set.split(',').slice(0, showAllSkills ? undefined : 5).map((skill, skillIndex) => (
                  <span key={skillIndex} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded-full">
                    {skill.trim()}
                  </span>
                ))}
                {skill_set.split(',').length > 5 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowAllSkills(!showAllSkills);
                    }}
                    className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded-full hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors"
                  >
                    {showAllSkills ? 'Show Less' : `+${skill_set.split(',').length - 5} More`}
                  </button>
                )}
              </div>
            </div>
          )}

          {employee.projects && employee.projects.length > 0 && (
            <div className="mb-2">
              <span className="text-slate-500 dark:text-slate-400 text-xs">Projects: </span>
              <span className="text-xs text-slate-700 dark:text-slate-300">
                {employee.projects.map((project, projectIndex) => (
                  <span key={projectIndex}>
                    <span className="font-semibold">{project.project_name}</span>
                    <span className="text-slate-500 dark:text-slate-400"> ({project.customer})</span>
                    {projectIndex < employee.projects.length - 1 && <span className="text-slate-400">, </span>}
                  </span>
                ))}
              </span>
            </div>
          )}

          {ai_reason && (
            <div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowReason(!showReason);
                }}
                className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
              >
                <span>Why this match?</span>
                {showReason ? (
                  <ChevronUp className="w-3 h-3" />
                ) : (
                  <ChevronDown className="w-3 h-3" />
                )}
              </button>
              {showReason && (
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 bg-white/50 dark:bg-slate-800/50 p-2 rounded-lg">
                  {ai_reason}
                </p>
              )}
            </div>
          )}
        </div>
        
        {/* Right Section - Score & Category Breakdown */}
        <div className="w-full lg:w-48 flex-shrink-0">
          <div className="flex items-center justify-center mb-2">
            <div className="relative w-14 h-14 lg:w-16 lg:h-16">
              <svg className="w-14 h-14 lg:w-16 lg:h-16 transform rotate-0" viewBox="0 0 36 36">
                <path
                  className="text-slate-200 dark:text-slate-700"
                  stroke="currentColor"
                  strokeWidth="3"
                  fill="transparent"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={colors.scoreColor.replace('text-', 'text-')}
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeDasharray={`${ai_score || 0}, 100`}
                  strokeLinecap="round"
                  fill="transparent"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className={`text-sm font-bold ${colors.scoreColor}`}>
                  {ai_score || 0}%
                </div>
              </div>
            </div>
          </div>
          
          {employee.ai_criteria && (
            <div className="space-y-1.5">
              {Object.entries(employee.ai_criteria).map(([criteria, criteriaScore]) => (
                <div key={criteria}>
                  <div className="flex justify-between items-center mb-0.5">
                    <span className="text-[14px] font-medium text-slate-600 dark:text-slate-400">
                      {criteria}
                    </span>
                    <span className="text-[13px] font-bold text-slate-700 dark:text-slate-300">
                      {criteriaScore}%
                    </span>
                  </div>
                  <div className="bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        criteriaScore >= 80 ? 'bg-green-500' :
                        criteriaScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${criteriaScore}%` }}
                    >
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
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

  // Check if this is a project requirement query from API response
  const isProjectQuery = dynamicData?.employee_search;

  // Extract employees from dynamicData
  let employees = dynamicData?.data || dynamicData?.database_results?.select_employees_0?.data || [];
  
  if (employees?.rows && Array.isArray(employees.rows)) {
    employees = employees.rows;
  }

  if (!employees || employees.length === 0) {
    return (
      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-yellow-800 font-bold">No Employee Data Found</h3>
      </div>
    );
  }

  // const getFieldLabel = (fieldKey) =>
  //   fieldKey.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

  // If project requirement query → use RequirementCard (mock data has scores)
  if (isProjectQuery===false && Array.isArray(employees)) {
    
    const sortedEmployees = [...employees].sort((a, b) => (b.score || 0) - (a.score || 0));
    
    return (
      <div className="space-y-6 p-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">
          Project Requirement Matches
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          {sortedEmployees.length} candidates found, sorted by match score
        </p>
        
        <div className="space-y-4">
          {sortedEmployees.map((emp, index) => (
            <RequirementCard key={index} employee={emp} index={index} />
          ))}
        </div>
      </div>
    );
  }
  
  // Else → use EmployeeCard list for search API results
  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">
        Employee Search Results
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
        {employees.length} employees found
      </p>
      
      <div className="space-y-3">
        {employees.map((emp, index) => (
          <EmployeeCard key={index} employee={emp} index={index} />
        ))}
      </div>
    </div>
  );
};

export default DynamicUIComponent;