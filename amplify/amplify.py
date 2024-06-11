from fvalues import F

from ice.recipe import recipe
from ice.utils import map_async


Question = str
Answer = str
Subs = list[tuple[Question, Answer]]

def make_subquestion_prompt(question: str) -> str:
    return F(
        f"""Decompose the following question into 2-5 subquestions that would help you answer the question. Make the questions stand alone, so that they can be answered without the context of the original question.

Question: "{question}"
Subquestions:
-"""
    ).strip()


async def ask_subquestions(
    question: str = "What is the effect of creatine on cognition?",
):
    prompt = make_subquestion_prompt(question)
    subquestions_text = await recipe.agent().complete(prompt=prompt, max_tokens=512)
    subquestions = [line.strip("- ") for line in subquestions_text.split("\n")]
    return subquestions


recipe.main(ask_subquestions)

def render_background(subs: Subs) -> str:
    if not subs:
        return ""
    subs_text = F("\n\n").join(F(f"Q: {q}\nA: {a}") for (q, a) in subs)
    return F(f"Here is relevant background information:\n\n{subs_text}\n\n")


def make_qa_prompt(question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return F(
        f"""{background_text}Answer the following question, using the background information above where helpful:

Question: "{question}"
Answer: "
"""
    ).strip()


async def get_subs(question: str, depth: int) -> Subs:
    subquestions = await ask_subquestions(question=question)
    subanswers = await map_async(
        subquestions, lambda q: answer_by_amplification(question=q, depth=depth)
    )
    return list(zip(subquestions, subanswers))


async def answer_by_amplification(
    question: str = "What is the effect of creatine on cognition?", depth: int = 1
):
    subs = await get_subs(question, depth - 1) if depth > 0 else []
    prompt = make_qa_prompt(question, subs=subs)
    answer = await recipe.agent().complete(prompt=prompt, stop='"', max_tokens=512)
    return answer


recipe.main(answer_by_amplification)
