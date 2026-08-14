import { useEffect, useState } from "react";
import { api } from "../api";
import type { Novel, StyleProfile } from "../types";
import { Bar, Btn, Card, LevelBadge, OriginBadge } from "../components/ui";

export default function StylesPage() {
  const [novels, setNovels] = useState<Novel[]>([]);
  const [profiles, setProfiles] = useState<StyleProfile[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [name, setName] = useState("");
  const [msg, setMsg] = useState("");
  const [active, setActive] = useState<StyleProfile | null>(null);
  // 风格组合（§20）
  const [comboSel, setComboSel] = useState<Set<number>>(new Set());
  const [comboName, setComboName] = useState("");

  const load = () => {
    api.novels().then((n) => setNovels(n.filter((x) => x.distill_status === "完成")));
    api.styles().then(setProfiles);
  };
  useEffect(() => { load(); }, []);

  const toggle = (id: number) => {
    const s = new Set(selected);
    s.has(id) ? s.delete(id) : s.add(id);
    setSelected(s);
  };

  const toggleCombo = (id: number) => {
    const s = new Set(comboSel);
    s.has(id) ? s.delete(id) : s.add(id);
    setComboSel(s);
  };

  const cluster = async () => {
    if (selected.size < 2) { setMsg("请至少勾选 2 本已蒸馏小说"); return; }
    if (!name.trim()) { setMsg("请填写风格名称"); return; }
    try {
      const p = await api.cluster(name.trim(), [...selected]);
      setMsg(`已生成风格「${p.name}」，综合稳定性 ${p.stability}%`);
      setName(""); setSelected(new Set());
      load();
      setActive(p);
    } catch (e) { setMsg(String(e)); }
  };

  const combine = async () => {
    if (comboSel.size < 2) { setMsg("请至少勾选 2 个已有风格进行组合"); return; }
    if (!comboName.trim()) { setMsg("请填写组合风格名称"); return; }
    try {
      const p = await api.combineStyles(comboName.trim(), [...comboSel]);
      const conflicts = p.features.filter((f) => f.origin === "冲突-采纳").length;
      setMsg(`已组合生成「${p.name}」，综合稳定性 ${p.stability}%，${conflicts} 处规则冲突已按优先级取舍`);
      setComboName(""); setComboSel(new Set());
      load();
      setActive(p);
    } catch (e) { setMsg(String(e)); }
  };

  const del = async (id: number) => {
    if (!confirm("删除该风格？")) return;
    await api.deleteStyle(id);
    if (active?.id === id) setActive(null);
    load();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">风格中心</h1>
      <p className="text-sm text-slate-500 -mt-3">多小说聚类 → 共同特征提取 → 稳定性分析 → Style Profile → 风格组合</p>
      {msg && <div className="text-sm text-indigo-600">{msg}</div>}

      <Card title="① 选择已蒸馏小说进行聚类">
        {!novels.length && <div className="text-sm text-slate-400">暂无已蒸馏小说，请先在「小说库」蒸馏。</div>}
        <div className="grid md:grid-cols-3 gap-2">
          {novels.map((n) => (
            <label key={n.id} className={`flex items-center gap-2 border rounded-lg px-3 py-2 text-sm cursor-pointer ${
              selected.has(n.id) ? "border-indigo-500 bg-indigo-50" : "border-slate-200"
            }`}>
              <input type="checkbox" checked={selected.has(n.id)} onChange={() => toggle(n.id)} />
              <span className="truncate">{n.title}</span>
              <span className="text-slate-400 text-xs ml-auto">{n.genre}</span>
            </label>
          ))}
        </div>
        <div className="flex gap-2 mt-4">
          <input placeholder="风格名称，如 男频都市商战快节奏爽文" value={name}
            onChange={(e) => setName(e.target.value)} className="border rounded-lg px-3 py-2 text-sm flex-1" />
          <Btn onClick={cluster}>生成 Style Profile（已选 {selected.size}）</Btn>
        </div>
      </Card>

      <Card title="② 风格组合：把多个风格重新计算共同规则 / 冲突规则 / 优先级">
        {profiles.length < 2 && (
          <div className="text-sm text-slate-400">至少需要 2 个已有风格才能组合，请先在上方生成风格。</div>
        )}
        {profiles.length >= 2 && (
          <>
            <div className="grid md:grid-cols-3 gap-2">
              {profiles.map((p) => (
                <label key={p.id} className={`flex items-center gap-2 border rounded-lg px-3 py-2 text-sm cursor-pointer ${
                  comboSel.has(p.id) ? "border-emerald-500 bg-emerald-50" : "border-slate-200"
                }`}>
                  <input type="checkbox" checked={comboSel.has(p.id)} onChange={() => toggleCombo(p.id)} />
                  <span className="truncate">{p.name}</span>
                  <span className="text-slate-400 text-xs ml-auto">{p.stability}%</span>
                </label>
              ))}
            </div>
            <div className="flex gap-2 mt-4">
              <input placeholder="组合风格名称，如 都市商战智斗悬疑风" value={comboName}
                onChange={(e) => setComboName(e.target.value)} className="border rounded-lg px-3 py-2 text-sm flex-1" />
              <Btn tone="emerald" onClick={combine}>生成组合风格（已选 {comboSel.size}）</Btn>
            </div>
          </>
        )}
      </Card>

      <div className="grid md:grid-cols-2 gap-5">
        <Card title={`③ 风格列表（${profiles.length}）`}>
          <ul className="space-y-2">
            {profiles.map((p) => (
              <li key={p.id}
                className={`border rounded-lg p-3 cursor-pointer ${active?.id === p.id ? "border-indigo-500 bg-indigo-50" : "border-slate-200"}`}
                onClick={() => setActive(p)}>
                <div className="flex justify-between items-center">
                  <div className="font-medium">{p.name}</div>
                  <Btn small tone="red" onClick={() => del(p.id)}>删除</Btn>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  稳定性 {p.stability}% · {p.features.length} 特征 · {p.novels.length} 本来源
                </div>
              </li>
            ))}
            {!profiles.length && <li className="text-slate-400 text-sm">暂无风格</li>}
          </ul>
        </Card>

        <Card title="④ 风格详情 / 稳定性">
          {!active && <div className="text-sm text-slate-400">点击左侧风格查看详情</div>}
          {active && (
            <div className="space-y-4">
              <div>
                <div className="font-semibold">{active.name}</div>
                <div className="text-xs text-slate-500">综合稳定性 {active.stability}%</div>
                {active.description && <div className="text-xs text-slate-400 mt-1">{active.description}</div>}
              </div>
              <div className="space-y-1.5 max-h-72 overflow-auto pr-1">
                {[...active.features]
                  .sort((a, b) => (a.origin === "冲突-弃用" ? 1 : 0) - (b.origin === "冲突-弃用" ? 1 : 0) || b.stability - a.stability)
                  .map((f) => (
                  <div key={f.id} className={`text-xs ${f.origin === "冲突-弃用" ? "opacity-60" : ""}`}>
                    <div className="flex justify-between mb-0.5">
                      <span className="text-slate-600 flex items-center gap-1">
                        <OriginBadge origin={f.origin} />
                        {f.dimension} · <b>{f.feature}</b>
                      </span>
                      <span className="flex items-center gap-1"><LevelBadge level={f.level} />{f.stability}%</span>
                    </div>
                    <Bar value={f.stability} />
                  </div>
                ))}
              </div>
              <details className="text-xs">
                <summary className="cursor-pointer text-indigo-600">查看 Style Profile YAML</summary>
                <pre className="bg-slate-900 text-slate-100 rounded-lg p-3 mt-2 overflow-auto max-h-60">{active.profile_yaml}</pre>
              </details>
              <a href="/skills" className="inline-block text-sm text-indigo-600">→ 前往 Skill 导出</a>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
