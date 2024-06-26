from fvalues import F

from ice.recipe import recipe


DEFAULT_CONTEXT = "We're running a hackathon on 9/9/2022 to decompose complex reasoning tasks into subtasks that are easier to automate & evaluate with language models. Our team is currently breaking down reasoning about the quality of evidence in randomized controlled trials into smaller tasks e.g. placebo, intervention adherence rate, blinding procedure, etc."

DEFAULT_QUESTION = "What is happening on 9/9/2022?"


def make_qa_prompt(context: str, question: str) -> str:
    return F(
        f"""
Background text: "{context}"

Answer the following question about the background text above:

Question: "{question}"
\n\nAssistant: "Let’s think step by step. 
"""
    ).strip()


def present_qa(context: str) -> str:
    return F(
        f""" This is a conversation between a human and a chatbot.
        
        Conversation: 
        "{context}"
        Given this conversation, can you answer the original question in a better, more refined, more concise way than the original answer?
        \n\nAssistant: "Let’s think step by step. 
        """
    ).strip()


async def answer(
    context: str = DEFAULT_CONTEXT, question: str = DEFAULT_QUESTION
) -> str:
    prompt = make_qa_prompt(context, question)
    answer = await recipe.agent().complete(prompt=prompt)
    for _ in range(3):
        prompt = prompt + ' \n\nAssistant: "Let’s think step by step. ' + answer
        answer = await recipe.agent().complete(prompt=present_qa(prompt), stop='"')
    return answer


recipe.main(answer)
