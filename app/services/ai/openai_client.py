import base64

from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


class OpenAIClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.settings.openai_api_key is None:
            raise DocSuiteException("OPENAI_API_KEY no configurada", status_code=503)

        from openai import APIError, AsyncOpenAI, OpenAIError, RateLimitError

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except RateLimitError as exc:
            raise DocSuiteException(
                "OpenAI rechazo la solicitud por limite de uso. Intenta con un documento mas corto o vuelve a intentar en unos minutos.",
                status_code=503,
            ) from exc
        except APIError as exc:
            raise DocSuiteException("OpenAI no pudo procesar la solicitud.", status_code=502) from exc
        except OpenAIError as exc:
            raise DocSuiteException("Error al comunicarse con OpenAI.", status_code=502) from exc

        return response.choices[0].message.content or ""

    async def generate_with_images(
        self,
        system_prompt: str,
        user_prompt: str,
        images: list[tuple[bytes, str]],
    ) -> str:
        if self.settings.openai_api_key is None:
            raise DocSuiteException("OPENAI_API_KEY no configurada", status_code=503)

        from openai import APIError, AsyncOpenAI, OpenAIError, RateLimitError

        content: list[dict] = [{"type": "text", "text": user_prompt}]
        for image_bytes, mime_type in images:
            image_base64 = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                }
            )

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                temperature=0.1,
            )
        except RateLimitError as exc:
            raise DocSuiteException(
                "OpenAI rechazo la interpretacion visual por limite de uso.",
                status_code=503,
            ) from exc
        except APIError as exc:
            raise DocSuiteException("OpenAI no pudo interpretar la imagen.", status_code=502) from exc
        except OpenAIError as exc:
            raise DocSuiteException("Error al comunicarse con OpenAI para vision.", status_code=502) from exc

        return response.choices[0].message.content or ""
