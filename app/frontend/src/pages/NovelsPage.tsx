import { useEffect, useState } from "react";
import { api } from "../api";
import type { Distillation, Novel } from "../types";
import { Btn, Card } from "../components/ui";
import DistillDetail from "../components/DistillDetail";

const MARKETS = ["男频", "女频", "其他"];

export default function NovelsPage() {
  const [novels, setNovels] = useState<Novel[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [detail, setDetail] = useState<Distillation | null>(null);
  const [msg, setMsg] = useState("");

  // 上传表单
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [market, setMarket] = useState("男频");
  const [genre, setGenre] = useState("");
  const [tags, setTags] = useState("");

  const load = () => api.novels().then(setNovels).catch((e) => setMsg(String(e)));
  useEffect(() => { load(); }, []);

  const upload = async () => {
    if (!file) { setMsg("请先选择 txt 文件"); return; }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title);
    fd.append("market", market);
    fd.append("genre", genre);
    fd.append("tags", tags);
    try {
      await api.uploadNovel(fd);
      setFile(null); setTitle(""); setGenre(""); setTags("");
      setMsg("导入成功");
      load();
    } catch (e) { setMsg(String(e)); }
  };

  const distill = async (id: number) => {
    setBusy(id); setMsg("");
    try {
      await api.distill(id);
      setMsg("蒸馏完成");
      load();
    } catch (e) { setMsg(String(e)); }
    finally { setBusy(null); }
  };

  const view = async (id: number) => {
    try { setDetail(await api.distillation(id)); }
    catch (e) { setMsg(String(e)); }
  };

  const del = async (id: number) => {
    if (!confirm("确认删除该小说？")) return;
    await api.deleteNovel(id); load();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">小说库 / 蒸馏中心</h1>
      {msg && <div className="text-sm text-indigo-600">{msg}</div>}

      <Card title="导入小说（上传 txt）">
        <div className="grid md:grid-cols-2 gap-3 text-sm">
          <input type="file" accept=".txt" onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="border rounded-lg px-3 py-2" />
          <input placeholder="标题（留空取文件名）" value={title} onChange={(e) => setTitle(e.target.value)}
            className="border rounded-lg px-3 py-2" />
          <select value={market} onChange={(e) => setMarket(e.target.value)} className="border rounded-lg px-3 py-2">
            {MARKETS.map((m) => <option key={m}>{m}</option>)}
          </select>
          <input placeholder="题材（如 玄幻/都市）" value={genre} onChange={(e) => setGenre(e.target.value)}
            className="border rounded-lg px-3 py-2" />
          <input placeholder="标签（逗号分隔，如 爽文,升级,热血）" value={tags} onChange={(e) => setTags(e.target.value)}
            className="border rounded-lg px-3 py-2 md:col-span-2" />
        </div>
        <div className="mt-3"><Btn onClick={upload}>导入</Btn></div>
      </Card>

      <Card title={`小说列表（${novels.length}）`}>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr>
              <th className="py-2">标题</th><th>市场</th><th>题材</th><th>标签</th>
              <th>字数</th><th>状态</th><th className="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {novels.map((n) => (
              <tr key={n.id} className="border-b border-slate-100">
                <td className="py-2 font-medium">{n.title}</td>
                <td>{n.market}</td>
                <td>{n.genre || "—"}</td>
                <td className="max-w-[180px]">
                  <div className="flex flex-wrap gap-1">
                    {n.tags.map((t) => (
                      <span key={t.id} className="bg-slate-100 text-slate-600 px-1.5 rounded text-xs">{t.name}</span>
                    ))}
                  </div>
                </td>
                <td>{n.word_count.toLocaleString()}</td>
                <td>
                  <span className={
                    n.distill_status === "完成" ? "text-emerald-600" :
                    n.distill_status === "失败" ? "text-red-600" : "text-amber-600"
                  }>{n.distill_status}</span>
                </td>
                <td className="text-right space-x-1 whitespace-nowrap">
                  <Btn small tone="indigo" disabled={busy === n.id} onClick={() => distill(n.id)}>
                    {busy === n.id ? "蒸馏中…" : "蒸馏"}
                  </Btn>
                  {n.distill_status === "完成" && (
                    <Btn small tone="slate" onClick={() => view(n.id)}>查看</Btn>
                  )}
                  <Btn small tone="red" onClick={() => del(n.id)}>删除</Btn>
                </td>
              </tr>
            ))}
            {!novels.length && <tr><td colSpan={7} className="py-4 text-slate-400">暂无小说，请先导入</td></tr>}
          </tbody>
        </table>
      </Card>

      {detail && (
        <Card title={`蒸馏结果 · 引擎：${detail.model || "mock"}`} extra={<Btn small tone="slate" onClick={() => setDetail(null)}>关闭</Btn>}>
          <DistillDetail result={detail.result} />
        </Card>
      )}
    </div>
  );
}
