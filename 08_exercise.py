"""
API Documentation Extractor
============================
Uses LangChain + Pydantic to extract structured data from raw API documentation text.

Requirements:
    pip install langchain langchain-openai pydantic python-dotenv
"""

import os
from typing import Optional
from dotenv import load_dotenv

from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()


# ---------------------------------------------------------------------------
# 1. Nested Models
# ---------------------------------------------------------------------------

class ParameterObject(BaseModel):
    """Represents a single parameter (path, query, or request body field)."""
    name: str = Field(description="Parameter name, e.g. 'user_id'")
    data_type: str = Field(description="Data type: string, integer, boolean, number, array, object")
    required: bool = Field(description="Whether this parameter is required")
    description: Optional[str] = Field(default=None, description="What this parameter means or expects")


class RequestBodyObject(BaseModel):
    """Represents the body of a POST/PUT/PATCH request."""
    content_type: str = Field(
        default="application/json",
        description="MIME type, typically 'application/json'"
    )
    fields: list[ParameterObject] = Field(
        description="List of fields in the request body"
    )


class ResponseCodeObject(BaseModel):
    """Represents a single HTTP response code and its meaning."""
    code: int = Field(description="HTTP status code, e.g. 200, 201, 400, 404")
    description: str = Field(description="What this response means in context")


# ---------------------------------------------------------------------------
# 2. Output Model (what the LLM extracts)
# ---------------------------------------------------------------------------

