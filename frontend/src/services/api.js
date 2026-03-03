import axios from 'axios'
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
    timeout: 10000,
})

/**
 * GET /buildings — list all campus buildings
 */
export async function getBuildings() {
    if (USE_MOCK) return MOCK_BUILDINGS
    const { data } = await client.get('/buildings')
    return data.buildings
}

/**
 * POST /predict — hourly forecast for a building
 */
export async function getForecast(buildingId, horizon = 24, whatIfModifiers = null) {
    if (USE_MOCK) return MOCK_FORECAST
    const { data } = await client.post('/predict', {
        building_id: buildingId,
        horizon,
        what_if_modifiers: whatIfModifiers,
    })
    return data
}

/**
 * POST /recommendations — load-shifting recommendations
 */
export async function getRecommendations(buildingId) {
    if (USE_MOCK) return MOCK_RECOMMENDATIONS
    const { data } = await client.post('/recommendations', { building_id: buildingId })
    return data
}

/**
 * POST /explain — SHAP-style feature explanations
 */
export async function getExplanation(buildingId) {
    if (USE_MOCK) return MOCK_EXPLANATION
    const { data } = await client.post('/explain', { building_id: buildingId })
    return data
}

/**
 * POST /whatif — scenario simulation
 */
export async function postWhatIf(buildingId, changes) {
    if (USE_MOCK) return MOCK_WHATIF(changes.temperature_offset, changes.occupancy_multiplier)
    const { data } = await client.post('/whatif', {
        building_id: buildingId,
        changes,
    })
    return data
}
