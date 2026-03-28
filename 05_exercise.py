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


invalid_review_json = """
{
  "review_id": "",
  "rating": 3,
  "date": "1 month ago",
  "text": ""
}
"""

review = Review.model_validate_json(invalid_review_json)

pprint(review)

