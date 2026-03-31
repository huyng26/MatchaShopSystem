import { apiClient } from './client'

export type CostCategory = 'electricity' | 'water' | 'staff' | 'rent' | 'other'

export interface OperationalCost {
  id: number
  category: CostCategory
  amount: string
  period_month: number
  period_year: number
  description?: string
  notes?: string
  recorded_at: string
  updated_at: string
}

export interface OperationalCostCreate {
  category: CostCategory
  amount: number
  period_month: number
  period_year: number
  description?: string
  notes?: string
}

export interface ProfitSummary {
  period_month: number
  period_year: number
  revenue: string
  cogs: string
  operational_costs: string
  net_profit: string
  order_count: number
}

export const financeApi = {
  listCosts: (params?: { month?: number; year?: number; skip?: number; limit?: number }) =>
    apiClient.get<OperationalCost[]>('/finance/costs', { params }).then((r) => r.data),

  createCost: (data: OperationalCostCreate) =>
    apiClient.post<OperationalCost>('/finance/costs', data).then((r) => r.data),

  getCost: (id: number) =>
    apiClient.get<OperationalCost>(`/finance/costs/${id}`).then((r) => r.data),

  updateCost: (id: number, data: Partial<OperationalCostCreate>) =>
    apiClient.patch<OperationalCost>(`/finance/costs/${id}`, data).then((r) => r.data),

  deleteCost: (id: number) =>
    apiClient.delete(`/finance/costs/${id}`),

  getSummary: (month: number, year: number) =>
    apiClient.get<ProfitSummary>('/finance/summary', { params: { month, year } }).then((r) => r.data),
}