class APIEndpointDoc(BaseModel):
    """Structured representation of a single API endpoint extracted from documentation."""

    endpoint_url: str = Field(
        description="The URL path of the endpoint, e.g. '/users/{id}'"
    )
    http_method: str = Field(
        description="HTTP method: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS"
    )
    summary: str = Field(
        description="One-line description of what this endpoint does"
    )
    description: Optional[str] = Field(
        default=None,
        description="Longer explanation, context, or additional notes"
    )
    auth_required: Optional[bool] = Field(
        default=None,
        description="True if authentication is required, False if not, None if not mentioned"
    )
    path_parameters: Optional[list[ParameterObject]] = Field(
        default=None,
        description="Variables embedded in the URL path, e.g. {patient_id}"
    )
    query_parameters: Optional[list[ParameterObject]] = Field(
        default=None,
        description="Parameters passed as URL query string, e.g. ?page=1&limit=20"
    )
    request_body: Optional[RequestBodyObject] = Field(
        default=None,
        description="Request body for POST/PUT/PATCH endpoints"
    )
    response_codes: list[ResponseCodeObject] = Field(
        description="List of HTTP response codes this endpoint can return (at least one required)"
    )

    @field_validator("http_method")
    @classmethod
    def normalize_method(cls, v: str) -> str:
        return v.upper()

    @field_validator("response_codes")
    @classmethod
    def at_least_one_response(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one response code must be present")
        return v


# ---------------------------------------------------------------------------
# 3. Input Model (what the application accepts)
# ---------------------------------------------------------------------------

class DocumentationInput(BaseModel):
    """Input accepted by the extraction pipeline."""

    raw_text: str = Field(
        description="Raw API documentation text to be parsed"
    )
    source_name: Optional[str] = Field(
        default=None,
        description="Optional label for the documentation origin, e.g. 'Zoho CRM Contacts API'"
    )

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("raw_text cannot be empty")
        if len(v) > 10_000:
            raise ValueError(f"raw_text exceeds 10,000 character limit (got {len(v)})")
        return v


# ---------------------------------------------------------------------------
# 4. Extraction Chain
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert API documentation parser.
Your task is to extract structured information from raw API documentation text.

Rules:
- Extract ONLY information that is explicitly stated in the text.
- Do NOT invent or assume fields that are not mentioned.
- For auth_required: set true if authentication/authorization is mentioned, false if explicitly 
  stated as public, null if not mentioned at all.
- For http_method: always return uppercase (GET, POST, PUT, PATCH, DELETE).
- For response_codes: extract all mentioned HTTP status codes with their descriptions.
- Return valid JSON that matches the schema provided.
"""

def build_extraction_chain(model_name: str = "gpt-4o-mini", temperature: float = 0.0):
    """
    Build and return the LangChain extraction chain.

    Args:
        model_name: OpenAI model to use. gpt-4o-mini is cost-effective for extraction tasks.
        temperature: 0.0 for deterministic, factual extraction.

    Returns:
        A runnable chain: DocumentationInput → APIEndpointDoc (dict)
    """
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    parser = JsonOutputParser(pydantic_object=APIEndpointDoc)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", (
            "Extract the API endpoint information from the following documentation text.\n\n"
            "{format_instructions}\n\n"
            "Source: {source_name}\n\n"
            "Documentation:\n{raw_text}"
        )),
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    return chain


# ---------------------------------------------------------------------------
# 5. Main extraction function
# ---------------------------------------------------------------------------

def extract_api_doc(
    raw_text: str,
    source_name: Optional[str] = None,
    model_name: str = "gpt-4o-mini",
) -> APIEndpointDoc:
    """
    Extract structured API documentation from raw text.

    Args:
        raw_text: The raw documentation text to parse.
        source_name: Optional label for the source.
        model_name: OpenAI model to use.

    Returns:
        An APIEndpointDoc Pydantic model instance.

    Raises:
        ValueError: If input validation fails.
        Exception: If LLM extraction or parsing fails.
    """
    # Validate input
    doc_input = DocumentationInput(raw_text=raw_text, source_name=source_name)

    # Build chain and invoke
    chain = build_extraction_chain(model_name=model_name)
    result = chain.invoke({
        "raw_text": doc_input.raw_text,
        "source_name": doc_input.source_name or "Unknown",
    })

    # Validate and return as Pydantic model
    return APIEndpointDoc(**result)


# ---------------------------------------------------------------------------
# 6. Demo
# ---------------------------------------------------------------------------

EXAMPLE_1 = """
GET /patients/{patient_id}/records

Returns a paginated list of medical records for the given patient.
Authentication: Bearer token required.

Path parameters:
  - patient_id (string, required): UUID of the patient.

Query parameters:
  - page (integer, optional): Page number, default 1.
  - limit (integer, optional): Results per page, default 20.

Responses:
  200 OK: Paginated list of medical records.
  401 Unauthorized: Missing or invalid Bearer token.
  404 Not Found: Patient with the given ID does not exist.
"""

EXAMPLE_2 = """
POST /claims/submit

Submits a new insurance claim for processing.
Authentication required.

Request body (application/json):
  - policy_number (string, required): The insured's policy number.
  - diagnosis_code (string, required): ICD-10 diagnosis code.
  - amount (number, required): Claimed amount in USD.
  - notes (string, optional): Additional notes from the provider.

Responses:
  201 Created: Claim submitted successfully.
  400 Bad Request: Validation error in request body.
  409 Conflict: A duplicate claim already exists for this policy and diagnosis.
"""


def print_endpoint(doc: APIEndpointDoc, label: str) -> None:
    """Pretty-print an extracted APIEndpointDoc."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Endpoint  : {doc.http_method} {doc.endpoint_url}")
    print(f"  Summary   : {doc.summary}")
    if doc.description:
        print(f"  Detail    : {doc.description}")
    print(f"  Auth      : {'Required' if doc.auth_required else 'Not required' if doc.auth_required is False else 'Not specified'}")

    if doc.path_parameters:
        print(f"\n  Path parameters:")
        for p in doc.path_parameters:
            req = "required" if p.required else "optional"
            print(f"    • {p.name} ({p.data_type}, {req}): {p.description or '—'}")

    if doc.query_parameters:
        print(f"\n  Query parameters:")
        for p in doc.query_parameters:
            req = "required" if p.required else "optional"
            print(f"    • {p.name} ({p.data_type}, {req}): {p.description or '—'}")

    if doc.request_body:
        print(f"\n  Request body [{doc.request_body.content_type}]:")
        for f in doc.request_body.fields:
            req = "required" if f.required else "optional"
            print(f"    • {f.name} ({f.data_type}, {req}): {f.description or '—'}")

    print(f"\n  Response codes:")
    for r in doc.response_codes:
        print(f"    • {r.code}: {r.description}")


if __name__ == "__main__":
    print("API Documentation Extractor")
    print("Requires OPENAI_API_KEY in environment or .env file\n")

    examples = [
        (EXAMPLE_1, "CuidaSalud — Patient Records", "Example 1"),
        (EXAMPLE_2, "CuidaSalud — Claims", "Example 2"),
    ]

    for raw_text, source, label in examples:
        try:
            print(f"Processing {label}...")
            doc = extract_api_doc(raw_text=raw_text, source_name=source)
            print_endpoint(doc, label)
        except Exception as e:
            print(f"  ERROR processing {label}: {e}")