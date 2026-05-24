<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createStyle,
  deleteStyle,
  listStylesAdmin,
  updateStyle,
} from '@/api/admin/catalog'
import type { Style } from '@/types'

const rows = ref<Style[]>([])
const loading = ref(false)
const drawer = ref(false)
const editing = ref<Style | null>(null)
const form = ref({
  name: '',
  cover_image_url: '',
  rule_version: 1,
  sort_order: 0,
  is_active: true,
})

async function load() {
  loading.value = true
  rows.value = await listStylesAdmin()
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.value = { name: '', cover_image_url: '', rule_version: 1, sort_order: 0, is_active: true }
  drawer.value = true
}

function openEdit(row: Style) {
  editing.value = row
  form.value = { ...row }
  drawer.value = true
}

async function save() {
  if (editing.value) {
    await updateStyle(editing.value.id, form.value)
  } else {
    await createStyle(form.value)
  }
  ElMessage.success('已保存')
  drawer.value = false
  await load()
}

async function remove(row: Style) {
  await ElMessageBox.confirm(`删除风格「${row.name}」？`, '确认')
  await deleteStyle(row.id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">风格模板</h1>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column label="封面" width="80">
        <template #default="{ row }">
          <img v-if="row.cover_image_url" :src="row.cover_image_url" class="h-10 w-10 rounded object-cover" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="rule_version" label="规则版本" width="100" />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="drawer" :title="editing ? '编辑风格' : '新建风格'" size="420px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="封面 URL"><el-input v-model="form.cover_image_url" /></el-form-item>
        <el-form-item label="规则版本"><el-input-number v-model="form.rule_version" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawer = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>
