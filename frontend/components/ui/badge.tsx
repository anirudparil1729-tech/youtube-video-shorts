import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { JobStatus } from '@/types';
import { CheckCircle, Clock, Play, XCircle, AlertCircle, Pause } from 'lucide-react';

interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  status?: JobStatus;
}

const statusConfig = {
  pending: { variant: 'default', icon: Clock },
  queued: { variant: 'info', icon: Clock },
  processing: { variant: 'warning', icon: Play },
  completed: { variant: 'success', icon: CheckCircle },
  failed: { variant: 'error', icon: XCircle },
  cancelled: { variant: 'default', icon: Pause },
};

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', status, ...props }, ref) => {
    const BadgeIcon = status ? statusConfig[status].icon : null;
    const variantClass = status ? statusConfig[status].variant : variant;

    const variants = {
      default: 'bg-gray-100 text-gray-800',
      success: 'bg-success-100 text-success-800',
      warning: 'bg-warning-100 text-warning-800',
      error: 'bg-error-100 text-error-800',
      info: 'bg-primary-100 text-primary-800',
    };

    const sizes = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-2.5 py-1.5 text-sm',
      lg: 'px-3 py-2 text-base',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full font-medium',
          variants[variantClass],
          sizes[size],
          className
        )}
        {...props}
      >
        {BadgeIcon && (
          <BadgeIcon className={cn(
            size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4',
            size !== 'sm' && 'mr-1'
          )} />
        )}
        {status ? status.charAt(0).toUpperCase() + status.slice(1) : props.children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';

export { Badge };
export type { BadgeProps };
