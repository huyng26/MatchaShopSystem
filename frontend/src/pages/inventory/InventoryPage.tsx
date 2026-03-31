import { useEffect, useState } from 'react'
import { inventoryApi } from '@/api/inventory'
import type { Ingredient } from '@/api/inventory'

export default function InventoryPage() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    inventoryApi
      .listIngredients()
      .then(setIngredients)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <p className="p-6 text-gray-500">Loading inventory…</p>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Inventory</h1>
        <button className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
          + Add Ingredient
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-100 text-sm">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Unit</th>
              <th className="px-4 py-3">Stock</th>
              <th className="px-4 py-3">Min Threshold</th>
              <th className="px-4 py-3">Cost / Unit</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {ingredients.map((ing) => {
              const isLow = Number(ing.current_stock) <= Number(ing.min_stock_threshold)
              return (
                <tr key={ing.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{ing.name}</td>
                  <td className="px-4 py-3 text-gray-600">{ing.unit}</td>
                  <td className="px-4 py-3 text-gray-800">{ing.current_stock}</td>
                  <td className="px-4 py-3 text-gray-500">{ing.min_stock_threshold}</td>
                  <td className="px-4 py-3 text-gray-800">₫{Number(ing.cost_per_unit).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    {isLow ? (
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">Low</span>
                    ) : (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">OK</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
