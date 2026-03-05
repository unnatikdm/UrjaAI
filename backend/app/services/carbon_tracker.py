from datetime import datetime
from typing import Dict, List, Optional
import logging

class CarbonTracker:
    """Carbon footprint tracker for energy savings with regional grid intensity"""
    
    def __init__(self, region: str = "India"):
        self.region = region
        self.logger = logging.getLogger(__name__)
        
        # Regional grid intensity values (kg CO2/kWh)
        self.grid_intensities = {
            "India": 0.820,  # Central Electricity Authority of India (2023)
            "Hungary": 0.242,  # European Environment Agency (2023)
            "EU_Average": 0.276,  # IPCC default
            "Germany": 0.401,
            "France": 0.059,
            "Poland": 0.765,
            "UK": 0.209,
            "USA": 0.386
        }
        
        # Time-of-day adjustment factors
        self.time_factors = {
            "solar": (9, 16, 0.85),    # 9-16: 15% reduction (solar)
            "evening_peak": (16, 21, 1.10),  # 16-21: 10% increase
            "night": (0, 6, 1.05)       # 0-6: 5% increase
        }
        
        # Badge thresholds (kg CO2 saved)
        self.badges = {
            "seedling": {"threshold": 10, "icon": "🌱", "name": "Seedling"},
            "sapling": {"threshold": 50, "icon": "🌿", "name": "Sapling"},
            "tree": {"threshold": 200, "icon": "🌳", "name": "Tree"},
            "forest": {"threshold": 500, "icon": "🌲", "name": "Forest"},
            "carbon_hero": {"threshold": 1000, "icon": "🏆", "name": "Carbon Hero"}
        }
        
        # Cumulative savings tracking
        self.cumulative_co2_saved = 0.0
    
    def get_grid_intensity(self, timestamp: Optional[datetime] = None) -> float:
        """Get grid intensity with time-of-day adjustment"""
        
        base_intensity = self.grid_intensities.get(self.region, 0.242)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        
        # Apply time-of-day adjustments
        for period, (start_hour, end_hour, factor) in self.time_factors.items():
            if start_hour <= hour < end_hour:
                return base_intensity * factor
        
        # Default (6-9 and 21-24): no adjustment
        return base_intensity
    
    def calculate_carbon_impact(self, energy_saved_kwh: float, 
                              timestamp: Optional[datetime] = None) -> Dict:
        """Calculate carbon impact metrics for energy savings"""
        
        grid_intensity = self.get_grid_intensity(timestamp)
        
        # Core calculations
        co2_saved_kg = energy_saved_kwh * grid_intensity
        co2_saved_tons = co2_saved_kg / 1000
        
        # Relatable metrics conversions
        trees_equivalent = co2_saved_kg / 20  # 1 tree absorbs 20 kg CO2/year
        car_km_avoided = co2_saved_kg * 4     # 250g CO2/km → 4 km per kg
        smartphone_charges = energy_saved_kwh * 100  # 100 charges per kWh
        homes_daily = (energy_saved_kwh / 1000) * (365/12)  # Simplified
        
        # Update cumulative savings
        self.cumulative_co2_saved += co2_saved_kg
        
        # Determine badge
        current_badge = self.get_current_badge()
        
        return {
            "energy_saved_kwh": round(energy_saved_kwh, 2),
            "co2_saved_kg": round(co2_saved_kg, 2),
            "co2_saved_tons": round(co2_saved_tons, 4),
            "trees_equivalent": round(trees_equivalent, 2),
            "car_km_avoided": round(car_km_avoided, 2),
            "smartphone_charges": round(smartphone_charges, 0),
            "homes_daily": round(homes_daily, 2),
            "grid_intensity": round(grid_intensity, 3),
            "region": self.region,
            "badge_earned": current_badge,
            "cumulative_co2_saved": round(self.cumulative_co2_saved, 2)
        }
    
    def get_current_badge(self) -> Optional[Dict]:
        """Get current badge based on cumulative savings"""
        
        for badge_key, badge_info in reversed(self.badges.items()):
            if self.cumulative_co2_saved >= badge_info["threshold"]:
                return {
                    "key": badge_key,
                    "icon": badge_info["icon"],
                    "name": badge_info["name"],
                    "threshold": badge_info["threshold"]
                }
        
        return None
    
    def get_all_badges(self) -> Dict:
        """Get all badges with progress"""
        
        badges_status = {}
        
        for badge_key, badge_info in self.badges.items():
            progress = min(100, (self.cumulative_co2_saved / badge_info["threshold"]) * 100)
            badges_status[badge_key] = {
                **badge_info,
                "progress": round(progress, 1),
                "unlocked": self.cumulative_co2_saved >= badge_info["threshold"]
            }
        
        return badges_status
    
    def reset_cumulative_savings(self):
        """Reset cumulative savings tracking"""
        self.cumulative_co2_saved = 0.0
        self.logger.info("Cumulative CO2 savings reset to zero")
    
    def set_region(self, region: str):
        """Update region for grid intensity calculations"""
        if region in self.grid_intensities:
            self.region = region
            self.logger.info(f"Region updated to {region}")
        else:
            self.logger.warning(f"Region {region} not found, using default values")
    
    def get_grid_intensity_forecast(self, timestamps: List[datetime]) -> List[float]:
        """Get grid intensity forecast for multiple timestamps"""
        
        intensities = []
        for timestamp in timestamps:
            intensity = self.get_grid_intensity(timestamp)
            intensities.append(intensity)
        
        return intensities
