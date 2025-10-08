import { motion } from 'framer-motion';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  Clock,
  Calendar,
  TrendingUp,
  Megaphone,
  MoreVertical,
  Users,
  DollarSign,
  UserCheck,
  CheckSquare,
  Building2,
  GraduationCap,
  BarChart2,
  PartyPopper,
  Star,
  Pin,
} from 'lucide-react';
import useThemeColors from '../hooks/useThemeColors';
import useStore from '../store/useStore';

const PinnedIconCard = ({ card, onClick }) => {
  const colors = useThemeColors();
  const { togglePin } = useStore();

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
        return <Clock className="w-5 h-5" />;
      case 'leave':
        return <Calendar className="w-5 h-5" />;
      case 'chart':
        return <TrendingUp className="w-5 h-5" />;
      case 'announcements':
        return <Megaphone className="w-5 h-5" />;
      case 'recruitment':
        return <UserCheck className="w-5 h-5" />;
      case 'payroll':
        return <DollarSign className="w-5 h-5" />;
      case 'team':
        return <Users className="w-5 h-5" />;
      case 'approvals':
        return <CheckSquare className="w-5 h-5" />;
      case 'department':
        return <Building2 className="w-5 h-5" />;
      case 'training':
        return <GraduationCap className="w-5 h-5" />;
      case 'stats':
        return <BarChart2 className="w-5 h-5" />;
      case 'holidays':
        return <PartyPopper className="w-5 h-5" />;
      case 'employee-list':
        return <Users className="w-5 h-5" />;
      case 'leave-requests':
        return <Calendar className="w-5 h-5" />;
      case 'performance-list':
        return <Star className="w-5 h-5" />;
      default:
        return <MoreVertical className="w-5 h-5" />;
    }
  };

  const handlePinClick = (e) => {
    e.stopPropagation();
    togglePin(card.id);
  };

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      {...attributes}
      layout
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.8, opacity: 0 }}
      onClick={onClick}
      className="relative flex flex-col items-center gap-2 p-3 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-all cursor-pointer group min-w-[80px]"
    >
      <button
        onClick={handlePinClick}
        className={`absolute top-1 right-1 p-1 rounded-md transition-colors opacity-0 group-hover:opacity-100 ${colors.bgLight} ${colors.bgDark} ${colors.text} ${colors.textDark} z-10`}
      >
        <Pin className="w-3 h-3 fill-current" />
      </button>
      <div
        {...listeners}
        className="flex flex-col items-center gap-2 cursor-grab active:cursor-grabbing"
      >
        <div className={`p-3 rounded-xl text-white bg-gradient-to-br ${colors.pinnedGradient} group-hover:scale-110 transition-transform`}>
          {renderIcon()}
        </div>
        <span className="text-xs font-medium text-slate-700 dark:text-slate-300 text-center leading-tight">
          {card.title}
        </span>
      </div>
    </motion.div>
  );
};

export default PinnedIconCard;