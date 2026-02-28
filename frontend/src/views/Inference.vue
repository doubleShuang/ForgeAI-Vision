<template>
  <div>
    <h2>媒体识别</h2>
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card>
          <template #header>上传与配置</template>
          <input type="file" @change="handleFileChange" accept="image/*,video/*" />
          
          <div style="margin-top: 20px;">
             <h4>1. 选择模型</h4>
             <el-select v-model="selectedModelId" placeholder="选择模型" style="width: 100%" @change="onModelChange">
                <el-option 
                  v-for="model in modelList" 
                  :key="model.id" 
                  :label="model.name" 
                  :value="model.id" 
                />
             </el-select>
          </div>

          <div style="margin-top: 20px;">
             <h4>2. 目标筛选 (可选)</h4>
             <div v-if="currentModelClasses && Object.keys(currentModelClasses).length > 0">
                 <el-checkbox-group v-model="selectedClasses">
                    <el-checkbox v-for="(name, id) in currentModelClasses" :key="id" :label="id">{{ name }}</el-checkbox>
                 </el-checkbox-group>
             </div>
             <div v-else style="color: #999; font-size: 12px;">
                 当前模型未配置筛选清单，默认检测所有目标。
             </div>
          </div>

          <div style="margin-top: 20px;">
             <el-button type="primary" @click="startInference" :disabled="!file || isProcessing" :loading="isProcessing" style="width: 100%">
               {{ isProcessing ? '处理中...' : '开始识别' }}
             </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
            <template #header>识别结果</template>
            <div class="result-container" style="position: relative;">
                
                <!-- Image Mode -->
                <template v-if="fileType === 'image'">
                    <canvas ref="resultCanvas" style="max-width: 100%; border: 1px solid #ddd;"></canvas>
                    <div v-if="detections.length > 0" style="margin-top: 10px;">
                        <h4>检测详情 ({{ detections.length }}):</h4>
                        <div style="max-height: 200px; overflow-y: auto;">
                            <div v-for="(det, idx) in detections" :key="idx">
                                <el-tag size="small">{{ det.class }}</el-tag> 
                                置信度: {{ (det.confidence * 100).toFixed(1) }}%
                            </div>
                        </div>
                    </div>
                </template>

                <!-- Video Mode -->
                <template v-if="fileType === 'video'">
                    <video 
                        v-if="videoUrl" 
                        controls 
                        autoplay
                        style="width: 100%; max-height: 500px; background: #000;"
                        :src="videoUrl"
                    >
                        您的浏览器不支持 Video 标签。
                    </video>
                    <div v-else-if="isProcessing" style="text-align: center; padding: 50px;">
                        <el-icon class="is-loading" size="50"><Loading /></el-icon>
                        <p>视频正在处理中，请稍候...</p>
                    </div>
                    <div v-else style="text-align: center; padding: 50px; color: #999;">
                        请上传视频并点击开始识别
                    </div>
                </template>

            </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import api from '../api'

const file = ref(null)
const selectedModelId = ref(null) // Use ID for selection to handle duplicate paths
const detections = ref([])
const modelList = ref([])
const resultCanvas = ref(null)
const originalImage = ref(null)
const isProcessing = ref(false)
const videoUrl = ref(null)

// Computed file type
const fileType = computed(() => {
    if (!file.value) return 'image'
    return file.value.type.startsWith('video') ? 'video' : 'image'
})

// Dynamic classes
const currentModelClasses = ref({})
const selectedClasses = ref([])

const fetchModels = async () => {
  try {
    const res = await api.getModels()
    modelList.value = res.data
    if (modelList.value.length > 0) {
      // Select first one by default
      const firstModel = modelList.value[0]
      selectedModelId.value = firstModel.id
      updateCurrentClasses(firstModel)
    }
  } catch (error) {
    console.error("Failed to fetch models:", error)
    // Fallback
    modelList.value = [{id: 0, name: 'YOLOv8n (Default)', file_path: 'yolov8n.pt'}]
    selectedModelId.value = 0
  }
}

const onModelChange = (id) => {
    const model = modelList.value.find(m => m.id === id)
    if (model) {
        updateCurrentClasses(model)
    }
}

const updateCurrentClasses = (model) => {
    if (model.classes) {
        currentModelClasses.value = model.classes
    } else {
        currentModelClasses.value = {}
    }
    selectedClasses.value = [] // Reset selection when model changes
}

const handleFileChange = (e) => {
    file.value = e.target.files[0]
    detections.value = []
    videoUrl.value = null
    isProcessing.value = false
    
    if (file.value && fileType.value === 'image') {
        const reader = new FileReader()
        reader.onload = (event) => {
            const img = new Image()
            img.onload = () => {
                originalImage.value = img
                // Wait for DOM update
                setTimeout(() => drawCanvas(img, []), 100)
            }
            img.src = event.target.result
        }
        reader.readAsDataURL(file.value)
    }
}

const drawCanvas = (img, boxes) => {
    if (!resultCanvas.value) return
    const canvas = resultCanvas.value
    const ctx = canvas.getContext('2d')
    
    canvas.width = img.width
    canvas.height = img.height
    ctx.drawImage(img, 0, 0)
    
    boxes.forEach(det => {
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

const startInference = async () => {
    if (!file.value || selectedModelId.value === null) return
    isProcessing.value = true
    
    const model = modelList.value.find(m => m.id === selectedModelId.value)
    if (!model) {
        alert("请选择有效的模型")
        isProcessing.value = false
        return
    }

    const formData = new FormData()
    formData.append('model_path', model.file_path || model.name)
    formData.append('file', file.value)
    
    if (selectedClasses.value.length > 0) {
        const classIds = selectedClasses.value.map(Number)
        formData.append('classes', JSON.stringify(classIds))
    }
    
    try {
        if (fileType.value === 'image') {
            const res = await api.predictImage(formData)
            detections.value = res.data.data
            if (originalImage.value) {
                drawCanvas(originalImage.value, detections.value)
            }
        } else {
            // Video
            const res = await api.predictVideo(formData)
            videoUrl.value = `http://localhost:8000${res.data.data.video_url}`
        }
    } catch (error) {
        console.error(error)
        alert("识别失败: " + (error.response?.data?.message || error.message))
    } finally {
        isProcessing.value = false
    }
}

onMounted(fetchModels)
</script>

<style scoped>
.result-container {
    width: 100%;
    min-height: 300px;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background: #f5f7fa;
}
</style>
