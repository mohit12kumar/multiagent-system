import { Loader2 } from 'lucide-react';

interface SpinnerProps { size?: 'sm' | 'md' | 'lg'; color?: string; label?: string; }

const SIZES = { sm: 'w-4 h-4', md: 'w-7 h-7', lg: 'w-10 h-10' };
const BORDER = { sm: 'border-2', md: 'border-[3px]', lg: 'border-4' };

export const Spinner = ({ size = 'md', color = 'var(--teal)', label }: SpinnerProps) => (
  <div className="flex flex-col items-center gap-3">
    <div
      className={`${SIZES[size]} ${BORDER[size]} rounded-full animate-spin`}
      style={{ borderColor: `${color}30`, borderTopColor: color }}
    />
    {label && <p className="text-sm text-[var(--text-muted)] font-medium">{label}</p>}
  </div>
);

export const FullPageSpinner = ({ label }: { label?: string }) => (
  <div className="flex items-center justify-center h-full min-h-[200px]">
    <Spinner size="lg" label={label} />
  </div>
);

export const InlineSpinner = () => <Loader2 className="w-4 h-4 animate-spin" />;
