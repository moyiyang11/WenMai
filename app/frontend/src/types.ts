// 与后端 schemas.py 对齐的类型
export interface Tag { id: number; name: string; kind: string; }

export interface Novel {
  id: number;
  title: string;
  author: string;
  market: string;
  genre: string;
  novel_type: string;
  status: string;
  word_count: number;
  chapter_count: number;
  summary: string;
  selling_point: string;
  source: string;
  distill_status: string;
  created_at: string;
  tags: Tag[];
}

export interface Distillation {
  id: number;
  novel_id: number;
  model: string;
  error: string;
  result: Record<string, any>;
  updated_at: string;
}

export interface StyleFeature {
  id: number;
  dimension: string;
  feature: string;
  stability: number;
  level: string;
}

export interface StyleProfile {
  id: number;
  name: string;
  description: string;
  stability: number;
  profile_yaml: string;
  created_at: string;
  features: StyleFeature[];
  novels: Novel[];
}

export interface Skill {
  id: number;
  profile_id: number;
  name: string;
  version: string;
  stability: number;
  source_count: number;
  feature_count: number;
  export_path: string;
  created_at: string;
}

export interface LLMConfig {
  configured: boolean;
  source: string; // db / env / none
  model: string;
  base_url: string;
  masked_key: string;
}

export interface Dashboard {
  total_novels: number;
  distilled: number;
  pending: number;
  failed: number;
  profile_count: number;
  skill_count: number;
  market_dist: Record<string, number>;
  genre_dist: Record<string, number>;
  style_dist: Record<string, number>;
  recent_novels: Novel[];
  recent_skills: Skill[];
}
