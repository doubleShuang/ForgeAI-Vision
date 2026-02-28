<template>
  <div>
    <h2>识别历史记录</h2>
    
    <div style="margin-bottom: 20px;">
        <el-radio-group v-model="viewMode">
            <el-radio-button label="list">列表视图</el-radio-button>
            <el-radio-button label="card">卡片视图</el-radio-button>
        </el-radio-group>
        <el-button @click="fetchHistory" :icon="Refresh" circle style="margin-left: 10px;" />
    </div>

    <!-- List View -->
    <el-table v-if="viewMode === 'list'" :data="history" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="预览" width="120">
          <template #default="scope">
              <el-image 
                v-if="scope.row.file_type === 'image'"
                style="width: 100px; height: 100px; cursor: pointer;" 
                :src="getFileUrl(scope.row.input_path)" 
                fit="cover" 
                @click="viewImageResult(scope.row)"
              />
              <div v-else style="width: 100px; height: 100px; background: #000; color: #fff; display: flex; align-items: center; justify-content: center;">
                  VIDEO
              </div>
          </template>
      </el-table-column>
      <el-table-column prop="name" label="名称/备注">
          <template #default="scope">
              <span v-if="!scope.row.isEditing">{{ scope.row.name }}</span>
              <el-input v-else v-model="scope.row.editName" size="small" />
          </template>
      </el-table-column>
      <el-table-column prop="model_name" label="使用模型" />
      <el-table-column prop="file_type" label="类型" width="100" />
      <el-table-column prop="created_at" label="时间" width="180">
          <template #default="scope">
              {{ new Date(scope.row.created_at).toLocaleString() }}
          </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
          <template #default="scope">
              <el-button v-if="!scope.row.isEditing" size="small" @click="startEdit(scope.row)">编辑</el-button>
              <el-button v-else size="small" type="success" @click="saveEdit(scope.row)">保存</el-button>
              
              <el-button v-if="scope.row.file_type === 'video' && scope.row.output_path" size="small" type="primary" @click="viewVideoResult(scope.row)">查看结果</el-button>
               <el-button v-if="scope.row.file_type === 'image'" size="small" type="primary" @click="viewImageResult(scope.row)">查看结果</el-button>
              <el-button size="small" type="danger" @click="deleteRecord(scope.row.id)">删除</el-button>
          </template>
      </el-table-column>
    </el-table>

    <!-- Card View -->
    <el-row v-else :gutter="20" v-loading="loading">
        <el-col :span="6" v-for="item in history" :key="item.id" style="margin-bottom: 20px;">
            <el-card :body-style="{ padding: '0px' }">
                <div style="height: 150px; overflow: hidden; position: relative;">
                     <el-image 
                        v-if="item.file_type === 'image'"
                        style="width: 100%; height: 100%; cursor: pointer;" 
                        :src="getFileUrl(item.input_path)" 
                        fit="cover"
                        @click="viewImageResult(item)"
                      />
                      <div v-else style="width: 100%; height: 100%; background: #333; display: flex; align-items: center; justify-content: center; color: white;">
                          <el-icon size="40"><VideoPlay /></el-icon>
                      </div>
                </div>
                <div style="padding: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ item.name }}</span>
                        <el-tag size="small">{{ item.file_type }}</el-tag>
                    </div>
                    <div style="margin-top: 10px; color: #999; font-size: 12px;">
                        <div>模型: {{ item.model_name }}</div>
                        <div>{{ new Date(item.created_at).toLocaleString() }}</div>
                    </div>
                    <div style="margin-top: 10px; display: flex; justify-content: space-between;">
                        <el-button type="text" @click="startEdit(item)">重命名</el-button>
                        <el-button type="text" style="color: red;" @click="deleteRecord(item.id)">删除</el-button>
                    </div>
                     <div v-if="item.isEditing" style="margin-top: 5px;">
                        <el-input v-model="item.editName" size="small" placeholder="新名称">
                            <template #append>
                                <el-button @click="saveEdit(item)">OK</el-button>
                            </template>
                        </el-input>
                    </div>
                </div>
            </el-card>
        </el-col>
    </el-row>

    <!-- Video Preview Dialog -->
    <el-dialog v-model="videoDialogVisible" title="视频结果预览" width="60%">
        <video v-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay style="width: 100%"></video>
    </el-dialog>
    
    <!-- Image Preview Dialog with Canvas -->
    <el-dialog v-model="imageDialogVisible" title="图片识别结果" width="60%" @opened="drawImageResult">
        <div style="position: relative; width: 100%; min-height: 400px; display: flex; justify-content: center;">
             <canvas ref="imageCanvas" style="max-width: 100%; border: 1px solid #ddd;"></canvas>
        </div>
        <div v-if="currentImageDetections && currentImageDetections.length > 0" style="margin-top: 10px;">
            <p>检测到 {{ currentImageDetections.length }} 个目标</p>
        </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Refresh, VideoPlay } from '@element-plus/icons-vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const history = ref([])
