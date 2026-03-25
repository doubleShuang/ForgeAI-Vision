<template>
  <div class="h-full flex flex-col">
    <!-- 搜索区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 mb-4 flex gap-4 transition-colors">
      <el-input v-model="searchQuery" placeholder="参数名称/参数键名" class="w-64" clearable @keyup.enter="handleSearch">
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
        <h2 class="text-lg font-medium text-gray-800 dark:text-gray-200">参数配置</h2>
        <div>
          <el-button type="primary" plain :icon="Plus" @click="handleAdd">新增参数</el-button>
        </div>
      </div>
      
      <!-- 参数数据表格 -->
      <el-table :data="tableData" style="width: 100%" class="flex-1" v-loading="loading">
        <el-table-column prop="id" label="参数主键" width="100" align="center" />
        <el-table-column prop="config_name" label="参数名称" />
        <el-table-column prop="config_key" label="参数键名" />
        <el-table-column prop="config_value" label="参数键值" />
        <el-table-column prop="config_type" label="系统内置" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.config_type === 'Y' ? 'warning' : 'info'">
              {{ scope.row.config_type === 'Y' ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="550px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="参数名称" prop="config_name">
          <el-input v-model="formData.config_name" placeholder="请输入参数名称" />
        </el-form-item>
        <el-form-item label="参数键名" prop="config_key">
          <el-input v-model="formData.config_key" placeholder="请输入参数键名" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="参数键值" prop="config_value">
          <el-input v-model="formData.config_value" placeholder="请输入参数键值" />
        </el-form-item>
        <el-form-item label="系统内置">
          <el-radio-group v-model="formData.config_type">
            <el-radio value="Y">是</el-radio>
            <el-radio value="N">否</el-radio>
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
 * 参数配置管理页面
 * 功能：系统参数的增删改查
 * 数据来源：后端 /api/v1/system/configs/* 接口
 */
import { ref, onMounted, reactive } from 'vue'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getConfigList, addConfig, updateConfig, removeConfigs } from '@/api/system'

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const tableData = ref([])
const loading = ref(false)

/** 获取参数配置列表 */
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getConfigList({ keyword: searchQuery.value, page: currentPage.value, page_size: pageSize.value })
    tableData.value = res.list || []
    total.value = res.total || 0
  } catch (err) { ElMessage.error('获取参数列表失败') }
  finally { loading.value = false }
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchQuery.value = ''; currentPage.value = 1; fetchData() }

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const formRef = ref(null)

const formData = reactive({ id: null, config_name: '', config_key: '', config_value: '', config_type: 'N', remark: '' })
const formRules = {
  config_name: [{ required: true, message: '请输入参数名称', trigger: 'blur' }],
  config_key: [{ required: true, message: '请输入参数键名', trigger: 'blur' }],
  config_value: [{ required: true, message: '请输入参数键值', trigger: 'blur' }]
}

const resetForm = () => { Object.assign(formData, { id: null, config_name: '', config_key: '', config_value: '', config_type: 'N', remark: '' }) }
const handleAdd = () => { resetForm(); dialogTitle.value = '新增参数'; dialogVisible.value = true }
const handleEdit = (row) => { resetForm(); Object.assign(formData, row); dialogTitle.value = '编辑参数'; dialogVisible.value = true }

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const api = formData.id ? updateConfig : addConfig
    const res = await api({ ...formData })
    if (res.code === 200) { ElMessage.success(res.msg); dialogVisible.value = false; fetchData() }
    else { ElMessage.warning(res.msg) }
  } catch (err) { ElMessage.error('操作失败') }
  finally { submitLoading.value = false }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除参数「${row.config_name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      const res = await removeConfigs([row.id])
      if (res.code === 200) { ElMessage.success('删除成功'); fetchData() }
    }).catch(() => {})
}

onMounted(() => { fetchData() })
</script>
