import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getResult(resultId) {
  const { data } = await api.get(`/result/${resultId}`)
  return data
}

export async function downloadPL(resultId) {
  const response = await api.get(`/download-pl/${resultId}`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  const disposition = response.headers['content-disposition']
  const filename = disposition
    ? disposition.split('filename=')[1]?.replace(/"/g, '')
    : 'PL.xlsx'
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function loadContainer(resultId, containerType) {
  const { data } = await api.post(`/container-load/${resultId}`, {
    container_type: containerType,
  })
  return data
}
