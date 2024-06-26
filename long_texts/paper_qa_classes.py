from fvalues import F

from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import recipe
from ice.utils import map_async


def make_prompt(paragraph: Paragraph, question: str) -> str:
    return F(
        f"""Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:"""
    )


async def classify_paragraph(paragraph: Paragraph, question: str) -> float:
    choice_probs, _ = await recipe.agent().classify(
        prompt=make_prompt(paragraph, question), choices=(" Yes", " No"), truncate=True
    )
    return choice_probs.get(" Yes", 0.0)


async def answer_for_paper(
    paper: Paper, question: str = "What was the study population?"
):
    paper.paragraphs = [p for p in paper.paragraphs]
    probs = await map_async(
        paper.paragraphs,
        lambda par: classify_paragraph(par, question),
    )
    return probs


recipe.main(answer_for_paper)
