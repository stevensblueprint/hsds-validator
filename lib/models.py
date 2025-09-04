from pydantic import BaseModel
from typing import List, Optional

'''
Pydantic Models for the current HSDS 3.1 standard.

**Currently, counts optional fields as required**

'''
## Four Core Objects

class Organization(BaseModel):
    id: str # required
    name: str # required
    alternate_name: str
    description: str # required
    email: str
    website: str
    additional_websites: List[URL]
    tax_status: str
    id: str
    tax_id: str
    year_incorporated: int
    legal_status: str
    logo: str
    uri: str
    parent_organization_id: str
    funding: List[Funding]
    contacts: List[Contact]
    phones: List[Phone]
    locations: List[Location]
    programs: List[Program]
    prganization_identifiers: List[Organization_Identifier]
    attributes: List[Attribute]
    metadata: List[Metadata]

class Service(BaseModel):
    id: str
    name: str
    alternate_name: str
    description: str
    url: str
    additional_urls: List[URL]
    email: str
    status: str
    interpretation_services: str
    application_process: str
    fees_description: str
    wait_time: str
    fees: str
    accreditations: str
    eligibility_description: str
    minimum_age: int
    maximum_age: int
    assurer_date: str
    assurer_email: str
    licenses: str
    alert: str
    last_modified: str # format datetime
    phones: List[Phone]
    schedules: List[Schedule]
    service_areas: List[Service_Area]
    service_at_locations: List[Service_At_Location]
    languages: List[Language]
    organization: Organization
    funding: List[Funding]
    cost_options: List[Cost_Option]
    program: Program
    required_documents: List[Required_Document]
    contacts: List[Contacts]
    capacities: List[Service_Capacity]
    attributes: List[Attribute]
    metadata: List[Metadata]

class Location(BaseModel):
    id: str
    location_type: str
    url: str
    name: str
    alternative_name: str
    description: str
    transportation: str
    latitude: int
    longitude: int
    external_identifier: str
    external_identifier_type: str
    languages: List[Language]
    addresses: List[Address]
    contacts: List[Contact]
    accessibility: List[Accessibility]
    phones: List[Phone]
    schedules: List[Schedules]
    attributes: List[Attribute]
    metadata: List[Metadata]

class Service_At_Location(BaseModel):
    id: str
    service_id: str
    description: str
    service_areas: List[Service_Area]
    contacts: List[Contact]
    phones: List[Phone]
    schedules: List[Schedules]
    location: Location
    attributes: List[Attribute]
    metadata: List[Metadata]

## Rest of the objects

class Address(BaseModel):
    id: str
    location_id: str
    attention: str
    address_1: str
    address_2: str
    city: str
    region: str
    state_province: str
    postal_code: str
    country: str
    address_type: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Phone(BaseModel):
    id: str
    location_id: str
    service_id: str
    organization_id: str
    contact_id: str
    service_at_location_id: str
    number: str
    extension: int
    type: str
    description: str
    languages: List[Language]
    attributes: List[Attribute]
    metadata: List[Metadata]

class Schedule(BaseModel): 
    id: str
    service_id: str
    location_id: str
    service_at_location_id: str
    valid_from: str
    valid_to: str
    dtstart: str
    timezone: int
    until: str
    count: int
    wkst: str
    freq: str
    interval: int
    byday: str
    byweekno: str
    bymonthday: str
    byyearday: str
    description: str
    opens_at: str
    closes_at: str
    schedule_link: str
    attending_type: str
    notes: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Service_Area(BaseModel):
    id: str
    service_id: str
    service_at_location_id: str
    name: str
    description: str
    extent: str
    extent_type: str
    uri: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Language(BaseModel):
    id: str
    service_id: str
    location_id: str
    phone_id: str
    name: str
    code: str
    note: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Funding(BaseModel):
    id: str
    organization_id: str
    service_id: str
    source: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Accessibility(BaseModel):
    id: str
    location_id: str
    description: str
    details: str
    url: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Cost_Option(BaseModel):
    id: str
    service_id: str
    valid_from: str
    valid_to: str
    option: str
    currency: str
    amount: int
    amount_description: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Program(BaseModel):
    id: str
    organization_id: str
    name: str
    alternate_name: str
    description: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Required_Document(BaseModel):
    id: str
    service_id: str
    document: str
    uri: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Contact(BaseModel):
    id: str
    organization_id: str
    service_id: str
    service_at_location_id: str
    location_id: str
    name: str
    title: str
    department: str
    email: str
    phones: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Organization_Identifier(BaseModel):
    id: str
    organization_id: str
    identifier_scheme: str
    identifier_type: str
    identifier: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Unit(BaseModel):
    id: str
    name: str
    scheme: str
    identifier: str
    uri: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Service_Capacity(BaseModel):
    id: str
    service_id: str
    unit: Unit
    available: int
    maximum: int
    description: str
    updated: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Attribute(BaseModel):
    id: str
    link_id: str
    link_type: str
    link_entity: str
    value: str
    taxonomy_term: taxonomy_term
    metadata: List[Metadata]
    label: str

class URL(BaseModel):
    id: str
    label: str
    url: str
    organization_id: str
    service_id: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Metadata(BaseModel):
    id: str
    resource_id: str
    resource_type: str
    last_action_date: str
    last_action_type: str
    field_name: str
    previous_value: str
    replacement_value: str
    updated_by: str

class Meta_Table_Description(BaseModel):
    id: str
    name: str
    language: str
    character_set: str
    attributes: List[Attribute]
    metadata: List[Metadata]

class Taxonomy(BaseModel):
    id: str
    name: str
    description: str
    uri: str
    version: str
    metadata: List[Metadata]

class Taxonomy_Term(BaseModel):
    id: str
    code: str
    name: str
    description: str
    parent_id: str
    taxonomy: Taxonomy
    taxonomy_detail: str
    language: str
    taxonomy_id: str
    term_uri: str
    metadata: List[Metadata]
