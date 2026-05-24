import { getJob } from '@/api/generation'
import type { GenerationHistoryItem, GenerationJob } from '@/types'

export function metaFromJob(job: GenerationJob) {
  const categoryName = job.prompt_snapshot?.category?.name?.trim() || ''
  const styleName = job.prompt_snapshot?.style?.name?.trim() || ''
  const promptHint =
    job.request_snapshot?.prompt_hint?.trim() ||
    job.prompt_snapshot?.prompt_hint?.trim() ||
    ''
  return { categoryName, styleName, promptHint }
}

/** 列表接口缺字段时，用详情接口补齐（与详情页同源） */
export async function enrichHistoryItems(
  rows: GenerationHistoryItem[],
): Promise<GenerationHistoryItem[]> {
  return Promise.all(
    rows.map(async (row) => {
      const needsEnrich =
        !row.category_name?.trim() || !row.style_name?.trim() || !row.prompt_hint?.trim()
      if (!needsEnrich) return row

      try {
        const job = await getJob(row.job_id)
        const meta = metaFromJob(job)
        return {
          ...row,
          category_name: row.category_name?.trim() || meta.categoryName,
          style_name: row.style_name?.trim() || meta.styleName,
          prompt_hint: row.prompt_hint?.trim() || meta.promptHint,
          raw_result_download_url:
            row.raw_result_download_url || job.raw_result_download_url || null,
          watermarked_result_download_url:
            row.watermarked_result_download_url ||
            job.watermarked_result_download_url ||
            null,
          source_preview_url: row.source_preview_url || job.source_preview_url || null,
        }
      } catch {
        return row
      }
    }),
  )
}
