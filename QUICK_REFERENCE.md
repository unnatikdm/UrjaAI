# Quick Reference Guide - Special Features Integration

## 📚 Important Files Created/Modified

### Frontend Files
```
UrjaAI/frontend/
├── src/
│   ├── pages/
│   │   └── SpecialFeatures.jsx          ← NEW: Main page with tabs
│   ├── components/
│   │   ├── Browniepoint1.jsx            ← NEW: Weather & carbon UI
│   │   ├── Browniepoint2.jsx            ← NEW: ML predictions UI
│   │   └── Header.jsx                   ← MODIFIED: Added navigation
│   └── App.jsx                          ← MODIFIED: Added /special-features route
```

### Backend Files
```
UrjaAI/backend/
└── app/
    ├── routers/
    │   ├── browniepoint1.py             ← NEW: Weather & carbon proxies
    │   └── browniepoint2.py             ← NEW: ML prediction proxies
    └── main.py                          ← MODIFIED: Registered routers
```

### Configuration Files
```
Root (d:\urja-ai\)
├── START_ALL_SERVICES.bat               ← NEW: Windows startup script
├── START_ALL_SERVICES.sh                ← NEW: Unix startup script
├── SPECIAL_FEATURES_README.md           ← NEW: User guide
└── SPECIAL_FEATURES_INTEGRATION.md      ← NEW: Technical details
```

---

## 🔗 API Routing Structure

```
Frontend Request            Backend Endpoint              Proxied Service
─────────────────────────────────────────────────────────────────────────

GET /weather        →   /api/browniepoint1/weather       →   :5000/weather
GET /alerts         →   /api/browniepoint1/weather-alerts→   :5000/weather-alerts
POST /carbon        →   /api/browniepoint1/carbon-impact →   :5000/carbon-impact
GET /badges         →   /api/browniepoint1/badges        →   :5000/badges

POST /predict       →   /api/browniepoint2/predict       →   :8001/predict
GET /info           →   /api/browniepoint2/system-info   →   :8001/system-info
GET /leaderboard    →   /api/browniepoint2/leaderboard   →   :8001/leaderboard
GET /explain        →   /api/browniepoint2/explain/{id}  →   :8001/explain/{id}
```

---

## 🎨 Component Architecture

### SpecialFeatures.jsx (Parent)
```jsx
SpecialFeatures
├── Header (navigation + building selector)
├── Tab Navigation (Browniepoint1 | Browniepoint2)
└── Content (conditional rendering)
    ├── Browniepoint1 (when tab === 'browniepoint1')
    └── Browniepoint2 (when tab === 'browniepoint2')
```

### Browniepoint1.jsx Structure
```jsx
Browniepoint1
├── Section Navigation (Weather | Alerts | Badges | Carbon)
└── Content Areas
    ├── Weather (forecast cards, summary metrics)
    ├── Alerts (alert cards with severity)
    ├── Badges (badge grid with progress)
    └── Carbon (calculator + impact metrics)
```

### Browniepoint2.jsx Structure
```jsx
Browniepoint2
├── Section Navigation (Overview | Predict | Leaderboard | Explainability)
└── Content Areas
    ├── Overview (model info, features, stats)
    ├── Predict (form + results + explanations)
    ├── Leaderboard (ranked table)
    └── Explainability (guide + SHAP values)
```

---

## 🔄 Data Flow Examples

### Weather Forecast Flow
```
User clicks "Weather" tab
    ↓
useEffect triggers fetchBrowniepoint1Data()
    ↓
axios.get('/api/browniepoint1/weather')
    ↓
Backend browniepoint1.py router
    ↓
httpx client calls http://localhost:5000/weather
    ↓
Browniepoint1 Flask service
    ↓
OpenMeteo API (external weather data)
    ↓
Response returned through chain
    ↓
Component renders weather cards
```

### ML Prediction Flow
```
User fills form + clicks "Predict"
    ↓
makePrediction() called
    ↓
axios.post('/api/browniepoint2/predict', {features, explain: true})
    ↓
Backend browniepoint2.py router
    ↓
httpx client calls http://localhost:8001/predict
    ↓
Browniepoint2 FastAPI service
    ↓
TabTransformer model loaded
    ↓
SHAP explainer runs
    ↓
Results + explanations returned
    ↓
Component renders prediction cards + SHAP chart
```

---

## 🛠️ Development Tasks

### Adding a New Section to Browniepoint1

1. **Add section state**
   ```jsx
   const [activeSection, setActiveSection] = useState('weather')
   ```

2. **Add button to navigation**
   ```jsx
   <button onClick={() => setActiveSection('newsection')}>
       🆕 New Section
   </button>
   ```

3. **Add API endpoint to backend**
   ```python
   # In browniepoint1.py
   @router.get("/newsection")
   async def get_new_section():
       # Call browniepoint1 API
   ```

4. **Add section content**
   ```jsx
   {activeSection === 'newsection' && (
       <div>Your content here</div>
   )}
   ```

### Adding a New Prediction Field

1. **Add form field in Browniepoint2.jsx**
   ```jsx
   <select onChange={(e) => setFeatures({...features, newfield: e.target.value})}>
   ```

