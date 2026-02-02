import "../../styles/shared/badge.css";

export type BadgeVariant = "success" | "warning" | "info" | "danger" | "neutral";

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const Badge = ({ variant, children, className = "" }: BadgeProps) => {
  return (
    <span className={`badge badge-${variant} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;
