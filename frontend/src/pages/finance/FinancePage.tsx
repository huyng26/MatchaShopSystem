import { useEffect, useState } from 'react'
import { financeApi } from '@/api/finance'
import type { OperationalCost, ProfitSummary } from '@/api/finance'

export default function FinancePage() {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [summary, setSummary] = useState<ProfitSummary | null>(null)
  const [costs, setCosts] = useState<OperationalCost[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.all([
      financeApi.getSummary(month, year),
      financeApi.listCosts({ month, year }),
    ])
      .then(([s, c]) => { setSummary(s); setCosts(c) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [month, year])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Finance</h1>
        <div className="flex items-center gap-2">
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
          >
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {new Date(0, i).toLocaleString('default', { month: 'long' })}
              </option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24 rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
          />
          <button
            onClick={load}
            className="rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
          >
            Load
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : summary ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            { label: 'Revenue', value: summary.revenue, color: 'green' },
            { label: 'COGS', value: summary.cogs, color: 'yellow' },
            { label: 'Op. Costs', value: summary.operational_costs, color: 'orange' },
            { label: 'Net Profit', value: summary.net_profit, color: Number(summary.net_profit) >= 0 ? 'green' : 'red' },
          ].map(({ label, value, color }) => (
            <div
              key={label}
              className={`rounded-xl border p-4 ${
                color === 'green' ? 'border-green-200 bg-green-50 text-green-700' :
                color === 'yellow' ? 'border-yellow-200 bg-yellow-50 text-yellow-700' :
                color === 'orange' ? 'border-orange-200 bg-orange-50 text-orange-700' :
                'border-red-200 bg-red-50 text-red-700'
              }`}
            >
              <p className="text-sm opacity-75">{label}</p>
              <p className="mt-1 text-2xl font-bold">₫{Number(value).toLocaleString()}</p>
            </div>
          ))}
        </div>
      ) : null}

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-700">Operational Costs</h2>
        <button className="rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700">
          + Add Cost
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-100 text-sm">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Recorded</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {costs.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-400">No costs recorded.</td></tr>
            )}
            {costs.map((c) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 capitalize font-medium text-gray-700">{c.category}</td>
                <td className="px-4 py-3 text-gray-500">{c.description ?? '—'}</td>
                <td className="px-4 py-3 font-medium text-gray-800">₫{Number(c.amount).toLocaleString()}</td>
                <td className="px-4 py-3 text-gray-500">{new Date(c.recorded_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
