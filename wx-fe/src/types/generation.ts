export interface GenerationCategory {
  id: string
  category_code: string
  name: string
  sort_order: number
  is_active: boolean
}

export interface GenerationStyle {
  id: string
  name: string
  cover_image_url: string
  rule_version: number
  sort_order: number
  is_active: boolean
}

export interface PresignUploadResponse {
  upload_url: string
  key: string
  expires_in: number
}

export interface GenerationAssetResponse {
  asset_id: string
  tenant_id: string
  job_id: string | null
  asset_role: string
  oss_bucket: string
  oss_key: string
  original_filename: string
  content_type: string
  size_bytes: number | null
  sha256: string
  width: number | null
  height: number | null
  download_url: string
  download_expires_in: number
  created_at: string
  updated_at: string
}

export interface GenerationJobResponse {
  job_id: string
  tenant_id: string
  client_request_id: string
  status: string
  provider: string
  model_name: string
  source_asset_id: string
  raw_result_asset_id: string | null
  watermarked_result_asset_id: string | null
  task_id: string | null
  rule_snapshot: Record<string, unknown>
  prompt_snapshot: Record<string, unknown>
  request_snapshot: Record<string, unknown>
  error_code: string
  error_message: string
  raw_result_download_url?: string | null
  watermarked_result_download_url?: string | null
  source_preview_url?: string | null
  created_at: string
  updated_at: string
}

export interface GenerationHistoryItem {
  job_id: string
  status: string
  created_at: string
  updated_at: string
  source_preview_url?: string | null
  raw_result_download_url?: string | null
  watermarked_result_download_url?: string | null
  error_message: string
}

export interface QuotaSummary {
  total_units: number
  available_units: number
  frozen_units: number
  active_plan_name?: string | null
  updated_at?: string | null
}

export interface PrivacyStatus {
  has_privacy_agreement: boolean
  privacy_accepted_at?: string | null
}

export interface GenerationUploadPayload {
  filename: string
  content_type?: string
}

export interface GenerationAssetConfirmPayload {
  oss_key: string
  filename: string
  content_type: string
  size_bytes?: number | null
  sha256?: string
  asset_role?: string
  oss_bucket?: string | null
  width?: number | null
  height?: number | null
  extra_metadata?: Record<string, unknown> | null
}

export interface GenerationJobCreatePayload {
  client_request_id: string
  source_asset_id: string
  category_id?: string | null
  style_id?: string | null
  prompt_hint?: string
}

export interface LocalFileSelection {
  path: string
  name: string
  size?: number
  type?: string
}

export interface GenerationUploadResult {
  local_file: LocalFileSelection
  confirmed_asset: GenerationAssetResponse
}
