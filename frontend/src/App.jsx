import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import SpecialFeatures from './pages/SpecialFeatures'
import DeepRecommendations from './pages/DeepRecommendations'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/special-features"
                    element={
                        <ProtectedRoute>
                            <SpecialFeatures />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/deep-recommendations/:buildingId"
                    element={
                        <ProtectedRoute>
                            <DeepRecommendations />
                        </ProtectedRoute>
                    }
                />
                {/* Catch-all */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    )
}
