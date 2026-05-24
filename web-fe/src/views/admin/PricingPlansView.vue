<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPricingPlan,
  deletePricingPlan,
  listPricingPlans,
  updatePricingPlan,
} from '@/api/admin/billing'
import type { PricingPlan } from '@/types'

const rows = ref<PricingPlan[]>([])
const loading = ref(false)
const drawer = ref(false)
const editing = ref<PricingPlan | null>(null)
const form = ref({
  plan_code: '',
  plan_name: '',
  quota_units: 100,
  price_cents: 0,
  valid_days: 30,
  sort_order: 0,
  is_active: true,
})

async function load() {
  loading.value = true
  rows.value = await listPricingPlans()
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.value = {
    plan_code: '',
    plan_name: '',
    quota_units: 100,
    price_cents: 0,
    valid_days: 30,
    sort_order: 0,
    is_active: true,
  }
  drawer.value = true
}

function openEdit(row: PricingPlan) {
  editing.value = row
  form.value = {
    plan_code: row.plan_code,
    plan_name: row.plan_name,
    quota_units: row.quota_units,
    price_cents: row.price_cents,
    valid_days: row.valid_days,
    sort_order: row.sort_order,
    is_active: row.is_active,
  }
  drawer.value = true
}

async function save() {
  if (editing.value) {
    await updatePricingPlan(editing.value.id, {
      plan_name: form.value.plan_name,
      quota_units: form.value.quota_units,
      price_cents: form.value.price_cents,
      valid_days: form.value.valid_days,
      sort_order: form.value.sort_order,
      is_active: form.value.is_active,
    })
  } else {
    await createPricingPlan(form.value)
  }
  ElMessage.success('已保存')
  drawer.value = false
  await load()
}

async function remove(row: PricingPlan) {
  await ElMessageBox.confirm(`删除套餐「${row.plan_name}」？`, '确认')
  await deletePricingPlan(row.id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex justify-between">
      <h1 class="text-2xl font-bold">定价套餐</h1>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="plan_code" label="编码" width="120" />
      <el-table-column prop="plan_name" label="名称" />
      <el-table-column prop="quota_units" label="额度张数" width="100" />
      <el-table-column prop="valid_days" label="有效天" width="90" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-drawer v-model="drawer" :title="editing ? '编辑套餐' : '新建套餐'" size="400px">
      <el-form label-position="top">
        <el-form-item v-if="!editing" label="编码"><el-input v-model="form.plan_code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.plan_name" /></el-form-item>
        <el-form-item label="额度"><el-input-number v-model="form.quota_units" /></el-form-item>
        <el-form-item label="价格(分)"><el-input-number v-model="form.price_cents" /></el-form-item>
        <el-form-item label="有效天数"><el-input-number v-model="form.valid_days" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawer = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>
