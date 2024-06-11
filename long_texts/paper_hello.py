from ice.paper import Paper, parse_txt
from ice.recipe import recipe
from pathlib import Path
from parse_pdf import parse_pdf
from merge_args import merge_args
import defopt
import asyncio


async def answer_for_paper(paper: Paper):
    return paper.paragraphs[0]


recipe.main(answer_for_paper)
