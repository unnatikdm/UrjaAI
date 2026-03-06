"""
Bosch Data API Wrapper
Serves Bosch Parquet data via REST endpoints for real data integration
"""

import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="Bosch Energy Data API",
    description="API wrapper for Bosch campus energy data",
    version="1.0.0"
)

# Global data storage
energy_data = {}
building_metadata = {}
recommendations_db = []
outcomes_db = []

# Data models
class EnergyDataResponse(BaseModel):
    building_id: str
    start_date: str
    end_date: str
    data: List[Dict[str, Any]]
    total_records: int

class BuildingMetadata(BaseModel):
    building_id: str
    building_type: str
    size_sqft: float
    hvac_type: str
    construction_year: int
    occupancy_patterns: Dict[str, Any]
    thermal_mass: str
    insulation_level: str

class Recommendation(BaseModel):
    id: str
    building_id: str
    action: str
    predicted_savings_kwh: float
    predicted_savings_cost: float
    issued_at: str
    target_date: str
    weather_forecast: Dict[str, Any]
    occupancy_forecast: Dict[str, Any]
    model_version: str
    status: str = "pending"

class RecommendationOutcome(BaseModel):
    recommendation_id: str
    actual_savings_kwh: float
    actual_savings_cost: float
    success: bool
    feedback: Optional[str] = None
    evaluated_at: str

def load_bosch_data():
    """Load Bosch Parquet files into memory"""
    global energy_data, building_metadata
    
    # Look for Bosch data files in parent directories
    data_paths = [
        "../browniepoint2/data",
        "../data", 
        "../../data",
        "data"
    ]
    
    bosch_data_path = None
    for path in data_paths:
        if os.path.exists(path):
            bosch_data_path = path
            break
    
    if not bosch_data_path:
        print("Warning: Bosch data files not found. Using synthetic data.")
        generate_synthetic_data()
        return
    
    print(f"Loading Bosch data from: {bosch_data_path}")
    
    try:
        # Load energy data
        energy_files = [
            f for f in os.listdir(bosch_data_path) 
            if f.endswith('.parquet') and ('energy' in f.lower() or 'consumption' in f.lower())
        ]
        
        for file in energy_files:
            building_id = file.split('_')[0] if '_' in file else 'building_A'
            file_path = os.path.join(bosch_data_path, file)
            
            try:
                df = pd.read_parquet(file_path)
                if 'timestamp' in df.columns:
                    df.set_index('timestamp', inplace=True)
                elif 'date' in df.columns:
                    df.set_index('date', inplace=True)
                
                energy_data[building_id] = df
                print(f"Loaded energy data for {building_id}: {len(df)} records")
                
            except Exception as e:
                print(f"Failed to load {file}: {e}")
        
        # Load metadata
        metadata_files = [
            f for f in os.listdir(bosch_data_path) 
            if f.endswith('.parquet') and ('metadata' in f.lower() or 'building' in f.lower())
        ]
        
        for file in metadata_files:
            file_path = os.path.join(bosch_data_path, file)
            try:
                df = pd.read_parquet(file_path)
                for _, row in df.iterrows():
                    building_id = row.get('building_id', 'building_A')
                    building_metadata[building_id] = row.to_dict()
                print(f"Loaded metadata: {len(df)} buildings")
                
            except Exception as e:
                print(f"Failed to load metadata {file}: {e}")
        
        # If no real data loaded, generate synthetic
        if not energy_data:
            print("No energy data loaded, generating synthetic data")
            generate_synthetic_data()
            
    except Exception as e:
        print(f"Error loading Bosch data: {e}")
        generate_synthetic_data()

