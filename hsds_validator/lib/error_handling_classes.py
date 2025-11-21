from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

# Error Handling Classes for File Validation

class ValidationErrorType(str, Enum):
    """Enumeration of possible validation error types."""
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_EMPTY = "FILE_EMPTY"
    INVALID_JSON = "INVALID_JSON"
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    FILE_ACCESS_ERROR = "FILE_ACCESS_ERROR"
    ENCODING_ERROR = "ENCODING_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class FileValidationError(Exception):
    """
    Custom exception for file validation errors.
    
    This exception provides structured information about file validation failures,
    including the error type, file path, and detailed error message.
    """
    
    def __init__(self, error_type: ValidationErrorType, filepath: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a file validation error.
        
        Args:
            error_type (ValidationErrorType): The type of validation error
            filepath (str): Path to the file that caused the error
            message (str): Human-readable error message
            details (Optional[Dict[str, Any]]): Additional error details (line numbers, etc.)
        """
        self.error_type = error_type
        self.filepath = filepath
        self.message = message
        self.details = details or {}
        
        # Create the full error message
        full_message = f"[{error_type.value}] {message} (File: {filepath})"
        if details:
            detail_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
            full_message += f" - Details: {detail_str}"
            
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the error
        """
        return {
            "error_type": self.error_type.value,
            "filepath": self.filepath,
            "message": self.message,
            "details": self.details
        }

class ValidationResult(BaseModel):
    """
    Structured response for validation results.
    
    This class provides a consistent format for validation results,
    whether they represent success or failure.
    """
    
    success: bool
    error_type: Optional[ValidationErrorType] = None
    message: Optional[str] = None
    filepath: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_result(cls, data: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """
        Create a successful validation result.
        
        Args:
            data (Optional[Dict[str, Any]]): The validated data
            
        Returns:
            ValidationResult: Success result
        """
        return cls(
            success=True,
            message="Validation successful",
            data=data
        )
    
    @classmethod
    def error_result(cls, error_type: ValidationErrorType, filepath: str, message: str, details: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """
        Create an error validation result.
        
        Args:
            error_type (ValidationErrorType): The type of error
            filepath (str): Path to the file that caused the error
            message (str): Error message
            details (Optional[Dict[str, Any]]): Additional error details
            
        Returns:
            ValidationResult: Error result
        """
        return cls(
            success=False,
            error_type=error_type,
            filepath=filepath,
            message=message,
            details=details
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the result
        """
        result = {
            "success": self.success,
            "message": self.message
        }
        
        if not self.success:
            result.update({
                "error_type": self.error_type.value if self.error_type else None,
                "filepath": self.filepath,
                "details": self.details
            })
        else:
            result["data"] = self.data
            
        return result