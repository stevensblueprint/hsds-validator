import os
import json
from pathlib import Path
from typing import Tuple, Dict, Any, List
from .models import ValidationResult, ValidationErrorType, FileValidationError

def validate_file_exists(filepath: str) -> bool:
    """
    Check if a file exists at the given path.
    
    Args:
        filepath (str): Path to the file to check
        
    Returns:
        bool: True if file exists, False otherwise
    """
    return os.path.exists(filepath)

def validate_file_not_empty(filepath: str) -> bool:
    """
    Check if a file has content (not empty).
    
    A file is considered "empty" if it contains only:
    - Empty JSON objects: {}
    - Empty JSON arrays: []
    - Whitespace around empty JSON structures
    
    Args:
        filepath (str): Path to the file to check
        
    Returns:
        bool: True if file has content, False if empty
        
    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If there's an error accessing the file
    """
    try:
        # First check if file has any content at all
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return False
            
        # Read and parse the JSON to check if it's "meaningfully empty"
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            
        # Check if content is empty after stripping whitespace
        if not content:
            return False
            
        # Try to parse as JSON
        try:
            parsed_data = json.loads(content)
            
            # Check if it's an empty object or array
            if parsed_data == {} or parsed_data == []:
                return False
                
            # If it's a dict or list, check if it has any meaningful content
            if isinstance(parsed_data, dict):
                return len(parsed_data) > 0
            elif isinstance(parsed_data, list):
                return len(parsed_data) > 0
            else:
                # Other types (string, number, boolean, null) are considered content
                return True
                
        except json.JSONDecodeError:
            # If it's not valid JSON, consider it as having content
            return True
            
    except (FileNotFoundError, OSError) as e:
        raise e

def validate_json_format(filepath: str) -> Tuple[bool, str]:
    """
    Check if a file contains valid JSON syntax.
    
    Args:
        filepath (str): Path to the file to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
            - (True, "") if valid JSON
            - (False, "error message") if invalid JSON or file error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            json.load(file)
        return True, ""
    except FileNotFoundError:
        return False, f"File not found: {filepath}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}"
    except UnicodeDecodeError as e:
        return False, f"File encoding error: {e.reason}"
    except OSError as e:
        return False, f"File access error: {e.strerror}"
    except Exception as e:
        return False, f"Unexpected error reading file: {str(e)}"

def read_json_file(filepath: str) -> Dict[str, Any]:
    """
    Safely read and parse a JSON file.
    
    Args:
        filepath (str): Path to the JSON file to read
        
    Returns:
        Dict[str, Any]: Parsed JSON data as a dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        OSError: If there's an error accessing the file
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}", e.doc, e.pos)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"File encoding error: {e.reason}")
    except OSError as e:
        raise OSError(f"File access error: {e.strerror}")

def validate_files(input_filepath: str, schema_filepath: str) -> ValidationResult:
    """
    Validate input and schema files to ensure they are non-empty JSON files.
    
    This function performs the required pre-validation steps:
    1. Validates that both files exist and are non-empty JSON files
    2. Reads and parses the JSON data into a format ready for Pydantic
    
    Args:
        input_filepath (str): Path to the input JSON file to validate
        schema_filepath (str): Path to the JSON schema file
        
    Returns:
        ValidationResult: Structured result with success/error information
    """
    try:
        # Step 1: Validate input file
        input_result = _validate_single_file(input_filepath, "input")
        if not input_result.success:
            return input_result
            
        # Step 2: Validate schema file
        schema_result = _validate_single_file(schema_filepath, "schema")
        if not schema_result.success:
            return schema_result
            
        # Step 3: Read the validated files into Pydantic-ready format
        try:
            input_data = read_json_file(input_filepath)
            schema_data = read_json_file(schema_filepath)
        except Exception as e:
            return ValidationResult.error_result(
                ValidationErrorType.UNKNOWN_ERROR,
                input_filepath,
                f"Failed to read validated files: {str(e)}"
            )
            
        # Return success with the parsed data ready for Pydantic validation
        return ValidationResult.success_result({
            "input_data": input_data,
            "schema_data": schema_data,
            "message": "Files validated successfully and ready for Pydantic validation"
        })
            
    except Exception as e:
        return ValidationResult.error_result(
            ValidationErrorType.UNKNOWN_ERROR,
            input_filepath,
            f"Unexpected error during file validation: {str(e)}"
        )

def _validate_single_file(filepath: str, file_type: str) -> ValidationResult:
    """
    Validate a single file for existence, content, and JSON format.
    
    Args:
        filepath (str): Path to the file to validate
        file_type (str): Type of file ("input" or "schema") for error messages
        
    Returns:
        ValidationResult: Result of the file validation
    """
    # Check if file exists
    if not validate_file_exists(filepath):
        return ValidationResult.error_result(
            ValidationErrorType.FILE_NOT_FOUND,
            filepath,
            f"{file_type.capitalize()} file not found"
        )
    
    # Check if file is not empty
    try:
        if not validate_file_not_empty(filepath):
            return ValidationResult.error_result(
                ValidationErrorType.FILE_EMPTY,
                filepath,
                f"{file_type.capitalize()} file is empty"
            )
    except FileNotFoundError:
        return ValidationResult.error_result(
            ValidationErrorType.FILE_NOT_FOUND,
            filepath,
            f"{file_type.capitalize()} file not found"
        )
    except OSError as e:
        return ValidationResult.error_result(
            ValidationErrorType.FILE_ACCESS_ERROR,
            filepath,
            f"Cannot access {file_type} file: {e.strerror}"
        )
    
    # Check if file contains valid JSON
    is_valid_json, error_message = validate_json_format(filepath)
    if not is_valid_json:
        # Determine error type based on error message
        if "File not found" in error_message:
            error_type = ValidationErrorType.FILE_NOT_FOUND
        elif "encoding" in error_message.lower():
            error_type = ValidationErrorType.ENCODING_ERROR
        elif "JSON syntax" in error_message:
            error_type = ValidationErrorType.INVALID_JSON
        else:
            error_type = ValidationErrorType.JSON_PARSE_ERROR
            
        return ValidationResult.error_result(
            error_type,
            filepath,
            f"Invalid {file_type} file: {error_message}"
        )
    
    # All validations passed
    return ValidationResult.success_result()

def validate(json_data, json_schema) -> dict:
    
    generate_models(json_schema)

    # Use pydantic to validate
    
    return {"success": True}

def generate_models(json_schema):
    # Generate pydantic models from json schema
