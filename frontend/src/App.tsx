import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import DashboardPage from '@/pages/dashboard/DashboardPage'
import InventoryPage from '@/pages/inventory/InventoryPage'
import PosPage from '@/pages/pos/PosPage'
import DeliveryPage from '@/pages/delivery/DeliveryPage'
import CustomersPage from '@/pages/customers/CustomersPage'
import FinancePage from '@/pages/finance/FinancePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="pos" element={<PosPage />} />
          <Route path="delivery" element={<DeliveryPage />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="finance" element={<FinancePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
