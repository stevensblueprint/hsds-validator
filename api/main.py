from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import json
import zipfile
import io
from jsonschema import validate as js_validate, ValidationError
import os
from lib.error_handling_classes import ValidationResult, ValidationErrorType, FileValidationError
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
      raise HTTPException(status_code=400, detail="ZIP file is required")
  
   if not json_schema:
      raise HTTPException(status_code=400, detail="JSON schema is required")
   
   # Validate that uploaded file is a ZIP
   if not input_dir.filename.lower().endswith('.zip'):
      raise HTTPException(status_code=400, detail="Uploaded input_dir file must be a ZIP file")
   
   try:
      schema_content = json_schema.file.read()
      if not schema_content or len(schema_content) == 0:
         result = ValidationResult.error_result(
            ValidationErrorType.FILE_EMPTY,
            json_schema.filename,
            "Schema file is empty"
         )
         return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
      schema_path = f"/tmp/{json_schema.filename}"
      with open(schema_path, 'wb') as f:
         f.write(schema_content)
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
   except Exception as e:
      result = ValidationResult.error_result(
        ValidationErrorType.UNKNOWN_ERROR,
        json_schema.filename,
        str(e)
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}

   # Unzip files and validate
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
               file_path = f"/tmp/{os.path.basename(fname)}"
               with z.open(fname) as f_in, open(file_path, 'wb') as f_out:
                  f_out.write(f_in.read())
               is_valid, error_message = validate_json_format(file_path)
               if not is_valid:
                  raise FileValidationError(
                     ValidationErrorType.INVALID_JSON,
                     fname,
                     error_message
                  )
               with open(file_path, 'r', encoding='utf-8') as f:
                  data = json.load(f)
                  try:
                     js_validate(instance=data, schema=schema)
                  except ValidationError as ve:
                     raise FileValidationError(
                        ValidationErrorType.INVALID_JSON,
                        fname,
                        str(ve)
                     )
               os.remove(file_path)
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
               errors.append(f"{result.filepath}: {result.error_type.value}")
         if errors:
            return {"success": False, "errors": errors}
         result = ValidationResult.success_result()
         return result.to_dict()
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
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}

def main():
   uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
   main()
