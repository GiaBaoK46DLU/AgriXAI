// Kiểu TypeScript khớp trực tiếp với các schema Pydantic ở backend/app/schemas.
// Tên trường giữ nguyên snake_case như JSON trả về — không đổi sang camelCase
// để khỏi phải viết lớp map hai chiều cho một dự án đồ án quy mô nhỏ.

export type UserRole = "admin" | "farmer";

export interface UserOut {
  id: number;
  username: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type PlotStatus = "active" | "fallow" | "archived";

export interface PlotWithStats {
  id: number;
  puc: string;
  owner_id: number;
  name: string;
  region: string | null;
  area_m2: number | null;
  crop: string;
  status: PlotStatus;
  note: string | null;
  created_at: string;
  owner_name: string | null;
  diagnosis_count: number;
  last_diagnosis_at: string | null;
  last_disease_name: string | null;
  last_severity: string | null;
}

export type Severity = "none" | "mild" | "moderate" | "severe";

export interface DiagnosisOut {
  id: number;
  plot_id: number | null;
  user_id: number;
  disease_key: string;
  disease_name: string;
  confidence: number;
  severity: Severity;
  severity_name: string;
  affected_ratio: number;
  explanation: string | null;
  model_version: string;
  latency_ms: number;
  note: string | null;
  created_at: string;
  image_path: string;
  overlay_path: string | null;
  image_url: string;
  overlay_url: string | null;
  plot_puc: string | null;
  plot_name: string | null;
}

export interface DiagnosisImageOut {
  id: number;
  disease_key: string;
  disease_name: string;
  confidence: number;
  image_path: string;
  overlay_path: string | null;
  image_url: string;
  overlay_url: string | null;
}

export interface ProbabilityItem {
  disease_key: string;
  name_vi: string;
  probability: number;
}

export interface ProductLink {
  name: string;
  group: string | null;
  purchase_url: string | null;
  note: string | null;
}

export interface DiseaseInfo {
  key: string;
  name_vi: string;
  name_en: string;
  pathogen: string | null;
  is_healthy: boolean;
  visual_cue: string | null;
  symptoms: string;
  favorable_conditions: string | null;
  treatments: string[];
  prevention: string[];
  reference_url: string | null;
  products: ProductLink[];
  video_url: string | null;
}

export interface DiagnosisDetail extends DiagnosisOut {
  disease: DiseaseInfo | null;
  top_predictions: ProbabilityItem[];
  disclaimer: string;
  images: DiagnosisImageOut[];
}

export interface DiagnosisPage {
  items: DiagnosisOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface OverviewStats {
  total_plots: number;
  total_farmers: number;
  total_diagnoses: number;
  recent_alerts: number;
}

export interface TimeseriesPoint {
  day: string;
  count: number;
}

export interface DiseaseCount {
  disease_key: string;
  name_vi: string;
  count: number;
}

export interface SeverityCount {
  severity: string;
  name_vi: string;
  count: number;
}

export interface DashboardStats {
  overview: OverviewStats;
  timeseries: TimeseriesPoint[];
  by_disease: DiseaseCount[];
  by_severity: SeverityCount[];
  using_real_model: boolean;
  model_version: string;
}

export interface MedicineOut {
  id: number;
  name: string;
  group: string | null;
  purchase_url: string | null;
}

export interface DiseaseMedicineOut {
  id: number;
  disease_key: string;
  medicine_id: number;
  note: string | null;
  medicine_name: string;
}

export interface DiseaseGuideOut {
  disease_key: string;
  video_url: string;
}

export type ForumPostType = "agree" | "disagree" | "medicine_issue" | "tip";

export interface ForumPostOut {
  id: number;
  user_id: number;
  disease_key: string;
  diagnosis_id: number | null;
  type: ForumPostType;
  content: string;
  likes_count: number;
  created_at: string;
  user_full_name: string;
  user_role: string;
  diagnosis_summary: string | null;
  disease_name: string;
  is_liked_by_me: boolean;
  comments_count: number;
}

export interface ForumCommentOut {
  id: number;
  post_id: number;
  user_id: number;
  content: string;
  created_at: string;
  user_full_name: string;
  user_role: string;
}

export interface ForumPostDetail extends ForumPostOut {
  comments: ForumCommentOut[];
}

export interface ForumPostPage {
  items: ForumPostOut[];
  total: number;
  page: number;
  page_size: number;
}
