import aiohttp
import json
from typing import AsyncGenerator, Dict, Any, List
from pydantic import BaseModel, Field

# 全局管理 aiohttp.ClientSession 以复用连接池
AIOHTTP_SESSION = None


async def get_aiohttp_session() -> aiohttp.ClientSession:
    """获取或创建全局 aiohttp 客户端会话。"""
    global AIOHTTP_SESSION
    if AIOHTTP_SESSION is None or AIOHTTP_SESSION.closed:
        AIOHTTP_SESSION = aiohttp.ClientSession()
    return AIOHTTP_SESSION


class Pipe:
    """
    一个高性能、支持多模型的 OpenWebUI 管道（Manifold），
    用于与 Cloudflare Workers AI 的 /v1/responses 端点进行交互。
    使用 aiohttp 实现异步请求以提升性能。
    """

    type: str = "manifold"
    id: str = "cloudflare_responses"

    class Valves(BaseModel):
        CLOUDFLARE_ACCOUNT_ID: str = Field(
            default="",
            title="Cloudflare Account ID",
            description="您的 Cloudflare 账户 ID。",
        )
        CLOUDFLARE_API_KEY: str = Field(
            default="",
            title="Cloudflare API Key",
            description="您的 Cloudflare Workers AI API 密钥。",
            extra={"type": "password"},
        )
        CLOUDFLARE_MODEL_IDS: str = Field(
            default="@cf/openai/gpt-oss-120b,@cf/openai/gpt-oss-20b",
            title="Cloudflare Model IDs",
            description="要使用的 Cloudflare模型ID列表，用逗号分隔。例如：@cf/model/a,@cf/model/b",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def pipes(self) -> List[Dict[str, str]]:
        """动态注册 Valves 中配置的所有模型。"""
        model_ids = [
            model_id.strip()
            for model_id in self.valves.CLOUDFLARE_MODEL_IDS.split(",")
            if model_id.strip()
        ]
        return [
            {"id": model_id, "name": f"Cloudflare: {model_id.split('/')[-1]}"}
            for model_id in model_ids
        ]

    async def pipe(
        self, body: dict, __user__: dict, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        # 正确地读取到值
        account_id = self.valves.CLOUDFLARE_ACCOUNT_ID
        api_key = self.valves.CLOUDFLARE_API_KEY

        full_model_id = body.get("model", "")

        model_id_start_index = full_model_id.find("@cf/")
        if model_id_start_index != -1:
            model_id = full_model_id[model_id_start_index:]
        else:
            model_id = full_model_id

        if not all([account_id, api_key, model_id]):
            yield "错误：Cloudflare 账户 ID、API 密钥或模型 ID 未正确配置或传递。"
            return

        api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/responses"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_id,
            "input": body.get("messages", []),
            "stream": False,
        }

        body_without_internal_keys = {
            k: v for k, v in body.items() if k not in ["model", "messages", "stream"]
        }
        payload.update(body_without_internal_keys)

        try:
            session = await get_aiohttp_session()
            async with session.post(api_url, headers=headers, json=payload) as response:
                if response.status >= 400:
                    error_content = await response.text()
                    yield (
                        f"调用 Cloudflare API 时发生 HTTP 错误: {response.status} {response.reason} - {error_content}"
                    )
                    return

                result = await response.json()

            final_text_parts = []
            if "output" in result and isinstance(result.get("output"), list):
                for item in result["output"]:
                    if (
                        item.get("type") == "message"
                        and item.get("role") == "assistant"
                    ):
                        if "content" in item and isinstance(item.get("content"), list):
                            for content_part in item["content"]:
                                if (
                                    content_part.get("type") == "output_text"
                                    and "text" in content_part
                                ):
                                    final_text_parts.append(content_part["text"])

            final_response = "".join(final_text_parts).strip()

            if final_response:
                yield final_response
            else:
                yield "错误：API 响应成功，但未能从中解析出有效的回复文本。"
                print(f"--- UNPARSABLE CLOUDFLARE RESPONSE FOR MODEL {model_id} ---")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("----------------------------------------------------")

        except aiohttp.ClientError as e:
            yield f"调用 Cloudflare API 时发生网络请求错误: {e}"
        except json.JSONDecodeError:
            yield f"错误：无法将 Cloudflare API 的成功响应解析为 JSON。"
        except Exception as e:
            yield f"发生意外错误: {e}"
