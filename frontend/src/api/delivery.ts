import { apiClient } from './client'

export type BatchStatus = 'pending' | 'dispatched' | 'completed' | 'cancelled'
export type DeliveryStatus = 'pending' | 'in_transit' | 'delivered' | 'failed'

export interface DeliveryOrderItem {
  id: number
  order_id: number
  batch_id?: number
  delivery_address: string
  status: DeliveryStatus
  delivery_notes?: string
  delivered_at?: string
}

export interface DeliveryBatch {
  id: number
  batch_number: string
  driver_name?: string
  driver_phone?: string
  status: BatchStatus
  notes?: string
  scheduled_at?: string
  dispatched_at?: string
  completed_at?: string
  created_at: string
  delivery_orders: DeliveryOrderItem[]
}

export interface DeliveryBatchCreate {
  driver_name?: string
  driver_phone?: string
  notes?: string
  scheduled_at?: string
  order_ids?: number[]
}

export const deliveryApi = {
  listBatches: (skip = 0, limit = 50) =>
    apiClient.get<DeliveryBatch[]>('/delivery/batches', { params: { skip, limit } }).then((r) => r.data),

  createBatch: (data: DeliveryBatchCreate) =>
    apiClient.post<DeliveryBatch>('/delivery/batches', data).then((r) => r.data),

  getBatch: (id: number) =>
    apiClient.get<DeliveryBatch>(`/delivery/batches/${id}`).then((r) => r.data),

  updateBatch: (id: number, data: Partial<DeliveryBatchCreate & { status: BatchStatus }>) =>
    apiClient.patch<DeliveryBatch>(`/delivery/batches/${id}`, data).then((r) => r.data),

  assignOrders: (batchId: number, order_ids: number[]) =>
    apiClient.post<DeliveryBatch>(`/delivery/batches/${batchId}/assign`, { order_ids }).then((r) => r.data),

  suggestBatches: (max_per_batch = 10) =>
    apiClient.get<number[][]>('/delivery/batches/suggest', { params: { max_per_batch } }).then((r) => r.data),

  getUnassigned: () =>
    apiClient.get<DeliveryOrderItem[]>('/delivery/orders/unassigned').then((r) => r.data),
}
