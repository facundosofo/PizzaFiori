// Reusable SVG Icons for Sales module

import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  DollarSign,
  Eye,
  Info,
  KeyRound,
  Layers,
  Loader,
  Minus,
  BadgePercent,
  Pencil,
  Pizza,
  Plus,
  Save,
  Search,
  ShieldOff,
  ShoppingCart,
  Trash2,
  Columns3Cog,
  FolderTree,
  X,
} from "lucide-react";

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

const renderLucideIcon = (Icon: LucideIcon, props: IconProps, strokeWidth = 2) => {
  const { size = 20, color = "currentColor", className = "" } = props;
  return (
    <Icon size={size} color={color} strokeWidth={strokeWidth} className={className} />
  );
};

export const EyeIcon = (props: IconProps) => renderLucideIcon(Eye, props);

export const EditIcon = (props: IconProps) => renderLucideIcon(Pencil, props);

export const TrashIcon = (props: IconProps) => renderLucideIcon(Trash2, props);

export const SearchIcon = (props: IconProps) => renderLucideIcon(Search, props);

export const XIcon = (props: IconProps) =>
  renderLucideIcon(X, {
    ...props,
    className: `drop-shadow-[0_0_6px_rgba(255,77,79,0.8)] ${props.className ?? ""}`,
  });

export const WarningIcon = (props: IconProps) =>
  renderLucideIcon(AlertTriangle, {
    ...props,
    className: `drop-shadow-[0_0_6px_rgba(250,204,21,0.35)] ${props.className ?? ""}`,
  });

export const ErrorIcon = (props: IconProps) =>
  renderLucideIcon(AlertCircle, {
    ...props,
    className: `drop-shadow-[0_0_6px_rgba(255,77,79,0.35)] ${props.className ?? ""}`,
  });

export const SpinnerIcon = (props: IconProps) => renderLucideIcon(Loader, props);

export const InfoIcon = (props: IconProps) => renderLucideIcon(Info, props);

export const PlusIcon = (props: IconProps) => renderLucideIcon(Plus, props);

export const MinusIcon = (props: IconProps) => renderLucideIcon(Minus, props);

export const ChevronDownIcon = (props: IconProps) => renderLucideIcon(ChevronDown, props);

export const ChevronRightIcon = (props: IconProps) => renderLucideIcon(ChevronRight, props);

export const ShoppingCartIcon = (props: IconProps) => renderLucideIcon(ShoppingCart, props);

export const Columns3CogIcon = (props: IconProps) => renderLucideIcon(Columns3Cog, props);

export const FolderTreeIcon = (props: IconProps) => renderLucideIcon(FolderTree, props);

export const ClockIcon = (props: IconProps) => renderLucideIcon(Clock, props);

export const PizzaIcon = ({
  size = 28,
  color = "#6b7280",
  className = "",
}: IconProps) => (
  <Pizza size={size} color={color} strokeWidth={2} className={className} />
);

export const CheckIcon = ({ size = 40, color = "#22c55e", className = "" }: IconProps) =>
  renderLucideIcon(CheckCircle2, {
    size,
    color,
    className: `drop-shadow-[0_0_12px_rgba(34,197,94,0.35)] ${className}`,
  });

export const DiscountIcon = (props: IconProps) => renderLucideIcon(BadgePercent, props);

export const PesoIcon = (props: IconProps) => renderLucideIcon(DollarSign, props);

export const ShieldOffIcon = (props: IconProps) =>
  renderLucideIcon(ShieldOff, {
    ...props,
    className: `drop-shadow-[0_0_8px_rgba(239,68,68,0.35)] ${props.className ?? ""}`,
  });

export const KeyIcon = (props: IconProps) => renderLucideIcon(KeyRound, props);

export const AlertCircleIcon = (props: IconProps) => renderLucideIcon(AlertCircle, props);

export const LoaderIcon = (props: IconProps) => renderLucideIcon(Loader, props);

export const SaveIcon = (props: IconProps) => renderLucideIcon(Save, props);

export const LayersIcon = (props: IconProps) => renderLucideIcon(Layers, props);