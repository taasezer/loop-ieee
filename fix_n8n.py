import os
import glob
import json

def fix_n8n_files():
    workflows_dir = os.path.join("n8n", "workflows")
    json_files = glob.glob(os.path.join(workflows_dir, "*.json"))
    
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # N8n v1+ requires "jsCode" instead of "functionCode"
        if '"functionCode":' in content:
            content = content.replace('"functionCode":', '"jsCode":')
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed: {os.path.basename(file_path)}")
        else:
            print(f"⏩ Already okay: {os.path.basename(file_path)}")

if __name__ == "__main__":
    fix_n8n_files()
