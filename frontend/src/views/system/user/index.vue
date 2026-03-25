<template>
  <div class="h-full flex flex-col">
    <!-- 搜索区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 mb-4 flex gap-4 transition-colors">
      <el-input v-model="searchQuery" placeholder="搜索用户名/昵称" class="w-64" clearable @keyup.enter="handleSearch">
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
        <h2 class="text-lg font-medium text-gray-800 dark:text-gray-200">用户列表</h2>
        <div>
          <el-button type="primary" plain :icon="Plus" @click="handleAdd">新增用户</el-button>
          <el-button type="danger" plain :icon="Delete" :disabled="!selectedRows.length" @click="handleBatchDelete">批量删除</el-button>
        </div>
      </div>
      
      <!-- 用户数据表格 -->
      <el-table :data="tableData" style="width: 100%" class="flex-1" @selection-change="handleSelectionChange" v-loading="loading">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="用户昵称" />
        <el-table-column prop="department" label="所属部门" />
        <el-table-column prop="role" label="角色" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
              {{ scope.row.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button link type="primary" :icon="Edit" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="550px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="用户昵称" prop="nickname">
          <el-input v-model="formData.nickname" placeholder="请输入用户昵称" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号码">
          <el-input v-model="formData.phone" placeholder="请输入手机号码" />
        </el-form-item>
        <el-form-item label="密码" v-if="!formData.id">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
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
 * 用户管理页面
 * 功能：用户列表展示、搜索、新增、编辑、删除、批量删除
 * 数据来源：后端 /api/v1/system/users/* 接口
 */
import { ref, onMounted, reactive } from 'vue'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, addUser, updateUser, removeUsers } from '@/api/system'

// ==================== 列表数据 ====================
const searchQuery = ref('')        // 搜索关键词
const selectedRows = ref([])       // 当前选中的行
const currentPage = ref(1)         // 当前页码
const pageSize = ref(10)           // 每页条数
const total = ref(0)               // 总记录数
const tableData = ref([])          // 表格数据
const loading = ref(false)         // 加载状态

/**
 * 从后端获取用户列表数据
 */
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      keyword: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value
    })
    tableData.value = res.list || []
    total.value = res.total || 0
  } catch (err) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

/** 搜索按钮点击 */
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

/** 重置搜索条件 */
const handleReset = () => {
  searchQuery.value = ''
  currentPage.value = 1
  fetchData()
}

/** 表格多选变化 */
const handleSelectionChange = (val) => {
  selectedRows.value = val
}

// ==================== 新增/编辑弹窗 ====================
const dialogVisible = ref(false)   // 弹窗显隐
const dialogTitle = ref('')        // 弹窗标题
const submitLoading = ref(false)   // 提交按钮加载状态
const formRef = ref(null)          // 表单引用

// 表单数据
const formData = reactive({
  id: null,
  username: '',
  nickname: '',
  email: '',
  phone: '',
  dept_id: 0,
  role_id: 0,
  password: '',
  status: 1,
  remark: ''
})

// 表单验证规则
const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入用户昵称', trigger: 'blur' }]
}

/** 重置表单数据 */
const resetForm = () => {
  formData.id = null
  formData.username = ''
  formData.nickname = ''
  formData.email = ''
  formData.phone = ''
  formData.dept_id = 0
  formData.role_id = 0
  formData.password = ''
  formData.status = 1
  formData.remark = ''
}

/** 打开新增弹窗 */
const handleAdd = () => {
  resetForm()
  dialogTitle.value = '新增用户'
  dialogVisible.value = true
}

/** 打开编辑弹窗 */
const handleEdit = (row) => {
  resetForm()
  Object.assign(formData, row)
  dialogTitle.value = '编辑用户'
  dialogVisible.value = true
}

/** 提交表单（新增或编辑） */
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const api = formData.id ? updateUser : addUser
    const res = await api({ ...formData })
    if (res.code === 200) {
      ElMessage.success(res.msg)
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.warning(res.msg)
    }
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 删除操作 ====================

/** 删除单个用户 */
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除用户「${row.username}」吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const res = await removeUsers([row.id])
    if (res.data.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    }
  }).catch(() => {})
}

/** 批量删除用户 */
const handleBatchDelete = () => {
  const ids = selectedRows.value.map(r => r.id)
  ElMessageBox.confirm(`确定要删除选中的 ${ids.length} 个用户吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const res = await removeUsers(ids)
    if (res.data.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    }
  }).catch(() => {})
}

// 页面加载时获取数据
onMounted(() => {
  fetchData()
})
</script>
