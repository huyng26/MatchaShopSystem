import { apiClient } from './client'

export interface Customer {
  id: number
  name: string
  phone?: string
  address?: string
  notes?: string
  created_at: string
}

export interface CustomerCreate {
  name: string
  phone?: string
  address?: string
  notes?: string
}

export const customersApi = {
  list: (skip = 0, limit = 100) =>
    apiClient.get<Customer[]>('/customers', { params: { skip, limit } }).then((r) => r.data),

  create: (data: CustomerCreate) =>
    apiClient.post<Customer>('/customers', data).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Customer>(`/customers/${id}`).then((r) => r.data),

  update: (id: number, data: Partial<CustomerCreate>) =>
    apiClient.patch<Customer>(`/customers/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/customers/${id}`),
}
