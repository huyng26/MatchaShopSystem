import { NavLink, Outlet } from 'react-router-dom'
import { useAppStore } from '@/store/useAppStore'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/inventory', label: 'Inventory', icon: '🌿' },
  { to: '/pos', label: 'POS', icon: '🛒' },
  { to: '/delivery', label: 'Delivery', icon: '🚚' },
  { to: '/customers', label: 'Customers', icon: '👥' },
  { to: '/finance', label: 'Finance', icon: '💰' },
]

export default function Layout() {
  const { sidebarOpen, toggleSidebar } = useAppStore()

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside
        className={`flex flex-col bg-white shadow-md transition-all duration-200 ${
          sidebarOpen ? 'w-56' : 'w-16'
        }`}
      >
        <div className="flex h-14 items-center justify-between px-4 border-b border-gray-100">
          {sidebarOpen && (
            <span className="text-base font-bold text-green-700 whitespace-nowrap">🍵 Matcha Shop</span>
          )}
          <button
            onClick={toggleSidebar}
            className="ml-auto rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV_ITEMS.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-green-50 text-green-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <span className="text-base">{icon}</span>
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
