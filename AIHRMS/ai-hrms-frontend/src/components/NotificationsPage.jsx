import {
  ArrowLeft,
  AlertTriangle,
  Clock,
  CheckCircle,
  UserPlus,
  UserMinus,
  Briefcase,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const NotificationsPage = () => {
  const navigate = useNavigate();

  const notifications = [
    {
      type: "project",
      title: "VVDN_MEXS",
      message: "Project ends in 3 days",
      priority: "critical",
      time: "2 hours ago",
      icon: AlertTriangle,
    },
    {
      type: "project",
      title: "INSU_PEGS",
      message: "Project ends in 7 days",
      priority: "warning",
      time: "5 hours ago",
      icon: AlertTriangle,
    },
    {
      type: "project",
      title: "NTGU_IMDV",
      message: "Project ends in 12 days",
      priority: "notice",
      time: "1 day ago",
      icon: AlertTriangle,
    },
    {
      type: "employee",
      title: "New Employee Added",
      message: "John Mathew has joined the Cloud & Mobile Apps team",
      priority: "success",
      time: "Just now",
      icon: UserPlus,
    },
    {
      type: "employee",
      title: "Employee Resigned",
      message: "Neha Sharma has resigned from the IoT Team",
      priority: "critical",
      time: "30 minutes ago",
      icon: UserMinus,
    },

    {
      type: "project",
      title: "New Client Project",
      message: "Received a new project from ACME Corp",
      priority: "success",
      time: "1 hour ago",
      icon: Briefcase,
    },
  ];

  const getPriorityDot = (priority) => {
    switch (priority) {
      case "critical":
        return "bg-red-600";
      case "warning":
        return "bg-orange-500";
      case "notice":
        return "bg-yellow-500";
      case "success":
        return "bg-green-600";
      default:
        return "bg-blue-500";
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case "critical":
        return "text-red-600";
      case "warning":
        return "text-orange-500";
      case "notice":
        return "text-yellow-500";
      case "success":
        return "text-green-600";
      default:
        return "text-blue-500";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200">
            Notifications
          </h1>
        </div>

        {/* All Notifications */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-xl p-6">
          <div className="space-y-4">
            {notifications.map((notification, index) => {
              const IconComponent = notification.icon;
              return (
                <div
                  key={index}
                  className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors"
                >
                  <div
                    className={`w-3 h-3 rounded-full ${getPriorityDot(
                      notification.priority
                    )}`}
                  ></div>
                  <IconComponent
                    className={`w-5 h-5 ${getPriorityIcon(
                      notification.priority
                    )}`}
                  />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800 dark:text-gray-200">
                      {notification.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {notification.message}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {notification.time}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;
