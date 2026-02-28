<template>
  <div class="annotation-page">
    <div class="header">
      <el-page-header @back="goBack" v-if="projectId">
        <template #content>
          <span class="text-large font-600 mr-3"> 在线标注: {{ project.name }} </span>
        </template>
        <template #extra>
            <el-select v-model="currentClass" placeholder="选择类别" style="width: 150px; margin-right: 10px;">
                <el-option v-for="(cls, idx) in classes" :key="idx" :label="cls" :value="idx" />
            </el-select>
            <el-button type="primary" @click="saveAnnotation">保存标注</el-button>
        </template>
      </el-page-header>
      <h2 v-else>在线标注 (演示模式)</h2>
    </div>

    <el-container style="height: calc(100vh - 100px); border: 1px solid #eee;">
      <el-aside width="200px" style="border-right: 1px solid #eee; padding: 10px;">
        <div v-if="projectId">
            <h4>图片列表</h4>
            <div class="image-list">
                <div 
                    v-for="img in images" 
                    :key="img" 
                    class="image-item" 
                    :class="{ active: currentImageName === img }"
                    @click="selectImage(img)"
                >
                    {{ img }}
                </div>
            </div>
        </div>
        <div v-else>
            <input type="file" @change="loadLocalImage" accept="image/*" />
        </div>
      </el-aside>
      
      <el-main style="padding: 0; display: flex; justify-content: center; align-items: center; background: #f0f0f0; overflow: hidden;">
        <div class="canvas-wrapper" ref="canvasWrapper">
            <canvas ref="canvas" 
                @mousedown="startDrawing" 
                @mousemove="draw" 
                @mouseup="endDrawing"
            ></canvas>
        </div>
      </el-main>
      
      <el-aside width="250px" style="border-left: 1px solid #eee; padding: 10px;">
          <h4>标注信息</h4>
          <div v-for="(box, idx) in boxes" :key="idx" class="box-item">
              <span>{{ classes[box.cls] || 'Unknown' }}</span>
              <div class="actions">
                  <el-button size="small" type="text" @click="editBoxClass(idx)">修改</el-button>
                  <el-button size="small" type="text" style="color: red;" @click="deleteBox(idx)">删除</el-button>
              </div>
              <div style="font-size: 12px; color: #666; width: 100%;">
                  {{ box.w.toFixed(0) }}x{{ box.h.toFixed(0) }}
              </div>
          </div>
      </el-aside>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectId = route.query.projectId
const project = ref({})
const images = ref([])
const classes = ref([])
const currentImageName = ref('')
const currentImageObj = ref(null)
const currentClass = ref(0)

const canvas = ref(null)
const ctx = ref(null)
const isDrawing = ref(false)
const startX = ref(0)
const startY = ref(0)
const boxes = ref([]) 

onMounted(async () => {
    ctx.value = canvas.value.getContext('2d')
    if (projectId) {
        await fetchProjectData()
    }
})

const fetchProjectData = async () => {
    try {
        const pRes = await api.getProject(projectId)
        project.value = pRes.data
        const iRes = await api.getProjectImages(projectId)
        images.value = iRes.data
        const cRes = await api.getClasses(projectId)
        classes.value = cRes.data
        
        if (images.value.length > 0) {
            selectImage(images.value[0])
        }
    } catch (e) {
        ElMessage.error("加载工程数据失败")
    }
}

const selectImage = async (imgName) => {
    // 1. Set target and clear current state to avoid mismatch during load
    currentImageName.value = imgName
    boxes.value = []
    currentImageObj.value = null // Hide old image while loading new one
    
    const url = `http://localhost:8000/workspaces/${project.value.name}/images/${imgName}`
    
    try {
        // 2. Load Image and Annotation in parallel
        const imagePromise = new Promise((resolve, reject) => {
            const img = new Image()
            img.crossOrigin = "Anonymous"
            img.onload = () => resolve(img)
            img.onerror = reject
            img.src = url
        })
        
        const annotationPromise = api.getAnnotation(projectId, imgName)
            .then(res => res.data.content)
            .catch(() => "") // Treat error (404) as empty annotation
            
        const [img, content] = await Promise.all([imagePromise, annotationPromise])
        
        // 3. Race condition check: Ensure the loaded data matches the currently selected image
        if (currentImageName.value !== imgName) return
        
        // 4. Update State and Render
        currentImageObj.value = img
        resizeCanvas(img.width, img.height)
        parseAnnotations(content, img)
        redraw()
        
    } catch (e) {
        ElMessage.error("加载失败")
    }
}

