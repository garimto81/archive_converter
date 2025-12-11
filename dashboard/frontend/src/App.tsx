import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import MatchingMatrix from './pages/MatchingMatrix'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/matching" replace />} />
          <Route path="matching" element={<MatchingMatrix />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
