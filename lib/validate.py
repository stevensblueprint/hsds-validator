from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Type
from dydantic import create_model_from_schema
from pydantic import BaseModel, ValidationError
import json
import os
from lib.models import HSDS_MODELS

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


def bulk_validate(json_data_list: List[Tuple[str, dict]], filename: str, json_schemas: List[dict]) -> List[dict]:
    """
    Generate a single model from the provided schemas and validate each JSON document
    in json_data_list against that model. Each item in json_data_list is a tuple of
    (filename, json_data). Returns a list of result dicts mirroring the single-item
    validate() output for each input, including the filename.
    """
    if not json_schemas:
        raise ValueError("No schemas provided")

    main_schema = detect_main_schema_by_filename(json_schemas, filename)
    pydantic_model = generate_models(main_schema, json_schemas)

    results: List[dict] = []
    for filename, json_data in json_data_list:
        result = validate(json_data, filename, pydantic_model)
        results.append(result)

    return results

def validate(json_data: dict, filename: str, model: Type[BaseModel]) -> dict:
    """
    Validate JSON data against a JSON schema using Pydantic.
    """
    try:
        model.model_validate(json_data)
        return {"filename": filename, "success": True}
    except ValidationError as e:
        error_dict = e.errors()
        err_message = []
        for error in error_dict:
            err_message.append({
                "column": ".".join(str(x) for x in error.get("loc", [])),
                "error": error.get("msg")
                # "input": error.get("input")
                
            })
        return {"filename": filename, "success": False, "errors": err_message}
    except Exception as e:
        # Catch-all for unexpected errors during validation
        return {"filename": filename, "success": False, "errors": [{"error": str(e)}]}

def detect_main_schema_by_filename(schemas: List[dict], filename: str) -> dict:
    """
    Detect the main schema by using the filename to determine which schema to use.
    This function relies entirely on pick_model_to_validate to determine the main schema.
    
    Args:
        schemas: List of schema dictionaries
        filename: The filename to use for schema selection
    
    Returns:
        The main schema that matches the model determined from the filename
        
    Raises:
        ValueError: If no schemas provided or no matching model found
    """
    if not schemas:
        raise ValueError("No schemas provided")
    
    if not filename:
        raise ValueError("Filename is required for schema selection")
    
    # Use pick_model_to_validate to determine which model to use
    model, model_name = pick_model_to_validate(filename)
    if model is None:
        raise ValueError(f"No matching model found for filename '{filename}'")
    
    # Find the schema that matches the selected model
    for schema in schemas:
        schema_name = get_schema_identifier(schema)
        if schema_name and schema_name.lower() == model_name.lower():
            print(f"Main schema selected based on filename '{filename}': {schema_name}")
            return schema
    
    # If we couldn't find a matching schema, raise an error
    schema_names = [get_schema_identifier(s) for s in schemas if get_schema_identifier(s)]
    raise ValueError(
        f"Could not find schema matching model '{model_name}'. "
        f"Available schemas: {schema_names}"
    )

def get_schema_identifier(schema: dict) -> str:
    """Get a unique identifier for a schema."""
    return schema.get('name')

def find_all_refs(obj) -> set:
    """Find all $ref references in a schema object."""
    refs = set()
    
    def extract_refs(item):
        if isinstance(item, dict):
            if '$ref' in item:
                refs.add(item['$ref'])
            for value in item.values():
                extract_refs(value)
        elif isinstance(item, list):
            for value in item:
                extract_refs(value)
    
    extract_refs(obj)
    return refs

