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

'''
Pydantic Models for the current HSDS 3.1 standard.
Schema reference: https://docs.openreferral.org/en/3.1/hsds/schema_reference.html
Specification Github: https://github.com/openreferral/specification/tree/3.1/schema

Any field not specified as optional is required.
'''

# Four Core Objects

class Organization(BaseModel):
    id: str 
    name: str 
    alternate_name: Optional[str] = None
    description: str 
    email: Optional[str] = None
    website: Optional[str] = None
    additional_websites: List[URL]
    tax_status: Optional[str] = None
    id: Optional[str] = None
    tax_id: Optional[str] = None
    year_incorporated: Optional[int] = None
    legal_status: Optional[str] = None
    logo: Optional[str] = None
    uri: Optional[str] = None
    parent_organization_id: Optional[str] = None
    funding: Optional[List[Funding]] = None
    contacts: Optional[List[Contact]] = None
    phones: Optional[List[Phone]] = None
    locations: Optional[List[Location]] = None
    programs: Optional[List[Programs]] = None
    prganization_identifiers: Optional[List[Organization_Identifier]] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Service(BaseModel):
    id: str 
    name: str 
    alternate_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    additional_urls: List[URL]
    email: Optional[str] = None
    status: str 
    interpretation_services: Optional[str] = None
    application_process: Optional[str] = None
    fees_description: Optional[str] = None
    wait_time: Optional[str] = None
    fees: Optional[str] = None
    accreditations: Optional[str] = None
    eligibility_description: Optional[str] = None
    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None
    assurer_date: Optional[str] = None
    assurer_email: Optional[str] = None
    licenses: Optional[str] = None
    alert: Optional[str] = None
    last_modified: Optional[str] = None # format datetime
    phones: Optional[List[Phone]] = None
    schedules: Optional[List[Schedule]] = None
    service_areas: Optional[List[Service_Area]] = None
    service_at_locations: Optional[List[Service_At_Location]] = None
    languages: Optional[List[Language]] = None
    organization: Optional[Organization] = None
    funding: Optional[List[Funding]] = None
    cost_options: Optional[List[Cost_Option]] = None
    program: Optional[Program] = None
    required_documents: Optional[List[Required_Document]] = None
    contacts: Optional[List[Contacts]] = None
    capacities: Optional[List[Service_Capacity]] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Location(BaseModel):
    id: str 
    location_type: str 
    url: Optional[str] = None
    name: Optional[str] = None
    alternative_name: Optional[str] = None
    description: Optional[str] = None
    transportation: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    external_identifier: Optional[str] = None
    external_identifier_type: Optional[str] = None
    languages: Optional[List[Language]] = None
    addresses: Optional[List[Address]] = None
    contacts: Optional[List[Contact]] = None
    accessibility: Optional[List[Accessibility]] = None
    phones: Optional[List[Phone]] = None
    schedules: Optional[List[Schedule]] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Service_At_Location(BaseModel):
    id: str 
    service_id: Optional[str] = None
    description: Optional[str] = None
    service_areas: Optional[List[Service_Area]] = None
    contacts: Optional[List[Contact]] = None
    phones: Optional[List[Phone]] = None
    schedules: Optional[List[Schedule]] = None
    location: Optional[Location] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

# Rest of the objects

