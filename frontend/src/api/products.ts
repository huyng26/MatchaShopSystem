import { apiClient } from './client'

export interface ProductIngredient {
  id: number
  ingredient_id: number
  quantity_required: string
}

export interface Product {
  id: number
  name: string
  category: string
  description?: string
  selling_price: string
  is_available: boolean
  ingredients: ProductIngredient[]
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  name: string
  category: string
  description?: string
  selling_price: number
  is_available?: boolean
  ingredients?: { ingredient_id: number; quantity_required: number }[]
}

export const productsApi = {
  list: (skip = 0, limit = 100) =>
    apiClient.get<Product[]>('/products', { params: { skip, limit } }).then((r) => r.data),

  create: (data: ProductCreate) =>
    apiClient.post<Product>('/products', data).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Product>(`/products/${id}`).then((r) => r.data),

  update: (id: number, data: Partial<ProductCreate>) =>
    apiClient.patch<Product>(`/products/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/products/${id}`),
}
