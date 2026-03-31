import { useEffect, useState } from 'react'
import { financeApi } from '@/api/finance'
import type { ProfitSummary } from '@/api/finance'

export default function DashboardPage() {
  const now = new Date()
  const [summary, setSummary] = useState<ProfitSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    financeApi
      .getSummary(now.getMonth() + 1, now.getFullYear())
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="p-6 text-gray-500">Loading dashboard…</p>

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
      <p className="text-gray-500">
        {now.toLocaleString('default', { month: 'long' })} {now.getFullYear()}
      </p>

      {summary && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Revenue" value={`₫${Number(summary.revenue).toLocaleString()}`} color="green" />
          <StatCard label="COGS" value={`₫${Number(summary.cogs).toLocaleString()}`} color="yellow" />
          <StatCard label="Op. Costs" value={`₫${Number(summary.operational_costs).toLocaleString()}`} color="orange" />
          <StatCard
            label="Net Profit"
            value={`₫${Number(summary.net_profit).toLocaleString()}`}
            color={Number(summary.net_profit) >= 0 ? 'green' : 'red'}
          />
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    red: 'bg-red-50 border-red-200 text-red-700',
  }
  return (
    <div className={`rounded-xl border p-4 ${colors[color] ?? colors.green}`}>
      <p className="text-sm font-medium opacity-75">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  )
}
