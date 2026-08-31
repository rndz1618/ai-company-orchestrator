import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import Agents from './pages/Agents'
import Tasks from './pages/Tasks'
import TaskDetail from './pages/TaskDetail'
import Budgets from './pages/Budgets'
import OrgChart from './pages/OrgChart'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="companies" element={<Companies />} />
          <Route path="agents" element={<Agents />} />
          <Route path="org" element={<OrgChart />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="tasks/:taskId" element={<TaskDetail />} />
          <Route path="budgets" element={<Budgets />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
