from pydantic import BaseModel
from typing import List, Optional

'''
Pydantic Models for the current HSDS 3.1 standard.
Schema reference: https://docs.openreferral.org/en/3.1/hsds/schema_reference.html
Specification Github: https://github.com/openreferral/specification/tree/3.1/schema
'''

# Four Core Objects

class Organization(BaseModel):
    id: str # required
    name: str # required
    alternate_name: Optional[str] = None
    description: str # required
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
    id: str # required
    name: str # required
    alternate_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    additional_urls: List[URL]
    email: Optional[str] = None
    status: str # required
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
    id: str # required
    location_type: str # required
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
    id: str # required
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
    id: str # required
    location_id: Optional[str] = None
    attention: Optional[str] = None
    address_1: str # required
    address_2: Optional[str] = None
    city: str # required
    region: Optional[str] = None
    state_province: str # required
    postal_code: str # required
    country: str # required
    address_type: str # required
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Phone(BaseModel):
    id: str # required
    location_id: Optional[str] = None
    service_id: Optional[str] = None
    organization_id: Optional[str] = None
    contact_id: Optional[str] = None
    service_at_location_id: Optional[str] = None
    number: str # required
    extension: Optional[int] = None
    type: Optional[str] = None
    description: Optional[str] = None
    languages: Optional[List[Language]] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Schedule(BaseModel): 
    id: str # required
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
    id: str # required
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
    id: str # required
    service_id: Optional[str] = None
    location_id: Optional[str] = None
    phone_id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    note: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Funding(BaseModel):
    id: str # required
    organization_id: Optional[str] = None
    service_id: Optional[str] = None
    source: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Accessibility(BaseModel):
    id: str # required
    location_id: Optional[str] = None
    description: Optional[str] = None
    details: Optional[str] = None
    url: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Cost_Option(BaseModel):
    id: str # required
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
    id: str # required
    organization_id: Optional[str] = None
    name: str # required
    alternate_name: Optional[str] = None
    description: str # required
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Required_Document(BaseModel):
    id: str # required
    service_id: Optional[str] = None
    document: Optional[str] = None
    uri: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Contact(BaseModel):
    id: str # required
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
    id: str # required
    organization_id: Optional[str] = None
    identifier_scheme: Optional[str] = None
    identifier_type: str # required
    identifier: str # required
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Unit(BaseModel):
    id: str # required
    name: str # required
    scheme: Optional[str] = None
    identifier: Optional[str] = None
    uri: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Service_Capacity(BaseModel):
    id: str # required
    service_id: Optional[str] = None
    unit: Unit # required
    available: int # required
    maximum: Optional[int] = None
    description: Optional[str] = None
    updated: str # required
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Attribute(BaseModel):
    id: str # required
    link_id: Optional[str] = None
    link_type: Optional[str] = None
    link_entity: Optional[str] = None
    value: Optional[str] = None
    taxonomy_term: Optional[List[Taxonomy_Term]] = None
    metadata: Optional[List[Metadata]] = None
    label: Optional[str] = None

class URL(BaseModel):
    id: str # required
    label: Optional[str] = None
    url: str # required
    organization_id: Optional[str] = None
    service_id: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Metadata(BaseModel):
    id: str # required
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    last_action_date: str # required
    last_action_type: str # required
    field_name: str # required
    previous_value: str # required
    replacement_value: str # required
    updated_by: str # required

class Meta_Table_Description(BaseModel):
    id: str # required
    name: Optional[str] = None
    language: Optional[str] = None
    character_set: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[Metadata]] = None

class Taxonomy(BaseModel):
    id: str # required
    name: str # required
    description: str # required
    uri: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[List[Metadata]] = None

class Taxonomy_Term(BaseModel):
    id: str # required
    code: Optional[str] = None
    name: str # required
    description: str # required
    parent_id: Optional[str] = None
    taxonomy: Optional[Taxonomy] = None
    taxonomy_detail: Optional[str] = None
    language: Optional[str] = None
    taxonomy_id: Optional[str] = None
    term_uri: Optional[str] = None
    metadata: Optional[List[Metadata]] = None