const loading = ref(false)
const viewMode = ref('list')

// Video
const videoDialogVisible = ref(false)
const currentVideoUrl = ref('')

// Image
const imageDialogVisible = ref(false)
const currentImageUrl = ref('')
const currentImageDetections = ref([])
const imageCanvas = ref(null)

const fetchHistory = async () => {
    loading.value = true
    try {
        const res = await api.getHistory()
        history.value = res.data.map(item => ({
            ...item,
            isEditing: false,
            editName: item.name
        }))
    } catch (error) {
        console.error(error)
        ElMessage.error('获取历史记录失败')
    } finally {
        loading.value = false
    }
}

const getFileUrl = (path) => {
    if (!path) return ''
    const filename = path.split(/[\\/]/).pop()
    return `http://localhost:8000/api/v1/history/file/${filename}`
}

const deleteRecord = (id) => {
    ElMessageBox.confirm('确定删除该记录吗?', '提示', { type: 'warning' }).then(async () => {
        try {
            await api.deleteHistory(id)
            ElMessage.success('删除成功')
            fetchHistory()
        } catch (error) {
            ElMessage.error('删除失败')
        }
    })
}

const startEdit = (item) => {
    item.isEditing = true
    item.editName = item.name
}

const saveEdit = async (item) => {
    try {
        await api.updateHistory(item.id, item.editName)
        item.name = item.editName
        item.isEditing = false
        ElMessage.success('更新成功')
    } catch (error) {
        ElMessage.error('更新失败')
    }
}

const viewVideoResult = (item) => {
    if (item.output_path) {
        currentVideoUrl.value = getFileUrl(item.output_path)
        videoDialogVisible.value = true
    }
}

const viewImageResult = (item) => {
    currentImageUrl.value = getFileUrl(item.input_path)
    try {
        if (!item.detections_summary) {
             currentImageDetections.value = []
        } else {
            const parsed = JSON.parse(item.detections_summary)
            // Ensure result is an array
            currentImageDetections.value = Array.isArray(parsed) ? parsed : []
        }
    } catch (e) {
        console.error("Error parsing detections:", e)
        currentImageDetections.value = []
    }
    imageDialogVisible.value = true
}

const drawImageResult = () => {
    nextTick(() => {
        const canvas = imageCanvas.value
        if (!canvas) return
        const ctx = canvas.getContext('2d')
        const img = new Image()
        img.onload = () => {
            canvas.width = img.width
            canvas.height = img.height
            ctx.drawImage(img, 0, 0)
            
            // Draw boxes
            currentImageDetections.value.forEach(det => {
                if (!det.bbox) return
                const [x1, y1, x2, y2] = det.bbox
                const label = `${det.class} ${(det.confidence * 100).toFixed(0)}%`
                
                ctx.strokeStyle = '#00FF00'
                ctx.lineWidth = 3
                ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
                
                ctx.fillStyle = '#00FF00'
                const textWidth = ctx.measureText(label).width
                ctx.fillRect(x1, y1 - 20, textWidth + 10, 20)
                
                ctx.fillStyle = '#000000'
                ctx.font = '14px Arial'
                ctx.fillText(label, x1 + 5, y1 - 5)
            })
        }
        img.src = currentImageUrl.value
    })
}

onMounted(fetchHistory)
</script>
