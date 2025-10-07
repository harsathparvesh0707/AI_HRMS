import React, { useState } from 'react';
import { employees } from '@/components/common/emp_details';
import { MoreVertical } from 'lucide-react';

const colors = [
  "bg-green-500",
  "bg-blue-500", 
  "bg-yellow-500",
  "bg-red-500",
  "bg-purple-500",
];

const OccupancyBar = ({ occupancyProjects, colors }) => {
  const [tooltip, setTooltip] = useState({ show: false, content: '', x: 0, y: 0 });

  const handleMouseEnter = (proj, event) => {
    const rect = event.target.getBoundingClientRect();
    setTooltip({
      show: true,
      content: `${proj.name}: ${proj.occupancy}%`,
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    });
  };

  const handleMouseLeave = () => {
    setTooltip({ show: false, content: '', x: 0, y: 0 });
  };

  return (
    <div className="w-full relative">
      <div className="w-full bg-gray-200 h-3 rounded-full flex overflow-hidden">
        {occupancyProjects.map((proj, i) => {
          const projectColors = proj.isFree ? "bg-gray-300" : colors[i % colors.length];
          return (
            <div
              key={i}
              className={`${projectColors} h-3 cursor-pointer hover:opacity-80 transition-opacity`}
              style={{ width: `${proj.occupancy}%` }}
              onMouseEnter={(e) => handleMouseEnter(proj, e)}
              onMouseLeave={handleMouseLeave}
            />
          );
        })}
      </div>
      {tooltip.show && (
        <div
          className="fixed z-50 px-2 py-1 text-xs bg-gray-900 text-white rounded shadow-lg pointer-events-none"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: 'translate(-50%, -100%)'
          }}
        >
          {tooltip.content}
        </div>
      )}
    </div>
  );
};

const EmployeeTable = ({ filter }) => {
  const filteredEmployees = filter ? employees.filter(emp => emp.status === filter) : employees;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">All Employees</h2>
        <p className="text-gray-600">{filteredEmployees.length} employees total</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        {/* Header */}
        <div className="bg-gray-50 p-4 grid grid-cols-7 gap-4 text-sm font-semibold text-gray-600 border-b">
          <div className="col-span-2">Employee</div>
          <div>Experience</div>
          <div>Skills</div>
          <div>Projects</div>
          <div>Occupancy</div>
          <div className="text-right">Actions</div>
        </div>

        {/* Scrollable rows */}
        <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
          {filteredEmployees.map((emp) => {
            const allProjects = emp.projects_worked_on || [];

            // Convert occupancy object → array of {name, occupancy}
            let occupancyProjects = Object.entries(emp.occupancy || {}).map(
              ([name, occ]) => ({ name, occupancy: occ })
            );

            // For freepool employees, show past project experience + free time
            if (emp.status === "freepool") {
              if (occupancyProjects.length === 0) {
                occupancyProjects = [
                  { name: "Free Pool", occupancy: 100, isFree: true },
                ];
              } else {
                const totalOccupied = occupancyProjects.reduce((sum, proj) => sum + proj.occupancy, 0);
                if (totalOccupied < 100) {
                  occupancyProjects.push({
                    name: "Free Pool",
                    occupancy: 100 - totalOccupied,
                    isFree: true
                  });
                }
              }
            }

            return (
              <div
                key={emp.id}
                className="p-4 grid grid-cols-7 gap-4 items-center border-b hover:bg-gray-50"
              >
                {/* Employee Info */}
                <div className="col-span-2 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center font-bold text-blue-600">
                    {emp.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium">{emp.name}</p>
                    <p className="text-xs text-gray-500">{emp.designation}</p>
                    <p className="text-xs text-gray-400">{emp.contact}</p>
                  </div>
                </div>

                {/* Experience */}
                <div>{emp.years_of_experience} yrs</div>

                {/* Skills */}
                <div className="flex flex-wrap gap-1">
                  {emp.skills.slice(0, 3).map((skill, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600"
                    >
                      {skill}
                    </span>
                  ))}
                  {emp.skills.length > 3 && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                      +{emp.skills.length - 3}
                    </span>
                  )}
                </div>

                {/* Projects */}
                <div className="flex flex-wrap gap-1">
                  {allProjects.length > 0 ? (
                    allProjects.slice(0, 2).map((proj, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-600"
                      >
                        {proj}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-red-500">No Projects</span>
                  )}
                  {allProjects.length > 2 && (
                    <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600">
                      +{allProjects.length - 2}
                    </span>
                  )}
                </div>

                {/* Occupancy Bar */}
                <OccupancyBar occupancyProjects={occupancyProjects} colors={colors} />

                {/* Actions */}
                <div className="text-right">
                  <button className="p-1 hover:bg-gray-100 rounded">
                    <MoreVertical className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default EmployeeTable;