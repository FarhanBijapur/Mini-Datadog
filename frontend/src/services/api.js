import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  timeout: 5000,
})

export const fetchMetrics = async () => {
  const response = await api.get('/metrics')
  return response.data
}

export const fetchLogs = async () => {
  const response = await api.get('/logs')
  return response.data
}

export const sendLog = async (payload) => {
  const response = await api.post('/logs', payload)
  return response.data
}
