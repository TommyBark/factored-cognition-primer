from fvalues import F

from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import recipe
from ice.recipes.primer.qa import answer
from ice.utils import map_async, truncate_prompt


def make_classification_prompt(paragraph: Paragraph, question: str) -> str:
    return F(
        f"""Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:"""
    )


async def classify_paragraph(paragraph: Paragraph, question: str) -> float:
    choice_probs, _ = await recipe.agent().classify(
        prompt=make_classification_prompt(
            truncate_prompt(paragraph.sentences[0], max_tokens=4000), question
        ),
        choices=(" Yes", " No"),
    )
    return choice_probs.get(" Yes", 0.0)


async def get_relevant_paragraphs(
    paper: Paper, question: str, top_n: int = 3
) -> list[Paragraph]:
    probs = await map_async(
        paper.paragraphs,
        lambda par: classify_paragraph(par, question),
        show_progress_bar=True,
        max_concurrency=5,
    )
    sorted_pairs = sorted(
        zip(paper.paragraphs, probs), key=lambda x: x[1], reverse=True
    )
    return [par for par, prob in sorted_pairs[:top_n]]


async def answer_for_paper(
    paper: Paper, question: str = "What was the study population?"
):
    relevant_paragraphs = await get_relevant_paragraphs(paper, question)
    relevant_str = F("\n\n").join(str(p) for p in relevant_paragraphs)
    response = await answer(context=relevant_str, question=question)
    return response


recipe.main(answer_for_paper)
