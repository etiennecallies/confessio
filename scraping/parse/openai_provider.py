import os
from typing import Optional

from openai import OpenAI, BadRequestError
from pydantic import ValidationError

from scraping.parse.llm_client import LLMClientInterface, LLMProvider
from scraping.parse.schedules import SchedulesList


class OpenAILLMClient(LLMClientInterface):
    client: OpenAI

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def get_completions(self,
                        messages: list[dict],
                        temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=SchedulesList,
                temperature=temperature,
            )
        except BadRequestError as e:
            print(e)
            return None, str(e)
        except ValidationError as e:
            print(e)
            return None, str(e)

        message = response.choices[0].message
        schedules_list = message.parsed
        if not schedules_list:
            return None, message.refusal

        return schedules_list, None

    def get_provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    def get_model(self) -> str:
        return self.model


def get_openai_client(openai_api_key: Optional[str] = None) -> OpenAI:
    if not openai_api_key:
        openai_api_key = os.getenv("OPENAI_API_KEY")

    return OpenAI(api_key=openai_api_key)


def get_openai_llm_client() -> OpenAILLMClient:
    # TODO get latest fine-tuned model
    # openai_model = 'ft:gpt-4o-2024-08-06:confessio::AHfh95wJ'
    openai_model = 'gpt-4o-2024-08-06'  # or "gpt-4o-mini"

    return OpenAILLMClient(get_openai_client(), openai_model)
