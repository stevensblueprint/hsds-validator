from pydantic import BaseModel, ValidationError
import json

from lib.models import Organization

def validate(json_data: dict, json_schema: dict) -> dict:
    """
    Validate JSON data against a JSON schema using Pydantic.
    """
    # generate_models does not currently function
    # Include in generate_model the config to forbid extra fields
    # For now, we will directly use the Organization model
    model = Organization
    json_data_str = json.dumps(json_data)
    
    
    try:
        model.model_validate_json(json_data_str)
    except ValidationError as e:
        error_dict = e.errors()
        err_message = []
        for error in error_dict:
            err_message.append({"column": ".".join(str(x) for x in error['loc']), "input": error['input'], "error": error['msg']})
        return {"success": False, "errors": err_message}
    
    return {"success": True}

def generate_models(json_schema) -> BaseModel:
    # Generate pydantic models from json schema
    # Will return a file containing the models
    pass