from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Type
from dydantic import create_model_from_schema
from pydantic import BaseModel, ValidationError
import json

from lib.models import Organization

def bulk_validate(json_data_list: List[Tuple[str, dict]], json_schemas: List[dict]) -> List[dict]:
    """
    Generate a single model from the provided schemas and validate each JSON document
    in json_data_list against that model. Each item in json_data_list is a tuple of
    (filename, json_data). Returns a list of result dicts mirroring the single-item
    validate() output for each input, including the filename.
    """
    if not json_schemas:
        raise ValueError("No schemas provided")

    main_schema = detect_main_schema_by_references(json_schemas)
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
    json_data_str = json.dumps(json_data)
    try:
        model.model_validate_json(json_data_str)
        return {"filename": filename, "success": True}
    except ValidationError as e:
        error_dict = e.errors()
        err_message = []
        for error in error_dict:
            err_message.append({
                "column": ".".join(str(x) for x in error.get("loc", [])),
                "input": error.get("input"),
                "error": error.get("msg")
            })
        return {"filename": filename, "success": False, "errors": err_message}
    except Exception as e:
        # Catch-all for unexpected errors during validation
        return {"filename": filename, "success": False, "errors": [{"error": str(e)}]}

def detect_main_schema_by_references(schemas: List[dict]) -> dict:
    """
    Detect the main schema by finding schemas that are NOT referenced by others.
    Raises an error if multiple unreferenced schemas are found.
    
    Args:
        schemas: List of schema dictionaries
    
    Returns:
        The main schema (not referenced by others)
        
    Raises:
        ValueError: If no schemas or multiple unreferenced schemas found
    """
    if not schemas:
        raise ValueError("No schemas provided")
    
    if len(schemas) == 1:
        return schemas[0]
    
    # Find all external references across all schemas
    referenced_ids = set()
    schema_lookup = {}
    
    for schema in schemas:
        schema_id = get_schema_identifier(schema)
        schema_lookup[schema_id] = schema
        
        # Find all $ref references in this schema
        refs = find_all_refs(schema)
        for ref in refs:
            if not ref.startswith("#"):  # External ref only
                referenced_ids.add(ref)
                # Also add filename variations for flexible matching
                referenced_ids.add(Path(ref).name)
    
    # Find schemas that are not referenced by others
    unreferenced_schemas = []
    for schema in schemas:
        schema_id = get_schema_identifier(schema)
        
        # Check if this schema is referenced
        is_referenced = (
            schema_id in referenced_ids or 
            f"{schema_id}.json" in referenced_ids    # Add .json to schema_id
        )
        
        if not is_referenced:
            unreferenced_schemas.append(schema)
    
    if len(unreferenced_schemas) == 0:
        raise ValueError(
            "No main schema found: all schemas are referenced by others. "
            "This suggests a circular reference or missing main schema."
        )
    
    if len(unreferenced_schemas) > 1:
        schema_ids = [get_schema_identifier(s) for s in unreferenced_schemas]
        raise ValueError(
            f"Multiple potential main schemas found: {schema_ids}. "
            "Cannot determine which schema is the main one. "
            "Please ensure only one schema is not referenced by others."
        )
    
    print(f"Main schema detected: {get_schema_identifier(unreferenced_schemas[0])}")
    return unreferenced_schemas[0]

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
    
    def clean_properties(obj):
        if isinstance(obj, dict):
            # Remove HSDS-specific fields
            hsds_fields = {"core", "name", "datapackage_metadata", "example", "order"}
            cleaned = {k: v for k, v in obj.items() if k not in hsds_fields}
            
            # Handle constraints field - convert to JSON Schema equivalents where possible
            if "constraints" in obj:
                constraints = obj["constraints"]
                if isinstance(constraints, dict):
                    # Remove constraints as it's not standard JSON Schema
                    pass
            
            return {k: clean_properties(v) if isinstance(v, (dict, list)) else v for k, v in cleaned.items()}
        elif isinstance(obj, list):
            return [clean_properties(item) for item in obj]
        return obj
    
    return clean_properties(schema)

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
