import React, { useState } from "react";
import { MoreVertical, Users, Briefcase, UserMinus } from "lucide-react";
import { employees } from "@/components/common/emp_details";

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

const TableContent = () => {
  return (
    <div className="p-5 space-y-4">
      {/* Header */}
      <div className="bg-gray-100 shadow-sm rounded-lg p-3 grid grid-cols-7 gap-x-7 text-sm font-semibold text-gray-600 sticky top-0 z-10">
        <div className="col-span-2">Employee</div>
        <div>Experience</div>
        <div>Skills</div>
        <div>Projects</div>
        <div>Occupancy</div>
        <div className="text-right">Actions</div>
      </div>

      {/* Scrollable rows */}
      <div className="max-h-[310px] overflow-y-auto space-y-3 pr-2">
        {employees.map((emp) => {
          const allProjects = emp.projects_worked_on || [];

          // Convert occupancy object → array of {name, occupancy}
          let occupancyProjects = Object.entries(emp.occupancy || {}).map(
            ([name, occ]) => ({ name, occupancy: occ })
          );

          // For freepool employees, show past project experience + free time
          if (emp.status === "freepool") {
            if (occupancyProjects.length === 0) {
              // No current projects, show 100% free
              occupancyProjects = [
                { name: "Free Pool", occupancy: 100, isFree: true },
              ];
            } else {
              // Has some project occupancy, add free pool for remaining
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
              className="bg-white shadow-md rounded-lg p-3 grid grid-cols-7 gap-x-7 items-center"
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
                {emp.skills.map((skill, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600"
                  >
                    {skill}
                  </span>
                ))}
              </div>

              {/* Projects */}
              <div className="flex flex-wrap gap-1">
                {allProjects.length > 0 ? (
                  allProjects.slice(0, 4).map((proj, i) => (
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
  );
};

// Projects Section (unchanged for now, unless you want from employees data)
const upcomingProjects = [
  { date: "03 Jan", name: "E-commerce Website Redesign" },
  { date: "05 Jan", name: "Mobile App Development" },
  { date: "07 Jan", name: "HR Management System Upgrade" },
  { date: "10 Jan", name: "IoT Dashboard Implementation" },
  { date: "12 Jan", name: "AI Chatbot Integration" },
];

const Projects = () => {
  const visibleProjects = upcomingProjects.slice(0, 3);
  return (
    <div className="flex flex-col gap-4">
      {visibleProjects.map((project, index) => (
        <div
          key={index}
          className="flex items-center gap-4 border-b pb-3 last:border-b-0"
        >
          {/* Date */}
          <div className="text-center">
            <p className="text-lg font-bold text-gray-800">
              {project.date.split(" ")[0]}
            </p>
            <p className="text-sm text-gray-500">{project.date.split(" ")[1]}</p>
          </div>

          {/* Project Name */}
          <div className="flex-1">
            <p className="font-medium text-gray-800">{project.name}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

// Stats will be fetched from API
const employeeStats = [];

const EmployeeStat = () => {
  return <div>Stats will be loaded from API</div>;
};

export { TableContent, Projects, EmployeeStat };
