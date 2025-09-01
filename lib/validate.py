def validate(json_data, json_schema) -> dict:
    
    generate_models(json_schema)

    # Use pydantic to validate
    
    return {"success": True}

def generate_models(json_schema):
    # Generate pydantic models from json schema
    return