import { useEffect, useState } from 'react'
import { posApi } from '@/api/pos'
import type { Order, OrderStatus } from '@/api/pos'

const STATUS_COLORS: Record<OrderStatus, string> = {
  pending: 'bg-gray-100 text-gray-700',
  confirmed: 'bg-blue-100 text-blue-700',
  preparing: 'bg-yellow-100 text-yellow-700',
  ready: 'bg-teal-100 text-teal-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
}

export default function PosPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    posApi
      .listOrders({ limit: 50 })
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <p className="p-6 text-gray-500">Loading orders…</p>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Point of Sale</h1>
        <button className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
          + New Order
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-100 text-sm">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Order #</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Items</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Payment</th>
              <th className="px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-700">#{order.id}</td>
                <td className="px-4 py-3 capitalize text-gray-600">{order.order_type}</td>
                <td className="px-4 py-3 text-gray-600">{order.items.length}</td>
                <td className="px-4 py-3 font-medium text-gray-800">
                  ₫{Number(order.total_amount).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_COLORS[order.status]}`}>
                    {order.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {order.payment ? (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 capitalize">
                      {order.payment.method}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(order.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
