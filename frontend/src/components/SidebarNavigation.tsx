import { motion, AnimatePresence } from 'motion/react';
import {
  Settings,
  TrendingUp,
  AlertTriangle,
  FileText,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
} from 'lucide-react';

export type PageType = 'control' | 'forecast' | 'risk' | 'mitigation';

interface SidebarNavigationProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
  isMinimized: boolean;
  onToggleMinimize: () => void;
}

interface NavItem {
  id: PageType;
  label: string;
  icon: typeof Settings;
  description?: string;
}

const navItems: NavItem[] = [
  { id: 'control', label: 'Control Panel', icon: Settings, description: 'Configure & Start' },
  { id: 'forecast', label: 'Forecast Analysis', icon: TrendingUp, description: 'View Forecasts' },
  { id: 'risk', label: 'Risk Analysis', icon: AlertTriangle, description: 'Risk Details' },
  { id: 'mitigation', label: 'Action Plan', icon: FileText, description: 'Mitigations' },
];

export function SidebarNavigation({
  currentPage,
  onPageChange,
  isMinimized,
  onToggleMinimize,
}: SidebarNavigationProps) {
  return (
    <motion.aside
      initial={false}
      animate={{
        width: isMinimized ? '5rem' : '18rem',
      }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
      }}
      className="fixed left-0 top-0 h-screen bg-[#191919] text-white shadow-2xl z-40 flex flex-col"
    >
      {/* Logo/Header Section */}
      <div className="h-20 flex items-center justify-between px-4 border-b border-gray-800/50 flex-shrink-0">
        <AnimatePresence mode="wait">
          {!isMinimized ? (
            <motion.div
              key="logo"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-3"
            >
              <div className="p-2 bg-[#1769FF]/20 rounded-lg">
                <LayoutDashboard className="w-6 h-6 text-[#1769FF]" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-base leading-tight">Supply Chain</span>
                <span className="text-xs text-gray-400 leading-tight">Risk Analysis</span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="logo-icon"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              className="flex items-center justify-center w-full"
            >
              <div className="p-2 bg-[#1769FF]/20 rounded-lg">
                <LayoutDashboard className="w-6 h-6 text-[#1769FF]" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <motion.button
          onClick={onToggleMinimize}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="p-2 hover:bg-gray-800/50 rounded-lg transition-colors duration-200"
          aria-label={isMinimized ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isMinimized ? (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronLeft className="w-5 h-5 text-gray-400" />
          )}
        </motion.button>
      </div>

      {/* Navigation Items - Scrollable */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-3 space-y-2">
        {navItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;

          return (
            <motion.button
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05, duration: 0.3 }}
              whileHover={{ x: isMinimized ? 0 : 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onPageChange(item.id)}
              className={`relative w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-300 group ${
                isActive
                  ? 'bg-[#1769FF] text-white shadow-lg shadow-[#1769FF]/30'
                  : 'text-gray-300 hover:bg-gray-800/50 hover:text-white'
              }`}
              title={isMinimized ? item.label : undefined}
            >
              {/* Active Indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 top-0 bottom-0 w-1 bg-white rounded-r-full"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}

              {/* Icon */}
              <motion.div
                animate={{
                  scale: isActive ? 1.1 : 1,
                }}
                transition={{ duration: 0.2 }}
                className={`flex-shrink-0 ${
                  isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
              </motion.div>

              {/* Label and Description */}
              <AnimatePresence>
                {!isMinimized && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col items-start flex-1 min-w-0"
                  >
                    <span className="text-sm font-semibold whitespace-nowrap">
                      {item.label}
                    </span>
                    {item.description && (
                      <span className="text-xs text-gray-400 group-hover:text-gray-300 whitespace-nowrap">
                        {item.description}
                      </span>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Hover Glow Effect */}
              {!isActive && (
                <motion.div
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-[#1769FF]/0 via-[#1769FF]/5 to-[#1769FF]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  initial={false}
                />
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Footer Section */}
      <div className="h-16 border-t border-gray-800/50 flex items-center justify-center px-4 flex-shrink-0">
        <AnimatePresence>
          {!isMinimized ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-xs text-gray-500 text-center"
            >
              <p>Supply Chain Risk</p>
              <p className="text-[10px]">Analysis Dashboard</p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-8 h-8 rounded-full bg-[#1769FF]/20 flex items-center justify-center"
            >
              <LayoutDashboard className="w-4 h-4 text-[#1769FF]" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}

