<template>
  <div class="project-detail" v-loading="loading">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <span class="text-large font-600 mr-3"> {{ project.name }} </span>
        </template>
        <template #extra>
          <div class="flex items-center">
            <el-button type="primary" class="ml-2" @click="uploadDialogVisible = true">上传图片</el-button>
            <el-button type="warning" class="ml-2" @click="vocDialogVisible = true">导入VOC数据</el-button>
            <el-button type="success" class="ml-2" @click="goToAnnotation">开始标注</el-button>
            <el-button class="ml-2" @click="classDialogVisible = true">分类管理</el-button>
          </div>
        </template>
      </el-page-header>
    </div>

    <div class="stats" style="margin: 20px 0;">
       <el-descriptions border>
        <el-descriptions-item label="描述">{{ project.description || '无' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
        <el-descriptions-item label="图片数量">{{ totalHint }}</el-descriptions-item>
        <el-descriptions-item label="类别">{{ classes.join(', ') || 'object' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <el-tabs type="border-card">
      <el-tab-pane label="图片列表">
          <div class="image-grid" ref="gridRef">
              <div v-for="(img, idx) in images" :key="img + '_' + idx" class="image-item">
                  <el-image 
                    :src="getImageUrl(img)" 
                    fit="cover" 
                    style="width: 150px; height: 150px; border-radius: 4px;"
                    :preview-src-list="[getImageUrl(img)]" 
                  />
                  <div class="image-name">{{ img }}</div>
              </div>
              <div v-if="images.length === 0 && !loadingMore" class="empty-text">暂无图片，请上传</div>
              <div ref="sentinelRef" class="sentinel"></div>
              <div v-if="loadingMore" class="loading-text">加载中...</div>
              <div v-if="finished && images.length > 0" class="end-text">已加载全部</div>
          </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Upload Images Dialog -->
    <el-dialog v-model="uploadDialogVisible" title="批量上传图片">
      <el-upload
        class="upload-demo"
        drag
        action="#"
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        list-type="picture"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
      </el-upload>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">开始上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Upload VOC Dialog -->
    <el-dialog v-model="vocDialogVisible" title="导入VOC数据集 (ZIP)">
      <div style="margin-bottom: 10px; color: #666; font-size: 12px;">
          请上传包含 images/ 和 xml/ 的 ZIP 压缩包，系统将自动解析并导入。
      </div>
      <el-upload
        class="upload-demo"
        drag
        action="#"
        :auto-upload="false"
        :limit="1"
        accept=".zip"
        :on-change="handleVocFileChange"
        :file-list="vocFileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽 ZIP 文件到此处或 <em>点击上传</em>
        </div>
      </el-upload>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="vocDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitVocUpload" :loading="uploading">开始导入</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Class Management Dialog -->
    <el-dialog v-model="classDialogVisible" title="分类管理">
        <el-input v-model="classInput" type="textarea" :rows="10" placeholder="每行一个类别名称" />
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="classDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="saveClasses">保存</el-button>
            </span>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const project = ref({})
const images = ref([])
const pageSize = ref(50)
const offset = ref(0)
const loadingMore = ref(false)
const finished = ref(false)
const gridRef = ref(null)
const sentinelRef = ref(null)
const totalHint = ref('加载中')
const classes = ref([])
const loading = ref(false)
const uploading = ref(false)

// Upload Images
const uploadDialogVisible = ref(false)
const fileList = ref([])

// Upload VOC
const vocDialogVisible = ref(false)
const vocFileList = ref([])

// Class Management
const classDialogVisible = ref(false)
const classInput = ref('')

const fetchProject = async () => {
  loading.value = true
  try {
    const res = await api.getProject(projectId)
    project.value = res.data
    images.value = []
    offset.value = 0
    finished.value = false
    await loadMore()
    const clsRes = await api.getClasses(projectId)
    classes.value = clsRes.data
    classInput.value = classes.value.join('\n')
  } catch (error) {
    ElMessage.error('获取工程详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
    router.push('/projects')
}

const goToAnnotation = () => {
    router.push({ path: '/annotation', query: { projectId: projectId } })
}

const getImageUrl = (filename) => {
    if (project.value && project.value.name) {
        return `http://localhost:8000/workspaces/${project.value.name}/images/${filename}`
    }
    return ''
}

// Image Upload Logic
const handleFileChange = (file, files) => { fileList.value = files }
const submitUpload = async () => {
    if (fileList.value.length === 0) return
    uploading.value = true
    try {
        const formData = new FormData()
        fileList.value.forEach(file => { formData.append('files', file.raw) })
        await api.uploadProjectImages(projectId, formData)
        ElMessage.success('上传成功')
        uploadDialogVisible.value = false
        fileList.value = []
        fetchProject()
    } catch (error) { ElMessage.error('上传失败') } finally { uploading.value = false }
}

// VOC Upload Logic
const handleVocFileChange = (file, files) => { vocFileList.value = files.slice(-1) }
const submitVocUpload = async () => {
    if (vocFileList.value.length === 0) return
    uploading.value = true
    try {
        const formData = new FormData()
        formData.append('file', vocFileList.value[0].raw)
        const res = await api.uploadVocDataset(projectId, formData)
        ElMessage.success(`成功导入 ${res.data.processed} 张图片及标注`)
        vocDialogVisible.value = false
        vocFileList.value = []
        fetchProject()
    } catch (error) { ElMessage.error('导入失败') } finally { uploading.value = false }
}

// Class Management Logic
const saveClasses = async () => {
    const newClasses = classInput.value.split('\n').map(c => c.trim()).filter(c => c)
    if (newClasses.length === 0) return ElMessage.warning("至少需要一个类别")
    try {
        const data = {
            classes: newClasses.join(',')
        }
        await api.saveClasses(projectId, data)
        ElMessage.success("分类已更新")
        classDialogVisible.value = false
        fetchProject()
    } catch (e) { ElMessage.error("更新失败") }
}

onMounted(fetchProject)

const loadMore = async () => {
  if (loadingMore.value || finished.value) return
  loadingMore.value = true
  try {
    const res = await api.getProjectImages(projectId, offset.value, pageSize.value)
    const items = res.data || []
    if (items.length === 0) {
      finished.value = true
    } else {
      images.value = images.value.concat(items)
      offset.value += items.length
      totalHint.value = `${offset.value}`
      if (items.length < pageSize.value) finished.value = true
    }
  } catch (e) {
  } finally {
    loadingMore.value = false
  }
}

const observeSentinel = () => {
  const el = sentinelRef.value
  if (!el) return
  const io = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadMore()
  })
  io.observe(el)
}

onMounted(() => {
  setTimeout(observeSentinel, 0)
})
</script>

<style scoped>
.image-grid { display: flex; flex-wrap: wrap; gap: 15px; }
.image-item { text-align: center; }
.image-name { font-size: 12px; color: #666; margin-top: 5px; width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-text { padding: 20px; color: #999; }
</style>
