from pydantic import BaseModel, ValidationError
import json
import os

from models import HSDS_MODELS

def pick_model_to_validate(filename: str):
    """
    Returns (model_cls, model_name) picked from scanning file
    If none or multiple returns (None, error_message)
    """
    
    base = os.path.basename(filename) # File name
    file_name, file_type = os.path.splitext(base)
    norm_name = file_name.lower().replace("_", "") # Case sensitive file name

    matches = []

    # Loops through all HSDS Models in HSDS_MODELS.py
    for canonical, model in HSDS_MODELS.items():
        base_token = canonical.lower().replace("_", "") # Case sensitive model name
        candidate_tokens = {base_token}

        if any(token == norm_name for token in candidate_tokens): # If match, append to matches
            matches.append((canonical, model))

    if not matches: # If no matches, returns None and error message
        return None, f"No HSDS model name found in filename '{base}'."

    # If multiple models of the same name were found, returns error
    if len(matches) > 1:
        names = ", ".join(c for c, _ in matches)
        return None, (
            f"Ambiguous HSDS model in filename '{base}'. "
            f"Matched multiple models: {names}."
        )

    # Returns (class + name)
    canonical, model = matches[0]
    return model, canonical


def validate(json_data: dict, filename: str, json_schema: dict) -> dict:
    """
    Validate JSON data against a JSON schema using Pydantic.
    """
    # generate_models does not currently function
    # Include in generate_model the config to forbid extra fields

    # Verify model exists and is not multiple
    model_class, model_name = pick_model_to_validate(filename)
    if model_class is None:
        return {"success": False, "errors": [{"column": "<file>", "input": filename, "error": model_name}]}
    
    try:
        model_class.model_validate(json_data)
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