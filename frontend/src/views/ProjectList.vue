<template>
  <div class="project-list">
    <div class="header">
      <h2>标注工程管理</h2>
      <el-button type="primary" @click="dialogVisible = true">创建新工程</el-button>
    </div>

    <el-table :data="projects" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="工程名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作" width="250">
        <template #default="scope">
          <el-button size="small" @click="openProject(scope.row)">管理数据</el-button>
          <el-button size="small" type="success" @click="startAnnotation(scope.row)">去标注</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create Dialog -->
    <el-dialog v-model="dialogVisible" title="创建新标注工程">
      <el-form :model="form">
        <el-form-item label="工程名称" label-width="80px">
          <el-input v-model="form.name" placeholder="请输入工程名称 (英文)" />
        </el-form-item>
        <el-form-item label="描述" label-width="80px">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createProject">创建</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({ name: '', description: '' })

const fetchProjects = async () => {
  loading.value = true
    try {
        const res = await api.getProjects()
        // request.js 已解构，res 即为项目列表或报文对象
        projects.value = Array.isArray(res) ? res : (res.data || [])
    } catch (error) {
    ElMessage.error('获取工程列表失败')
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  if (!form.value.name) return ElMessage.warning('请输入工程名称')
  try {
    const data = {
      name: form.value.name,
      description: form.value.description
    }
    await api.createProject(data)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    form.value = { name: '', description: '' }
    fetchProjects()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除该工程及其所有数据吗？此操作不可恢复。', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.deleteProject(row.id)
      ElMessage.success('删除成功')
      fetchProjects()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const openProject = (row) => {
    router.push(`/projects/${row.id}`)
}

const startAnnotation = (row) => {
    router.push({ path: '/annotation', query: { projectId: row.id } })
}

onMounted(fetchProjects)
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
