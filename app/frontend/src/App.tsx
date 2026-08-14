import { NavLink, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import NovelsPage from "./pages/NovelsPage";
import StylesPage from "./pages/StylesPage";
import SkillsPage from "./pages/SkillsPage";
import SettingsPage from "./pages/SettingsPage";

const nav = [
  { to: "/", label: "工作台", end: true },
  { to: "/novels", label: "小说库 / 蒸馏" },
  { to: "/styles", label: "风格中心" },
  { to: "/skills", label: "Skill 导出" },
  { to: "/settings", label: "系统设置 · AI" },
];

export default function App() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-slate-900 text-slate-200 flex flex-col">
        <div className="px-5 py-5 border-b border-slate-700">
          <div className="text-lg font-bold text-white">风格蒸馏系统</div>
          <div className="text-xs text-slate-400 mt-1">Style Distill &amp; Skill</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm ${
                  isActive ? "bg-indigo-600 text-white" : "hover:bg-slate-800"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-[11px] text-slate-500 leading-relaxed border-t border-slate-800">
          小说 → 蒸馏 → 聚类 → 风格 → Skill
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/novels" element={<NovelsPage />} />
            <Route path="/styles" element={<StylesPage />} />
            <Route path="/skills" element={<SkillsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
