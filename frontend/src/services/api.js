import axios from 'axios'
import { getToken, logout } from './auth'
import {
    MOCK_FORECAST,
    MOCK_RECOMMENDATIONS,
    MOCK_EXPLANATION,
    MOCK_WHATIF,
    MOCK_BUILDINGS,
} from './mockData'

const USE_MOCK = !import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL

const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '',
    timeout: 60000,
})

client.interceptors.request.use(config => {
    const token = getToken()
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

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

export async function getDeepRecommendations(buildingId, modifiers = null) {
    if (USE_MOCK) {
        // Return mock deep recommendations when in mock mode
        return [
            {
                action: 'Pre-cool building during off-peak hours (22:00–06:00)',
                savings_kwh: 13.5,
                savings_cost_inr: 101.25,
                priority: 'high',
                reason: 'Shifting cooling load to off-peak tariff bands reduces demand charges and cuts unit cost by ~30%.\n\nDeep Insights:\nWeather Context: Based on historical patterns, this strategy typically yields 15-20% additional savings during summer months.',
                is_enriched: false,
                sources: []
            },
            {
                action: 'Raise HVAC setpoint by 1 °C during 11:00–14:00 peak window',
                savings_kwh: 9.0,
                savings_cost_inr: 67.5,
                priority: 'medium',
                reason: 'Each 1 °C setpoint increase reduces HVAC energy consumption by approximately 6–8%.\n\nDeep Insights:\nOccupancy patterns show this adjustment has minimal impact on comfort during peak hours.',
                is_enriched: false,
                sources: []
            }
        ]
    }
    
    const payload = { building_id: buildingId }
    if (modifiers) {
        payload.temperature_offset = modifiers.temperature_offset || 0.0
        payload.occupancy_multiplier = modifiers.occupancy_multiplier || 1.0
    }
    const { data } = await client.post('/rag/deep-recommendations', payload)
    return data
}

export async function chatWithRecommendationAI(recommendation, message, chatHistory = []) {
    if (USE_MOCK) {
        // Mock chat response
        return {
            response: `I understand you're asking about: "${message}". This is a mock response since the backend is not connected. In a real deployment, I would provide detailed insights about the recommendation: "${recommendation.action}"`,
            sources: []
        }
    }
    
    const { data } = await client.post('/rag/chat', {
        recommendation,
        message,
        chat_history: chatHistory
    })
    return data
}

export async function getEnhancedRecommendations(buildingId, includeBenchmarks = true, includeMultipleLevels = true) {
    const { data } = await client.get(`/enhanced/recommendations/${buildingId}`, {
        params: {
            include_benchmarks: includeBenchmarks,
            include_multiple_levels: includeMultipleLevels
        }
    })
    return data
}

export async function getPricingContext() {
    const { data } = await client.get('/enhanced/pricing/context')
    return data
}

export async function getEnhancedWeatherAlerts() {
    const { data } = await client.get('/enhanced/weather/alerts')
    return data
}

export async function getOccupancy(buildingId) {
    const { data } = await client.get(`/enhanced/occupancy/${buildingId}`)
    return data
}

export async function calculateWhatIf(buildingId, currentSetpoint, newSetpoint, outdoorTemp, occupancyCount, durationHours = 3) {
    const { data } = await client.post('/rag/what-if', {
        building_id: buildingId,
        current_setpoint: currentSetpoint,
        proposed_setpoint: newSetpoint,
        outdoor_temp: outdoorTemp,
        occupancy_count: occupancyCount,
        duration_hours: durationHours
    })
    return data
}

export async function submitFeedback(recommendationId, buildingId, wasHelpful, feedbackText = null, actualSavings = null, rating = null) {
    const { data } = await client.post('/rag/feedback', {
        recommendation_id: recommendationId,
        building_id: buildingId,
        was_helpful: wasHelpful,
        feedback_text: feedbackText,
        actual_savings_kwh: actualSavings,
        rating: rating
    })
    return data
}

export async function getFeedbackStats() {
    const { data } = await client.get('/rag/feedback/stats')
    return data
}
