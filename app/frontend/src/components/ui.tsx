import type { ReactNode } from "react";

export function Card({ title, children, extra }: { title?: string; children: ReactNode; extra?: ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      {(title || extra) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h2 className="font-semibold text-slate-700">{title}</h2>}
          {extra}
        </div>
      )}
      {children}
    </div>
  );
}

export function Stat({ label, value, tone = "slate" }: { label: string; value: ReactNode; tone?: string }) {
  const tones: Record<string, string> = {
    slate: "text-slate-800",
    green: "text-emerald-600",
    amber: "text-amber-600",
    red: "text-red-600",
    indigo: "text-indigo-600",
  };
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${tones[tone] ?? tones.slate}`}>{value}</div>
    </div>
  );
}

const levelColor: Record<string, string> = {
  核心特征: "bg-emerald-100 text-emerald-700",
  重要特征: "bg-indigo-100 text-indigo-700",
  辅助特征: "bg-amber-100 text-amber-700",
  偶然特征: "bg-slate-100 text-slate-500",
};

export function LevelBadge({ level }: { level: string }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${levelColor[level] ?? levelColor["偶然特征"]}`}>
      {level}
    </span>
  );
}

export function Btn({
  children,
  onClick,
  tone = "indigo",
  disabled,
  small,
}: {
  children: ReactNode;
  onClick?: () => void;
  tone?: "indigo" | "slate" | "red" | "emerald";
  disabled?: boolean;
  small?: boolean;
}) {
  const tones = {
    indigo: "bg-indigo-600 hover:bg-indigo-700 text-white",
    emerald: "bg-emerald-600 hover:bg-emerald-700 text-white",
    slate: "bg-slate-200 hover:bg-slate-300 text-slate-700",
    red: "bg-red-100 hover:bg-red-200 text-red-700",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-lg ${small ? "px-2.5 py-1 text-xs" : "px-4 py-2 text-sm"} ${
        tones[tone]
      } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {children}
    </button>
  );
}

export function Bar({ value }: { value: number }) {
  const color = value >= 90 ? "bg-emerald-500" : value >= 70 ? "bg-indigo-500" : value >= 50 ? "bg-amber-500" : "bg-slate-300";
  return (
    <div className="w-full bg-slate-100 rounded h-2">
      <div className={`${color} h-2 rounded`} style={{ width: `${Math.min(value, 100)}%` }} />
    </div>
  );
}
