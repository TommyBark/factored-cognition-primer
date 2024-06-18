from ice.recipe import recipe
from prompt import (
    make_action_selection_prompt,
    action_types,
    make_sufficient_info_prompt,
    make_final_prompt,
)
from action_types import Action
from fvalues import F
from ice.utils import map_async

Question = str
Answer = str
Subs = list[tuple[Question, Answer]]


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
    if prob > 0.95:
        return True
    return False


def make_subquestion_prompt(
    question: str, parent_questions: list = [], last_k_questions: int = 10
) -> str:

    if last_k_questions > 0:
        parent_questions = parent_questions[-last_k_questions:]
    prompt = F(
        f"""decompose the Question, start your response with 'Subquestions:' followed by 1 to 3 subquestions that are stand-alone and can be answered without the context of the original Question.

Question: "{question}" """
    )

    if len(parent_questions) > 1:

        prefix = (
            F(
                """  The following Question was generated based on the following parent questions. Consider these parent questions when decomposing and answering. 
Parent questions:"""
            )
            + F("\n").join(F(f"- {q}") for q in parent_questions)
            + F("\n\n")
            + F(
                """

Based on these questions, your own knowledge, and common sense, decide whether to:
1. Decompose the Question into subquestions that will help in answering it, or
2. Answer the Question directly.

If you decide to answer the Question directly, start your response with the word 'STOP' followed by the answer.

If you decide to  """
            )
        )
        prompt = prefix + prompt
    return prompt


def check_for_stop(text: str) -> bool:
    if "STOP" in text:
        return True
    return False


async def ask_subquestions(
    question: str = "What is the effect of creatine on cognition?",
    parent_questions: list[str] = [],
):
    prompt = make_subquestion_prompt(question, parent_questions=parent_questions)
    subquestions_text = await recipe.agent().complete(prompt=prompt)
    if check_for_stop(subquestions_text):
        return None, subquestions_text
    else:
        if "Subquestions:" in subquestions_text:
            subquestions = [
                line.strip("- ") for line in subquestions_text.split("\n")[1:]
            ]
        else:
            subquestions = [line.strip("- ") for line in subquestions_text.split("\n")]
        return subquestions, None


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
    subquestions, direct_answer = await ask_subquestions(
        question=question, parent_questions=parent_questions
    )
    if direct_answer is not None:
        return [(question, direct_answer)]
    subanswers = await map_async(
        subquestions,
        lambda q: unified_answer(
            question=q, depth=depth - 1, parent_questions=parent_questions
        ),
    )
    return list(zip(subquestions, subanswers))


async def unified_answer(
    question: str,
    depth: int = 2,
    max_tool_use: int = 1,
    parent_questions: list[str] = [],
) -> str:
    if not parent_questions:
        parent_questions = [question]
    else:
        parent_questions.append(question)

    context = []
    for _ in range(max_tool_use):
        action = await select_action(question, context=context)
        if action.name == "Reasoning":
            subquestions, direct_answer = await ask_subquestions(
                question=question, parent_questions=parent_questions
            )
            if direct_answer is not None:
                return direct_answer
            subanswers = await map_async(
                subquestions,
                lambda q: unified_answer(
                    question=q, depth=depth - 1, parent_questions=parent_questions
                ),
            )
            subs = list(zip(subquestions, subanswers))
            final_prompt = make_qa_prompt(question, subs)
            final_answer = await recipe.agent().complete(prompt=final_prompt, stop='"')
            return final_answer
        else:
            result, reasoning = await action.recipe(question=question, context=context)
            context.append(get_reasoning_context(result, reasoning, action))
            sufficient_prompt = make_sufficient_info_prompt(question, context)
            if await is_info_sufficient(sufficient_prompt):
                break

    answer = await recipe.agent().complete(
        prompt=make_final_prompt(question, context), stop='"'
    )
    return answer


recipe.main(unified_answer)
