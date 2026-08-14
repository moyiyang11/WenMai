// 轻量 SVG 折线图，无第三方依赖。用于情绪/节奏/冲突曲线（说明书 §11/§12/§9）。
export function LineChart({
  series,
  height = 140,
  labels,
}: {
  series: { name: string; data: number[]; color: string }[];
  height?: number;
  labels?: string[];
}) {
  const width = 520;
  const pad = 24;
  const valid = series.filter((s) => s.data && s.data.length > 1);
  const n = Math.max(...valid.map((s) => s.data.length), 2);
  const xStep = (width - pad * 2) / (n - 1);
  const y = (v: number) => height - pad - (Math.max(0, Math.min(100, v)) / 100) * (height - pad * 2);
  const x = (i: number) => pad + i * xStep;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {/* 网格线 */}
        {[0, 25, 50, 75, 100].map((g) => (
          <g key={g}>
            <line x1={pad} x2={width - pad} y1={y(g)} y2={y(g)} stroke="#e2e8f0" strokeWidth={1} />
            <text x={2} y={y(g) + 3} fontSize={8} fill="#94a3b8">{g}</text>
          </g>
        ))}
        {valid.map((s) => (
          <polyline
            key={s.name}
            fill="none"
            stroke={s.color}
            strokeWidth={2}
            points={s.data.map((v, i) => `${x(i)},${y(v)}`).join(" ")}
          />
        ))}
        {labels &&
          labels.map((lb, i) => (
            <text key={i} x={x(i)} y={height - 6} fontSize={8} fill="#94a3b8" textAnchor="middle">
              {lb}
            </text>
          ))}
      </svg>
      <div className="flex flex-wrap gap-3 mt-1">
        {valid.map((s) => (
          <span key={s.name} className="flex items-center gap-1 text-xs text-slate-500">
            <span className="inline-block w-3 h-0.5" style={{ background: s.color }} />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}
