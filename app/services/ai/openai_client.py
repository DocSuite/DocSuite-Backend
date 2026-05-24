from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


class OpenAIClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.settings.openai_api_key is None:
            raise DocSuiteException("OPENAI_API_KEY no configurada", status_code=503)

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
