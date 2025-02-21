import json
import os
from time import sleep
from typing import Optional

from mistralai import Mistral, SDKError
from mistralai.extra import ParsedChatCompletionResponse
from pydantic import ValidationError

from scraping.parse.llm_client import LLMClientInterface, LLMProvider
from scraping.parse.schedules import SchedulesList


class MistralLLMClient(LLMClientInterface):
    client: Mistral

    def __init__(self, client: Mistral, model: str):
        self.client = client
        self.model = model

    def attempt_completion(self, messages: list[dict], temperature: float,
                           max_attempts=3) -> ParsedChatCompletionResponse:
        try:
            return self.client.chat.parse(
                model=self.model,
                messages=messages,
                response_format=SchedulesList,
                temperature=temperature,
            )
        except SDKError as e:
            if 'API error occurred: Status 429' in str(e):
                print('Rate limit exceeded, waiting 30 seconds')
                sleep(30)

                return self.attempt_completion(messages, temperature, max_attempts=max_attempts - 1)

            raise e

    def get_completions(self,
                        messages: list[dict],
                        temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        try:
            response = self.client.chat.parse(
                model=self.model,
                messages=messages,
                response_format=SchedulesList,
                temperature=temperature,
            )
        except SDKError as e:
            print('Mistral exception', e)
            return None, str(e)
        except ValidationError as e:
            print('validation error during llm call')
            print(e)
            return None, str(e)
        except json.JSONDecodeError as e:
            print('json error during llm call')
            print(e)
            return None, str(e)

        try:
            message_content = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            print('json error during parsing response')
            print(e)
            return None, str(e)

        try:
            schedules_list = SchedulesList.model_validate(message_content)
        except ValidationError as e:
            print('validation error during parsing response')
            print(e)
            return None, str(e)

        return schedules_list, None

    def get_provider(self) -> LLMProvider:
        return LLMProvider.MISTRAL

    def get_model(self) -> str:
        return self.model


def get_mistral_client(mistral_api_key: Optional[str] = None) -> Mistral:
    if not mistral_api_key:
        mistral_api_key = os.getenv("MISTRAL_API_KEY")

    return Mistral(api_key=mistral_api_key)


def get_mistral_llm_client() -> MistralLLMClient:
    mistral_model = 'mistral-large-latest'

    return MistralLLMClient(get_mistral_client(), mistral_model)
