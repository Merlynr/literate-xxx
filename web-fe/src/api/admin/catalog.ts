import { request } from '../request'
import type { Category, Style } from '@/types'

export function listCategoriesAdmin(includeInactive = true) {
  const active = includeInactive ? '' : 'is_active=true&'
  return request<Category[]>({ url: `/categories/?${active}limit=500` })
}

export function createCategory(data: {
  category_code: string
  name: string
  sort_order?: number
  is_active?: boolean
}) {
  return request<Category>({ url: '/categories/', method: 'POST', data })
}

export function updateCategory(
  id: string,
  data: Partial<{ name: string; sort_order: number; is_active: boolean }>,
) {
  return request<Category>({ url: `/categories/${id}`, method: 'PUT', data })
}

export function deleteCategory(id: string) {
  return request<void>({ url: `/categories/${id}`, method: 'DELETE' })
}

export function listStylesAdmin(includeInactive = true) {
  const active = includeInactive ? '' : 'is_active=true&'
  return request<Style[]>({ url: `/styles/?${active}limit=500` })
}

export function createStyle(data: {
  name: string
  cover_image_url?: string
  rule_version?: number
  sort_order?: number
  is_active?: boolean
}) {
  return request<Style>({ url: '/styles/', method: 'POST', data })
}

export function updateStyle(
  id: string,
  data: Partial<{
    name: string
    cover_image_url: string
    rule_version: number
    sort_order: number
    is_active: boolean
  }>,
) {
  return request<Style>({ url: `/styles/${id}`, method: 'PUT', data })
}

export function deleteStyle(id: string) {
  return request<void>({ url: `/styles/${id}`, method: 'DELETE' })
}
