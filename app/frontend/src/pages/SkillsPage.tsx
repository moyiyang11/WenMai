import { useEffect, useState } from "react";
import { api } from "../api";
import type { Skill, StyleProfile } from "../types";
import { Btn, Card } from "../components/ui";

export default function SkillsPage() {
  const [profiles, setProfiles] = useState<StyleProfile[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [profileId, setProfileId] = useState<number | "">("");
  const [version, setVersion] = useState("v1.0");
  const [msg, setMsg] = useState("");
  const [preview, setPreview] = useState<{ files: Record<string, string> } | null>(null);
  const [activeFile, setActiveFile] = useState("SKILL.md");

  const load = () => {
    api.styles().then(setProfiles);
    api.skills().then(setSkills);
  };
  useEffect(() => { load(); }, []);

  const doExport = async () => {
    if (!profileId) { setMsg("请选择要导出的风格"); return; }
    try {
      const s = await api.exportSkill(Number(profileId), version);
      setMsg(`已导出 Skill「${s.name}」${s.version}`);
      load();
    } catch (e) { setMsg(String(e)); }
  };

  const showPreview = async (id: number) => {
    const p = await api.previewSkill(id);
    setPreview(p);
    setActiveFile("SKILL.md");
  };

  const del = async (id: number) => {
    if (!confirm("删除该 Skill？")) return;
    await api.deleteSkill(id); load();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Skill 导出</h1>
      <p className="text-sm text-slate-500 -mt-3">Style Profile → 生成 Skill 包 → 预览 → 下载</p>
      {msg && <div className="text-sm text-indigo-600">{msg}</div>}

      <Card title="从风格导出 Skill">
        <div className="flex flex-wrap gap-2 items-center text-sm">
          <select value={profileId} onChange={(e) => setProfileId(e.target.value ? Number(e.target.value) : "")}
            className="border rounded-lg px-3 py-2 min-w-64">
            <option value="">选择风格…</option>
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>{p.name}（稳定性 {p.stability}%）</option>
            ))}
          </select>
          <input value={version} onChange={(e) => setVersion(e.target.value)} className="border rounded-lg px-3 py-2 w-24" />
          <Btn tone="emerald" onClick={doExport}>导出为 Skill</Btn>
        </div>
      </Card>

      <Card title={`已导出 Skill（${skills.length}）`}>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">名称</th><th>版本</th><th>稳定性</th><th>来源</th><th>特征</th><th className="text-right">操作</th></tr>
          </thead>
          <tbody>
            {skills.map((s) => (
              <tr key={s.id} className="border-b border-slate-100">
                <td className="py-2 font-medium">{s.name}</td>
                <td>{s.version}</td>
                <td>{s.stability}%</td>
                <td>{s.source_count} 本</td>
                <td>{s.feature_count}</td>
                <td className="text-right space-x-1 whitespace-nowrap">
                  <Btn small tone="slate" onClick={() => showPreview(s.id)}>预览</Btn>
                  <a href={api.downloadSkillUrl(s.id)} className="inline-block px-2.5 py-1 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700">下载 zip</a>
                  <Btn small tone="red" onClick={() => del(s.id)}>删除</Btn>
                </td>
              </tr>
            ))}
            {!skills.length && <tr><td colSpan={6} className="py-4 text-slate-400">暂无导出</td></tr>}
          </tbody>
        </table>
      </Card>

      {preview && (
        <Card title="Skill 预览" extra={<Btn small tone="slate" onClick={() => setPreview(null)}>关闭</Btn>}>
          <div className="flex gap-1 flex-wrap mb-3">
            {Object.keys(preview.files).map((f) => (
              <button key={f} onClick={() => setActiveFile(f)}
                className={`px-2.5 py-1 rounded text-xs ${activeFile === f ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                {f}
              </button>
            ))}
          </div>
          <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-xs overflow-auto max-h-96 whitespace-pre-wrap">
            {preview.files[activeFile]}
          </pre>
        </Card>
      )}
    </div>
  );
}
