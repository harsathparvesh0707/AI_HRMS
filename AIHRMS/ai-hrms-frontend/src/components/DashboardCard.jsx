import { motion } from 'framer-motion';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  Pin,
  X,
  Clock,
  Calendar,
  TrendingUp,
  Megaphone,
  MoreVertical,
  GripVertical,
  Users,
  DollarSign,
  UserCheck,
  CheckSquare,
  Building2,
  GraduationCap,
  BarChart2,
  PartyPopper,
  ArrowUp,
  ArrowDown,
  Mail,
  Star,
  Filter,
} from 'lucide-react';
import useStore from '../store/useStore';
import useThemeColors from '../hooks/useThemeColors';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Area,
  AreaChart,
  Cell,
} from 'recharts';

const DashboardCard = ({ card }) => {
  const { togglePin, removeCard } = useStore();
  const colors = useThemeColors();

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const renderIcon = () => {
    switch (card.type) {
      case 'attendance':
        return <Clock className="w-4 h-4" />;
      case 'leave':
        return <Calendar className="w-4 h-4" />;
      case 'chart':
        return <TrendingUp className="w-4 h-4" />;
      case 'announcements':
        return <Megaphone className="w-4 h-4" />;
      case 'recruitment':
        return <UserCheck className="w-4 h-4" />;
      case 'payroll':
        return <DollarSign className="w-4 h-4" />;
      case 'team':
        return <Users className="w-4 h-4" />;
      case 'approvals':
        return <CheckSquare className="w-4 h-4" />;
      case 'department':
        return <Building2 className="w-4 h-4" />;
      case 'training':
        return <GraduationCap className="w-4 h-4" />;
      case 'stats':
        return <BarChart2 className="w-4 h-4" />;
      case 'holidays':
        return <PartyPopper className="w-4 h-4" />;
      case 'employee-list':
        return <Users className="w-4 h-4" />;
      case 'leave-requests':
        return <Calendar className="w-4 h-4" />;
      case 'performance-list':
        return <Star className="w-4 h-4" />;
      default:
        return <MoreVertical className="w-4 h-4" />;
    }
  };

  const renderContent = () => {
    switch (card.type) {
      case 'attendance':
        return (
          <div className="flex flex-col items-center justify-center py-2">
            <div className="relative w-24 h-24">
              <svg className="transform -rotate-90 w-24 h-24">
                <circle
                  cx="48"
                  cy="48"
                  r="42"
                  stroke="currentColor"
                  strokeWidth="6"
                  fill="none"
                  className="text-slate-200 dark:text-slate-700"
                />
                <circle
                  cx="48"
                  cy="48"
                  r="42"
                  stroke="currentColor"
                  strokeWidth="6"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 42}`}
                  strokeDashoffset={`${
                    2 * Math.PI * 42 * (1 - card.data.percentage / 100)
                  }`}
                  className="text-blue-600 transition-all duration-1000"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {card.data.percentage}%
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">
                  Attendance
                </span>
              </div>
            </div>
            <div className="mt-2 text-center">
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {card.data.hoursWorked} / {card.data.totalHours} hours
              </p>
            </div>
          </div>
        );

      case 'leave':
        return (
          <div className="py-3">
            <div className="flex justify-between items-center mb-3">
              <div>
                <p className="text-xl font-bold text-slate-900 dark:text-white">
                  {card.data.available}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400">
                  Days Available
                </p>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-slate-900 dark:text-white">
                  {card.data.used}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400">
                  Days Used
                </p>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{
                      width: `${(card.data.used / card.data.total) * 100}%`,
                    }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className="h-full bg-gradient-to-r from-blue-600 to-cyan-600"
                  />
                </div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400">
                  {((card.data.used / card.data.total) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        );

      case 'chart':
        const chartHeight = card.size === 'wide' || card.size === 'large' ? 'h-32' : 'h-28';
        return (
          <div className={`py-2 ${chartHeight}`}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={card.data.series}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.3} />
                <XAxis
                  dataKey="month"
                  stroke="#64748b"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#colorValue)"
                  dot={{ fill: '#3b82f6', r: 4, strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 6, strokeWidth: 2, stroke: '#fff' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        );

      case 'announcements':
        const announcementHeight = card.size === 'tall' || card.size === 'large' ? 'max-h-80' : 'max-h-40';
        return (
          <div className={`py-1 space-y-2 ${announcementHeight} overflow-y-auto scrollbar-hide`}>
            {card.data.items.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <p className="text-xs text-slate-900 dark:text-white mb-0.5">
                  {item.text}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400">
                  {new Date(item.date).toLocaleDateString()}
                </p>
              </motion.div>
            ))}
          </div>
        );

      case 'recruitment':
        const recruitmentHeight = card.size === 'wide' || card.size === 'large' ? 'h-36' : 'h-32';
        return (
          <div className="py-2">
            <div className={`${recruitmentHeight}`}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={card.data.stages}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.3} />
                  <XAxis
                    dataKey="name"
                    stroke="#64748b"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  />
                  <Bar
                    dataKey="count"
                    radius={[8, 8, 0, 0]}
                  >
                    {card.data.stages.map((entry, index) => {
                      const colors = ['#3b82f6', '#06b6d4', '#8b5cf6', '#10b981'];
                      return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'payroll':
        return (
          <div className="py-2">
            <div className="text-center mb-3">
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {card.data.current}
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                Current Month
              </div>
            </div>
            <div className="flex items-center justify-center gap-2 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <ArrowUp className="w-3 h-3 text-green-600 dark:text-green-400" />
              <span className="text-xs font-semibold text-green-600 dark:text-green-400">
                +{card.data.change}% vs last month
              </span>
            </div>
            <div className="mt-2 text-center">
              <span className="text-xs text-slate-600 dark:text-slate-400">
                {card.data.employees} employees paid
              </span>
            </div>
          </div>
        );

      case 'team':
        const teamHeight = card.size === 'tall' || card.size === 'large' ? 'max-h-80' : 'max-h-40';
        return (
          <div className={`py-1 space-y-2 ${teamHeight} overflow-y-auto scrollbar-hide`}>
            {card.data.members.map((member, index) => (
              <motion.div
                key={member.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-2 p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <img
                  src={member.avatar}
                  alt={member.name}
                  className="w-8 h-8 rounded-full"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                    {member.name}
                  </p>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                    {member.role}
                  </p>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  member.status === 'active' ? 'bg-green-500' : 'bg-orange-500'
                }`} />
              </motion.div>
            ))}
          </div>
        );

      case 'approvals':
        return (
          <div className="py-2">
            <div className="text-center mb-3">
              <div className="text-3xl font-bold text-slate-900 dark:text-white">
                {card.data.total}
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                Pending Items
              </div>
            </div>
            <div className="space-y-1.5">
              {card.data.items.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-xs text-slate-700 dark:text-slate-300">
                    {item.type}
                  </span>
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'department':
        const deptHeight = card.size === 'wide' || card.size === 'large' ? 'h-36' : 'h-32';
        return (
          <div className="py-2">
            <div className="flex items-center justify-between mb-2 px-2">
              <span className="text-lg font-bold text-slate-900 dark:text-white">
                {card.data.total}
              </span>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">
                Total Staff
              </span>
            </div>
            <div className={`${deptHeight}`}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={card.data.departments} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.3} />
                  <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="#64748b"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                    width={80}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                    {card.data.departments.map((dept, index) => (
                      <Cell key={`cell-${index}`} fill={dept.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'training':
        return (
          <div className="py-2">
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center">
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {card.data.completed}
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400">
                  Completed
                </div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {card.data.ongoing}
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400">
                  Ongoing
                </div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-orange-600 dark:text-orange-400">
                  {card.data.upcoming}
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400">
                  Upcoming
                </div>
              </div>
            </div>
            <div className="p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg text-center">
              <span className="text-xs font-semibold text-slate-900 dark:text-white">
                {card.data.completionRate}% Completion Rate
              </span>
            </div>
          </div>
        );

      case 'stats':
        return (
          <div className="py-2">
            <div className="grid grid-cols-2 gap-2">
              {card.data.metrics.map((metric, idx) => (
                <div key={idx} className="p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <div className="text-lg font-bold text-slate-900 dark:text-white">
                    {metric.value}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400 mb-1">
                    {metric.label}
                  </div>
                  <div className={`flex items-center gap-1 text-[10px] font-semibold ${
                    metric.trend === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {metric.trend === 'up' ? (
                      <ArrowUp className="w-3 h-3" />
                    ) : (
                      <ArrowDown className="w-3 h-3" />
                    )}
                    {metric.change}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'holidays':
        return (
          <div className="py-2 space-y-2">
            {card.data.holidays.map((holiday, idx) => (
              <div
                key={idx}
                className="flex justify-between items-center p-2 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-lg"
              >
                <div>
                  <p className="text-xs font-semibold text-slate-900 dark:text-white">
                    {holiday.name}
                  </p>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400">
                    {new Date(holiday.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </p>
                </div>
                <PartyPopper className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
            ))}
          </div>
        );

      case 'employee-list':
        return (
          <div className="py-2">
            <div className="flex gap-1 mb-2 overflow-x-auto scrollbar-hide">
              {card.data.filters.slice(0, 3).map((filter, idx) => (
                <button
                  key={idx}
                  className="px-2 py-1 text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors whitespace-nowrap"
                >
                  {filter}
                </button>
              ))}
            </div>
            <div className="space-y-1 max-h-64 overflow-y-auto scrollbar-hide">
              {card.data.employees.slice(0, 6).map((emp, idx) => (
                <motion.div
                  key={emp.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.03 }}
                  className="flex items-center gap-2 p-1.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                      {emp.name}
                    </p>
                    <div className="flex items-center gap-2">
                      <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                        {emp.position}
                      </p>
                      <span className="text-[10px] text-slate-400">•</span>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400">
                        {emp.department}
                      </p>
                    </div>
                  </div>
                  <div className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                    emp.status === 'Active'
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                      : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                  }`}>
                    {emp.status}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        );

      case 'leave-requests':
        return (
          <div className="py-2">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700">
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Employee</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Type</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Duration</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Days</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {card.data.requests.map((req, idx) => (
                    <motion.tr
                      key={req.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.05 }}
                      className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    >
                      <td className="py-2 text-slate-900 dark:text-white font-medium">{req.employee}</td>
                      <td className="py-2 text-slate-600 dark:text-slate-400">{req.type}</td>
                      <td className="py-2 text-slate-600 dark:text-slate-400 text-[10px]">
                        {new Date(req.from).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - {new Date(req.to).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </td>
                      <td className="py-2 text-slate-900 dark:text-white font-semibold">{req.days}</td>
                      <td className="py-2">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                          req.status === 'Approved'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                        }`}>
                          {req.status}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      case 'performance-list':
        return (
          <div className="py-2">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700">
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Employee</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Reviewer</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Score</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Status</th>
                    <th className="text-left py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {card.data.reviews.map((review, idx) => (
                    <motion.tr
                      key={review.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.05 }}
                      className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    >
                      <td className="py-2 text-slate-900 dark:text-white font-medium">{review.employee}</td>
                      <td className="py-2 text-slate-600 dark:text-slate-400">{review.reviewer}</td>
                      <td className="py-2">
                        {review.score ? (
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                            <span className="text-slate-900 dark:text-white font-semibold">{review.score}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                      <td className="py-2">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                          review.status === 'Completed'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : review.status === 'In Progress'
                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                            : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-400'
                        }`}>
                          {review.status}
                        </span>
                      </td>
                      <td className="py-2 text-slate-600 dark:text-slate-400 text-[10px]">
                        {new Date(review.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      default:
        return <div className="py-2 text-xs">No data available</div>;
    }
  };

  // Determine grid size classes based on card size
  const getSizeClasses = () => {
    switch (card.size) {
      case 'small':
        return 'col-span-1';
      case 'medium':
        return 'col-span-1';
      case 'wide':
        return 'col-span-1 md:col-span-2';
      case 'large':
        return 'col-span-1 md:col-span-2';
      case 'tall':
        return 'col-span-1';
      default:
        return 'col-span-1';
    }
  };

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      {...attributes}
      layout
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      className={`${getSizeClasses()} bg-white dark:bg-slate-800 rounded-xl shadow-sm border ${
        card.pinned
          ? `${colors.border} ring-1 ${colors.ring} dark:${colors.ring}`
          : 'border-slate-200 dark:border-slate-700'
      } overflow-hidden hover:shadow-md transition-all`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <button
            {...listeners}
            className="cursor-grab active:cursor-grabbing text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            aria-label="Drag to reorder"
          >
            <GripVertical className="w-3 h-3" />
          </button>
          <div className={`p-1.5 rounded-lg text-white ${
            card.pinned
              ? `bg-gradient-to-br ${colors.pinnedGradient}`
              : `bg-gradient-to-br ${colors.iconGradient}`
          }`}>
            {renderIcon()}
          </div>
          <h3 className="font-semibold text-sm text-slate-900 dark:text-white">
            {card.title}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => togglePin(card.id)}
            className={`p-1 rounded-md transition-colors ${
              card.pinned
                ? `${colors.bgLight} ${colors.bgDark} ${colors.text} ${colors.textDark}`
                : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400'
            }`}
          >
            <Pin
              className={`w-3 h-3 ${card.pinned ? 'fill-current' : ''}`}
            />
          </button>
          <button
            onClick={() => removeCard(card.id)}
            className="p-1 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-3">{renderContent()}</div>

      {/* Footer */}
      {(card.type === 'attendance' || card.type === 'leave' || card.type === 'recruitment' ||
        card.type === 'payroll' || card.type === 'approvals' || card.type === 'department' ||
        card.type === 'employee-list' || card.type === 'leave-requests' || card.type === 'performance-list') && (
        <div className="px-3 pb-3">
          <button
            className={`w-full py-1.5 px-3 bg-gradient-to-r ${colors.gradient} text-white rounded-lg ${colors.gradientHover} transition-all font-medium text-xs`}
          >
            View Details
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default DashboardCard;
