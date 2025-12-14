import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, variant = 'default', showLabel = false, size = 'md', ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    
    const variants = {
      default: 'bg-primary-600',
      success: 'bg-success-600',
      warning: 'bg-warning-600',
      error: 'bg-error-600',
    };
    
    const sizes = {
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative w-full overflow-hidden rounded-full bg-gray-200',
          sizes[size],
          className
        )}
        {...props}
      >
        <div
          className={cn(
            'h-full transition-all duration-300 ease-in-out',
            variants[variant]
          )}
          style={{ width: `${percentage}%` }}
        />
        {showLabel && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-medium text-gray-900">
              {Math.round(percentage)}%
            </span>
          </div>
        )}
      </div>
    );
  }
);

Progress.displayName = 'Progress';

export { Progress };
