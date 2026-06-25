"""
智慧芽新药情报 MCP Server
封装接口：B049（药物类型ID查询）+ B007（药物搜索）
Transport：Streamable HTTP

认证方式：Bearer Token（每个用户在 Eureka Desktop 注册时填入自己的智慧芽 API Key）
  - 优先从请求 Header 读取：Authorization: Bearer <api_key>
  - 没有 Bearer Token 时，fallback 到环境变量 ZHIHUIYA_API_KEY（可留空）
"""

import os
import httpx
from fastmcp import FastMCP
from starlette.requests import Request

# ── 配置 ──────────────────────────────────────────────
BASE_URL = "https://connect.zhihuiya.com"

# 环境变量兜底（HF Spaces 可留空，让用户自己传 Bearer Token）
DEFAULT_API_KEY = os.environ.get("ZHIHUIYA_API_KEY", "")

mcp = FastMCP("zhihuiya-drug-intel")


def _get_api_key(request: Request) -> str:
    """
    从请求 Header 中提取 API Key。
    优先级：Authorization: Bearer <key>  >  环境变量 ZHIHUIYA_API_KEY
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        key = auth_header[len("Bearer "):].strip()
        if key:
            return key
    return DEFAULT_API_KEY


def _build_headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "apikey": api_key,
    }


# ── 工具1：B049 药物类型ID查询 ────────────────────────
@mcp.tool()
async def zhihuiya_drug_type_autocomplete(
    prefix: str,
    limit: int = 10,
) -> dict:
    """
    [B049] 输入药物类型关键字，返回匹配的药物类型ID及名称。
    用于获取 drug_type_id 后传入药物搜索接口。

    Args:
        prefix: 药物类型关键字，例如 "CAR-NK"、"ADC"、"双特异性抗体"
        limit:  返回条数，默认10，最大不限
    """
    # 从当前请求 context 获取 API Key
    from fastmcp.server import get_http_request
    request = get_http_request()
    api_key = _get_api_key(request) if request else DEFAULT_API_KEY

    url = f"{BASE_URL}/synapse/drug-type/autocomplete"
    payload = {"prefix": prefix, "limit": limit}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=_build_headers(api_key))
        resp.raise_for_status()
        return resp.json()


# ── 工具2：B007 药物搜索 ──────────────────────────────
@mcp.tool()
async def zhihuiya_drug_search(
    drug_type_ids: list[str] | None = None,
    target_ids: list[str] | None = None,
    disease_ids: list[str] | None = None,
    organization_ids: list[str] | None = None,
    mechanism_action_ids: list[str] | None = None,
    global_highest_dev_status: list[str] | None = None,
    dev_status: list[str] | None = None,
    country: list[str] | None = None,
    organization_type: list[str] | None = None,
    exist_deal: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    """
    [B007] 通过药物类型、靶点、适应症、机构等条件搜索药物管线。

    Args:
        drug_type_ids:              药物类型ID列表（由 B049 查询获取），OR 逻辑
        target_ids:                 靶点ID列表，支持 AND/OR（此处默认OR）
        disease_ids:                适应症ID列表，OR 逻辑
        organization_ids:           机构ID列表，OR 逻辑
        mechanism_action_ids:       作用机制ID列表，OR 逻辑
        global_highest_dev_status:  全球最高研发阶段过滤，枚举值：
                                    Discovery, Preclinical, IND, IND_Approval,
                                    Early_Phase_1, Phase_1, Phase_1_2, Phase_2,
                                    Phase_2_3, Phase_3, NDA_BLA, Approved,
                                    Clinical, Pending, Discontinued, Withdraw, Suspended, Unknown
        dev_status:                 按适应症研发状态过滤，枚举值同上
        country:                    国家/地区，枚举值：US, EU, JP, CN, Other
        organization_type:          机构类型，枚举值：Company, University_Institution, Other
        exist_deal:                 是否存在交易（True/False/None不过滤）
        offset:                     分页偏移，默认0
        limit:                      返回条数，默认50，最大1000；offset+limit<=10000
    """
    # 从当前请求 context 获取 API Key
    from fastmcp.server import get_http_request
    request = get_http_request()
    api_key = _get_api_key(request) if request else DEFAULT_API_KEY

    url = f"{BASE_URL}/synapse/drug/search"

    body: dict = {"offset": offset, "limit": limit}

    if drug_type_ids:
        body["drug_type"] = {"value": drug_type_ids, "condition": "OR"}
    if target_ids:
        body["target"] = {"value": target_ids, "condition": "OR"}
    if disease_ids:
        body["disease"] = {"value": disease_ids, "condition": "OR"}
    if organization_ids:
        body["organization"] = {"value": organization_ids, "condition": "OR"}
    if mechanism_action_ids:
        body["mechanism_action"] = {"value": mechanism_action_ids, "condition": "OR"}
    if global_highest_dev_status:
        body["global_highest_dev_status"] = global_highest_dev_status
    if dev_status:
        body["dev_status"] = dev_status
    if country:
        body["country"] = country
    if organization_type:
        body["organization_type"] = organization_type
    if exist_deal is not None:
        body["exist_deal"] = exist_deal

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=body, headers=_build_headers(api_key))
        resp.raise_for_status()
        return resp.json()


# ── 启动入口 ──────────────────────────────────────────
# 通过 uvicorn 启动：
#   uvicorn server:mcp_app --host 0.0.0.0 --port 8000
mcp_app = mcp.http_app(path="/mcp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)