class Address(BaseModel):
    id: str 
    location_id: Optional[str] = None
    attention: Optional[str] = None
    address_1: str 
    address_2: Optional[str] = None
    city: str 
    region: Optional[str] = None
    state_province: str
    postal_code: str
    country: str
    address_type: str
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Phone(BaseModel):
    id: str 
    location_id: Optional[str] = None
    service_id: Optional[str] = None
    organization_id: Optional[str] = None
    contact_id: Optional[str] = None
    service_at_location_id: Optional[str] = None
    number: str 
    extension: Optional[int] = None
    type: Optional[str] = None
    description: Optional[str] = None
    languages: Optional[List[Language]] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Schedule(BaseModel): 
    id: str 
    service_id: Optional[str] = None
    location_id: Optional[str] = None
    service_at_location_id: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    dtstart: Optional[str] = None
    timezone: Optional[int] = None
    until: Optional[str] = None
    count: Optional[int] = None
    wkst: Optional[str] = None
    freq: Optional[str] = None
    interval: Optional[int] = None
    byday: Optional[str] = None
    byweekno: Optional[str] = None
    bymonthday: Optional[str] = None
    byyearday: Optional[str] = None
    description: Optional[str] = None
    opens_at: Optional[str] = None
    closes_at: Optional[str] = None
    schedule_link: Optional[str] = None
    attending_type: Optional[str] = None
    notes: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Service_Area(BaseModel):
    id: str 
    service_id: Optional[str] = None
    service_at_location_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    extent: Optional[str] = None
    extent_type: Optional[str] = None
    uri: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Language(BaseModel):
    id: str 
    service_id: Optional[str] = None
    location_id: Optional[str] = None
    phone_id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    note: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Funding(BaseModel):
    id: str 
    organization_id: Optional[str] = None
    service_id: Optional[str] = None
    source: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Accessibility(BaseModel):
    id: str
    location_id: Optional[str] = None
    description: Optional[str] = None
    details: Optional[str] = None
    url: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Cost_Option(BaseModel):
    id: str 
    service_id: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    option: Optional[str] = None
    currency: Optional[str] = None
    amount: Optional[int] = None
    amount_description: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Program(BaseModel):
    id: str 
    organization_id: Optional[str] = None
    name: str 
    alternate_name: Optional[str] = None
    description: str 
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Required_Document(BaseModel):
    id: str 
    service_id: Optional[str] = None
    document: Optional[str] = None
    uri: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Contact(BaseModel):
    id: str 
    organization_id: Optional[str] = None
    service_id: Optional[str] = None
    service_at_location_id: Optional[str] = None
    location_id: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phones: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Organization_Identifier(BaseModel):
    id: str
    organization_id: Optional[str] = None
    identifier_scheme: Optional[str] = None
    identifier_type: str 
    identifier: str 
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Unit(BaseModel):
    id: str 
    name: str 
    scheme: Optional[str] = None
    identifier: Optional[str] = None
    uri: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Service_Capacity(BaseModel):
    id: str 
    service_id: Optional[str] = None
    unit: Unit 
    available: int 
    maximum: Optional[int] = None
    description: Optional[str] = None
    updated: str 
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Attribute(BaseModel):
    id: str 
    link_id: Optional[str] = None
    link_type: Optional[str] = None
    link_entity: Optional[str] = None
    value: Optional[str] = None
    taxonomy_term: Optional[List[Taxonomy_Term]] = None
    metadata: Optional[List[Metadata]] = None
    label: Optional[str] = None

class URL(BaseModel):
    id: str 
    label: Optional[str] = None
    url: str 
    organization_id: Optional[str] = None
    service_id: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Metadata(BaseModel):
    id: str 
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    last_action_date: str 
    last_action_type: str 
    field_name: str 
    previous_value: str 
    replacement_value: str 
    updated_by: str

class Meta_Table_Description(BaseModel):
    id: str
    name: Optional[str] = None
    language: Optional[str] = None
    character_set: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Taxonomy(BaseModel):
    id: str 
    name: str 
    description: str 
    uri: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[List[Metadata]] = None

class Taxonomy_Term(BaseModel):
    id: str
    code: Optional[str] = None
    name: str 
    description: str 
    parent_id: Optional[str] = None
    taxonomy: Optional[Taxonomy] = None
    taxonomy_detail: Optional[str] = None
    language: Optional[str] = None
    taxonomy_id: Optional[str] = None
    term_uri: Optional[str] = None
    metadata: Optional[List[Metadata]] = None
