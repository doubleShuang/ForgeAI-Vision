<template>
  <div class="h-full flex flex-col">
    <!-- 搜索区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 mb-4 flex gap-4 transition-colors">
      <el-input v-model="searchQuery" placeholder="搜索角色名称/标识" class="w-64" clearable @keyup.enter="handleSearch">
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
        <h2 class="text-lg font-medium text-gray-800 dark:text-gray-200">角色列表</h2>
        <div>
          <el-button type="primary" plain :icon="Plus" @click="handleAdd">新增角色</el-button>
        </div>
      </div>
      
      <!-- 角色数据表格 -->
      <el-table :data="tableData" style="width: 100%" class="flex-1" v-loading="loading">
        <el-table-column prop="id" label="角色编号" width="100" />
        <el-table-column prop="role_name" label="角色名称" />
        <el-table-column prop="role_key" label="权限字符" />
        <el-table-column prop="sort" label="显示顺序" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
              {{ scope.row.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button link type="primary" :icon="Edit" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="formData.role_name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="权限字符" prop="role_key">
          <el-input v-model="formData.role_key" placeholder="请输入权限字符（如 admin）" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="显示顺序">
          <el-input-number v-model="formData.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="请输入备注" />
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
 * 角色管理页面
 * 功能：角色列表展示、搜索、新增、编辑、删除
 * 数据来源：后端 /api/v1/system/roles/* 接口
 */
import { ref, onMounted, reactive } from 'vue'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoleList, addRole, updateRole, removeRoles } from '@/api/system'

// ==================== 列表数据 ====================
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const tableData = ref([])
const loading = ref(false)

/** 获取角色列表 */
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getRoleList({ keyword: searchQuery.value, page: currentPage.value, page_size: pageSize.value })
    tableData.value = res.list || []
    total.value = res.total || 0
  } catch (err) {
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchQuery.value = ''; currentPage.value = 1; fetchData() }

// ==================== 新增/编辑弹窗 ====================
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const formRef = ref(null)

const formData = reactive({ id: null, role_name: '', role_key: '', sort: 0, status: 1, remark: '' })
const formRules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  role_key: [{ required: true, message: '请输入权限字符', trigger: 'blur' }]
}

const resetForm = () => { Object.assign(formData, { id: null, role_name: '', role_key: '', sort: 0, status: 1, remark: '' }) }

const handleAdd = () => { resetForm(); dialogTitle.value = '新增角色'; dialogVisible.value = true }
const handleEdit = (row) => { resetForm(); Object.assign(formData, row); dialogTitle.value = '编辑角色'; dialogVisible.value = true }

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const api = formData.id ? updateRole : addRole
    const res = await api({ ...formData })
    if (res.code === 200) { ElMessage.success(res.msg); dialogVisible.value = false; fetchData() }
    else { ElMessage.warning(res.msg) }
  } catch (err) { ElMessage.error('操作失败') }
  finally { submitLoading.value = false }
}

// ==================== 删除 ====================
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除角色「${row.role_name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      const res = await removeRoles([row.id])
      if (res.code === 200) { ElMessage.success('删除成功'); fetchData() }
    }).catch(() => {})
}

onMounted(() => { fetchData() })
</script>
