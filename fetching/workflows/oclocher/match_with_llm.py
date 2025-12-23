import os

from openai import OpenAI, BadRequestError
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam, \
    ChatCompletionContentPartTextParam
from pydantic import ValidationError

from fetching.workflows.oclocher.oclocher_matrix import OClocherMatrix
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.llm_client import LLMProvider


def get_prompt_template():
    return """Please help me match churches from Source A to Source B.
Please return a json dict with key "mappings" being a list of pairs of int.
Each pair [a,b] indicates that Source A church with id a matches Source B church with id b.

Example:
Source A churches:
1: St. Peter's Church
2: Church of the Holy Trinity
Source B churches:
10: St. John's Parish
20: Holy Trinity Church
30: St. James' Cathedral
Would output:
{{"mappings": [[2,20]]}}

The Source A churches ids and locations to consider:
{church_description}

The Source B churches ids and locations to consider:
{location_description}"""


def get_church_desc(church_desc_by_id: dict[int, str]):
    return "\n".join(f'{church_id}: {desc}'
                     for church_id, desc in church_desc_by_id.items())


def build_prompt_text(prompt_template: str,
                      church_desc_by_id: dict[int, str],
                      location_desc_by_id: dict[int, str]) -> str:
    church_description = "\n".join(f'{church_id}: {desc}'
                                   for church_id, desc in church_desc_by_id.items())
    location_description = "\n".join(f'{location_id}: {desc}'
                                     for location_id, desc in location_desc_by_id.items())

    return prompt_template.format(church_description=church_description,
                                  location_description=location_description)


def build_input_messages(prompt_template: str,
                         church_desc_by_id: dict[int, str],
                         location_desc_by_id: dict[int, str]) -> list[ChatCompletionMessageParam]:
    return [
        ChatCompletionUserMessageParam(
            role="user",
            content=[
                ChatCompletionContentPartTextParam(
                    type="text",
                    text=build_prompt_text(prompt_template, church_desc_by_id, location_desc_by_id)
                )
            ]
        )
    ]


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def run_llm_completion(
        llm_model: str,
        prompt_template: str,
        church_desc_by_id: dict[int, str],
        location_desc_by_id: dict[int, str]
) -> tuple[OClocherMatrix | None, str | None]:
    openai_client = get_openai_client()
    try:
        temperature_args = {'temperature': 0.0} if llm_model != 'o3' else {}
        response = openai_client.chat.completions.parse(
            model=llm_model,
            messages=build_input_messages(prompt_template, church_desc_by_id, location_desc_by_id),
            response_format=OClocherMatrix,
            **temperature_args
        )
    except BadRequestError as e:
        print(e)
        return None, str(e)
    except ValidationError as e:
        print(e)
        return None, str(e)

    message = response.choices[0].message
    llm_matrix = message.parsed
    if not llm_matrix:
        return None, message.refusal

    return llm_matrix, None


def match_oclocher_with_llm(
        church_desc_by_id: dict[int, str],
        location_desc_by_id: dict[int, str]
) -> tuple[OClocherMatrix, str | None, LLMProvider, str, str]:
    llm_provider = LLMProvider.OPENAI
    llm_model = 'gpt-4.1'
    prompt_template = get_prompt_template()
    prompt_template_hash = hash_string_to_hex(prompt_template)

    llm_matrix, llm_error_detail = run_llm_completion(
        llm_model,
        prompt_template,
        church_desc_by_id,
        location_desc_by_id
    )

    return llm_matrix, llm_error_detail, llm_provider, llm_model, prompt_template_hash
