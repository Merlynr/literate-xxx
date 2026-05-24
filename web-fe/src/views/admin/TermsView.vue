<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createTerm, deleteTerm, listTerms, updateTerm } from '@/api/admin/content'
import type { Term } from '@/types'

const rows = ref<Term[]>([])
const loading = ref(false)
const drawer = ref(false)
const editing = ref<Term | null>(null)
const form = ref({
  type: 'positive',
  content: '',
  weight: 10,
  sort_order: 0,
  is_active: true,
})

async function load() {
  loading.value = true
  rows.value = await listTerms()
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.value = { type: 'positive', content: '', weight: 10, sort_order: 0, is_active: true }
  drawer.value = true
}

function openEdit(row: Term) {
  editing.value = row
  form.value = { type: row.type, content: row.content, weight: row.weight, sort_order: row.sort_order, is_active: row.is_active }
  drawer.value = true
}

async function save() {
  if (editing.value) await updateTerm(editing.value.id, form.value)
  else await createTerm(form.value)
  ElMessage.success('已保存')
  drawer.value = false
  await load()
}

async function remove(row: Term) {
  await ElMessageBox.confirm('确认删除？', '词条')
  await deleteTerm(row.id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex justify-between">
      <h1 class="text-2xl font-bold">词条库</h1>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="weight" label="权重" width="80" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-drawer v-model="drawer" :title="editing ? '编辑词条' : '新建词条'" size="400px">
      <el-form label-position="top">
        <el-form-item label="类型">
          <el-select v-model="form.type" class="w-full">
            <el-option label="正向" value="positive" />
            <el-option label="负向" value="negative" />
            <el-option label="前缀" value="prefix" />
            <el-option label="品牌" value="brand" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" /></el-form-item>
        <el-form-item label="权重"><el-input-number v-model="form.weight" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawer = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>
