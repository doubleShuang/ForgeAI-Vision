import request from '@/utils/request'

export default {
  // Models
  getModels() { return request.get('/models/') },
  uploadModel(formData) { return request.post('/models/', formData) },
  
  // Inference
  predictImage(formData) { return request.post('/predict/image', formData) },
  predictVideo(formData) { return request.post('/predict/video', formData) },
  getHistory() { return request.get('/history/') },
  deleteHistory(id) { return request.delete(`/history/${id}`) },
  updateHistory(id, name) { return request.put(`/history/${id}`, { name }) },
 
  // Training
  startTraining(data) { return request.post('/train/', data) },
  getTrainingStatus(taskId) { return request.get(`/train/status/${taskId}`) },
  getTrainingHistory(skip = 0, limit = 20) { return request.get(`/train/history?skip=${skip}&limit=${limit}`) },
  deleteTrainingTask(taskId) { return request.delete(`/train/${taskId}`) },
 
  // Projects
  createProject(data) { return request.post('/projects/', data) },
  getProjects(skip = 0, limit = 100) { return request.get(`/projects/?skip=${skip}&limit=${limit}`) },
  getProject(id) { return request.get(`/projects/${id}`) },
  deleteProject(id) { return request.delete(`/projects/${id}`) },
  uploadProjectImages(id, formData) { return request.post(`/projects/${id}/images`, formData) },
  uploadVocDataset(id, formData) { return request.post(`/projects/${id}/voc`, formData) },
  getProjectImages(id, skip = 0, limit = 50) { return request.get(`/projects/${id}/images?skip=${skip}&limit=${limit}`) },
  getAnnotation(id, imageName) { return request.get(`/projects/${id}/annotations?image_name=${imageName}`) },
  saveAnnotation(id, data) { return request.post(`/projects/${id}/annotations`, data) },
  getClasses(id) { return request.get(`/projects/${id}/classes`) },
  saveClasses(id, data) { return request.post(`/projects/${id}/classes`, data) }
}
