import click
import os
import json
from lib.error_handling import validate_file_exists, validate_json_format
from lib.error_handling_classes import FileValidationError, ValidationErrorType
from lib.validate import bulk_validate

SYSTEM_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}

def is_system_file(filename):
    """Check if a file is a system file (matches API behavior)"""
    return (
        filename in SYSTEM_FILES or
        filename.startswith('._') or
        filename.startswith('.') or
        filename.startswith('__MACOSX/') or
        '/.DS_Store' in filename or
        '/._' in filename or
        '/Thumbs.db' in filename or
        '/desktop.ini' in filename or
        filename.endswith('.DS_Store') or
        filename.endswith('Thumbs.db') or
        filename.endswith('desktop.ini')
    )

def validate_schema_directory(ctx, param, value):
    """
    Checks directory for at least one JSON schema file
    Raises BadParameter error if:
    - Directory not found or empty
    - No JSON schema files found
    """
    # Check if directory exists
    if not validate_file_exists(value):
        raise click.BadParameter(f"Directory not found: {value}")
    
    # Check if directory is not empty
    try:
        if not os.listdir(value):
            raise click.BadParameter(f"Directory is empty: {value}")
    except Exception as e:
        raise click.BadParameter(f"Error accessing directory: {value} ({str(e)})")
    
    # Check for at least one JSON file (non-JSON files will be handled in main())
    has_json = False
    for root, dirs, files in os.walk(value):
        for f in files:
            if is_system_file(f):
                continue
            if f.lower().endswith('.json'):
                has_json = True
                break
        if has_json:
            break
    
    if not has_json:
        raise click.BadParameter(f"No JSON schema files found in directory: {value}")
    
    return value

def validate_directory(ctx, param, value):
    """
    Checks directory for at least one file inside
    If not applicable, throws BadParameter error
    If applicable, returns value to main function
    """
    # Check if directory exists
    if not validate_file_exists(value):
        raise click.BadParameter(f"Directory not found: {value}")
    
    # Check if directory is not empty
    try:
        if not os.listdir(value):
            raise click.BadParameter(f"Directory is empty: {value}")
    except Exception as e:
        raise click.BadParameter(f"Error accessing directory: {value} ({str(e)})")
    
    # Check for valid filepaths
    for root, dirs, files in os.walk(value):
        # Check nested dirs
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not validate_file_exists(dir_path) or not os.listdir(dir_path):
                raise click.BadParameter(f"Nested directory is empty: {os.path.abspath(dir_path)}")
        
        for f in files:
            if is_system_file(f):
                continue
            file_path = os.path.join(root, f)

            if not os.path.isfile(file_path):
                raise click.BadParameter(f"Expected file but found something else: {os.path.abspath(file_path)}")
    return value

# CLI Command Line Arguments
@click.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False),
    callback=validate_directory
)
@click.argument(
    "schema_dir",
    type=click.Path(exists=True, file_okay=False),
    callback=validate_schema_directory
)
@click.option(
    "-o", 
    "--save", 
    is_flag=True,
    help="Saves result to file.")


