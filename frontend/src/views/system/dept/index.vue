<template>
  <div class="h-full flex flex-col">
    <!-- 搜索区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 mb-4 flex gap-4 transition-colors">
      <el-input v-model="searchQuery" placeholder="输入部门名称搜索" class="w-64" clearable @keyup.enter="handleSearch">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 表格区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 flex-1 flex flex-col transition-colors overflow-hidden">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-medium text-gray-800 dark:text-gray-200">部门管理</h2>
        <div>
          <el-button type="primary" plain :icon="Plus" @click="handleAdd(0)">新增部门</el-button>
        </div>
      </div>
      
      <!-- 部门树形表格 -->
      <el-table
        :data="tableData"
        style="width: 100%"
        class="flex-1"
        row-key="id"
        default-expand-all
        :tree-props="{ children: 'children' }"
        v-loading="loading"
      >
        <el-table-column prop="dept_name" label="部门名称" />
        <el-table-column prop="leader" label="负责人" width="120" />
        <el-table-column prop="phone" label="联系电话" width="150" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
              {{ scope.row.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="scope">
            <el-button link type="primary" :icon="Edit" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="primary" :icon="Plus" @click="handleAdd(scope.row.id)">新增下级</el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="上级部门">
          <el-input-number v-model="formData.parent_id" :min="0" placeholder="0表示顶级部门" style="width: 100%" />
        </el-form-item>
        <el-form-item label="部门名称" prop="dept_name">
          <el-input v-model="formData.dept_name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="formData.leader" placeholder="请输入负责人" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="formData.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 部门管理页面
 * 功能：部门树形展示、搜索、新增（支持指定上级）、编辑、删除
 * 数据来源：后端 /api/v1/system/depts/* 接口
 */
import { ref, onMounted, reactive } from 'vue'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDeptList, addDept, updateDept, removeDepts } from '@/api/system'

// ==================== 列表数据 ====================
const searchQuery = ref('')
const tableData = ref([])
const loading = ref(false)

/** 获取部门树形列表 */
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getDeptList({ keyword: searchQuery.value })
    tableData.value = res.list || []
  } catch (err) {
    ElMessage.error('获取部门列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { fetchData() }
const handleReset = () => { searchQuery.value = ''; fetchData() }

// ==================== 新增/编辑弹窗 ====================
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const formRef = ref(null)

const formData = reactive({ id: null, parent_id: 0, dept_name: '', leader: '', phone: '', sort: 0, status: 1 })
const formRules = { dept_name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }] }

const resetForm = () => { Object.assign(formData, { id: null, parent_id: 0, dept_name: '', leader: '', phone: '', sort: 0, status: 1 }) }

/** 新增部门（支持传入上级部门ID） */
const handleAdd = (parentId = 0) => { resetForm(); formData.parent_id = parentId; dialogTitle.value = '新增部门'; dialogVisible.value = true }

/** 编辑部门 */
const handleEdit = (row) => { resetForm(); Object.assign(formData, row); dialogTitle.value = '编辑部门'; dialogVisible.value = true }

/** 提交表单 */
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const api = formData.id ? updateDept : addDept
    const res = await api({ ...formData })
    if (res.code === 200) { ElMessage.success(res.msg); dialogVisible.value = false; fetchData() }
    else { ElMessage.warning(res.msg) }
  } catch (err) { ElMessage.error('操作失败') }
  finally { submitLoading.value = false }
}

// ==================== 删除 ====================
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除部门「${row.dept_name}」吗？删除后其下级部门将一并删除。`, '提示', { type: 'warning' })
    .then(async () => {
      const res = await removeDepts([row.id])
      if (res.code === 200) { ElMessage.success('删除成功'); fetchData() }
    }).catch(() => {})
}

onMounted(() => { fetchData() })
</script>
