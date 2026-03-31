from pydantic import BaseModel, Field
import datetime
from devtools import pprint


class Review(BaseModel):
    review_id: str = Field(description="The ID of the review", pattern=r"^R\d{5}$")
    rating: str = Field(
        description="The rating of the review", pattern=r"^★{1,5}☆{0,4} \(\d stars\)$"
    )
    date: datetime.date = Field(
        description="The date of the review", format="YYYY-MM-DD"
    )
    text: str = Field(
        description="The text of the review", min_length=1, max_length=1000
    )


valid_review_json = """
{
  "review_id": "R12345",
  "rating": "★★★★☆ (4 stars)",
  "date": "2025-01-01",
  "text": "This is a great product!"
}
"""

review = Review.model_validate_json(valid_review_json)

pprint(review)

