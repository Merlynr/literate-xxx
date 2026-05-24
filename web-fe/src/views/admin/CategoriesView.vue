<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createCategory,
  deleteCategory,
  listCategoriesAdmin,
  updateCategory,
} from '@/api/admin/catalog'
import type { Category } from '@/types'

const rows = ref<Category[]>([])
const loading = ref(false)
const drawer = ref(false)
const editing = ref<Category | null>(null)
const form = ref({ category_code: '', name: '', sort_order: 0, is_active: true })

async function load() {
  loading.value = true
  rows.value = await listCategoriesAdmin()
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.value = { category_code: '', name: '', sort_order: 0, is_active: true }
  drawer.value = true
}

function openEdit(row: Category) {
  editing.value = row
  form.value = {
    category_code: row.category_code,
    name: row.name,
    sort_order: row.sort_order,
    is_active: row.is_active,
  }
  drawer.value = true
}

async function save() {
  if (editing.value) {
    await updateCategory(editing.value.id, {
      name: form.value.name,
      sort_order: form.value.sort_order,
      is_active: form.value.is_active,
    })
  } else {
    await createCategory(form.value)
  }
  ElMessage.success('已保存')
  drawer.value = false
  await load()
}

async function remove(row: Category) {
  await ElMessageBox.confirm(`删除类目「${row.name}」？`, '确认')
  await deleteCategory(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">商品类目</h1>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="category_code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="drawer" :title="editing ? '编辑类目' : '新建类目'" size="400px">
      <el-form label-position="top">
        <el-form-item v-if="!editing" label="编码">
          <el-input v-model="form.category_code" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" class="w-full" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawer = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>
