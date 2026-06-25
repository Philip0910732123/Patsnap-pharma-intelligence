"""
Hugging Face Spaces 入口文件
HF Spaces 默认识别 app.py，通过此文件启动 MCP Server
"""
import os
import uvicorn
from server import mcp_app  # 复用已有的 server.py

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))  # HF Spaces 默认端口 7860
    uvicorn.run(mcp_app, host="0.0.0.0", port=port)
