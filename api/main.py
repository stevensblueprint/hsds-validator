from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import json
import zipfile
import io
import os
import tempfile
from lib.error_handling_classes import ValidationResult, ValidationErrorType, FileValidationError
from lib.validate import validate as pyd_validate
from lib.error_handling import validate_json_format

app = FastAPI()


@app.get("/health")
def health():
   return {"ok": True}


@app.post("/validate")
def validate(
   input_dir: UploadFile = File(..., description="ZIP file containing the files to be validated"),
   json_schema: UploadFile = File(..., description="JSON schema to validate against")
):
   """
   Endpoint that validates files in a ZIP archive against a JSON schema
  
   Args:
       input_dir: ZIP file containing the files to be validated
       json_schema: JSON schema to validate against
  
   Returns:
       JSON response with validation results
   """

   # Basic input validation
   if not input_dir:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_NOT_FOUND,
         "input_dir",
         "ZIP file is required"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
  
   if not json_schema:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_NOT_FOUND,
         "json_schema",
         "JSON schema is required"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
   
   # Validate that uploaded file is a ZIP
   if not input_dir.filename.lower().endswith('.zip'):
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_ACCESS_ERROR,
         input_dir.filename,
         "Invalid ZIP file"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
     
   try:
      schema_content = json_schema.file.read()
      if not schema_content or len(schema_content) == 0:
         result = ValidationResult.error_result(
            ValidationErrorType.FILE_EMPTY,
            json_schema.filename,
            "Schema file is empty"
         )
         return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
      
      # Use NamedTemporaryFile for cross-platform compatibility
      with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
         temp_file.write(schema_content)
         schema_path = temp_file.name
      
      try:
         is_valid, error_message = validate_json_format(schema_path)
         if not is_valid:
            result = ValidationResult.error_result(
               ValidationErrorType.INVALID_JSON,
               json_schema.filename,
               error_message
            )
            return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
         with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
      finally:
         # Clean up the temporary file
         try:
            os.unlink(schema_path)
         except OSError:
            pass  # Ignore cleanup errors
   except Exception as e:
      result = ValidationResult.error_result(
        ValidationErrorType.UNKNOWN_ERROR,
        json_schema.filename,
        str(e)
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value} - {result.message}"]}

   # Unzip files and validate
   input_dir_data = []  # array to store file contents as dicts 
   try:
      zip_bytes = input_dir.file.read()
      with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
         file_list = z.namelist()
         if not file_list:
            result = ValidationResult.error_result(
               ValidationErrorType.FILE_EMPTY,
               input_dir.filename,
               "ZIP file is empty"
            )
            return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
         errors = []
         for fname in file_list:
            if fname.endswith('/'):
               continue
            # skip system files
            if (fname.startswith('__MACOSX/') or fname.endswith('.DS_Store') or fname.startswith('.') or '/.DS_Store' in fname or '/._' in fname or fname.endswith('Thumbs.db') or fname.endswith('desktop.ini') or '/Thumbs.db' in fname or '/desktop.ini' in fname):
               continue
            if not fname.endswith('.json'):
               result = ValidationResult.error_result(
                  ValidationErrorType.INVALID_JSON,
                  fname,
                  "Not a JSON file"
               )
               errors.append(f"{result.filepath}: {result.error_type.value}")
               continue
            try:
               # Use NamedTemporaryFile for cross-platform compatibility
               with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
                  with z.open(fname) as f_in:
                     temp_file.write(f_in.read())
                  file_path = temp_file.name
               
               try:
                  is_valid, error_message = validate_json_format(file_path)
                  if not is_valid:
                     raise FileValidationError(
                        ValidationErrorType.INVALID_JSON,
                        fname,
                        error_message
                     )
                  with open(file_path, 'r', encoding='utf-8') as f:
                     data = json.load(f)
                     input_dir_data.append(data)
               finally:
                  # Clean up the temporary file
                  try:
                     os.unlink(file_path)
                  except OSError:
                     pass  # Ignore cleanup errors
            except FileValidationError as ve:
               result = ValidationResult.error_result(
                  ve.error_type,
                  ve.filepath,
                  ve.message,
                  ve.details
               )
               errors.append(f"{result.filepath}: {result.error_type.value}")
            except Exception as e:
               result = ValidationResult.error_result(
                  ValidationErrorType.UNKNOWN_ERROR,
                  fname,
                  str(e)
               )
               errors.append(f"{result.filepath}: {result.error_type.value} - {result.message}")
         if errors:
            return {"success": False, "errors": errors}
   except zipfile.BadZipFile:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_ACCESS_ERROR,
         input_dir.filename,
         "Invalid ZIP file"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
   except Exception as e:
      result = ValidationResult.error_result(
         ValidationErrorType.UNKNOWN_ERROR,
         input_dir.filename if input_dir else "unknown",
         str(e)
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value} - {result.message}"]}
   
   # Validate each JSON object against the provided schema using lib.validate
   aggregated_errors = []
   for json_obj in input_dir_data:
      result = pyd_validate(json_obj, schema)
      if not result.get("success", False):
         aggregated_errors.extend(result.get("errors", [])) # add to errors list if validation fails

   if aggregated_errors:
      return {"success": False, "errors": aggregated_errors }

   return {"success": True}

def main():
   uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
   main()