def main(input_dir, schema_dir, save):
    click.echo(f"Input directory: {input_dir}")
    click.echo(f"Schema directory: {schema_dir}")
    click.echo(f"Save:  {save}")

    # Load all JSON schemas from the schema directory
    schemas = []
    schema_errors = []
    for root, dirs, files in os.walk(schema_dir):
        for fname in files:
            if is_system_file(fname):
                continue
            
            # Check if file is JSON, if not, add error and continue (matching API behavior)
            if not fname.lower().endswith('.json'):
                schema_path = os.path.join(root, fname)
                err = FileValidationError(
                    ValidationErrorType.INVALID_JSON,
                    os.path.abspath(schema_path),
                    "Not a JSON file"
                )
                schema_errors.append(err.to_dict())
                continue
            
            schema_path = os.path.join(root, fname)
            is_valid, error_message = validate_json_format(schema_path)
            if not is_valid:
                err = FileValidationError(
                    ValidationErrorType.INVALID_JSON,
                    os.path.abspath(schema_path),
                    f"Invalid JSON schema: {error_message}"
                )
                schema_errors.append(err.to_dict())
                continue
            
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    schemas.append(schema_data)
            except Exception as e:
                err = FileValidationError(
                    ValidationErrorType.FILE_ACCESS_ERROR,
                    os.path.abspath(schema_path),
                    f"Error loading schema: {str(e)}"
                )
                schema_errors.append(err.to_dict())

    if schema_errors:
        output = {"success": False, "errors": schema_errors}
        click.echo(json.dumps(output, indent=2))
        return

    if not schemas:
        output = {"success": False, "errors": [{"error": "No valid JSON schemas found in schema directory"}]}
        click.echo(json.dumps(output, indent=2))
        return

    # Collect all JSON files from input directory
    input_data_list = []  # List of (filename, json_data) tuples
    input_errors = []

    # Walk directory and collect each JSON file
    for root, dirs, files in os.walk(input_dir):
        for fname in files:
            if is_system_file(fname):
                continue
            
            # Check if file is JSON, if not, add error and continue (matching API behavior)
            if not fname.lower().endswith('.json'):
                file_path = os.path.join(root, fname)
                err = FileValidationError(
                    ValidationErrorType.INVALID_JSON,
                    os.path.abspath(file_path),
                    "Not a JSON file"
                )
                input_errors.append(err.to_dict())
                continue

            file_path = os.path.join(root, fname)
            is_valid, error_message = validate_json_format(file_path)
            if not is_valid:
                err = FileValidationError(
                    ValidationErrorType.INVALID_JSON,
                    os.path.abspath(file_path),
                    f"Invalid JSON: {error_message}"
                )
                input_errors.append(err.to_dict())
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Use just the filename (not full path) for model detection
                    input_data_list.append((fname, data))
            except Exception as e:
                err = FileValidationError(
                    ValidationErrorType.FILE_ACCESS_ERROR,
                    os.path.abspath(file_path),
                    f"Error loading file: {str(e)}"
                )
                input_errors.append(err.to_dict())

    if input_errors:
        output = {"success": False, "errors": input_errors}
        click.echo(json.dumps(output, indent=2))
        return

    if not input_data_list:
        output = {"success": False, "errors": [{"error": "No valid JSON files found in input directory"}]}
        click.echo(json.dumps(output, indent=2))
        return

    # Use bulk_validate to validate all files
    # Use the input directory name for schema detection (matching API behavior with ZIP filename)
    dir_basename = os.path.basename(os.path.normpath(input_dir))
    
    try:
        results = bulk_validate(input_data_list, dir_basename, schemas)
        
        # Process results to create output format matching API
        successful_files = []
        failed_files = []
        all_errors = []
        
        for result in results:
            filename = result.get("filename", "unknown")
            if result.get("success", False):
                successful_files.append(filename)
            else:
                failed_files.append(filename)
                all_errors.append({"filename": filename, "errors": result.get("errors", [])})
        
        # Return summary with success status, file lists, errors (matching API format)
        output = {
            "success": len(failed_files) == 0,
            "summary": {
                "total_files": len(results),
                "successful": len(successful_files),
                "failed": len(failed_files)
            },
            "successful_files": successful_files,
            "failed_files": failed_files,
            "errors": all_errors,
        }
        
    except Exception as e:
        output = {"success": False, "errors": [{"error": f"Validation failed: {str(e)}"}]}

    click.echo(json.dumps(output, indent=2))

    if save:
        out_path = os.path.join(input_dir, "validation_results.json")
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)
            click.echo(f"Saved results to: {os.path.abspath(out_path)}")
        except Exception as e:
            click.echo(f"Failed to save results: {str(e)}")

if __name__ == "__main__":
    main()
