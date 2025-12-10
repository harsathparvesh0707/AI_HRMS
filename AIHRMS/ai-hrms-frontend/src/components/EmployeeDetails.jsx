import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronUp, User } from 'lucide-react';
import { useState, useEffect } from 'react';
import useStore from '../store/useStore';

const EmployeeDetails = () => {
  // const { employeeId } = useParams();
  const { employeeId: rawId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { dynamicData } = useStore();
  const [isProjectsExpanded, setIsProjectsExpanded] = useState(true);
  const [navigationHistory, setNavigationHistory] = useState([]);

  const employeeId = decodeURIComponent(rawId); 

  // Initialize navigation history from location state or create new
  useEffect(() => {
    if (location.state?.history) {
      setNavigationHistory(location.state.history);
    } else {
      setNavigationHistory([{ id: employeeId, name: null }]);
    }
  }, [employeeId, location.state]);

  // Extract employees from dynamicData
  let employees = dynamicData?.data || dynamicData?.database_results?.select_employees_0?.data || [];
  
  if (employees?.rows && Array.isArray(employees.rows)) {
    employees = employees.rows;
  }

  // Find the specific employee by ID or index
  // const employee = employees.find((emp, index) => 
  //   emp.employee_id === employeeId || index.toString() === employeeId
  // );

  const employee = employees.find((emp, index) => {
  return (
    emp.employee_id?.trim() === employeeId?.trim() ||
    index.toString() === employeeId
  );
});


  if (!employee) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-red-800 font-bold">Employee not found</h3>
          </div>
        </div>
      </div>
    );
  }

  const {
    display_name,
    first_name,
    last_name,
    employee_id,
    designation,
    employee_department,
    tech_group,
    emp_location,
    rm_name,
    rm_id,
    total_exp,
    vvdn_exp,
    // deployment,
    // email,
    // phone,
    // date_of_joining,
    employee_status,
    skill_set,
    // ai_score,
    ai_reason
  } = employee;

  const fullName = display_name || `${first_name || ''} ${last_name || ''}`.trim();

  // Handle RM click - navigate to RM's details
  const handleRMClick = (rmId, rmName) => {
    const rmEmployee = employees.find(emp => emp.employee_id === rmId);
    if (rmEmployee) {
      const newHistory = [...navigationHistory, { id: employeeId, name: fullName }];
      navigate(`/employee/${encodeURIComponent(rmId)}`, { state: { history: newHistory } });
    }
    
  };

  // Handle back navigation
  const handleBack = () => {
    if (navigationHistory.length > 1) {
      const previousEmployee = navigationHistory[navigationHistory.length - 2];
      const newHistory = navigationHistory.slice(0, -1);
      navigate(`/employee/${encodeURIComponent(previousEmployee.id)}`, { state: { history: newHistory } });
      console.log("qwertyu",newHistory)
    } else {
      navigate(-1);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        {/* <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors mb-6"
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button> */}

        {/* Main Content */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl mt-6 p-4 h-[calc(100vh-100px)] overflow-y-auto">
          <div className="space-y-4">
            
            {/* Employee Profile */}
            <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-10 h-10 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200">
                    {fullName}
                  </h2>
                  <p className="text-base text-slate-500 dark:text-slate-400 mt-1">
                    ID: {employee_id} • {designation}
                  </p>
                </div>
              </div>
            </div>

            {/* Basic Information */}
            <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-3">
                Basic Information
              </h3>
              <div className="flex flex-wrap items-center gap-6 text-sm">
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Department:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{employee_department}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Tech Group:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{tech_group || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Location:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{emp_location || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">RM:</span>
                  {rm_id ? (
                    <button
                      onClick={() => handleRMClick(rm_id, rm_name)}
                      className="ml-2 font-medium text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
                    >
                      {rm_name} ({rm_id})
                    </button>
                  ) : (
                    <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">N/A</span>
                  )}
                </div>
                {/* <div>
                  <span className="text-slate-500 dark:text-slate-400">Email:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{email || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Phone:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{phone || 'N/A'}</span>
                </div> */}
                {/* <div>
                  <span className="text-slate-500 dark:text-slate-400">Status:</span>
                  <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                    employee_status?.toLowerCase() === 'active' || deployment?.toLowerCase() === 'billable'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : employee_status?.toLowerCase() === 'inactive' || deployment?.toLowerCase() === 'free'
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  }`}>
                    {employee_status || deployment || 'N/A'}
                  </span>
                </div> */}
              </div>
            </div>

            {/* Experience */}
            <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-3">
                Experience
              </h3>
              <div className="flex flex-wrap items-center gap-6 text-sm">
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Total Experience:</span>
                  <span className="ml-2 font-bold text-slate-700 dark:text-slate-300">{total_exp || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">VVDN Experience:</span>
                  <span className="ml-2 font-bold text-slate-700 dark:text-slate-300">{vvdn_exp || 'N/A'}</span>
                </div>
                {/* <div>
                  <span className="text-slate-500 dark:text-slate-400">Date of Joining:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{date_of_joining || 'N/A'}</span>
                </div> */}
                {/* <div>
                  <span className="text-slate-500 dark:text-slate-400">Deployment:</span>
                  <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">{deployment || 'N/A'}</span>
                </div> */}
              </div>
            </div>

            {/* Skills */}
            {skill_set && (
              <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
                <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-3">
                  Skills & Technologies
                </h3>
                <div className="flex flex-wrap gap-2">
                  {skill_set.split(',').map((skill, skillIndex) => (
                    <span 
                      key={skillIndex} 
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium"
                    >
                      {skill.trim()}
                    </span>
                  ))}
                </div>  
              </div>
            )}

            {/* Projects */}
            {employee.projects && employee.projects.length > 0 && (
              <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
                <button
                  onClick={() => setIsProjectsExpanded(!isProjectsExpanded)}
                  className="flex items-center justify-between w-full text-left mb-3"
                >
                  <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
                    Projects ({employee.projects.length})
                  </h3>
                  {isProjectsExpanded ? (
                    <ChevronUp className="w-5 h-5 text-slate-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-slate-500" />
                  )}
                </button>
                
                {isProjectsExpanded && (
                  <div className="space-y-3">
                    {employee.projects.map((project, projectIndex) => (
                      <div key={projectIndex} className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <span className="text-blue-600 dark:text-blue-400 font-medium text-sm">Project Name</span>
                            <p className="font-semibold text-slate-700 dark:text-slate-300">{project.project_name}</p>
                          </div>
                          <div>
                            <span className="text-blue-600 dark:text-blue-400 font-medium text-sm">Customer</span>
                            <p className="font-semibold text-slate-700 dark:text-slate-300">{project.customer}</p>
                          </div>
                          <div>
                            <span className="text-blue-600 dark:text-blue-400 font-medium text-sm">Role</span>
                            <p className="font-semibold text-slate-700 dark:text-slate-300">{project.role}</p>
                          </div>
                          <div>
                            <span className="text-blue-600 dark:text-blue-400 font-medium text-sm">Deployment</span>
                            <p className="font-semibold text-slate-700 dark:text-slate-300">{project.deployment}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* AI Reasoning */}
            {ai_reason && (
              <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
                <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-3">
                  AI Match Analysis
                </h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {ai_reason}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeDetails;