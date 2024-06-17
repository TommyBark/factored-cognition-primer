import httpx

from fvalues import F
from utils import remove_ordinal, get_body_text
from ice.recipe import recipe  # type: ignore
from dotenv import dotenv_values
import asyncio

config = dotenv_values("../.env")


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

    Answer the following question, using the search results if helpful:

    Question: "{question}"
    Answer: "
    """
    ).strip()

    return prefix_prompt + suffix_prompt


def choose_useful_link_prompt(contexts: list[str], queries: list[str], question: str) -> str:
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


def make_search_query_prompt(question: str, num_questions: int = 3) -> str:
    return F(
        f"""
You're trying to answer the question "{question}".
You get to type in {num_questions} separate search queries to Google, and then you'll be shown the results. What queries do you want to search for? Separate the queries by newline.

Queries: 
"""
    ).strip('" ')


async def search(query: str, max_results: str = "5") -> dict:
    async with httpx.AsyncClient() as client:
        params = {
            "q": query,
            "hl": "en",
            "gl": "us",
            "num": max_results,
            "api_key": config.get("SERPAPI_KEY"),
        }
        response = await client.get("https://serpapi.com/search", params=params)
        return response.json()


def process_results(data: dict, open_first_result:bool=True) -> str:
    if not data or not data.get("organic_results"):
        return "No results found"

    results = []
    for result in data["organic_results"]:
        title = result.get("title")
        link = result.get("link")
        snippet = result.get("snippet")
        if not title or not link or not snippet:
            continue
        if open_first_result:
            body_text = get_body_text(link)[:1000]

            results.append(
                F(
                    f"{title}\n{link}\n{snippet}\n Excerpt from the website text: {body_text}\n"
                )
            )
            open_first_result = False
            continue
        results.append(F(f"{title}\n{link}\n{snippet}\n"))
    results_str = F("\n").join(results)
    return results_str


async def choose_queries(question: str, num_questions: int = 3) -> list[str]:
    prompt = make_search_query_prompt(question, num_questions=num_questions)
    queries = await recipe.agent().complete(prompt=prompt, stop="\n\n")
    queries = [remove_ordinal(q) for q in queries.strip().split("\n")]
    return queries


async def answer_by_search(
    question: str = "Who is the president of the United States?",
) -> str:
    queries = await choose_queries(question, num_questions=2)

    results = [search(query) for query in queries]
    results = await asyncio.gather(*results)

    results_str = [render_results(result) for result in results]
    prompt = make_search_result_prompt(results_str, queries, question)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


recipe.main(answer_by_search)
