/**
 * Connection status indicator component
 * 
 * Displays the current WebSocket connection status with visual feedback
 */

import { motion, AnimatePresence } from 'framer-motion';
import type { ConnectionStatus } from '../../types/websocket.types';

interface ConnectionStatusProps {
  status: ConnectionStatus;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig = {
  disconnected: {
    color: 'bg-gray-500',
    label: 'Disconnected',
    pulse: false,
  },
  connecting: {
    color: 'bg-yellow-500',
    label: 'Connecting...',
    pulse: true,
  },
  connected: {
    color: 'bg-green-500',
    label: 'Connected',
    pulse: false,
  },
  error: {
    color: 'bg-red-500',
    label: 'Connection Error',
    pulse: true,
  },
};

const sizeConfig = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

export function ConnectionStatus({ 
  status, 
  showLabel = true,
  size = 'md' 
}: ConnectionStatusProps) {
  const config = statusConfig[status];
  const sizeClass = sizeConfig[size];

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <div className={`${sizeClass} ${config.color} rounded-full`} />
        
        {config.pulse && (
          <motion.div
            className={`absolute inset-0 ${config.color} rounded-full opacity-75`}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.75, 0, 0.75],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
      </div>

      <AnimatePresence mode="wait">
        {showLabel && (
          <motion.span
            key={status}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className="text-sm text-text-secondary"
          >
            {config.label}
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}
