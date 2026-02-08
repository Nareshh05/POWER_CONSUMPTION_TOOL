import sys
import os
import json
import plotly.io as pio
from main.tmodel import thermal, renewable, stats

# Set up paths so imports work
sys.path.append(os.getcwd())

def validate_json_structure(name, json_str):
    print(f"\n--- Validating {name} ---")
    print(f"Type: {type(json_str)}")
    print(f"Length: {len(json_str)}")
    print(f"Preview: {json_str[:100]}...")
    
    try:
        data = json.loads(json_str)
        print("Status: Valid JSON")
        
        if 'data' in data:
            print(f"Contains 'data' key: Yes (Type: {type(data['data'])})")
            if len(data['data']) > 0:
                print("Data array is NOT empty.")
            else:
                print("Data array IS empty (Pre-fix behavior would crash here if it was just {})")
        else:
            print("Contains 'data' key: NO")
            
        if 'layout' in data:
            print("Contains 'layout' key: Yes")
        else:
            print("Contains 'layout' key: NO")
            
        return True
    except json.JSONDecodeError as e:
        print(f"Status: INVALID JSON - {e}")
        return False

if __name__ == "__main__":
    print("Running Integration Test for tmodel.py outputs...")
    
    # Test with a typical value (e.g., 5 years)
    val = 5
    
    print(f"\nCalling thermal({val})...")
    img1 = thermal(val)
    validate_json_structure("Thermal (img1)", img1)
    
    print(f"\nCalling renewable({val})...")
    img2 = renewable(val)
    validate_json_structure("Renewable (img2)", img2)
    
    print(f"\nCalling stats({val})...")
    img3, img4 = stats(val)
    validate_json_structure("Stats (img3 - Pie)", img3)
    validate_json_structure("Stats (img4 - Bar)", img4)
