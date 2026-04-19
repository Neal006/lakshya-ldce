'use client';

import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  pressed?: boolean;
  style?: React.CSSProperties;
}

export function Card({ children, className = '', hover = true, pressed = false, style }: CardProps) {
  if (pressed) {
    return (
      <div className={`card-pressed ${className}`} style={style}>
        {children}
      </div>
    );
  }

  return (
    <div
      className={`card-skeuo ${className} ${hover ? 'hover:shadow-[16px_16px_32px_rgba(0,0,0,0.8),-16px_-16px_32px_rgba(255,255,255,0.02),inset_1px_1px_2px_rgba(255,255,255,0.05)] hover:-translate-y-0.5' : ''} transition-all duration-300`}
      style={style}
    >
      {children}
    </div>
  );
}

interface ButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary';
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: () => void;
}

export function Button({ 
  children, 
  variant = 'primary', 
  className = '',
  disabled = false,
  type = 'button',
  onClick
}: ButtonProps) {
  const baseClass = variant === 'primary' ? 'btn-primary-skeuo' : 'btn-skeuo';
  
  return (
    <button
      className={`${baseClass} ${className} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium mb-2 text-[#F5F5F5] uppercase tracking-wider">
          {label}
        </label>
      )}
      <input
        className={`input-skeuo ${className} ${error ? 'ring-2 ring-[#EF4444]' : ''}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-[#EF4444]">{error}</p>
      )}
    </div>
  );
}

interface BadgeProps {
  children: ReactNode;
  variant?: 'priority' | 'success' | 'urgent' | 'default' | 'high' | 'medium' | 'low';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variantClasses = {
    priority: 'tag-priority',
    success: 'tag-success',
    urgent: 'tag-urgent',
    high: 'tag-high',
    medium: 'tag-medium',
    low: 'tag-low',
    default: 'bg-[#1A1A1D] text-[#F5F5F5] border border-white/10 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider',
  };

  return (
    <span className={`${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
}

interface ProgressBarProps {
  progress: number;
  className?: string;
  variant?: 'primary' | 'success' | 'warning' | 'error';
}

export function ProgressBar({ progress, className = '', variant = 'primary' }: ProgressBarProps) {
  const getBarColor = () => {
    switch (variant) {
      case 'success': return 'linear-gradient(165deg, #22C55E, #166534)';
      case 'warning': return 'linear-gradient(165deg, #F59E0B, #B45309)';
      case 'error': return 'linear-gradient(165deg, #EF4444, #B91C1C)';
      default: return 'linear-gradient(165deg, #FF4500, #CC3700)';
    }
  };

  return (
    <div className={`progress-track-skeuo ${className}`}>
      <div
        className="progress-fill-skeuo transition-all duration-1000"
        style={{ width: `${progress}%`, background: getBarColor() }}
      />
    </div>
  );
}
