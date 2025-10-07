import React from 'react';
import { employees } from '@/components/common/emp_details';
import Cards from '@/components/common/Cards';
import { Pin, MoreHorizontal } from 'lucide-react';

const EmployeeList = ({ filter = 'all' }) => {
  const cardActions = (
    <>
      <button className="p-1 rounded hover:bg-gray-100">
        <MoreHorizontal className="w-5 h-5 text-gray-600" />
      </button>
      <button className="p-1 rounded hover:bg-gray-100">
        <Pin className="w-4 h-4 text-gray-500" />
      </button>
    </>
  );

  const filteredEmployees = employees.filter(emp => {
    if (filter === 'freepool') return emp.status === 'freepool';
    if (filter === 'active') return emp.status === 'active';
    return true;
  });

  const getStatusColor = (status) => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  return (
    <Cards header={`${filter === 'freepool' ? 'Free Pool' : filter === 'active' ? 'Active' : 'All'} Employees`} actions={cardActions}>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filteredEmployees.map((emp) => (
          <div key={emp.id} className="flex items-center gap-3 p-3 bg-white rounded-lg border">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center font-bold text-blue-600 flex-shrink-0">
              {emp.name.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-medium text-gray-900 truncate">{emp.name}</h4>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(emp.status)}`}>
                  {emp.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{emp.designation}</p>
              <div className="flex flex-wrap gap-1">
                {emp.skills.slice(0, 3).map((skill, i) => (
                  <span key={i} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                    {skill}
                  </span>
                ))}
                {emp.skills.length > 3 && (
                  <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                    +{emp.skills.length - 3}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Cards>
  );
};

export default EmployeeList;