const parseAnnotations = (content, img) => {
    if (!content || !img) {
        boxes.value = []
        return
    }
    
    const lines = content.split('\n')
    const imgW = img.width
    const imgH = img.height
    
    boxes.value = lines.filter(l => l.trim()).map(line => {
        const parts = line.trim().split(' ')
        const cls = parseInt(parts[0])
        const cx = float(parts[1])
        const cy = float(parts[2])
        const nw = float(parts[3])
        const nh = float(parts[4])
        
        const w = nw * imgW
        const h = nh * imgH
        const x = (cx * imgW) - (w / 2)
        const y = (cy * imgH) - (h / 2)
        
        return { x, y, w, h, cls }
    })
}

const float = (v) => parseFloat(v)

const loadLocalImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
        const img = new Image()
        img.onload = () => {
            currentImageObj.value = img
            resizeCanvas(img.width, img.height)
            redraw()
            boxes.value = []
        }
        img.src = event.target.result
    }
    reader.readAsDataURL(file)
}

const resizeCanvas = (w, h) => {
    if (canvas.value) {
        canvas.value.width = w
        canvas.value.height = h
    }
}

const startDrawing = (e) => {
    if (!currentImageObj.value) return
    isDrawing.value = true
    startX.value = e.offsetX
    startY.value = e.offsetY
}

const draw = (e) => {
    if (!isDrawing.value) return
    const x = e.offsetX
    const y = e.offsetY
    
    redraw()
    
    // Draw crosshair or current box
    ctx.value.strokeStyle = '#00FF00'
    ctx.value.lineWidth = 2
    ctx.value.strokeRect(startX.value, startY.value, x - startX.value, y - startY.value)
}

const endDrawing = (e) => {
    if (!isDrawing.value) return
    isDrawing.value = false
    const x = e.offsetX
    const y = e.offsetY
    
    const w = x - startX.value
    const h = y - startY.value
    
    if (Math.abs(w) > 5 && Math.abs(h) > 5) {
        boxes.value.push({
            x: w > 0 ? startX.value : x,
            y: h > 0 ? startY.value : y,
            w: Math.abs(w),
            h: Math.abs(h),
            cls: currentClass.value
        })
    }
    redraw()
}

const redraw = () => {
    if (!ctx.value) return
    ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height)
    if (currentImageObj.value) {
        ctx.value.drawImage(currentImageObj.value, 0, 0)
    }
    
    boxes.value.forEach(box => {
        // Color based on class? For now just Green
        ctx.value.strokeStyle = '#00FF00'
        ctx.value.lineWidth = 2
        ctx.value.strokeRect(box.x, box.y, box.w, box.h)
        
        // Draw label
        ctx.value.fillStyle = '#00FF00'
        ctx.value.font = '12px Arial'
        const label = classes.value[box.cls] || box.cls
        ctx.value.fillText(label, box.x, box.y - 5)
    })
}

const deleteBox = (idx) => {
    boxes.value.splice(idx, 1)
    redraw()
}

const editBoxClass = (idx) => {
    // Simple toggle or prompt? Let's just set to current selected class
    boxes.value[idx].cls = currentClass.value
    redraw()
    ElMessage.success("类别已修改为当前选中类别")
}

const saveAnnotation = async () => {
    if (!projectId || !currentImageName.value) return
    
    const imgW = currentImageObj.value.width
    const imgH = currentImageObj.value.height
    
    const yoloLines = boxes.value.map(box => {
        const cx = (box.x + box.w / 2) / imgW
        const cy = (box.y + box.h / 2) / imgH
        const nw = box.w / imgW
        const nh = box.h / imgH
        return `${box.cls} ${cx.toFixed(6)} ${cy.toFixed(6)} ${nw.toFixed(6)} ${nh.toFixed(6)}`
    })
    
    const content = yoloLines.join('\n')
    
    try {
        const data = {
            image_name: currentImageName.value,
            content: content
        }
        
        await api.saveAnnotation(projectId, data)
        ElMessage.success("保存成功")
    } catch (e) {
        ElMessage.error("保存失败")
    }
}

const goBack = () => {
    if (projectId) {
        router.push(`/projects/${projectId}`)
    } else {
        router.push('/projects')
    }
}
</script>

<style scoped>
.header {
    margin-bottom: 10px;
    padding: 10px;
    border-bottom: 1px solid #eee;
}
.image-list {
    height: calc(100vh - 200px);
    overflow-y: auto;
}
.image-item {
    padding: 8px;
    cursor: pointer;
    border-bottom: 1px solid #f5f5f5;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.image-item:hover {
    background-color: #f0f9eb;
}
.image-item.active {
    background-color: #e1f3d8;
    color: #67c23a;
}
.box-item {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid #f5f5f5;
}
.canvas-wrapper {
    max-width: 100%;
    max-height: 100%;
    overflow: auto;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
</style>
