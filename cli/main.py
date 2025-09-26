import click
import os
from lib.error_handling import validate_file_exists, validate_file_not_empty, validate_json_format


SYSTEM_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
def is_system_file(filename):
    return (
        filename in SYSTEM_FILES or
        filename.startswith('._') or
        filename.startswith('.')
    )

def validate_json(ctx, param, value):
    """
    Validates that the file exists, is not empty, and is valid JSON
    """
    name = getattr(value, "name", "")
    if not name.lower().endswith(".json"):
        raise click.BadParameter("File must have a .json extension.")
    # Check file exists
    if not validate_file_exists(name):
        raise click.BadParameter(f"File not found: {name}")
    # Check file not empty
    try:
        if not validate_file_not_empty(name):
            raise click.BadParameter(f"File is empty: {name}")
    except Exception as e:
        raise click.BadParameter(f"Error accessing file: {name} ({str(e)})")
    # Check valid JSON
    is_valid, error_message = validate_json_format(name)
    if not is_valid:
        raise click.BadParameter(f"Invalid JSON: {error_message}")
    return value

def validate_directory(ctx, param, value):
    """
    Validates that the directory exists, is not empty, and contains only .json files (while ignoring system files).
    """
    if not os.path.isdir(value):
        raise click.BadParameter(f"Directory not found: {value}")
    files = os.listdir(value)
    if not files:
        raise click.BadParameter(f"Directory is empty: {value}")
    for f in files:
        if is_system_file(f) or os.path.isdir(os.path.join(value, f)): #skipping over system files and directories
            continue
        if not f.lower().endswith('.json'):
            raise click.BadParameter(f"Directory contains a non-JSON file: {f}")
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
    type=click.File("r"),
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

    # JSON validation and File IO

if __name__ == "__main__":
    main()
