<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPromoRule,
  deletePromoRule,
  listPromoRules,
  updatePromoRule,
} from '@/api/admin/content'
import type { PromoRule } from '@/types'

const rows = ref<PromoRule[]>([])
const loading = ref(false)
const drawer = ref(false)
const editing = ref<PromoRule | null>(null)
const form = ref({
  name: '',
  aspect_ratio: '1:1',
  term_selection_strategy: 'weighted_random',
  is_active: true,
})

async function load() {
  loading.value = true
  rows.value = await listPromoRules()
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.value = {
    name: '',
    aspect_ratio: '1:1',
    term_selection_strategy: 'weighted_random',
    is_active: true,
  }
  drawer.value = true
}

function openEdit(row: PromoRule) {
  editing.value = row
  form.value = {
    name: row.name,
    aspect_ratio: row.aspect_ratio,
    term_selection_strategy: row.term_selection_strategy,
    is_active: row.is_active,
  }
  drawer.value = true
}

async function save() {
  if (editing.value) await updatePromoRule(editing.value.id, form.value)
  else await createPromoRule(form.value)
  ElMessage.success('已保存')
  drawer.value = false
  await load()
}

async function remove(row: PromoRule) {
  await ElMessageBox.confirm(`删除规则「${row.name}」？`, '确认')
  await deletePromoRule(row.id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex justify-between">
      <h1 class="text-2xl font-bold">宣传规则</h1>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="aspect_ratio" label="画幅" width="90" />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-drawer v-model="drawer" :title="editing ? '编辑规则' : '新建规则'" size="420px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="画幅"><el-input v-model="form.aspect_ratio" /></el-form-item>
        <el-form-item label="词条策略"><el-input v-model="form.term_selection_strategy" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawer = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>
