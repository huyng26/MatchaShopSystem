import { apiClient } from './client'

export type OrderType = 'counter' | 'delivery'
export type OrderStatus = 'pending' | 'confirmed' | 'preparing' | 'ready' | 'completed' | 'cancelled'
export type PaymentMethod = 'cash' | 'card' | 'transfer'

export interface OrderItem {
  id: number
  product_id: number
  quantity: number
  unit_price: string
  subtotal: string
}

export interface Payment {
  id: number
  order_id: number
  method: PaymentMethod
  amount: string
  reference?: string
  paid_at: string
}

export interface Order {
  id: number
  order_type: OrderType
  status: OrderStatus
  customer_id?: number
  notes?: string
  total_amount: string
  items: OrderItem[]
  payment?: Payment
  created_at: string
  updated_at: string
}

export interface OrderCreate {
  order_type: OrderType
  customer_id?: number
  notes?: string
  items: { product_id: number; quantity: number }[]
  delivery_address?: string
}

export interface PaymentCreate {
  method: PaymentMethod
  amount: number
  reference?: string
}

export const posApi = {
  listOrders: (params?: { skip?: number; limit?: number; status?: OrderStatus }) =>
    apiClient.get<Order[]>('/pos/orders', { params }).then((r) => r.data),

  createOrder: (data: OrderCreate) =>
    apiClient.post<Order>('/pos/orders', data).then((r) => r.data),

  getOrder: (id: number) =>
    apiClient.get<Order>(`/pos/orders/${id}`).then((r) => r.data),

  updateStatus: (id: number, status: OrderStatus) =>
    apiClient.patch<Order>(`/pos/orders/${id}/status`, { status }).then((r) => r.data),

  recordPayment: (orderId: number, data: PaymentCreate) =>
    apiClient.post<Payment>(`/pos/orders/${orderId}/payment`, data).then((r) => r.data),
}
