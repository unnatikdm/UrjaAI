import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "iblend")

def generate_mock_iblend_data():
    """Generates a small mock version of the I-BLEND dataset for initial pipeline testing."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "energy"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "occupancy"), exist_ok=True)
    
    print("Generating Mock I-BLEND dataset...")
    
    # 1. Generate Institute Calendar (2024 for mock)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_list = [start_date + timedelta(days=x) for x in range((end_date-start_date).days + 1)]
    
    calendar_data = []
    academic_week = 0
    for d in date_list:
        if d.weekday() == 0:
            academic_week += 1
            
        day_type = "normal"
        description = "Regular Day"
        is_holiday = 0
        is_exam = 0
        is_break = 0
        
        # Mock Holidays
        if d.month == 1 and d.day == 26:
            day_type = "holiday"
            description = "Republic Day"
            is_holiday = 1
        elif d.month == 8 and d.day == 15:
            day_type = "holiday"
            description = "Independence Day"
            is_holiday = 1
        elif d.month == 12 and d.day == 25:
             day_type = "holiday"
             description = "Christmas"
             is_holiday = 1
             
        # Mock Exams (April 15 - May 5, Nov 15 - Dec 5)
        elif (d.month == 4 and d.day >= 15) or (d.month == 5 and d.day <= 5):
            day_type = "exam_period"
            description = "Spring Exams"
            is_exam = 1
        elif (d.month == 11 and d.day >= 15) or (d.month == 12 and d.day <= 5):
            day_type = "exam_period"
            description = "Fall Exams"
            is_exam = 1
            
        # Mock Breaks (May 6 - July 31, Dec 6 - Jan 10)
        elif (d.month == 5 and d.day > 5) or d.month == 6 or d.month == 7:
             day_type = "break"
             description = "Summer Vacation"
             is_break = 1
        elif (d.month == 12 and d.day > 5) or (d.month == 1 and d.day <= 10):
             day_type = "break"
             description = "Winter Vacation"
             is_break = 1
             
        calendar_data.append({
            "date": d.strftime("%Y-%m-%d"),
            "day_type": day_type,
            "description": description,
            "academic_week": academic_week,
            "is_holiday": is_holiday,
            "is_exam": is_exam,
            "is_break": is_break
        })
    
    calendar_df = pd.DataFrame(calendar_data)
    calendar_df.to_csv(os.path.join(DATA_DIR, "institute_calendar.csv"), index=False)
    print("Created institute_calendar.csv")

    # 2. Generate Building Metadata
    buildings = [
        {"building_id": "academic_1", "type": "lecture", "capacity": 500, "floor_area_sqm": 5000},
        {"building_id": "library", "type": "library", "capacity": 300, "floor_area_sqm": 3000},
        {"building_id": "dorm_boys", "type": "dorm", "capacity": 800, "floor_area_sqm": 12000}
    ]
    pd.DataFrame(buildings).to_csv(os.path.join(DATA_DIR, "building_metadata.csv"), index=False)
    print("Created building_metadata.csv")

    # 3. Generate Energy & Occupancy (1-hour resampled mock data for lightweight testing)
    # Instead of true 1-min / 10-min, we simulate hourly data right off the bat to save space
    # but structure it to mimic the target pipeline output
    times = pd.date_range(start="2024-01-01", end="2024-12-31 23:00:00", freq="H")
    
    for b in buildings:
        energy_records = []
        occupancy_records = []
        
        for t in times:
            # Base logic
            hour = t.hour
            is_weekend = t.weekday() >= 5
            
            # Lookup calendar
            date_str = t.strftime("%Y-%m-%d")
            cal_row = calendar_df[calendar_df["date"] == date_str].iloc[0]
            
            # Simulate profiles
            base_kw = 20.0
            occ_count = 0
            
            if b["type"] == "lecture":
                if cal_row["is_break"] or cal_row["is_holiday"] or is_weekend:
                    occ_count = np.random.randint(0, 10)
                    kw = base_kw + np.random.uniform(0, 5)
                elif cal_row["is_exam"]:
                    occ_count = np.random.randint(50, b["capacity"])
                    kw = base_kw + (occ_count * 0.1) + np.random.uniform(10, 30)
                else:
                    if 8 <= hour <= 18:
                        occ_count = np.random.randint(100, b["capacity"])
                        kw = base_kw + (occ_count * 0.1) + np.random.uniform(20, 50)
                    else:
                        occ_count = np.random.randint(0, 20)
                        kw = base_kw + np.random.uniform(2, 10)
            
            elif b["type"] == "library":
                if cal_row["is_break"] or cal_row["is_holiday"]:
                    occ_count = np.random.randint(0, 20)
                    kw = base_kw + np.random.uniform(5, 15)
                elif cal_row["is_exam"]:
                    # Exams = packed library even at night
                    if 8 <= hour <= 23:
                         occ_count = np.random.randint(200, b["capacity"])
                         kw = base_kw + (occ_count * 0.08) + np.random.uniform(30, 60)
                    else:
                         occ_count = np.random.randint(50, 150)
                         kw = base_kw + (occ_count * 0.08) + np.random.uniform(15, 30)
                else:
                    if 9 <= hour <= 21:
                        occ_count = np.random.randint(50, 250)
                        kw = base_kw + (occ_count * 0.08) + np.random.uniform(20, 40)
                    else:
                        occ_count = np.random.randint(0, 10)
                        kw = base_kw + np.random.uniform(5, 10)

            elif b["type"] == "dorm":
                 if cal_row["is_break"]:
                     occ_count = np.random.randint(0, 50) # mostly empty
                     kw = base_kw + np.random.uniform(10, 30)
                 else:
                     # High occupancy at night
                     if hour < 8 or hour > 18:
                         occ_count = np.random.randint(b["capacity"]*0.7, b["capacity"])
                         kw = base_kw + (occ_count * 0.15) + np.random.uniform(40, 80)
                     else:
                         occ_count = np.random.randint(50, 200)
                         kw = base_kw + (occ_count * 0.15) + np.random.uniform(20, 40)

            energy_records.append({"timestamp": t, "power_kw": max(0, kw)})
            occupancy_records.append({"timestamp": t, "occupancy_count": occ_count})
            
        pd.DataFrame(energy_records).to_csv(os.path.join(DATA_DIR, "energy", f"{b['building_id']}.csv"), index=False)
        pd.DataFrame(occupancy_records).to_csv(os.path.join(DATA_DIR, "occupancy", f"{b['building_id']}.csv"), index=False)
        print(f"Generated mock data for {b['building_id']}")

    print("Mock I-BLEND dataset generation complete!")

if __name__ == "__main__":
    generate_mock_iblend_data()
