import { useEffect, useState } from 'react'
import { customersApi } from '@/api/customers'
import type { Customer } from '@/api/customers'

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    customersApi
      .list()
      .then(setCustomers)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="p-6 text-gray-500">Loading customers…</p>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Customers</h1>
        <button className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
          + Add Customer
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-100 text-sm">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">Address</th>
              <th className="px-4 py-3">Joined</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {customers.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-400">No customers yet.</td></tr>
            )}
            {customers.map((c) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800">{c.name}</td>
                <td className="px-4 py-3 text-gray-600">{c.phone ?? '—'}</td>
                <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{c.address ?? '—'}</td>
                <td className="px-4 py-3 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
