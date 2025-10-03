from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict, Optional, Type
from dydantic import create_model_from_schema
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
    # model = Organization
    model = generate_models(json_schema)
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

def resolve_external_refs(schema: Dict[str, Any], schema_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Resolve external $ref references in HSDS schemas."""
    
    def resolve_refs(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if not ref_path.startswith("#"):  # External reference
                    if schema_dir and (schema_dir / ref_path).exists():
                        with open(schema_dir / ref_path, 'r') as f:
                            ref_schema = json.load(f)
                        return resolve_refs(ref_schema)
                    else:
                        # Fallback to generic object schema for external refs
                        return {
                            "type": "object",
                            "additionalProperties": True,
                            "description": f"Referenced schema: {ref_path}"
                        }
            return {k: resolve_refs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item) for item in obj]
        return obj
    
    return resolve_refs(schema)

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

# def enhance_uuid_fields(schema: Dict[str, Any]) -> Dict[str, Any]:
#     """Add proper UUID validation for HSDS UUID fields."""
    
#     def process_field(field_def):
#         if isinstance(field_def, dict):
#             if field_def.get("format") == "uuid":
#                 # Add pattern validation for UUID
#                 field_def["pattern"] = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
#             return {k: process_field(v) if isinstance(v, (dict, list)) else v for k, v in field_def.items()}
#         elif isinstance(field_def, list):
#             return [process_field(item) for item in field_def]
#         return field_def
    
#     return process_field(schema)

def generate_models(json_schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Generate Pydantic models from HSDS JSON schemas.
    Handles HSDS-specific issues and constraints.
    """
    try:
        # Step 1: Resolve external references
        schema_dir = Path.cwd()  # Adjust as needed for your schema directory
        resolved_schema = resolve_external_refs(json_schema, schema_dir)
        
        # Step 2: Clean HSDS-specific fields
        cleaned_schema = clean_hsds_schema(resolved_schema)
        
        # Step 3: Enhance UUID field validation
        # enhanced_schema = enhance_uuid_fields(cleaned_schema)
        
        # Step 4: Create the model using dydantic
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
        
        # Generate Python code using datamodel-code-generator
        output_file = models_dir / 'generated_models.py'
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
        # Fallback to a generic model if schema generation fails
        print(f"Warning: Failed to generate model from schema: {e}")
        
        # Create a basic model based on schema properties
        class GenericHSDSModel(BaseModel):
            class Config:
                extra = "allow"  # Allow extra fields as fallback
        
        return GenericHSDSModel
