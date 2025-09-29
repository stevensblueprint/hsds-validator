import click
import os
import json
from lib.error_handling import validate_file_exists, validate_json_format, _validate_single_file
from lib.error_handling_classes import FileValidationError, ValidationErrorType
from lib.validate import validate as pyd_validate

SYSTEM_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
def is_system_file(filename):
    return (
        filename in SYSTEM_FILES or
        filename.startswith('._') or
        filename.startswith('.')
    )

def validate_json(ctx, param, value):
    """
    Checks end of file for .json
    If not applicable, throws BadParameter error
    If applicable, returns value to main function
    """
    # value is a file path (string) from click.Path(exists=True)
    if not value.lower().endswith(".json"):
        raise click.BadParameter("File must have a .json extension.")

    result = _validate_single_file(value, "schema")
    if not result.success:
        raise click.BadParameter(result.message)

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
@click.option(
    "-i",
    "--input_dir",
    type=click.Path(exists=True, file_okay=False),  # Type must be an existing directory
    required=True,  # Required
    help="Input valid directory path. Directory must not be empty.",
    callback=validate_directory
)
@click.option(
    "-j",
    "--json_schema",
    type=click.Path(exists=True),
    required=True,  # Required
    help="Input JSON schema path.",
    callback=validate_json,  # Calls JSON Validation function
)
@click.option(
    "-s", 
    "--save", 
    is_flag=True, # Boolean value
    help="Saves result to file.")


def main(input_dir, json_schema, save):
    click.echo(f"Directory: {input_dir}")
    click.echo(f"JSON schema: {json_schema}")
    click.echo(f"Save:  {save}")

    # Load the JSON schema (already validated by callback)
    with open(json_schema, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    aggregated_errors = []

    # Walk directory and validate each JSON file
    for root, dirs, files in os.walk(input_dir):
        for fname in files:
            if is_system_file(fname):
                continue
            if not fname.lower().endswith('.json'):
                continue

            file_path = os.path.join(root, fname)
            is_valid, error_message = validate_json_format(file_path)
            if not is_valid:
                err = FileValidationError(
                    ValidationErrorType.INVALID_JSON,
                    os.path.abspath(file_path),
                    f"Invalid JSON: {error_message}"
                )
                aggregated_errors.append(err.to_dict())
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            result = pyd_validate(data, schema)   # validate against pydantic model
            if not result.get("success", False):
                errors = result.get("errors", [])
                # Attach filename context to each error
                for err in errors:
                    if isinstance(err, dict):
                        err_with_file = {"file": os.path.abspath(file_path), **err}
                        aggregated_errors.append(err_with_file)
                    else:
                        aggregated_errors.append({"file": os.path.abspath(file_path), "error": str(err)})

    output = {"success": True }
    if aggregated_errors: # add errors & 'false' to the output
        output["errors"] = aggregated_errors
        output["success"] = False

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
