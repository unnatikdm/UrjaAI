import os
import pandas as pd
import numpy as np
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "iblend")

class IBlendDataPipeline:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.calendar_df = None
        self.metadata_df = None

    def load_base_files(self):
        """Loads the calendar and metadata files containing the schedule mappings"""
        cal_path = os.path.join(self.data_dir, "institute_calendar.csv")
        meta_path = os.path.join(self.data_dir, "building_metadata.csv")
        
        if not os.path.exists(cal_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("Calendar or Metadata CSVs missing in I-BLEND dir.")
            
        self.calendar_df = pd.read_csv(cal_path)
        self.calendar_df['date'] = pd.to_datetime(self.calendar_df['date']).dt.date
        self.metadata_df = pd.read_csv(meta_path)
        
        print("Loaded Calendar and Metadata.")

    def process_building(self, building_id):
        """Merges energy, occupancy, and calendar features for a single building"""
        if self.calendar_df is None:
            self.load_base_files()
            
        energy_path = os.path.join(self.data_dir, "energy", f"{building_id}.csv")
        occ_path = os.path.join(self.data_dir, "occupancy", f"{building_id}.csv")
        
        if not os.path.exists(energy_path) or not os.path.exists(occ_path):
             print(f"Skipping {building_id} - data files missing.")
             return None
             
        # Load and set time index
        energy_df = pd.read_csv(energy_path)
        energy_df['timestamp'] = pd.to_datetime(energy_df['timestamp'])
        
        occ_df = pd.read_csv(occ_path)
        occ_df['timestamp'] = pd.to_datetime(occ_df['timestamp'])
        
        # Merge energy and occupancy on timestamp
        merged_df = pd.merge(energy_df, occ_df, on="timestamp", how="left")
        
        # Fill missing capacities/metadata
        meta_row = self.metadata_df[self.metadata_df["building_id"] == building_id]
        if meta_row.empty:
            print(f"No metadata for {building_id}")
            return None
            
        meta_row = meta_row.iloc[0]
        b_type = meta_row["type"]
        capacity = meta_row["capacity"]
        
        merged_df["building_id"] = building_id
        merged_df["building_type"] = b_type
        merged_df["capacity"] = capacity
        merged_df["occupancy_rate"] = merged_df["occupancy_count"] / capacity
        
        # Feature Engineering: Time
        merged_df["hour"] = merged_df["timestamp"].dt.hour
        merged_df["day_of_week"] = merged_df["timestamp"].dt.dayofweek
        merged_df["month"] = merged_df["timestamp"].dt.month
        merged_df["is_weekend"] = merged_df["day_of_week"].apply(lambda x: 1 if x >= 5 else 0)
        
        # Feature Engineering: Calendar
        merged_df['date'] = merged_df['timestamp'].dt.date
        
        # Note: We do a merge based on date
        merged_df = pd.merge(merged_df, self.calendar_df, on="date", how="left")
        
        # For 'days_to_exam' we could compute distance, simplified here as context 
        # (Assuming 'academic_week' feature serves as a continuous time indicator in proxy)
        
        # Feature Engineering: Lag & Rolling
        merged_df = merged_df.sort_values('timestamp')
        merged_df['lag_1h'] = merged_df['power_kw'].shift(1)
        merged_df['lag_24h'] = merged_df['power_kw'].shift(24)
        merged_df['rolling_mean_24h'] = merged_df['power_kw'].rolling(window=24, min_periods=1).mean()
        
        # Drop naive NaNs created by lagging at start
        merged_df = merged_df.dropna()
        
        return merged_df

    def process_all_buildings(self):
        """Returns a concatenated dataframe of all buildings fully engineered."""
        if self.calendar_df is None:
            self.load_base_files()
            
        all_dfs = []
        for b_id in self.metadata_df["building_id"].unique():
             df = self.process_building(b_id)
             if df is not None:
                 all_dfs.append(df)
                 
        if not all_dfs:
            return pd.DataFrame()
            
        full_df = pd.concat(all_dfs, ignore_index=True)
        return full_df

if __name__ == "__main__":
    pipeline = IBlendDataPipeline()
    df = pipeline.process_all_buildings()
    print(f"Engineered Dataset Shape: {df.shape}")
    print("\nColumns:", df.columns.tolist())
    # print(df.head())
