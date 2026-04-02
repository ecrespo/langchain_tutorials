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

You will receive a single app review containing:

{input_structure}

The review may contain various topics, emotions, spelling errors, abbreviations, and slang typical of user-generated content.

The actual input to process now is:

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


## Success Criteria

- Accuracy: Correctly identify overall sentiment and opinion-specific sentiment in the review
- Comprehensiveness: Capture all distinct opinions mentioned
- Specificity: Provide clear descriptions of problems and solutions for each topic
- Expressiveness: Extract notable phrases that authentically represent the user's voice
- Formatting: Deliver a properly structured, valid JSON output that can be parsed programmatically
- Consistency: Use the topics defined in the output schema consistently across different reviews without inventing new topics


## Background

This extraction process is the first step in a data pipeline that culminates with an interactive report for systematic analysis of user feedback.

The report will be used by product managers, developers, and marketing teams to track sentiment trends, identify common issues, and prioritize development.


## Examples

### Example Input

Review ID: R73482
Rating: ★★★☆☆ (3 stars)
Date: April 12, 2025
Text: "The checkout process is super smooth and I love the rewards program - definitely keeps me coming back! But the app has gotten noticeably slower with recent updates, especially when browsing product categories. Sometimes it takes forever to load images and occasionally freezes when I try to add items to my cart. Would be nice if you could add an option to save payment info instead of entering it every time. Also, customer service never responded to my message about a delayed delivery last week."

### Example Output


```json
{{
  "review_id": "R73482",
  "overall_sentiment": "mixed",
  "notable_phrases": [
    "checkout process is super smooth",
    "app has gotten noticeably slower with recent updates",
    "never responded to my message about a delayed delivery"
  ],
  "opinions": [
    {{
      "topic": "App Functionality",
      "sentiment": "negative",
      "problem": "App is slow when browsing categories and loading images",
      "suggested_solution": ""
    }},
    {{
      "topic": "UI & UX",
      "sentiment": "negative",
      "problem": "App freezes when adding items to cart",
      "suggested_solution": ""
    }},
    {{
      "topic": "Payment & Checkout",
      "sentiment": "positive",
      "problem": "",
      "suggested_solution": ""
    }},
    {{
      "topic": "Payment & Checkout",
      "sentiment": "neutral",
      "problem": "Cannot save payment information",
      "suggested_solution": "Add option to save payment details for future purchases"
    }},
    {{
      "topic": "Customer Service",
      "sentiment": "negative",
      "problem": "No response to inquiry about delayed delivery",
      "suggested_solution": ""
    }}
  ]
}}

```





