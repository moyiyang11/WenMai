import { useEffect, useState } from "react";
import { api } from "../api";
import type { Distillation, Novel } from "../types";
import { Btn, Card } from "../components/ui";
import DistillDetail from "../components/DistillDetail";

const MARKETS = ["男频", "女频", "其他"];
const GENRES = ["玄幻", "仙侠", "都市", "历史", "科幻", "悬疑", "灵异", "末世", "游戏", "无限流", "古言", "现言", "宫斗", "宅斗", "年代", "其他"];

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
  const [detecting, setDetecting] = useState(false);
  const [detectHint, setDetectHint] = useState("");

  const load = () => api.novels().then(setNovels).catch((e) => setMsg(String(e)));
  useEffect(() => { load(); }, []);

  const onFileChange = (f: File | null) => {
    setFile(f);
    setDetectHint("");
  };

  const autoDetect = async () => {
    if (!file) { setMsg("请先选择 txt 文件"); return; }
    setDetecting(true); setDetectHint("AI 识别中…"); setMsg("");
    try {
      const r = await api.detectNovel(file, title || file.name.replace(/\.txt$/i, ""));
      setMarket(r.market || "男频");
      setGenre(r.genre || "");
      const newTags = (r.style_tags || []).join(",");
      setTags(newTags);
      setDetectHint(
        `AI 识别完成：${r.market} · ${r.genre} · ${r.core_theme || ""}` +
        (r.style_tags?.length ? `  标签已预填：${newTags}` : "")
      );
    } catch (e) {
      setDetectHint("识别失败，请手动填写");
      setMsg(String(e));
    } finally {
      setDetecting(false);
    }
  };

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
      setFile(null); setTitle(""); setGenre(""); setTags(""); setDetectHint("");
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
          <div className="md:col-span-2 flex gap-2 items-center">
            <input type="file" accept=".txt" onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
              className="border rounded-lg px-3 py-2 flex-1" />
            <Btn tone="slate" disabled={!file || detecting} onClick={autoDetect}>
              {detecting ? "识别中…" : "AI 自动识别"}
            </Btn>
          </div>
          {detectHint && (
            <div className="md:col-span-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              {detectHint}
            </div>
          )}
          <input placeholder="标题（留空取文件名）" value={title} onChange={(e) => setTitle(e.target.value)}
            className="border rounded-lg px-3 py-2" />
          <select value={market} onChange={(e) => setMarket(e.target.value)} className="border rounded-lg px-3 py-2">
            {MARKETS.map((m) => <option key={m}>{m}</option>)}
          </select>
          <select value={genre} onChange={(e) => setGenre(e.target.value)} className="border rounded-lg px-3 py-2">
            <option value="">题材（请选择）</option>
            {GENRES.map((g) => <option key={g}>{g}</option>)}
          </select>
          <input placeholder="也可手动填写题材" value={genre} onChange={(e) => setGenre(e.target.value)}
            className="border rounded-lg px-3 py-2" />
          <input placeholder="标签（逗号分隔，如 爽文,升级,热血）" value={tags} onChange={(e) => setTags(e.target.value)}
            className="border rounded-lg px-3 py-2 md:col-span-2" />
        </div>
        <div className="mt-3 flex items-center gap-3">
          <Btn onClick={upload}>导入</Btn>
          <span className="text-xs text-slate-400">蒸馏时采用多段采样（头/中/尾），覆盖完整故事弧</span>
        </div>
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
                <td>
                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                    n.market === "男频" ? "bg-blue-100 text-blue-700" :
                    n.market === "女频" ? "bg-pink-100 text-pink-700" :
                    "bg-slate-100 text-slate-600"
                  }`}>{n.market}</span>
                </td>
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
        <Card title={`蒸馏结果 · 引擎：${detail.model || "mock"}${(detail.result as any)._sample_desc ? ` · ${(detail.result as any)._sample_desc}` : ""}`}
          extra={<Btn small tone="slate" onClick={() => setDetail(null)}>关闭</Btn>}>
          <DistillDetail result={detail.result} />
        </Card>
      )}
    </div>
  );
}