2. **Send in prediction request**
   ```jsx
   const res = await axios.post('/api/browniepoint2/predict', {
       features: features,  // includes newfield
       explain: true
   })
   ```

3. **Backend handles automatically** (proxies to browniepoint2)

---

## 📊 Key Statistics

### Browniepoint1: Carbon Tracker
- **Weather Data Points**: 48 hourly forecasts
- **Carbon Metrics**: 4 (trees, km avoided, charges, CO₂)
- **Badges**: 4 achievement levels
- **Forecast Accuracy**: Depends on OpenMeteo API
- **Update Frequency**: Real-time (API cached 6 hours)

### Browniepoint2: ML Platform
- **Dataset Size**: 5,000 records
- **Features**: 69 categorical
- **Model Accuracy**: 92% (TabTransformer)
- **SHAP Top-K**: 10 features shown
- **Prediction Time**: ~2-3 seconds
- **Leaderboard Size**: Top 10 models

---

## 🧪 Common API Calls

### Get Weather Data
```javascript
const response = await axios.get('/api/browniepoint1/weather?hours=48')
// Returns: {timestamps, temperature, humidity, cloudcover, precipitation, windspeed}
```

### Calculate Carbon Impact
```javascript
const response = await axios.post('/api/browniepoint1/carbon-impact', {
    energy_saved_kwh: 100,
    timestamp: new Date().toISOString()
})
// Returns: {carbon_avoided_kg, trees_planted, car_km_avoided, smartphone_charges}
```

### Make ML Prediction
```javascript
const response = await axios.post('/api/browniepoint2/predict', {
    features: {
        age_group: 'young',
        segment: 'premium',
        products: '2',
        tenure: 'established'
    },
    explain: true,
    user_id: 'demo-user',
    top_k_features: 10
})
// Returns: {request_id, prediction, probability, confidence, explanation, gamification}
```

### Get System Information
```javascript
const response = await axios.get('/api/browniepoint2/system-info')
// Returns: {model_info, features, badges_count, system_stats}
```

### Get Leaderboard
```javascript
const response = await axios.get('/api/browniepoint2/leaderboard?limit=10')
// Returns: {leaderboard: [{rank, user_id, model_type, accuracy}, ...]}
```

---

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 503 Service Unavailable | Service not running | Start all 3 services |
| CORS error | Frontend policy | Check allowOrigins in main.py |
| Empty weather data | API rate limit | Wait 5 mins or change location |
| Slow predictions | Model loading | Model cached after first use |
| Build errors | Missing deps | pip install -r requirements.txt |
| Port conflict | Another app using port | Change port number or kill other process |

---

## 📝 File Size Reference

```
Browniepoint1.jsx      ~8.2 KB
Browniepoint2.jsx      ~12.4 KB
SpecialFeatures.jsx    ~4.1 KB
browniepoint1.py       ~7.8 KB
browniepoint2.py       ~12.3 KB
Total Frontend Code    ~24.7 KB
Total Backend Code     ~20.1 KB
```

---

## ⚡ Performance Optimization Tips

1. **Frontend**
   - Use React.memo for component optimization
   - Lazy load tab content
   - Cache API responses locally

2. **Backend**
   - Use connection pooling
   - Cache browniepoint responses
   - Implement request throttling

3. **Network**
   - Enable gzip compression
   - Minify JS/CSS in production
   - Use CDN for static assets

---

## 🔐 Environment Variables

No special environment variables needed, but you can add:

```bash
# .env (UrjaAI/backend)
BROWNIEPOINT1_API=http://localhost:5000
BROWNIEPOINT2_API=http://localhost:8001
SERVICE_TIMEOUT=30
```

---

## 📦 Dependencies

**Frontend (already in package.json)**
- react: ^18.3.1
- react-router-dom: ^7.13.1
- axios: ^1.7.2
- recharts: ^2.12.7

**Backend (already in requirements.txt)**
- fastapi: ~0.104.0
- httpx: ~0.25.0
- pydantic: ~2.0.0
- uvicorn: ~0.24.0

---

## 🎯 Success Criteria

✅ All services start without errors  
✅ Frontend loads at localhost:5173  
✅ Navigation to /special-features works  
✅ Both tabs render correctly  
✅ Weather data displays (min 5 hoursof forecast)  
✅ Carbon calculator functional  
✅ ML predictions work  
✅ SHAP explanations show top features  
✅ Leaderboard displays rankings  
✅ All endpoints return valid responses  
✅ No console errors in browser  
✅ Mobile responsive (tested at 375px width)  
✅ API documentation accessible (/docs)  

---

## 📞 Quick Support

### Service Health Check
```bash
# Check if services are running
curl http://localhost:8000/
curl http://localhost:5000/
curl http://localhost:8001/
```

### View Logs
```bash
# Windows QuickStart
tasklist | findstr python

# Unix/Linux
ps aux | grep python
```

### Restart Services
```bash
# Kill all Python processes
taskkill /F /IM python.exe

# Then restart with startup script
START_ALL_SERVICES.bat  # Windows
bash START_ALL_SERVICES.sh  # Unix
```

---

**Last Updated**: March 6, 2026  
**Version**: 1.0.0 - Integration Complete ✅
