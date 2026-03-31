import { apiClient } from './client'

export interface Ingredient {
  id: number
  name: string
  unit: string
  cost_per_unit: string
  current_stock: string
  min_stock_threshold: string
  created_at: string
  updated_at: string
}

export interface IngredientCreate {
  name: string
  unit: string
  cost_per_unit: number
  current_stock?: number
  min_stock_threshold?: number
}

export interface IngredientPurchase {
  id: number
  ingredient_id: number
  quantity: string
  unit_cost: string
  total_cost: string
  supplier?: string
  notes?: string
  purchased_at: string
}

export interface IngredientPurchaseCreate {
  ingredient_id: number
  quantity: number
  unit_cost: number
  supplier?: string
  notes?: string
}

export const inventoryApi = {
  listIngredients: (skip = 0, limit = 100) =>
    apiClient.get<Ingredient[]>('/inventory/ingredients', { params: { skip, limit } }).then((r) => r.data),

  createIngredient: (data: IngredientCreate) =>
    apiClient.post<Ingredient>('/inventory/ingredients', data).then((r) => r.data),

  getIngredient: (id: number) =>
    apiClient.get<Ingredient>(`/inventory/ingredients/${id}`).then((r) => r.data),

  updateIngredient: (id: number, data: Partial<IngredientCreate>) =>
    apiClient.patch<Ingredient>(`/inventory/ingredients/${id}`, data).then((r) => r.data),

  deleteIngredient: (id: number) =>
    apiClient.delete(`/inventory/ingredients/${id}`),

  getLowStock: () =>
    apiClient.get<Ingredient[]>('/inventory/ingredients/low-stock').then((r) => r.data),

  listPurchases: (ingredient_id?: number, skip = 0, limit = 100) =>
    apiClient.get<IngredientPurchase[]>('/inventory/purchases', { params: { ingredient_id, skip, limit } }).then((r) => r.data),

  createPurchase: (data: IngredientPurchaseCreate) =>
    apiClient.post<IngredientPurchase>('/inventory/purchases', data).then((r) => r.data),
}
