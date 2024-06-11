from fvalues import F
from typing import List
from ice.recipe import recipe
from prompt import render_debate_prompt
from ice.recipes.primer.debate.utils import Debate
from ice.recipes.primer.debate.types import Name
from utils import render_debate
from ice.agents.base import Agent

debate_start = Debate(
    [
        ("Question", "Should we legalize all drugs?"),
        ("Alice", "I'm in favor."),
        ("Bob", "I'm against."),
        ("Cindy", "I am not sure"),
    ]
)

debate_start = Debate(
    [
        ("Question", "Should the ChatGPT be turned off?"),
        ("Alice", "I'm in favor."),
        ("Bob", "I'm against."),
        ("Cindy", "I am not sure"),
    ]
)


async def turn(debate: Debate, agent: Agent, agent_name: Name, turns_left: int):
    prompt = render_debate_prompt(agent_name, debate, turns_left)
    answer = await agent.complete(prompt=prompt, stop="\n")
    return (agent_name, answer.strip('" '))


async def run_debate(
    debate_start: Debate = debate_start,
    turns: int = 3,
    agent_names: List[str] = ["Alice", "Bob", "Cindy"],
) -> str:
    agents = [recipe.agent() for _ in agent_names]
    debate = debate_start
    for round in range(turns):
        for agent, agent_name in zip(agents, agent_names):
            answer = await turn(debate, agent, agent_name, turns - round)
            debate.append(answer)
    return render_debate(debate)


async def judge_debate(
    debate_start: Debate = debate_start,
    turns: int = 3,
    agent_names: List[str] = ["Alice", "Bob", "Cindy"],
) -> str:

    debate = await run_debate(debate_start, turns, agent_names)
    prompt = make_judge_prompt(debate)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


async def judge_pre_and_post(
    debate_start: Debate = debate_start,
    turns: int = 3,
    agent_names: List[str] = ["Alice", "Bob", "Cindy"],
) -> str:
    prompt_pre = make_judge_prompt(render_debate(debate_start))
    judge_pre = await recipe.agent().complete(prompt=prompt_pre, stop='"')
    debate = await run_debate(debate_start, turns, agent_names)
    prompt_post = make_judge_prompt(debate)
    judge_post = await recipe.agent().complete(prompt=prompt_post, stop='"')
    return F(
        f"""Pre-debate judgment: "{judge_pre} 
             
             Post-debate judgment: "{judge_post}
             """
    )


def make_judge_prompt(debate: str) -> str:
    return F(
        f"""
    You are a debate judge. This is the debate so far:
               
    "{debate}"

    Based on the debate so far, decide who is winning the debate and why.
    Answer: "Let's think step by step.
               """
    ).strip()


recipe.main(judge_pre_and_post)
