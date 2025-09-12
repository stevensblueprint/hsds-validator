from pydantic import BaseModel, ValidationError
import json

class User(BaseModel):
    id: int
    name: str
    email: str

def validate(json_data: dict, json_schema: dict) -> dict:
    
    model = generate_models(json_schema)
    json_data_str = json.dumps(json_data)
    
    try:
        model.model_validate_json(json_data_str)
    except ValidationError as e:
        error_dict = e.errors()
        err_message = []
        for error in error_dict:
            err_message.append({"column": error['loc'][0], "message": error['msg']})
        return {"success": False, "errors": err_message}
    
    return {"success": True}

def generate_models(json_schema) -> BaseModel:
    # Generate pydantic models from json schema
    return User