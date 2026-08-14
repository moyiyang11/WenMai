import { useEffect, useState } from "react";
import { api } from "../api";
import type { LLMConfig } from "../types";
import { Btn, Card } from "../components/ui";

export default function SettingsPage() {
  const [cfg, setCfg] = useState<LLMConfig | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("deepseek-chat");
  const [baseUrl, setBaseUrl] = useState("https://api.deepseek.com");
  const [msg, setMsg] = useState("");
  const [testing, setTesting] = useState(false);

  const load = () =>
    api.llmConfig().then((c) => {
      setCfg(c);
      setModel(c.model);
      setBaseUrl(c.base_url);
    });
  useEffect(() => { load(); }, []);

  const save = async () => {
    setMsg("");
    try {
      // apiKey 为空字符串时不改动（用 undefined 传），避免误清除
      await api.updateLlmConfig({
        api_key: apiKey ? apiKey : undefined,
        model,
        base_url: baseUrl,
      });
      setApiKey("");
      setMsg("已保存（Key 仅存于本地数据库 data/app.db，不会进入 Git）");
      load();
    } catch (e) { setMsg(String(e)); }
  };

  const clearKey = async () => {
    if (!confirm("确认清除已保存的 API Key？将回退到 mock 模式。")) return;
    await api.updateLlmConfig({ api_key: "" });
    setApiKey("");
    setMsg("已清除 API Key");
    load();
  };

  const test = async () => {
    setTesting(true); setMsg("");
    try {
      const r = await api.testLlm();
      setMsg((r.ok ? "✅ " : "❌ ") + r.message);
    } catch (e) { setMsg(String(e)); }
    finally { setTesting(false); }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">系统设置 · AI 接入</h1>
      <p className="text-sm text-slate-500 -mt-3">
        在此配置 DeepSeek API Key。Key 保存在后端本地数据库 <code>data/app.db</code>（已 gitignore），
        不写入任何会被提交到 GitHub 的文件。
      </p>
      {msg && <div className="text-sm text-indigo-600">{msg}</div>}

      <Card title="DeepSeek 接入配置">
        {cfg && (
          <div className="mb-4 text-sm flex items-center gap-3">
            <span className={`px-2 py-0.5 rounded text-xs ${cfg.configured ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
              {cfg.configured ? "已接入真实模型" : "mock 模式（未配置 Key）"}
            </span>
            <span className="text-slate-500">
              来源：{cfg.source === "db" ? "网页配置" : cfg.source === "env" ? ".env" : "无"}
              {cfg.masked_key && ` · 当前 Key：${cfg.masked_key}`}
            </span>
          </div>
        )}

        <div className="space-y-3 text-sm max-w-xl">
          <div>
            <label className="block text-slate-600 mb-1">API Key</label>
            <input
              type="password"
              placeholder={cfg?.masked_key ? "已配置，留空则不修改" : "sk-..."}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-slate-600 mb-1">模型</label>
            <input value={model} onChange={(e) => setModel(e.target.value)}
              className="w-full border rounded-lg px-3 py-2" />
          </div>
          <div>
            <label className="block text-slate-600 mb-1">Base URL</label>
            <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
              className="w-full border rounded-lg px-3 py-2" />
          </div>
          <div className="flex gap-2 pt-1">
            <Btn onClick={save}>保存</Btn>
            <Btn tone="slate" disabled={testing} onClick={test}>{testing ? "测试中…" : "测试连接"}</Btn>
            {cfg?.configured && cfg.source === "db" && (
              <Btn tone="red" onClick={clearKey}>清除 Key</Btn>
            )}
          </div>
        </div>
      </Card>

      <Card title="安全说明">
        <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
          <li>API Key 存储于后端 <code>data/app.db</code>，<code>data/</code> 已在 <code>.gitignore</code> 中排除。</li>
          <li>接口回显 Key 一律脱敏（如 <code>sk-1***abcd</code>），前端不保存明文。</li>
          <li>申请 Key：<a className="text-indigo-600" href="https://platform.deepseek.com" target="_blank">platform.deepseek.com</a></li>
          <li>不配置 Key 时系统以本地启发式 mock 运行，可离线跑通全流程。</li>
        </ul>
      </Card>
    </div>
  );
}
