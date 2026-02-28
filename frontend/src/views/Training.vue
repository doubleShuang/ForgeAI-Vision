<template>
  <div class="training-container">
    <el-row :gutter="20">
      <!-- Create Task -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>创建新训练任务</span>
            </div>
          </template>
          <el-form :model="form" label-width="120px">
            <el-form-item label="任务名称">
              <el-input v-model="form.model_name" placeholder="请输入任务名称" />
            </el-form-item>
            <el-form-item label="基础模型">
              <el-select v-model="form.base_model" placeholder="选择基础模型" style="width: 100%">
                 <el-option-group label="标准模型">
                    <el-option label="YOLOv8n (Nano)" value="yolov8n.pt" />
                    <el-option label="YOLOv8s (Small)" value="yolov8s.pt" />
                    <el-option label="YOLOv8m (Medium)" value="yolov8m.pt" />
                    <el-option label="YOLOv8l (Large)" value="yolov8l.pt" />
                    <el-option label="YOLOv8x (XLarge)" value="yolov8x.pt" />
                 </el-option-group>
                 <el-option-group label="自定义模型" v-if="customModels.length > 0">
                    <el-option v-for="m in customModels" :key="m.id" :label="m.name" :value="m.file_path" />
                 </el-option-group>
              </el-select>
              <div class="form-tip">选择用于初始化的预训练模型或自定义模型</div>
            </el-form-item>
            <el-form-item label="关联工程">
               <el-select v-model="form.project_id" placeholder="选择标注工程" style="width: 100%">
                  <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
               </el-select>
            </el-form-item>
            <el-form-item label="迭代次数">
              <el-input-number v-model="form.epochs" :min="1" :max="300" />
            </el-form-item>
            <el-form-item label="批次大小">
              <el-input-number v-model="form.batch_size" :min="1" :max="64" />
            </el-form-item>
            
            <el-divider content-position="left">高级设置</el-divider>
            
            <el-form-item label="训练设备">
              <el-select v-model="form.device" placeholder="选择设备">
                <el-option label="CPU" value="cpu" />
                <el-option label="GPU (0)" value="0" />
              </el-select>
              <div class="form-tip">指定训练使用的硬件设备。如果您的电脑只有一张显卡，请选择 GPU (0)。</div>
            </el-form-item>

            <el-form-item label="图片尺寸">
              <el-input-number v-model="form.imgsz" :step="32" :min="32" />
              <div class="form-tip">输入图片尺寸 (像素)，需为32的倍数，默认640。</div>
            </el-form-item>

            <el-form-item label="优化器">
              <el-select v-model="form.optimizer" placeholder="选择优化器">
                <el-option label="Auto" value="auto" />
                <el-option label="SGD" value="SGD" />
                <el-option label="Adam" value="Adam" />
                <el-option label="AdamW" value="AdamW" />
              </el-select>
              <div class="form-tip">选择模型训练的优化算法。</div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="startTraining" :loading="starting" style="width: 100%">启动训练</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Training History -->
      <el-col :span="14">
        <el-card>
            <template #header>
                <div class="flex justify-between items-center">
                    <span>训练历史记录</span>
                    <el-button size="small" @click="fetchHistory">刷新</el-button>
                </div>
            </template>
            <el-table :data="history" style="width: 100%" height="400">
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="model_name" label="任务名称" />
                <el-table-column prop="status" label="状态" width="100">
                    <template #default="scope">
                        <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="进度" width="150">
                    <template #default="scope">
                        <el-progress 
                            :percentage="scope.row.epochs > 0 ? Math.min(100, Math.floor((scope.row.current_epoch / scope.row.epochs) * 100)) : 0" 
                            :status="scope.row.status === 'failed' ? 'exception' : (scope.row.status === 'completed' ? 'success' : '')"
                        />
                    </template>
                </el-table-column>
                <el-table-column prop="accuracy" label="mAP" width="80">
                    <template #default="scope">
                        {{ (scope.row.accuracy * 100).toFixed(1) }}%
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="150">
                    <template #default="scope">
                        <el-button size="small" @click="viewDetails(scope.row)">详情</el-button>
                        <el-button size="small" type="danger" @click="deleteTask(scope.row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- Training Details Dialog -->
    <el-dialog v-model="detailsVisible" title="训练任务详情" width="60%">
        <div v-if="currentTask">
            <el-descriptions border>
                <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
                <el-descriptions-item label="名称">{{ currentTask.model_name }}</el-descriptions-item>
                <el-descriptions-item label="状态">{{ currentTask.status }}</el-descriptions-item>
                <el-descriptions-item label="进度">{{ currentTask.current_epoch }} / {{ currentTask.epochs }}</el-descriptions-item>
                <el-descriptions-item label="结果路径" :span="2">{{ currentTask.result_path || '-' }}</el-descriptions-item>
                <el-descriptions-item label="基础模型" :span="2">{{ currentTask.config && currentTask.config.base_model ? currentTask.config.base_model : 'yolov8n.pt' }}</el-descriptions-item>
                
                <el-descriptions-item label="设备">{{ currentTask.config ? currentTask.config.device : '-' }}</el-descriptions-item>
                <el-descriptions-item label="图片尺寸">{{ currentTask.config ? currentTask.config.imgsz : '-' }}</el-descriptions-item>
                <el-descriptions-item label="优化器">{{ currentTask.config ? currentTask.config.optimizer : '-' }}</el-descriptions-item>
            </el-descriptions>
            
            <div style="margin-top: 20px;">
                <h4>训练日志</h4>
                <div class="log-container">
                    <div v-for="(line, i) in (currentTask.log ? currentTask.log.split('\n') : [])" :key="i">{{ line }}</div>
                </div>
            </div>
        </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const projects = ref([])
