import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import SpecialFeatures from './pages/SpecialFeatures'
import DeepRecommendations from './pages/DeepRecommendations'
import EnhancedRecommendations from './pages/EnhancedRecommendations'
import Billing from './pages/Billing'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import UrjaConcierge from './components/UrjaConcierge'
import AnomalyNotifications from './components/AnomalyNotifications'

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
                <Route
                    path="/enhanced-recommendations/:buildingId"
                    element={
                        <ProtectedRoute>
                            <EnhancedRecommendations />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/billing"
                    element={
                        <ProtectedRoute>
                            <Billing />
                        </ProtectedRoute>
                    }
                />
                {/* Catch-all */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            {/* Real-time Anomaly Notifications */}
            <AnomalyNotifications />
            {/* Floating AI Assistant - Available on every page */}
            <UrjaConcierge />
        </BrowserRouter>
    )
}
