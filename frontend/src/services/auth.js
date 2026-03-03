const TOKEN_KEY = "urjaai_token"
const USER_KEY = "urjaai_user"

export async function login(username, password) {
    const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || "Invalid credentials")
    }
    const data = await res.json()
    localStorage.setItem(TOKEN_KEY, data.access_token)

    // Fetch and cache current user profile
    const me = await fetch("/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
    })
    if (me.ok) {
        localStorage.setItem(USER_KEY, JSON.stringify(await me.json()))
    }
    return data
}

export function logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
}

export function getToken() {
    return localStorage.getItem(TOKEN_KEY)
}

export function isLoggedIn() {
    return !!getToken()
}

export function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY)) || null
    } catch {
        return null
    }
}
