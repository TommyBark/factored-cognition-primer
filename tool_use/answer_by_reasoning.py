from fvalues import F
from typing import Tuple
from ice.recipe import recipe # type: ignore


def generate_reasoning_prompt(question: str, context: list[str] = []) -> str:
    prompt = F(
        f"""Answer the following question:

Question: "{question}"
Answer: "Let's think step by step.
"""
    ).strip()
    if context:
        context_str = F("\n").join(context)
        prompt = (
            F(
                f"""
        Given the following context: {context_str}
        """
            )
            + prompt
        )
    return prompt


def generate_answer_prompt(question: str, reasoning: str) -> str:
    return F(
        f"""Answer the following question using the reasoning shown below:

Question: "{question}"
Reasoning: "{reasoning}"
Short answer: "
"""
    ).strip()


async def get_reasoning(question: str,context:list=[]) -> str:
    reasoning_prompt = generate_reasoning_prompt(question,context=context)
    reasoning = await recipe.agent().complete(prompt=reasoning_prompt, stop='"')
    return reasoning


async def get_answer(question: str, reasoning: str) -> str:
    answer_prompt = generate_answer_prompt(question, reasoning)
    answer = await recipe.agent().complete(prompt=answer_prompt, stop='"')
    return answer


async def answer_by_reasoning(
    question: str = "What would happen if the average temperature in Northern California went up by 5 degrees Fahrenheit?",
context:list = []) -> Tuple[str, str]:
    reasoning = await get_reasoning(question,context=context)
    answer = await get_answer(question, reasoning)
    return answer, reasoning


recipe.main(answer_by_reasoning)
