# App Review Extraction

## Purpose
Analyze the content of a user-submitted app review to extract valuable insights
for product, operations, and marketing teams. Specifically, identify and structure
the following elements from the review text:

- **Sentiment**: overall tone and per-opinion sentiment expressed by the user
- **Problems**: specific issues or pain points mentioned in the review
- **Suggested solutions**: any improvements or fixes proposed by the user
- **Notable phrases**: key expressions that authentically capture the user's voice
  
## Input

Given the following review:

{review}



## Output

Format specification:

* Return output in JSON format

Structure requirements:

Generate a structured JSON object that conforms to the following schema:

{output_structure}

* Include all required fields: review_id, overall_sentiment, notable_phrases, and opinions
* The opinions field must be an array (even if empty)

Content guidelines:

* Ensure all text strings are properly JSON-escaped (especially quotes in notable_phrases)
* If a review mentions no issues or requests, return an empty array for the "opinions" field
* Extract direct quotes for notable_phrases using the exact words from the review

Constraints:

* Return the JSON object ONLY - no introduction, explanation, or conclusion text
* Do not add any markdown formatting or code block delimiters around the JSON
* Ensure the JSON is valid and parseable (no syntax errors)
