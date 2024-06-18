from fvalues import F
from typing import Optional

from action_types import action_types


def make_action_selection_prompt(question: str, context: list[str] = []) -> str:
    action_types_str = F("\n").join(
        [
            F(f"{i+1}. {action_type.description}")
            for i, action_type in enumerate(action_types)
        ]
    )

    prefix_string = F(f"""You want to answer the question "{question}" """)
    if context:
        prefix_string += F("\n").join(context)
    suffix_string = F(
        f"""
    You have the following options:

    {action_types_str}

    Q: Which of these options do you want to use before you answer the question? Choose the option that will most help you give an accurate answer.
    A: I want to use option #"""
    ).strip()
    return prefix_string + suffix_string


def make_sufficient_info_prompt(question: str, context: list[str]) -> str:
    context_str = F("\n").join(context)
    return F(
        f"""You want to answer the question "{question}".

        You have the following context from the past actions:
        {context_str}.

        Q:Do you think you have enough information to answer the question? Say "A: Yes" or "A: No".
        A:"""
    )


def make_final_prompt(question: str, context: list[str]) -> str:
    context_str = F("\n").join(context)
    return F(
        f"""
        You have the following context from the past actions:
        {context_str}.

        Given the context, answer the following question:
        Question: "{question}"
        Answer: "

        """
    )

