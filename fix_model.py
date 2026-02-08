import sys
import os

file_path = 'main/model.py'
if not os.path.exists(file_path):
    print(f"File {file_path} not found")
    sys.exit(1)

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # This is a bit hacky but should work if we match the exact line content
    if 'weather_data.reset_index(inplace=True)' in line:
        indent = line[:line.find('weather_data')]
        new_lines.append(f"{indent}if weather_data is not None and not weather_data.empty:\n")
        new_lines.append(f"{indent}    weather_data.reset_index(inplace=True)\n")
        # We need to wrap the next two lines as well
        # future = future.merge...
        # future.drop...
        continue
    
    if 'future = future.merge(weather_data' in line and i > 0 and 'if weather_data is not None' in new_lines[-2]:
         indent = line[:line.find('future')]
         new_lines.append(f"{indent}    " + line.lstrip())
         continue

    if 'future.drop(columns=[\'time\']' in line and i > 0 and 'future = future.merge' in new_lines[-1]:
         indent = line[:line.find('future')]
         new_lines.append(f"{indent}    " + line.lstrip())
         continue

    if 'future[\'tavg\'] = future[\'tavg\'].fillna' in line:
        indent = line[:line.find('future')]
        # This replaces the fillna part
        new_lines.append(f"{indent}if 'tavg' not in future.columns:\n")
        new_lines.append(f"{indent}    future['tavg'] = delhi['tavg'].mean()\n")
        new_lines.append(f"{indent}else:\n")
        new_lines.append(f"{indent}    future['tavg'] = future['tavg'].fillna(delhi['tavg'].mean())\n")
        continue

    new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("Successfully patched model.py")
