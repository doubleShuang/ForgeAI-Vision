import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1', // Backend API
  // headers: {
  //   'Content-Type': 'application/json',
  // },
})

export default {
  // Models
  getModels() { return apiClient.get('/models/') },
  uploadModel(formData) { return apiClient.post('/models/', formData) },
  
  // Inference
  predictImage(formData) { return apiClient.post('/predict/image', formData) },
  predictVideo(formData) { return apiClient.post('/predict/video', formData) },
  getHistory() { return apiClient.get('/history/') },
  deleteHistory(id) { return apiClient.delete(`/history/${id}`) },
  updateHistory(id, name) { return apiClient.put(`/history/${id}`, { name }) },

  // Training
  startTraining(data) { return apiClient.post('/train/', data) },
  getTrainingStatus(taskId) { return apiClient.get(`/train/status/${taskId}`) },
  getTrainingHistory(skip = 0, limit = 20) { return apiClient.get(`/train/history?skip=${skip}&limit=${limit}`) },
  deleteTrainingTask(taskId) { return apiClient.delete(`/train/${taskId}`) },

  // Projects
  createProject(data) { return apiClient.post('/projects/', data) },
  getProjects(skip = 0, limit = 100) { return apiClient.get(`/projects/?skip=${skip}&limit=${limit}`) },
  getProject(id) { return apiClient.get(`/projects/${id}`) },
  deleteProject(id) { return apiClient.delete(`/projects/${id}`) },
  uploadProjectImages(id, formData) { return apiClient.post(`/projects/${id}/images`, formData) },
  uploadVocDataset(id, formData) { return apiClient.post(`/projects/${id}/voc`, formData) },
  getProjectImages(id, skip = 0, limit = 50) { return apiClient.get(`/projects/${id}/images?skip=${skip}&limit=${limit}`) },
  getAnnotation(id, imageName) { return apiClient.get(`/projects/${id}/annotations?image_name=${imageName}`) },
  saveAnnotation(id, data) { return apiClient.post(`/projects/${id}/annotations`, data) },
  getClasses(id) { return apiClient.get(`/projects/${id}/classes`) },
  saveClasses(id, data) { return apiClient.post(`/projects/${id}/classes`, data) }
}