const customModels = ref([])
const history = ref([])
const starting = ref(false)
const detailsVisible = ref(false)
const currentTask = ref(null)
let pollTimer = null

const form = ref({
  model_name: '',
  project_id: null,
  epochs: 10,
  batch_size: 16,
  device: 'cpu',
  imgsz: 640,
  optimizer: 'auto',
  base_model: 'yolov8n.pt'
})

const fetchCustomModels = async () => {
  try {
    const res = await api.getModels()
    customModels.value = res.data
  } catch (e) {}
}

const fetchProjects = async () => {
    try {
        const res = await api.getProjects()
        projects.value = res.data
    } catch (e) {}
}

const fetchHistory = async () => {
    try {
        const res = await api.getTrainingHistory()
        history.value = res.data.data // Assuming backend structure
    } catch (e) {}
}

const startTraining = async () => {
    if (!form.value.project_id) return ElMessage.warning("请选择关联工程")
    starting.value = true
    try {
        const data = {
            model_name: form.value.model_name,
            project_id: form.value.project_id,
            epochs: form.value.epochs,
            batch_size: form.value.batch_size,
            device: form.value.device,
            imgsz: form.value.imgsz,
            optimizer: form.value.optimizer,
            base_model: form.value.base_model
        }
        
        await api.startTraining(data)
        ElMessage.success("任务已提交")
        fetchHistory()
    } catch (e) {
        ElMessage.error("启动失败")
    } finally {
        starting.value = false
    }
}

const getStatusType = (status) => {
    const map = {
        'pending': 'info',
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger'
    }
    return map[status] || 'info'
}

const viewDetails = (task) => {
    currentTask.value = task
    detailsVisible.value = true
    // Start polling for this task details if running
    if (task.status === 'running') {
        startPolling(task.id)
    }
}

const startPolling = (taskId) => {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = setInterval(async () => {
        if (!detailsVisible.value) {
            clearInterval(pollTimer)
            return
        }
        try {
            const res = await api.getTrainingStatus(taskId)
            // Update currentTask view
            const statusData = res.data
            // We need to merge status data with currentTask structure
            if (currentTask.value && currentTask.value.id === taskId) {
                currentTask.value.status = statusData.status
                currentTask.value.log = statusData.log.join('\n')
                currentTask.value.result_path = statusData.result_path
                currentTask.value.current_epoch = Math.floor((statusData.progress / 100) * currentTask.value.epochs)
                // Merge config from backend if available (since list API might not return it fully)
                if (statusData.config) {
                     currentTask.value.config = statusData.config
                }
                
                // Scroll to bottom
                const logContainer = document.querySelector('.log-container')
                if (logContainer) logContainer.scrollTop = logContainer.scrollHeight

                if (statusData.status !== 'running' && statusData.status !== 'starting' && statusData.status !== 'pending') {
                    clearInterval(pollTimer)
                    fetchHistory() // Refresh list
                }
            }
        } catch (e) {}
    }, 1000)
}

const deleteTask = (task) => {
    ElMessageBox.confirm('确定删除该记录吗？', '提示', { type: 'warning' })
    .then(async () => {
        await api.deleteTrainingTask(task.id)
        fetchHistory()
    })
}

onMounted(() => {
    fetchProjects()
    fetchHistory()
    fetchCustomModels()
})

onUnmounted(() => {
    if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.log-container {
    background: #1e1e1e;
    color: #fff;
    padding: 10px;
    height: 300px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 12px;
    border-radius: 4px;
}
</style>
