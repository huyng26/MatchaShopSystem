import { useEffect, useState } from 'react'
import { deliveryApi } from '@/api/delivery'
import type { DeliveryBatch } from '@/api/delivery'

export default function DeliveryPage() {
  const [batches, setBatches] = useState<DeliveryBatch[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    deliveryApi
      .listBatches()
      .then(setBatches)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <p className="p-6 text-gray-500">Loading delivery batches…</p>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Delivery Management</h1>
        <div className="flex gap-2">
          <button className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            Suggest Batches
          </button>
          <button className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
            + New Batch
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {batches.length === 0 && (
          <p className="py-8 text-center text-gray-400">No delivery batches yet.</p>
        )}
        {batches.map((batch) => (
          <div key={batch.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-mono text-sm font-semibold text-gray-700">{batch.batch_number}</span>
                {batch.driver_name && (
                  <span className="ml-3 text-sm text-gray-500">Driver: {batch.driver_name}</span>
                )}
              </div>
              <span className={`rounded-full px-3 py-0.5 text-xs font-medium capitalize ${
                batch.status === 'completed' ? 'bg-green-100 text-green-700' :
                batch.status === 'dispatched' ? 'bg-blue-100 text-blue-700' :
                batch.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {batch.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              {batch.delivery_orders.length} order(s)
              {batch.scheduled_at && ` · Scheduled: ${new Date(batch.scheduled_at).toLocaleString()}`}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
