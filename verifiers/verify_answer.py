from fvalues import F
from typing import Optional
from ice.recipe import recipe


def make_verification_prompt(
    question: str, answer: str, context: Optional[str] = None
) -> str:
    response_prefix = F(
        f"""Consider this question: "{question}" 
        """
    )
    if context:
        response_prefix += F(
            f""" 
        With this context: "{context}"
        """
        )
    response_sufix = F(
        f"""

Potential answer: "{answer}"

Q: Is the potential answer above correct? Say "A: Yes" or "A: No".
A:"""
    )
    return response_prefix + response_sufix

async def verify_answer(question: str, answer: str) -> float:
    prompt = make_verification_prompt(question=question, answer=answer)
    choice_probs, _ = await recipe.agent().classify(
        prompt=prompt, choices=(" Yes", " No")
    )
    return choice_probs.get(" Yes", 0)


recipe.main(verify_answer)
