import os
from typing import Optional

from openai import OpenAI, BadRequestError
from pydantic import ValidationError

from scraping.parse.schedules import SchedulesList


def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class OpenAILLMClient:
    client: OpenAI

    def __init__(self, client: OpenAI):
        self.client = client

    def get_completions(self,
                        model: str,
                        messages: list[dict],
                        temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        try:
            response = self.client.beta.chat.completions.parse(
                model=model,
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