def generate_synthetic_data():
    """Generate synthetic data when real Bosch data is not available"""
    global energy_data, building_metadata
    
    print("Generating synthetic Bosch-compatible data...")
    
    # Generate synthetic energy data for buildings A, B, C
    buildings = ['A', 'B', 'C']
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 7, 20)
    
    for building_id in buildings:
        # Generate hourly energy data
        dates = pd.date_range(start=start_date, end=end_date, freq='h')
        
        # Create realistic energy patterns
        base_consumption = 50 + np.random.randint(10, 30)
        
        # Add daily patterns (higher during day, lower at night)
        daily_pattern = np.sin(2 * np.pi * dates.hour / 24) * 20 + 10
        
        # Add weekly patterns (higher on weekdays)
        weekly_pattern = np.where(dates.dayofweek < 5, 15, -10)
        
        # Add seasonal patterns (higher in summer/winter)
        seasonal_pattern = 10 * np.sin(2 * np.pi * dates.dayofyear / 365)
        
        # Add random noise
        noise = np.random.normal(0, 5, len(dates))
        
        # Combine patterns
        energy_consumption = base_consumption + daily_pattern + weekly_pattern + seasonal_pattern + noise
        energy_consumption = np.maximum(energy_consumption, 5)  # Ensure positive
        
        # Create DataFrame
        df = pd.DataFrame({
            'energy_kwh': energy_consumption,
            'temperature': 20 + 15 * np.sin(2 * np.pi * dates.dayofyear / 365) + np.random.normal(0, 3, len(dates)),
            'occupancy': np.where(dates.hour < 9, 0.1, 
                                np.where(dates.hour > 18, 0.2, 
                                        np.where(dates.dayofweek < 5, 0.8, 0.3))),
            'building_id': building_id
        }, index=dates)
        
        energy_data[building_id] = df
        print(f"Generated synthetic data for {building_id}: {len(df)} records")
    
    # Generate building metadata
    building_types = {
        'A': {'type': 'lecture_hall', 'size': 2500, 'hvac': 'constant_volume', 'year': 1985},
        'B': {'type': 'library', 'size': 1800, 'hvac': 'vav', 'year': 1992},
        'C': {'type': 'dormitory', 'size': 1200, 'hvac': 'fan_coil', 'year': 1975}
    }
    
    for building_id, info in building_types.items():
        building_metadata[building_id] = {
            'building_id': building_id,
            'building_type': info['type'],
            'size_sqft': info['size'],
            'hvac_type': info['hvac'],
            'construction_year': info['year'],
            'occupancy_patterns': {
                'peak_hours': '09:00-17:00' if building_id != 'C' else '16:00-22:00',
                'weekend': 'low' if building_id == 'A' else 'medium',
                'holidays': 'closed' if building_id == 'A' else 'reduced'
            },
            'thermal_mass': 'high' if building_id == 'A' else 'medium' if building_id == 'B' else 'low',
            'insulation_level': 'moderate' if building_id == 'A' else 'high' if building_id == 'B' else 'low'
        }

# Load data on startup
@app.on_event("startup")
async def startup_event():
    load_bosch_data()
    print("Bosch Data API initialized")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Bosch Energy Data API", "buildings": list(energy_data.keys())}

@app.get("/buildings")
async def get_buildings():
    """Get list of all buildings"""
    return {
        "buildings": list(energy_data.keys()),
        "total_count": len(energy_data)
    }

@app.get("/buildings/{building_id}/energy", response_model=EnergyDataResponse)
async def get_energy_data(
    building_id: str,
    start: str = Query(..., description="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"),
    end: str = Query(..., description="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)")
):
    """Get energy data for a building within date range"""
    
    if building_id not in energy_data:
        raise HTTPException(status_code=404, detail=f"Building {building_id} not found")
    
    df = energy_data[building_id]
    
    try:
        # Parse dates
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        
        # Filter data
        mask = (df.index >= start_date) & (df.index <= end_date)
        filtered_df = df.loc[mask]
        
        # Convert to list of dictionaries
        data = []
        for idx, row in filtered_df.iterrows():
            data.append({
                'timestamp': idx.isoformat(),
                'energy_kwh': float(row['energy_kwh']),
                'temperature': float(row.get('temperature', 0)),
                'occupancy': float(row.get('occupancy', 0))
            })
        
        return EnergyDataResponse(
            building_id=building_id,
            start_date=start,
            end_date=end,
            data=data,
            total_records=len(data)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Date parsing error: {str(e)}")

@app.get("/buildings/{building_id}/metadata", response_model=BuildingMetadata)
async def get_building_metadata(building_id: str):
    """Get building metadata"""
    
    if building_id not in building_metadata:
        raise HTTPException(status_code=404, detail=f"Building {building_id} not found")
    
    metadata = building_metadata[building_id]
    
    return BuildingMetadata(
        building_id=metadata['building_id'],
        building_type=metadata['building_type'],
        size_sqft=metadata['size_sqft'],
        hvac_type=metadata['hvac_type'],
        construction_year=metadata['construction_year'],
        occupancy_patterns=metadata['occupancy_patterns'],
        thermal_mass=metadata['thermal_mass'],
        insulation_level=metadata['insulation_level']
    )

@app.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of recommendations to return")
):
    """Get recommendations (filtered by building and status)"""
    
    filtered_recs = recommendations_db
    
    if building_id:
        filtered_recs = [r for r in filtered_recs if r['building_id'] == building_id]
    
    if status:
        filtered_recs = [r for r in filtered_recs if r['status'] == status]
    
    # Limit results
    filtered_recs = filtered_recs[:limit]
    
    return [Recommendation(**rec) for rec in filtered_recs]