def resolve_external_refs(main_schema: Dict[str, Any], all_schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve external $ref references in HSDS schemas."""
    
    # Create a lookup dictionary for schemas
    schema_lookup = {}
    schemas_with_extension = []
    
    for schema in all_schemas:
        schema_id = get_schema_identifier(schema)
        schema_lookup[schema_id] = schema
        
        # Also add filename with .json extension for flexible matching
        schema_lookup[f"{schema_id}.json"] = schema
        schemas_with_extension.append(f"{schema_id}.json")
    
    def resolve_refs(obj, visited_refs=None):
        # Initialize visited_refs on first call
        if visited_refs is None:
            visited_refs = set()
            
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                
                # Skip internal references (fragments)
                if ref_path.startswith("#"):
                    return obj
                
                # Check for circular reference
                if ref_path in visited_refs:
                    print(f"Warning: Circular reference detected for '{ref_path}'")
                    return {
                        "type": "object",
                        "additionalProperties": True,
                        "description": f"Circular reference: {ref_path}"
                    }
                
                # Look for the referenced schema
                ref_schema = None
                filename_only = Path(ref_path).name
                stem_only = Path(ref_path).stem
                
                # Try different lookup strategies
                for lookup_key in [ref_path, filename_only, stem_only]:
                    if lookup_key in schema_lookup:
                        ref_schema = schema_lookup[lookup_key]
                        break
                
                if ref_schema is None:
                    raise ValueError(
                        f"Could not resolve reference '{ref_path}'. "
                        f"Available schemas: {schemas_with_extension}"
                    )
                
                # Add current ref to visited set before recursing
                visited_refs.add(ref_path)
                
                # Recursively resolve the referenced schema
                resolved = resolve_refs(ref_schema, visited_refs)
                
                # Remove current ref from visited set after recursion
                visited_refs.remove(ref_path)
                
                return resolved
            
            # Recursively process all properties
            return {k: resolve_refs(v, visited_refs) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item, visited_refs) for item in obj]
        return obj
    
    return resolve_refs(main_schema)

def clean_hsds_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Remove HSDS-specific fields that aren't part of standard JSON Schema."""
    
    # HSDS metadata fields to remove from property definitions (not from properties object itself)
    hsds_metadata_fields = {"name", "title", "constraints", "example", "core", "order"}
    
    # Root-level HSDS fields to remove
    root_hsds_fields = {"path", "datapackage_metadata", "tabular_required"}
    
    def clean_properties(obj, is_root=False):
        if isinstance(obj, dict):
            cleaned = {}
            for k, v in obj.items():
                # At root level, remove root-specific HSDS fields
                if is_root and k in root_hsds_fields:
                    continue
                    
                # If we're inside a property definition (has 'type' key), remove metadata
                if isinstance(v, dict) and 'type' in v:
                    # This is a property definition - clean its metadata
                    property_cleaned = {
                        pk: pv for pk, pv in v.items() 
                        if pk not in hsds_metadata_fields
                    }
                    cleaned[k] = clean_properties(property_cleaned)
                else:
                    # Keep the key, recursively clean the value
                    cleaned[k] = clean_properties(v)
            
            return cleaned
        elif isinstance(obj, list):
            return [clean_properties(item) for item in obj]
        return obj
    
    return clean_properties(schema, is_root=True)

def generate_models(main_schema: Dict[str, Any], all_schemas: List[Dict[str, Any]]) -> Type[BaseModel]:
    """
    Generate Pydantic models from HSDS JSON schemas.
    Handles HSDS-specific issues and constraints.
    """
    try:
        # Step 1: Resolve external references
        resolved_schema = resolve_external_refs(main_schema, all_schemas)

        # Step 2: Clean HSDS-specific fields
        cleaned_schema = clean_hsds_schema(resolved_schema)
        
        # Step 3: Create the model using dydantic
        model_class = create_model_from_schema(
            cleaned_schema,
            __config__={
                "extra": "forbid",  # Don't allow extra fields
                "validate_assignment": True,  # Validate on assignment
                "use_enum_values": True,  # Use enum values
            }
        )
        
        # Create models directory
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        
        # Save schema to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(cleaned_schema, temp_file, indent=2)
            temp_schema_path = temp_file.name
            
        filename = get_schema_identifier(main_schema) + ".py"
        
        # Generate Python code using datamodel-code-generator
        output_file = models_dir / filename
        subprocess.run([
            'datamodel-codegen',
            '--input', temp_schema_path,
            '--input-file-type', 'jsonschema',
            '--output', str(output_file)
        ], check=True)
        
        # Clean up temporary file
        Path(temp_schema_path).unlink()
        
        print(f"Generated Pydantic models saved to {output_file}")
            
        return model_class
        
    except Exception as e:
        raise Exception(f"Model generation failed: {e}")
