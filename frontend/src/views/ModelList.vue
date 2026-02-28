<template>
  <div>
    <h2>模型库管理</h2>
    <el-button type="primary" @click="dialogVisible = true">导入模型</el-button>
    <el-table :data="models" style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="type" label="类型" />
      <el-table-column prop="accuracy" label="精度" />
      <el-table-column prop="created_at" label="创建时间" />
    </el-table>

    <el-dialog v-model="dialogVisible" title="导入模型" width="30%">
      <el-form :model="form">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type">
            <el-option label="Detector" value="detector" />
            <el-option label="Segmentor" value="segmentor" />
          </el-select>
        </el-form-item>
        <el-form-item label="精度">
          <el-input-number v-model="form.accuracy" :precision="2" :step="0.01" />
        </el-form-item>
        <el-form-item label="模型文件">
           <input type="file" @change="handleFileChange" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const models = ref([])
const dialogVisible = ref(false)
const form = ref({
  name: '',
  type: 'detector',
  accuracy: 0.95,
  file: null
})

const fetchModels = async () => {
  try {
    const res = await api.getModels()
    models.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const handleFileChange = (e) => {
  form.value.file = e.target.files[0]
}

const submitUpload = async () => {
  if (!form.value.file) return
  const formData = new FormData()
  formData.append('name', form.value.name)
  formData.append('type', form.value.type)
  formData.append('accuracy', form.value.accuracy)
  formData.append('file', form.value.file)

  try {
    await api.uploadModel(formData)
    dialogVisible.value = false
    fetchModels()
  } catch (error) {
    console.error(error)
  }
}

onMounted(fetchModels)
</script>
