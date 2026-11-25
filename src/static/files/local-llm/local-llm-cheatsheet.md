# 本地推理部署速查（Ollama + Open WebUI）

> 文中所有地址均为文档示例地址（`192.0.2.10`），实际使用时替换成你的对端地址。端口、路径按默认保留。

## 机器与链路

- Mac mini M6：12 核 CPU（2 超级核 / 4 性能核 / 6 能效核）、12 核 GPU、24GB 统一内存
- macOS 27.2.1，460GB 盘
- 雷雳桥对端地址（示例）：`192.0.2.10`，链路 40Gb/s

## Ollama

- 版本 v0.40.17，解压在 `~/opt/ollama-v0.40.17`，不装 Homebrew、不用 sudo
- LaunchAgent：`com.ollama.serve`，端口 `11434`
- 模型：Qwen3-8B-Q4_K_M（5.03GB），命名 `qwen3-8b`，上下文 16384
- 实测：生成 29 token/s，预填充约 800 token/s，显存 6.8GB，空闲卸载后冷启动约 2 秒

```bash
# 命令行封装（加 -t 开思考模式）
~/bin/qwen "把这段文字里的时间、地点、人物抽成 JSON"

# 原生接口
curl http://192.0.2.10:11434/api/chat -d '{
  "model": "qwen3-8b",
  "messages": [{"role": "user", "content": "抽取时间、地点、参会人"}],
  "think": false,
  "stream": false
}'

# OpenAI 兼容
# base_url = http://192.0.2.10:11434/v1
# api_key  = "ollama"
```

批量处理一定要带 `"think": false`，或在消息末尾加 `/no_think`；否则 8B 会先输出一大段推理，慢 2–4 倍。

```bash
# 停止（先释放模型，再卸载服务）
curl -s http://192.0.2.10:11434/api/chat \
  -d '{"model":"qwen3-8b","keep_alive":0}'
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.ollama.serve.plist

# 恢复
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ollama.serve.plist
```

## Open WebUI

- 0.13.4，端口 `8080`，数据在 `~/.open-webui`，第一个注册的账号是管理员
- 生图：`images.connections` → ComfyUI `127.0.0.1:8188`；注册 qwen-image-2.1-turbo / krea2-turbo / moss-image-sft
- 生图代理：`127.0.0.1:8189`（LaunchAgent `com.comfyui.proxy`），只在切换底模时调 `/free`
- TTS 中转：Gradio → `/v1/audio/speech`，按 120 字切句，用 lameenc 直接出 MP3（不依赖 ffmpeg）
- 常驻只留 Open WebUI（约 130MB）与 Ollama API；Ollama 空闲 5 分钟卸载，TTS 空闲 10 分钟回收

```bash
# 图像工作台
# http://192.0.2.10:8080/playground/images

# 接口生图
curl -X POST http://192.0.2.10:8080/api/v1/images/generations \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"model":"comfyui-qwen:qwen-image-2.1-turbo","prompt":"一只橘猫在窗台","size":"1024x1024"}'
```

## /free 的判定条件

1. 用 `unet_name` + `clip_name` 生成底模签名，与上次相同就直接转发，不动内存
2. 换模型才卸载：先等队列空闲，再 `/free`
3. 卸载后等可用内存回到 6GB 以上，不够就重试
4. ComfyUI 不在跑就冷启动，所以可以随时 `pkill` 它来省内存

`/free` 返回 `0 models unloaded` 通常表示队列还在跑，不要把它当成「已卸载」。

## 24GB 上的实测单张（1024×1024）

- qwen-image-2.1-turbo：约 96 秒
- moss-image-sft：约 385 秒
- krea2-turbo：约 379 秒（13GB 权重 + 4.6GB 文本编码器，顶到 24GB 天花板）

## 降内存的顺序

1. 先降画布尺寸
2. 再减同时加载的模型 / LoRA
3. 最后才考虑放开 MPS 水位（速度会掉到约四分之一）
