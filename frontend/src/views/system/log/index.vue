<template>
  <div class="h-full flex flex-col">
    <!-- 搜索区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 mb-4 flex gap-4 transition-colors">
      <el-input v-model="searchQuery" placeholder="操作模块/操作人员" class="w-64" clearable @keyup.enter="handleSearch">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 260px"
      />
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
      <el-button type="danger" plain :icon="Delete" @click="handleClear">清空日志</el-button>
    </div>

    <!-- 表格区域 -->
    <div class="bg-white dark:bg-[#1d1e1f] p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 flex-1 flex flex-col transition-colors overflow-hidden">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-medium text-gray-800 dark:text-gray-200">操作日志</h2>
      </div>
      
      <!-- 日志数据表格 -->
      <el-table :data="tableData" style="width: 100%" class="flex-1" border v-loading="loading">
        <el-table-column prop="id" label="日志编号" width="100" align="center" />
        <el-table-column prop="module" label="系统模块" width="150" />
        <el-table-column prop="type" label="操作类型" width="100" align="center">
          <template #default="scope">
            <!-- 根据操作类型显示不同颜色标签 -->
            <el-tag :type="getTypeTagColor(scope.row.type)">{{ scope.row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人员" width="120" />
        <el-table-column prop="ip" label="操作IP" width="150" />
        <el-table-column prop="location" label="操作地点" width="180" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
              {{ scope.row.status === 1 ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" width="180" />
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 操作日志管理页面
 * 功能：日志列表展示、按模块/人员搜索、按日期范围筛选、清空日志
 * 数据来源：后端 /api/v1/system/logs/* 接口
 */
import { ref, onMounted } from 'vue'
import { Search, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getLogList, clearLogs } from '@/api/system'

const searchQuery = ref('')
const dateRange = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const tableData = ref([])
const loading = ref(false)

/**
 * 根据操作类型返回标签颜色
 * @param {string} type - 操作类型字符串
 * @returns {string} Element Plus 标签类型
 */
const getTypeTagColor = (type) => {
  const map = { 'INSERT': 'success', 'UPDATE': 'warning', 'DELETE': 'danger', 'SELECT': 'info' }
  return map[type] || 'info'
}

/** 获取日志列表 */
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      keyword: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value
    }
    // 如果选择了日期范围，传入开始和结束日期
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await getLogList(params)
    tableData.value = res.list || []
    total.value = res.total || 0
  } catch (err) {
    ElMessage.error('获取日志列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchQuery.value = ''; dateRange.value = null; currentPage.value = 1; fetchData() }

/** 清空所有日志 */
const handleClear = () => {
  ElMessageBox.confirm('确定要清空所有操作日志吗？此操作不可恢复！', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'error'
  }).then(async () => {
    const res = await clearLogs()
    if (res.data.code === 200) {
      ElMessage.success('日志已清空')
      fetchData()
    }
  }).catch(() => {})
}

onMounted(() => { fetchData() })
</script>
