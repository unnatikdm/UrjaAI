import axios from 'axios'
import { getToken, logout } from './auth'
import {
    MOCK_FORECAST,
    MOCK_RECOMMENDATIONS,
    MOCK_EXPLANATION,
    MOCK_WHATIF,
    MOCK_BUILDINGS,
} from './mockData'

const USE_MOCK = !import.meta.env.VITE_API_BASE_URL

const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '',
    timeout: 30000, // Increased to 30s to allow ML models to run inference
})

// ── Request interceptor: attach JWT ──────────────────────────────────────────
client.interceptors.request.use(config => {
    const token = getToken()
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// ── Response interceptor: handle 401 ────────────────────────────────────────
client.interceptors.response.use(
    res => res,
    err => {
        if (err.response?.status === 401) {
            logout()
            window.location.href = '/login'
        }
        return Promise.reject(err)
    }
)

export async function getBuildings() {
    if (USE_MOCK) return MOCK_BUILDINGS
    const { data } = await client.get('/buildings')
    return data.buildings
}

export async function getForecast(buildingId, horizon = 24, whatIfModifiers = null) {
    if (USE_MOCK) return MOCK_FORECAST
    const { data } = await client.post('/predict', {
        building_id: buildingId,
        horizon,
        what_if_modifiers: whatIfModifiers,
    })
    return data
}

export async function getRecommendations(buildingId, whatIfModifiers = null) {
    if (USE_MOCK) return MOCK_RECOMMENDATIONS
    const payload = { building_id: buildingId }
    if (whatIfModifiers) {
        if (whatIfModifiers.temperature_offset !== undefined) payload.temperature_offset = whatIfModifiers.temperature_offset
        if (whatIfModifiers.occupancy_multiplier !== undefined) payload.occupancy_multiplier = whatIfModifiers.occupancy_multiplier
    }
    const { data } = await client.post('/recommendations', payload)
    return data
}

export async function getExplanation(buildingId) {
    if (USE_MOCK) return MOCK_EXPLANATION
    const { data } = await client.post('/explain', { building_id: buildingId })
    return data
}

export async function postWhatIf(buildingId, changes) {
    if (USE_MOCK) return MOCK_WHATIF(changes.temperature_offset, changes.occupancy_multiplier)
    const { data } = await client.post('/whatif', {
        building_id: buildingId,
        changes,
    })
    return data
}

// ── Sustainability Endpoints ──────────────────────────────────────────────

export async function getWeather(hours = 48) {
    const { data } = await client.get(`/weather?hours=${hours}`)
    return data
}

export async function getWeatherAlerts() {
    const { data } = await client.get('/weather-alerts')
    return data.alerts || []
}

export async function getBadges() {
    const { data } = await client.get('/badges')
    return data
}

export async function getStats() {
    const { data } = await client.get('/stats')
    return data
}

export async function postCarbonImpact(energySaved) {
    const { data } = await client.post('/carbon-impact', {
        energy_saved_kwh: energySaved
    })
    return data
}
