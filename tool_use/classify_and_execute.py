from ice.recipe import recipe
from prompt import (
    make_action_selection_prompt,
    action_types,
    make_sufficient_info_prompt,
    make_final_prompt,
)
from action_types import Action
from fvalues import F


async def select_action(question: str, context: list[str] = []) -> Action:
    prompt = make_action_selection_prompt(question, context=context)
    choices = tuple(str(i) for i in range(1, 4))
    choice_probs, _ = await recipe.agent().classify(prompt=prompt, choices=choices)
    best_choice = max(choice_probs.items(), key=lambda x: x[1])[0]
    return action_types[int(best_choice) - 1]


def get_reasoning_context(result, reasoning: str, action) -> str:
    return F(
        f""" 
            ---
            Used action: {action.name}
            
            Reasoning from the action: {reasoning}

            Results of action: {result}

            ---
            """
    )


async def is_info_sufficient(prompt):
    choice_probs, _ = await recipe.agent().classify(
        prompt=prompt, choices=(" Yes", " No")
    )
    prob = choice_probs.get(" Yes", 0)
    if prob > .95:
        return True
    return False

#TODO: Somehow mix with amplify!
async def answer_by_dispatch(
    question: str = "How many people live in Germany?", max_tool_use: int = 2
) -> str:
    context = []
    for _ in range(max_tool_use):
        action = await select_action(question, context=context)
        result, reasoning = await action.recipe(question=question, context=context)
        context.append(get_reasoning_context(result, reasoning, action))
        sufficient_prompt = make_sufficient_info_prompt(question, context)
        if await is_info_sufficient(sufficient_prompt):
            break

    answer = await recipe.agent().complete(
        prompt=make_final_prompt(question, context), stop='"'
    )
    return answer


recipe.main(answer_by_dispatch)
