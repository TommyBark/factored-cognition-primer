from fvalues import F

from ice.recipe import recipe
from ice.utils import map_async


Question = str
Answer = str
Subs = list[tuple[Question, Answer]]


def make_subquestion_prompt(
    question: str, parent_questions: list = [], last_k_questions: int = 10
) -> str:

    if last_k_questions > 0:
        parent_questions = parent_questions[-last_k_questions:]
    prompt = F(
        f"""Decompose the following question into 2-5 subquestions that would help you answer the question. Make the questions stand alone, so that they can be answered without the context of the original question.

Question: "{question}"
Subquestions:
-"""
    ).strip()
    if len(parent_questions) > 1:
        prefix = (
            F(
                "The following Question was generated based on following parent questions, in decomposing and answering take consideration of them. \n "
            )
            + F("\n").join(F(f"- {q}") for q in parent_questions)
            + F("\n\n")
        )
        prompt = prefix + prompt
    return prompt


async def ask_subquestions(
    question: str = "What is the effect of creatine on cognition?",
    parent_questions: list[str] = [],
):
    prompt = make_subquestion_prompt(question, parent_questions=parent_questions)
    subquestions_text = await recipe.agent().complete(prompt=prompt)
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


async def get_subs(question: str, depth: int, parent_questions: list[str] = []) -> Subs:
    subquestions = await ask_subquestions(
        question=question, parent_questions=parent_questions
    )
    subanswers = await map_async(
        subquestions, lambda q: answer_by_amplification(question=q, depth=depth)
    )
    return list(zip(subquestions, subanswers))


async def answer_by_amplification(
    question: str = "What is the effect of creatine on cognition?",
    depth: int = 2,
    parent_questions: list[str] = [],
):
    if not parent_questions:
        parent_questions = [question]
    else:
        parent_questions.append(question)
    subs = (
        await get_subs(question, depth - 1, parent_questions=parent_questions)
        if depth > 0
        else []
    )
    prompt = make_qa_prompt(question, subs=subs)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


recipe.main(answer_by_amplification)
