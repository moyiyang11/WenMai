import { useEffect, useState } from "react";
import { api } from "../api";
import type { Dashboard } from "../types";
import { Card, Stat } from "../components/ui";

function DistBars({ data }: { data: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(data));
  const entries = Object.entries(data);
  if (!entries.length) return <div className="text-sm text-slate-400">暂无数据</div>;
  return (
    <div className="space-y-2">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center gap-2 text-sm">
          <div className="w-20 text-slate-600 truncate">{k}</div>
          <div className="flex-1 bg-slate-100 rounded h-4">
            <div className="bg-indigo-400 h-4 rounded" style={{ width: `${(v / max) * 100}%` }} />
          </div>
          <div className="w-8 text-right text-slate-500">{v}</div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [d, setD] = useState<Dashboard | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.dashboard().then(setD).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="text-red-600">加载失败：{err}（请确认后端已启动）</div>;
  if (!d) return <div className="text-slate-400">加载中…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">小说蒸馏工作台</h1>
        <p className="text-sm text-slate-500 mt-1">从优秀小说中提取稳定的创作规律，导出 AI Style Skill</p>
      </div>

      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        <Stat label="小说总数" value={d.total_novels} />
        <Stat label="已蒸馏" value={d.distilled} tone="green" />
        <Stat label="待蒸馏" value={d.pending} tone="amber" />
        <Stat label="蒸馏失败" value={d.failed} tone="red" />
        <Stat label="风格数量" value={d.profile_count} tone="indigo" />
        <Stat label="Skill 数量" value={d.skill_count} tone="indigo" />
      </div>

      <div className="grid md:grid-cols-3 gap-5">
        <Card title="市场分布"><DistBars data={d.market_dist} /></Card>
        <Card title="题材分布"><DistBars data={d.genre_dist} /></Card>
        <Card title="风格标签分布"><DistBars data={d.style_dist} /></Card>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <Card title="最近蒸馏">
          <ul className="divide-y divide-slate-100">
            {d.recent_novels.map((n) => (
              <li key={n.id} className="py-2 flex justify-between text-sm">
                <span className="truncate">{n.title}</span>
                <span className="text-slate-400">{n.distill_status}</span>
              </li>
            ))}
            {!d.recent_novels.length && <li className="py-2 text-slate-400 text-sm">暂无</li>}
          </ul>
        </Card>
        <Card title="最近生成的 Style Skill">
          <ul className="divide-y divide-slate-100">
            {d.recent_skills.map((s) => (
              <li key={s.id} className="py-2 flex justify-between text-sm">
                <span className="truncate">{s.name} <span className="text-slate-400">{s.version}</span></span>
                <span className="text-slate-400">稳定性 {s.stability}% · {s.source_count}本</span>
              </li>
            ))}
            {!d.recent_skills.length && <li className="py-2 text-slate-400 text-sm">暂无</li>}
          </ul>
        </Card>
      </div>
    </div>
  );
}
