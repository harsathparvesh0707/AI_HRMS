import React from "react";
import { CheckCircle, XCircle, Calendar, Bell, Folder, Clock } from "lucide-react";

const AttendanceCard = ({ status, leave_type, start_date, end_date }) => {
  const getStatusIcon = () => {
    switch (status) {
      case "Present": return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "Absent": return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Calendar className="w-5 h-5 text-orange-500" />;
    }
  };

  return (
    <div className="p-4">
      <div className="flex items-center gap-3">
        {getStatusIcon()}
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          status === "Present" ? "text-green-600 bg-green-50" : 
          status === "Absent" ? "text-red-600 bg-red-50" : "text-orange-600 bg-orange-50"
        }`}>
          {status}
        </span>
      </div>
    </div>
  );
};

const LeaveBalanceCard = ({ available, used }) => {
  const total = available + used;
  const usedPercentage = (used / total) * 100;

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-500" />
          <span className="text-lg font-semibold">{available}</span>
          <span className="text-sm text-gray-600">days left</span>
        </div>
        <span className="text-sm text-gray-600">{used} used</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${usedPercentage}%` }}></div>
      </div>
    </div>
  );
};

const RecentProjectsCard = ({ projects }) => (
  <div className="p-4 space-y-3">
    {(projects || []).slice(0, 3).map((project, index) => (
      <div key={index} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Folder className="w-4 h-4 text-gray-400" />
          <div>
            <p className="font-medium text-sm">{project.project_name}</p>
            <p className="text-xs text-gray-500">{project.department}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded text-xs ${
          project.status === "Completed" ? "text-green-600 bg-green-50" : "text-orange-600 bg-orange-50"
        }`}>
          {project.status}
        </span>
      </div>
    ))}
  </div>
);

const NotificationsCard = ({ notifications }) => (
  <div className="p-4 space-y-3">
    {(notifications || []).slice(0, 2).map((notification, index) => (
      <div key={index} className="flex gap-3">
        <Bell className="w-4 h-4 text-blue-500 mt-1" />
        <div>
          <p className="font-medium text-sm">{notification.title}</p>
          <p className="text-xs text-gray-600">{notification.summary}</p>
        </div>
      </div>
    ))}
  </div>
);

const DynamicCard = ({ type, data }) => {
  switch (type) {
    case "attendance": return <AttendanceCard {...data} />;
    case "leave_balance": return <LeaveBalanceCard {...data} />;
    case "recent_projects": return <RecentProjectsCard projects={data} />;
    case "notifications": return <NotificationsCard notifications={data} />;
    default: return <div className="p-4">Unknown card type</div>;
  }
};

export default DynamicCard;