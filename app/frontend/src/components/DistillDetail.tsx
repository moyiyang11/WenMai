import { useState } from "react";
import { LineChart } from "./LineChart";

// 展示单本小说的多维度蒸馏结果（说明书 §6-§13）。
// result 结构见 backend/services/llm.py 的 schema。

const TABS = [
  { key: "basic", label: "基础/结构" },
  { key: "character", label: "人物系统" },
  { key: "relations", label: "人物关系" },
  { key: "events", label: "剧情时间线" },
  { key: "conflict", label: "冲突" },
  { key: "foreshadow", label: "悬念伏笔" },
  { key: "emotion", label: "情绪曲线" },
  { key: "rhythm", label: "节奏曲线" },
  { key: "writing", label: "文风" },
  { key: "raw", label: "原始 JSON" },
];

function Field({ label, value }: { label: string; value: any }) {
  if (value == null || value === "") return null;
  return (
    <div className="text-sm">
      <span className="text-slate-400">{label}：</span>
      <span className="text-slate-700">{Array.isArray(value) ? value.join("、") : String(value)}</span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <h4 className="text-xs font-semibold text-indigo-600 mb-1.5">{title}</h4>
      <div className="space-y-1 pl-1">{children}</div>
    </div>
  );
}

export default function DistillDetail({ result, title }: { result: Record<string, any>; title?: string }) {
  const [tab, setTab] = useState("basic");
  const r = result || {};
  const ss = r.story_structure || {};
  const chars = r.characters || {};
  const p = chars.protagonist || {};
  const anta = chars.antagonist || {};

  return (
    <div>
      <div className="flex flex-wrap gap-1 mb-4 border-b pb-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-2.5 py-1 rounded text-xs ${tab === t.key ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "basic" && (
        <div className="grid md:grid-cols-2 gap-4">
          <Section title="基础信息（§6.1）">
            {title && <Field label="小说名" value={title} />}
            <Field label="市场" value={r.basic?.market} />
            <Field label="题材" value={r.basic?.genre} />
            <Field label="核心主题" value={r.basic?.core_theme} />
            <Field label="目标读者" value={r.basic?.target_reader} />
            <Field label="核心卖点" value={r.basic?.selling_point} />
            <Field label="故事定位" value={r.basic?.positioning} />
            <Field label="风格标签" value={r.style_tags} />
          </Section>
          <Section title="故事结构（§6.2）">
            <Field label="故事起点" value={ss.start} />
            <Field label="核心问题" value={ss.core_question} />
            <Field label="核心目标" value={ss.core_goal} />
            <Field label="主线" value={ss.main_line} />
            <Field label="支线" value={ss.sub_lines} />
            <Field label="故事阶段" value={ss.stages} />
            <Field label="关键事件" value={ss.key_events} />
            <Field label="转折" value={ss.turning_point} />
            <Field label="高潮" value={ss.climax} />
            <Field label="低谷" value={ss.low_point} />
            <Field label="结局" value={ss.ending} />
          </Section>
        </div>
      )}

      {tab === "character" && (
        <div className="grid md:grid-cols-2 gap-4">
          <Section title="主角">
            {Object.entries({
              身份: p.identity, 性格: p.personality, 欲望: p.desire, 目标: p.goal,
              恐惧: p.fear, 缺陷: p.flaw, 能力: p.ability, 行动方式: p.action_style,
              成长路线: p.growth_path, 人物弧光: p.arc,
            }).map(([k, v]) => <Field key={k} label={k} value={v} />)}
          </Section>
          <div>
            <Section title="反派">
              {Object.entries({
                身份: anta.identity, 目标: anta.goal, 动机: anta.motive, 能力: anta.ability,
                行动逻辑: anta.logic, 与主角冲突: anta.conflict, 最终结局: anta.ending,
              }).map(([k, v]) => <Field key={k} label={k} value={v} />)}
            </Section>
            <Section title="配角">
              {(chars.supporting || []).map((s: any, i: number) => (
                <div key={i} className="text-sm border-l-2 border-slate-200 pl-2 mb-1">
                  <b>{s.name}</b>（{s.role}）· {s.function} · {s.relation}
                </div>
              ))}
            </Section>
          </div>
        </div>
      )}

      {tab === "relations" && (
        <div className="space-y-2">
          {(r.relations || []).map((rel: any, i: number) => (
            <div key={i} className="text-sm bg-slate-50 rounded px-3 py-2">
              <span className="font-medium">{rel.from} → {rel.to}</span>
              <span className="ml-2 text-indigo-600 text-xs">{rel.type}</span>
              {rel.changes && (
                <div className="text-xs text-slate-500 mt-1">
                  关系变化：{(rel.changes as string[]).join(" → ")}
                </div>
              )}
            </div>
          ))}
          {!(r.relations || []).length && <div className="text-slate-400 text-sm">无关系数据</div>}
        </div>
      )}

      {tab === "events" && (
        <div className="relative pl-4 border-l-2 border-indigo-200 space-y-3">
          {(r.events || []).map((e: any, i: number) => (
            <div key={i} className="relative">
              <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-indigo-500" />
              <div className="text-sm font-medium">{e.name} <span className="text-xs text-slate-400">{e.chapter} · {e.type}</span></div>
              <div className="text-xs text-slate-500">冲突：{e.conflict}｜结果：{e.result}</div>
              <div className="text-xs text-slate-400">对主线：{e.impact_main}｜对人物：{e.impact_character}</div>
            </div>
          ))}
          {!(r.events || []).length && <div className="text-slate-400 text-sm">无时间线数据</div>}
        </div>
      )}

      {tab === "conflict" && (
        <div>
          <Field label="冲突类型" value={r.conflicts?.types} />
          <Field label="升级方式" value={r.conflicts?.escalation} />
          <Field label="解决方式" value={r.conflicts?.resolution} />
          <div className="mt-3">
            <div className="text-xs text-slate-500 mb-1">冲突曲线</div>
            <LineChart series={[{ name: "冲突强度", data: r.conflicts?.curve || [], color: "#ef4444" }]} />
          </div>
        </div>
      )}

      {tab === "foreshadow" && (
        <div className="space-y-2">
          {(r.foreshadows || []).map((f: any, i: number) => (
            <div key={i} className="text-sm bg-amber-50 rounded px-3 py-2">
              <div className="font-medium">{f.content}</div>
              <div className="text-xs text-slate-500 mt-1">
                埋设 {f.first_seen} → 回收 {f.payoff}（{f.method}）
              </div>
              <div className="text-xs text-slate-400">表面：{f.surface}｜真相：{f.truth}｜信息差：{f.info_gap}</div>
            </div>
          ))}
          {!(r.foreshadows || []).length && <div className="text-slate-400 text-sm">无伏笔数据</div>}
        </div>
      )}

      {tab === "emotion" && (
        <div>
          <Field label="情绪过程" value={r.emotion_curve?.process} />
          <div className="my-3">
            <LineChart series={[{ name: "情绪强度", data: r.emotion_curve?.curve || [], color: "#8b5cf6" }]} />
          </div>
          <Section title="爽点分布（§11）">
            {(r.emotion_curve?.payoff_points || []).map((pp: any, i: number) => (
              <div key={i} className="text-xs text-slate-600">
                {pp.position} · {pp.type} · 强度{pp.intensity}（前置：{pp.setup}）
              </div>
            ))}
          </Section>
        </div>
      )}

      {tab === "rhythm" && (
        <div>
          <Field label="章节字数" value={r.rhythm?.chapter_words} />
          <div className="my-3">
            <LineChart
              series={[
                { name: "对话比例", data: r.rhythm?.dialogue_ratio || [], color: "#0ea5e9" },
                { name: "信息密度", data: r.rhythm?.info_density || [], color: "#10b981" },
                { name: "爽点密度", data: r.rhythm?.payoff_density || [], color: "#f59e0b" },
                { name: "反转频率", data: r.rhythm?.reversal_freq || [], color: "#ef4444" },
              ]}
              height={180}
            />
          </div>
        </div>
      )}

      {tab === "writing" && (
        <div className="grid md:grid-cols-2 gap-4">
          <Section title="语言 / 叙事">
            <Field label="平均句长" value={r.writing?.language?.avg_sentence} />
            <Field label="长短句" value={r.writing?.language?.long_short_ratio} />
            <Field label="段落" value={r.writing?.language?.paragraph} />
            <Field label="人称" value={r.writing?.narration?.person} />
            <Field label="视角" value={r.writing?.narration?.viewpoint} />
            <Field label="驱动" value={r.writing?.narration?.driven} />
          </Section>
          <Section title="描写 / 情绪基调">
            <Field label="动作描写" value={r.writing?.description?.action} />
            <Field label="心理描写" value={r.writing?.description?.psychology} />
            <Field label="环境描写" value={r.writing?.description?.environment} />
            <Field label="感官描写" value={r.writing?.description?.sensory} />
            <Field label="严肃/幽默/压迫" value={[r.writing?.tone?.seriousness, r.writing?.tone?.humor, r.writing?.tone?.oppression].filter(Boolean).join(" / ")} />
            <Field label="情绪强度/文学性/通俗" value={[r.writing?.tone?.intensity, r.writing?.tone?.literariness, r.writing?.tone?.popularity].filter(Boolean).join(" / ")} />
          </Section>
        </div>
      )}

      {tab === "raw" && (
        <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-xs overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
