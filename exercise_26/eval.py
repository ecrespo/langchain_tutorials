import json
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

from langsmith import Client
from langsmith.evaluation import evaluate
from openevals.llm import create_llm_as_judge

from app import extract_structured_review

load_dotenv()

client = Client()

dataset_name = "app_reviews_pe"

judge_llm = init_chat_model(model="gpt-4o", temperature=0)


def load_examples():
    evaluation_dataset_path = (
        "data/prompt-engineering/prompt-management/evaluation_dataset.json"
    )

    # Load the evaluation dataset
    with open(evaluation_dataset_path, "r", encoding="utf-8") as file:
        examples = json.load(file)

    return examples


if client.has_dataset(dataset_name=dataset_name):
    print(f"Using existing dataset: {dataset_name}")
else:
    # Create a new dataset if not found
    print(f"Creating new dataset: {dataset_name}")
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Dataset for evaluating app review structured extraction",
    )

    examples = load_examples()
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"Dataset Created with {len(examples)} examples")


# Define the prediction function
def app_to_evaluate(example):
    return extract_structured_review(example["raw_review"]).model_dump()


# Overall sentiment correctness evaluator
def overall_sentiment_correctness_evaluator(
    inputs: dict, outputs: dict, reference_outputs: dict
):
    return (
        outputs["overall_sentiment"]
        == reference_outputs["structured_review"]["overall_sentiment"]
    )


def topic_similarity_evaluator(inputs: dict, outputs: dict, reference_outputs: dict):
    output_topics = set([opinion["topic"] for opinion in outputs["opinions"]])
    reference_topics = set(
        [
            opinion["topic"]
            for opinion in reference_outputs["structured_review"]["opinions"]
        ]
    )

    intersection = output_topics & reference_topics
    union = output_topics | reference_topics
    if len(union) == 0:
        jaccard_similarity = 0.0
    else:
        jaccard_similarity = len(intersection) / len(union)

    return jaccard_similarity


# Opinion correctness evaluator
class OpinionCorrectness(BaseModel):
    problem_correctness: float = Field(
        description="The ratio of opinions in the output that have the same problem as the reference output to the total number of opinions in the reference output"
    )
    solution_correctness: float = Field(
        description="The ratio of opinions in the output that have the same solution as the reference output to the total number of opinions in the reference output"
    )
    problem_score_explanation: str = Field(
        description="A short explanation of the problem score"
    )
    solution_score_explanation: str = Field(
        description="A short explanation of the solution score"
    )


def average_opinion_problem_and_solution_correctness_evaluator(
    inputs: dict, outputs: dict, reference_outputs: dict
):
    opinion_correctness_prompt = """
For each opinion in the reference output, compute and return the following
two scores:

- problem_correctness: Count the number of opinions in the output
  that have the same problem. Return the ratio of opinions with matched
  problems to the total number of opinions in the reference output (
  matched_opinion_problem_count / reference_opinion_count).
- solution_correctness: Out of the opinions in the output that
  have the same problem as the reference output, count the number of opinions
  that have the same solution. Return the ratio of opinions with matched
  problem and solution to the total number of opinions in the reference
  output (matched_opinion_problem_and_solution_count /
  reference_opinion_count).

Here is the input:
{inputs}

Here is the output:
{outputs}

Here is the reference output:
{reference_outputs}
"""

    evaluator = create_llm_as_judge(
        judge=judge_llm,
        prompt=opinion_correctness_prompt,
        continuous=True,
        feedback_key="opinion_correctness",
        output_schema=OpinionCorrectness,
    )
    eval_result = evaluator(
        inputs=inputs, outputs=outputs, reference_outputs=reference_outputs
    )

    # Convert the schema-based result to the format expected by LangSmith for multiple metrics
    return [
        {
            "key": "problem_correctness",
            "score": eval_result.problem_correctness,
            "comment": eval_result.problem_score_explanation,
        },
        {
            "key": "solution_correctness",
            "score": eval_result.solution_correctness,
            "comment": eval_result.solution_score_explanation,
        },
    ]


evaluators = [
    overall_sentiment_correctness_evaluator,
    topic_similarity_evaluator,
    average_opinion_problem_and_solution_correctness_evaluator,
]

experiment_name = "app_review_extraction_evaluation"

# Run the evaluation
results = evaluate(
    app_to_evaluate,
    data=dataset_name,
    evaluators=evaluators,
    experiment_prefix=experiment_name,
    max_concurrency=5,
)

results_df = results.to_pandas()

eval_summary_df = (
    results_df.agg(
        {
            "feedback.overall_sentiment_correctness_evaluator": "mean",
            "feedback.topic_similarity_evaluator": "mean",
            "feedback.problem_correctness": "mean",
            "feedback.solution_correctness": "mean",
            "execution_time": "mean",
        }
    )
    .reset_index()
    .rename(columns={"index": "metric"})
)

print(eval_summary_df.to_markdown(index=False))

