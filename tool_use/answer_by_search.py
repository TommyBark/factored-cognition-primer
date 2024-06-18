import httpx
from typing import Tuple
from fvalues import F
from utils import remove_ordinal, get_body_text, get_url_from_text
from ice.recipe import recipe  # type: ignore
from dotenv import dotenv_values
import asyncio

config = dotenv_values("../.env")

import sys
import os

# Add the verifiers directory to the system path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "verifiers"))
)

# Now you can import verify_answer
from verify_answer import verify_answer  # type: ignore


def make_search_result_prompt(
    contexts: list[str], queries: list[str], question: str
) -> str:
    prefix_prompt = F("")

    for query, context in zip(queries, contexts):
        prefix_prompt += F(
            f"""
    Search results from Google for the query {query}: "{context}"
    """
        )

    suffix_prompt = F(
        f"""

    Answer the following question, using the search results if helpful, you don't have to use them, you can also use your own reasoning step by step:

    Question: "{question}"
    Answer: "
    """
    ).strip()

    return prefix_prompt + suffix_prompt


def choose_useful_link_prompt(
    contexts: list[str], queries: list[str], question: str
) -> str:
    prefix_prompt = F("")

    for query, context in zip(queries, contexts):
        prefix_prompt += F(
            f"""
    Search results from Google for the query {query}: "{context}"
    """
        )

    suffix_prompt = F(
        f"""

    Given these results and the following question, return the most useful link from the search results to answer the question:

    Question: "{question}"
    Answer: "
    """
    ).strip()

    return prefix_prompt + suffix_prompt


def make_search_query_prompt(
    question: str, num_questions: int = 2, context: list = []
) -> str:
    prefix_prompt = F(
        f"""
You're trying to answer the question "{question}".
"""
    )
    if context:
        context_str = F("\n").join(context)
        prefix_prompt += F(f"""\nGiven the following context: {context_str}""")

    suffix_prompt = F(
        f"""You get to type in 1 to {num_questions} separate search queries to Google, and then you'll be shown the results. Don't make similar queries. What queries do you want to search for? Separate the queries by newline.

    Queries: 
    """
    ).strip('" ')
    return prefix_prompt + suffix_prompt


async def add_link_to_context(
    results: list[dict], contexts: list[str], queries: list[str], question: str
):
    prompt = choose_useful_link_prompt(contexts, queries, question)
    link = await recipe.agent().complete(prompt=prompt, stop="\n\n")
    link = get_url_from_text(link)
    if link is not None:
        body_text = get_body_text(link)
        if body_text is None:
            return contexts
        body_text = body_text[:1000]
        for i, result in enumerate(results):
            if result.get(link, None) is not None:
                result[link] += F(f"Excerpt from the website text: {body_text}\n")
                result_str = F("\n").join(result.values())
                contexts[i] = result_str
    return contexts


async def search(query: str, max_results: str = "5") -> dict:
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=60.0)
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        params = {
            "q": query,
            "hl": "en",
            "gl": "us",
            "num": max_results,
            "api_key": config.get("SERPAPI_KEY"),
        }
        response = await client.get("https://serpapi.com/search", params=params)
        return response.json()


def process_results(data: dict, open_first_result: bool = True) -> Tuple[dict, str]:
    if not data or not data.get("organic_results"):
        return {}, "No results found"

    results = {}
    for result in data["organic_results"]:
        title = result.get("title")
        link = result.get("link")
        snippet = result.get("snippet")
        if not title or not link or not snippet:
            continue
        if open_first_result:
            body_text = get_body_text(link)[:1000]

            results[link] = F(
                f"{title}\n{link}\n{snippet}\n Excerpt from the website text: {body_text}\n"
            )

            open_first_result = False
            continue
        results[link] = F(f"{title}\n{link}\n{snippet}\n")
    results_str = F("\n").join(results.values())
    return results, results_str


async def choose_queries(
    question: str, num_questions: int = 2, context: list = []
) -> list[str]:
    prompt = make_search_query_prompt(
        question, num_questions=num_questions, context=context
    )
    queries = await recipe.agent().complete(prompt=prompt, stop="\n\n")
    queries = [remove_ordinal(q) for q in queries.strip().split("\n")]
    return queries


async def answer_by_search_and_verify(question: str) -> float:
    answer = await answer_by_search(question)
    return await verify_answer(question, answer)


async def answer_by_search(
    question: str = "Who is the president of the United States?", context: list = []
) -> Tuple[str, str]:
    queries = await choose_queries(question, num_questions=2, context=context)

    results = [search(query) for query in queries]
    results = await asyncio.gather(*results)

    # For each web search query, process results and return a dict of results + the rendered string
    results_dict, results_str_list = zip(
        *[process_results(result, open_first_result=False) for result in results]
    )
    results_str_list = list(results_str_list)
    contexts = await add_link_to_context(
        results_dict, results_str_list, queries, question
    )
    prompt = make_search_result_prompt(contexts, queries, question)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer, prompt


recipe.main(answer_by_search_and_verify)
