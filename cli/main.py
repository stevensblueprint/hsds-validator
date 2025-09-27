import click
import os
from lib.error_handling import validate_files, validate_file_exists, validate_file_not_empty, validate_json_format, _validate_single_file
from lib.error_handling_classes import ValidationResult

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
    name = getattr(value, "name", "")
    if not name.lower().endswith(".json"):
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
    
    # Check for .json files recursively (ignoring system files) and validate JSON format
    found_json = False
    for root, dirs, files in os.walk(value):
        for f in files:
            if is_system_file(f):
                continue
            if f.lower().endswith('.json'):
                found_json = True
                file_path = os.path.join(root, f)
                is_valid, error_message = validate_json_format(file_path)
                if not is_valid:
                    raise click.BadParameter(f"Invalid JSON file: {os.path.abspath(file_path)} - {error_message}")

    if not found_json:
        raise click.BadParameter(
            f"Directory (including subdirectories) contains no JSON files: {os.path.abspath(value)}"
        )
    
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

    print("Hello from the HSDS Validator!")

    # No errors at this point means both args are valid filepaths that are not empty, and hold the correct file types



if __name__ == "__main__":
    main()
