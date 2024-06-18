from fvalues import F

from ice.recipe import recipe
from ice.utils import map_async

DEFAULT_QUESTION = "Beth bakes 4x 2 dozen batches of cookies in a week. If these cookies are shared amongst 16 people equally, how many cookies does each person consume?"

DEFAULT_STEPS = [
    "Beth bakes 4x 4 dozen batches of cookies for a total of 4*4 = 16 dozen cookies",
    "There are 12 cookies in a dozen and she makes 16 dozen cookies for a total of 12*16 = 192 cookies",
    "She splits the 192 cookies equally amongst 16 people so they each eat 192/16 = 12 cookies",
    "So, the final answer is 12 cookies per person.",
]


def render_steps(steps: list[str]) -> str:
    return F("\n").join(F(f"{i}. {step}") for (i, step) in enumerate(steps, start=1))


def make_verification_prompt(question: str, steps: list[str]) -> str:
    return F(
        f"""Consider this question: "{question}"

Here are the first few steps of an answer:

{render_steps(steps)}

Q: Is step {len(steps)} correct, assuming that the previous steps are correct? Say "A: Yes" or "A: No".
A:"""
    )


async def check_step(question: str, steps: list[str]) -> float:
    """
    Return the probability that the step is correct
    """
    prompt = make_verification_prompt(question=question, steps=steps)
    answer_probs, _ = await recipe.agent().classify(
        prompt=prompt, choices=(" Yes", " No")
    )
    return answer_probs.get(" Yes", 0.0)


async def verify_answer(
    question: str = DEFAULT_QUESTION, steps: list[str] = DEFAULT_STEPS
):
    """
    For each prefix of 1..n steps, check if the nth step is correct.
    """
    step_indices = list(range(1, len(steps) + 1))
    step_probs = await map_async(
        step_indices,
        lambda index: check_step(question=question, steps=steps[:index]),
    )
    return list(zip(step_probs, steps))


recipe.main(verify_answer)
