import React from 'react';
import { employees } from '@/components/common/emp_details';
import { Calendar, Code } from 'lucide-react';

const EmployeeCards = ({ filter = 'all' }) => {
  const filteredEmployees = employees.filter(emp => {
    if (filter === 'freepool') return emp.status === 'freepool';
    if (filter === 'active') return emp.status === 'active';
    return true;
  });

  const getStatusColor = (status) => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          {filter === 'freepool' ? 'Free Pool Employees' : filter === 'active' ? 'Active Employees' : 'All Employees'}
        </h2>
        <p className="text-gray-600">
          {filteredEmployees.length} employee{filteredEmployees.length !== 1 ? 's' : ''} found
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredEmployees.map((emp) => (
          <div key={emp.id} className="bg-white rounded-lg shadow-md border hover:shadow-lg transition-shadow p-6">
            {/* Profile Icon */}
            <div className="flex flex-col items-center mb-4">
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mb-3">
                <span className="text-2xl font-bold text-blue-600">
                  {emp.name.charAt(0)}
                </span>
              </div>
              
              {/* Status Badge */}
              <span className={`px-3 py-1 text-xs rounded-full font-medium ${getStatusColor(emp.status)}`}>
                {emp.status}
              </span>
            </div>

            {/* Employee Info */}
            <div className="text-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                {emp.name}
              </h3>
              <p className="text-sm text-gray-600 mb-2">
                {emp.designation}
              </p>
              
              {/* Experience */}
              <div className="flex items-center justify-center gap-1 text-sm text-gray-500 mb-3">
                <Calendar className="w-4 h-4" />
                <span>{emp.years_of_experience} years experience</span>
              </div>
            </div>

            {/* Skills */}
            <div className="mb-4">
              <div className="flex items-center gap-1 mb-2">
                <Code className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Skills</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {emp.skills.slice(0, 4).map((skill, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded border"
                  >
                    {skill}
                  </span>
                ))}
                {emp.skills.length > 4 && (
                  <span className="px-2 py-1 text-xs bg-gray-50 text-gray-600 rounded border">
                    +{emp.skills.length - 4} more
                  </span>
                )}
              </div>
            </div>

            {/* Department */}
            <div className="text-center">
              <span className="text-xs text-gray-500">
                {emp.department}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmployeeCards;