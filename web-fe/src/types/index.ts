export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserProfile {
  id: string
  openid: string
  nickname: string
  avatar_url: string
  tenant_id: string
  privacy_accepted_at?: string | null
}

export interface Category {
  id: string
  category_code: string
  name: string
  sort_order: number
  is_active: boolean
}

export interface Style {
  id: string
  name: string
  cover_image_url: string
  rule_version: number
  sort_order: number
  is_active: boolean
}

export interface Term {
  id: string
  type: string
  content: string
  weight: number
  sort_order: number
  scope: Record<string, unknown> | null
  is_active: boolean
}

export interface PromoRule {
  id: string
  name: string
  slot_template: Record<string, unknown> | null
  term_selection_strategy: string
  aspect_ratio: string
  watermark_config: Record<string, unknown> | null
  version: number
  is_active: boolean
}

export interface PricingPlan {
  id: number
  plan_code: string
  plan_name: string
  quota_units: number
  price_cents: number
  valid_days: number
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface QuotaSummary {
  total_units: number
  available_units: number
  frozen_units: number
  active_plan_name?: string | null
  updated_at?: string | null
}

export interface QuotaLedgerItem {
  id: string
  tenant_id: string
  job_id: string | null
  plan_id: number | null
  event_type: string
  delta_units: number
  available_before: number
  available_after: number
  frozen_before: number
  frozen_after: number
  reason: string
  created_at: string
}

export interface GenerationAsset {
  asset_id: string
  download_url: string
  original_filename: string
  content_type: string
  size_bytes: number | null
}

export interface GenerationJob {
  job_id: string
  status: string
  error_message: string
  raw_result_download_url?: string | null
  watermarked_result_download_url?: string | null
  source_preview_url?: string | null
  source_preview_urls?: string[] | null
  prompt_snapshot?: {
    category?: { name?: string; category_code?: string } | null
    style?: { name?: string } | null
    prompt_hint?: string
  }
  request_snapshot?: {
    prompt_hint?: string
  }
  created_at: string
  updated_at: string
}

export interface GenerationHistoryItem {
  job_id: string
  status: string
  created_at: string
  updated_at: string
  category_id?: string | null
  category_name?: string
  style_id?: string | null
  style_name?: string
  prompt_hint?: string
  source_preview_url?: string | null
  raw_result_download_url?: string | null
  watermarked_result_download_url?: string | null
  error_message: string
}

export interface GenerationJobDetail {
  job_id: string
  status: string
  error_message: string
  source_preview_url?: string | null
  raw_result_download_url?: string | null
  watermarked_result_download_url?: string | null
  prompt_snapshot: {
    category?: { name?: string; category_code?: string } | null
    style?: { name?: string } | null
    prompt_hint?: string
  }
  request_snapshot: {
    prompt_hint?: string
  }
  created_at: string
  updated_at: string
}

export interface PrivacyStatus {
  has_privacy_agreement: boolean
  privacy_accepted_at?: string | null
}
