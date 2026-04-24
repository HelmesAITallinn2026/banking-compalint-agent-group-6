import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
})

export const getCustomer = (id) =>
  api.get(`/api/customers/${id}`).then((r) => r.data)

export const getCustomerAccounts = (id) =>
  api.get(`/api/customers/${id}/accounts`).then((r) => r.data)

export const getRefusalReasons = () =>
  api.get('/api/refusal-reasons').then((r) => r.data)

export const createComplaint = (formData) =>
  api
    .post('/api/complaints', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)

export const getComplaints = (status) =>
  api
    .get('/api/complaints', { params: status ? { status } : {} })
    .then((r) => r.data)

export const getComplaint = (id) =>
  api.get(`/api/complaints/${id}`).then((r) => r.data)

export const getComplaintAttachments = (complaintId) =>
  api.get(`/api/complaints/${complaintId}/attachments`).then((r) => r.data)

export const getAttachmentFileUrl = (attachmentId) =>
  `${api.defaults.baseURL}/api/attachments/${attachmentId}/file`

export const approveComplaint = (id) =>
  api.post(`/api/complaints/${id}/approve`).then((r) => r.data)
