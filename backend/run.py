"""
Uvicorn 启动脚本，配置详细日志
"""
import uvicorn
import logging
import sys
from pathlib import Path

# 配置根日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# 设置应用日志级别
logging.getLogger('app').setLevel(logging.INFO)
logging.getLogger('app.routers').setLevel(logging.INFO)
logging.getLogger('app.services').setLevel(logging.INFO)

# 降低第三方库日志级别
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

if __name__ == "__main__":
    # 从环境变量或默认值获取配置
    import os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print("=" * 60)
    print("启动 OCR & Translate 后端")
    print("=" * 60)
    print(f"监听地址: {host}:{port}")
    print(f"日志级别: INFO")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
