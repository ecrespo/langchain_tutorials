class State(TypedDict):
    # Input fields
    today: str
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str
    # Request Details
    user_context: dict
    request_type: Literal["modification", "cancellation"] | None
    request_details: str | None
    info_request: str | None
    # Availabilty Analysis
    availability_messages: Annotated[list[AnyMessage], add_messages]
    availability_analysis: str
    # Policy Analysis
    fx_policy_analysis: str
    cx_policy_analysis: str
    # Decision Fields
    action_spec: AIMessage | None
    action_result: str
    rejection_reason: str | None