@app.post("/recommendations", response_model=Recommendation)
async def create_recommendation(recommendation: Recommendation):
    """Create a new recommendation"""
    
    # Add to database
    rec_dict = recommendation.dict()
    rec_dict['issued_at'] = datetime.now().isoformat()
    recommendations_db.append(rec_dict)
    
    print(f"Created recommendation: {rec_dict['id']} for building {rec_dict['building_id']}")
    
    return Recommendation(**rec_dict)

@app.get("/recommendations/{recommendation_id}/outcome", response_model=RecommendationOutcome)
async def get_recommendation_outcome(recommendation_id: str):
    """Get outcome for a specific recommendation"""
    
    for outcome in outcomes_db:
        if outcome['recommendation_id'] == recommendation_id:
            return RecommendationOutcome(**outcome)
    
    raise HTTPException(status_code=404, detail=f"Outcome for recommendation {recommendation_id} not found")

@app.post("/recommendations/{recommendation_id}/outcome", response_model=RecommendationOutcome)
async def create_recommendation_outcome(
    recommendation_id: str, 
    outcome: RecommendationOutcome
):
    """Create or update outcome for a recommendation"""
    
    # Check if recommendation exists
    rec_exists = any(r['id'] == recommendation_id for r in recommendations_db)
    if not rec_exists:
        raise HTTPException(status_code=404, detail=f"Recommendation {recommendation_id} not found")
    
    # Update recommendation status
    for rec in recommendations_db:
        if rec['id'] == recommendation_id:
            rec['status'] = 'evaluated'
            break
    
    # Add outcome
    outcome_dict = outcome.dict()
    outcome_dict['recommendation_id'] = recommendation_id
    outcome_dict['evaluated_at'] = datetime.now().isoformat()
    
    # Remove existing outcome if present
    outcomes_db[:] = [o for o in outcomes_db if o['recommendation_id'] != recommendation_id]
    
    # Add new outcome
    outcomes_db.append(outcome_dict)
    
    print(f"Created outcome for recommendation {recommendation_id}")
    
    return RecommendationOutcome(**outcome_dict)

@app.get("/buildings/{building_id}/energy-summary")
async def get_energy_summary(
    building_id: str,
    start: str = Query(...),
    end: str = Query(...)
):
    """Get energy summary statistics for a building"""
    
    if building_id not in energy_data:
        raise HTTPException(status_code=404, detail=f"Building {building_id} not found")
    
    df = energy_data[building_id]
    
    try:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        
        mask = (df.index >= start_date) & (df.index <= end_date)
        filtered_df = df.loc[mask]
        
        if len(filtered_df) == 0:
            return {"message": "No data found for the specified period"}
        
        summary = {
            'building_id': building_id,
            'period': {
                'start': start,
                'end': end
            },
            'statistics': {
                'total_energy_kwh': float(filtered_df['energy_kwh'].sum()),
                'average_energy_kwh': float(filtered_df['energy_kwh'].mean()),
                'peak_energy_kwh': float(filtered_df['energy_kwh'].max()),
                'minimum_energy_kwh': float(filtered_df['energy_kwh'].min()),
                'total_records': len(filtered_df),
                'average_temperature': float(filtered_df.get('temperature', pd.Series([0])).mean()),
                'average_occupancy': float(filtered_df.get('occupancy', pd.Series([0])).mean())
            }
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing data: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "buildings_loaded": len(energy_data),
        "metadata_loaded": len(building_metadata),
        "recommendations_stored": len(recommendations_db),
        "outcomes_stored": len(outcomes_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
