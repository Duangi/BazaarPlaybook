import onnxruntime
import json

model_path = "assets/models/yolo11m/best.onnx"

try:
    session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    meta = session.get_modelmeta()
    custom_metadata_map = meta.custom_metadata_map
    print("Metadata keys:", custom_metadata_map.keys())
    
    if "names" in custom_metadata_map:
        print("Classes found in metadata:")
        print(custom_metadata_map["names"])
    else:
        print("No 'names' found in metadata.")

    print(f"Description: {custom_metadata_map.get('description', 'N/A')}")
    print(f"Author: {custom_metadata_map.get('author', 'N/A')}")
    print(f"Version: {custom_metadata_map.get('version', 'N/A')}")
        
except Exception as e:
    print(f"Error: {e}")
