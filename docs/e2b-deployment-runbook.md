# Gemma 4 E2B Jetson 部署 Runbook

本文档把 `E2B部署方案.md` 收敛成可执行步骤。首版目标只做一条稳定主线：

- Jetson Orin Nano 8GB + JetPack 6.2.1 / L4T 36.4.4
- 原生 `llama.cpp` + Gemma 4 E2B Q4 + `mmproj`
- FastAPI 网关接收 M400 或网页上传的 JPEG/PNG
- 先局域网演示，最后再用 Cloudflare Tunnel 暴露在线链接

技术证据链见 [`technical-evidence.md`](technical-evidence.md)。部署完成后，建议用本文档的 Runbook 复现，并用技术证据链讲解工程优势。

M400 接入的 HTTP 契约见 [`m400-inference-contract.md`](m400-inference-contract.md)。

如果 Jetson 访问 GitHub 或 Hugging Face 不稳定，先看 [`network-troubleshooting.md`](network-troubleshooting.md)，并运行 `scripts/network_diagnostics.sh` 判断是 Wi-Fi、DNS、HTTPS 还是大文件长连接问题。

## 认证结论：当前最佳主线

按官方资料和模型仓库重新核验后，当前最稳主线是：

```text
Jetson Orin Nano 8GB
  -> JetPack 6.2.1 / L4T 36.4.4
  -> Jetson AI Lab Docker 命令先冒烟
  -> 原生 llama.cpp 固化交付
  -> unsloth/gemma-4-E2B-it-GGUF Q4_K_S 文本模型
  -> 同仓 mmproj-F16
  -> FastAPI multipart 网关
  -> M400 1280x720 JPEG 上传
```

不建议把 `Q8_0` 文本模型作为 Orin Nano 8GB 的首版交付主线；它适合在你的 RTX 3090 工作站或 Jetson A/B 测试中做质量对照。也不建议把 Gemma 4 E2B 的音频输入放进 llama.cpp 关键路径；Jetson AI Lab 当前明确提示 E2B 在 Orin 上走 llama.cpp 有音频问题，所以语音应作为旁路增强。

你的本地电脑（Core Ultra 9 185H、32GB RAM、RTX 3090 24GB、约 466GB 可用存储）适合作为开发与验证主机：

- 预下载 HF 模型、记录 SHA256、整理 manifest。
- 用 RTX 3090 跑 Q8_0 / BF16 / Q4_K_M / Q4_K_S 的质量对比。
- 录制网页 demo、编译前端、写 Android/M400 端代码。
- 不作为最终边缘性能指标来源；最终 SLA 仍以 Jetson Orin Nano 8GB 实测为准。

## 0. 你先准备好

硬件：

- Jetson Orin Nano 8GB Developer Kit
- 2TB M.2 NVMe SSD，本轮硬件研发基线，挂载点使用 `/mnt/nvme`
- 稳定供电和主动散热
- Vuzix M400，可先不用 APK，先用网页上传完成闭环

机器可读硬件清单见 [`hardware-baseline.json`](hardware-baseline.json)，其中记录了 Jetson Nano 8GB 项目简称、2TB SSD、模型目录、上传缓存和审计日志路径。

账号/网络：

- Hugging Face 账号，最好提前在浏览器同意 Gemma 相关模型许可
- Jetson 能访问 Hugging Face、GitHub、NVIDIA 容器源
- 如果要公网 demo，准备 Cloudflare 账号和域名

## 1. 刷写和确认 JetPack

用 NVIDIA SDK Manager 或官方镜像刷 JetPack 6.2.1。启动 Jetson 后执行：

```bash
cat /etc/nv_tegra_release
df -h
free -h
```

验收：

- L4T 显示为 R36.4.4 或 JetPack 6.2.1 对应版本
- NVMe 已挂载，后续模型目录使用 `/mnt/nvme`
- 2TB SSD 可见，空闲磁盘至少 100GB，模型与演示数据优先放在 `/mnt/nvme`

## 2. 把仓库放到 Jetson

```bash
cd ~
git clone https://github.com/davidmillerak2026-sys/WearEdge-Pro.git
cd WearEdge-Pro
cp .env.example .env
```

编辑 `.env`：

```bash
nano .env
```

至少改掉：

```bash
DEMO_TOKEN=换成你自己的长随机token
```

## 3. 安装 Jetson 依赖

```bash
chmod +x scripts/*.sh
scripts/setup_jetson.sh
source .venv/bin/activate
hf auth login
```

验收：

```bash
python --version
hf auth whoami
```

## 4. 编译 llama.cpp

```bash
scripts/build_llama_cpp.sh
```

验收：

```bash
~/llama.cpp/build/bin/llama-server --help | head
```

## 5. 下载模型和 mmproj

默认下载 Jetson AI Lab 当前给 Orin Nano 推荐的 Q4_K_S 路线：

- `unsloth/gemma-4-E2B-it-GGUF` 里匹配 `*Q4_K_S*.gguf` 的文本模型
- 同一个 `unsloth/gemma-4-E2B-it-GGUF` 仓里的 `mmproj-F16.gguf`

```bash
scripts/download_models.sh
cat /mnt/nvme/models/gemma4-e2b/manifest.lock
```

如果你要测试方案里设想的 Q4_K_M 主线，改成：

```bash
TEXT_GLOB="*Q4_K_M*.gguf" scripts/download_models.sh
```

如果要测试更大的 projector，再改成：

```bash
MMPROJ_GLOB="mmproj-BF16.gguf" scripts/download_models.sh
```

如果要测试 ggml-org 官方 Q8_0 对照线，使用同仓配对，不要把不同仓库的文本模型和 projector 混用：

```bash
TEXT_REPO="ggml-org/gemma-4-E2B-it-GGUF" \
TEXT_GLOB="*Q8_0*.gguf" \
MMPROJ_REPO="ggml-org/gemma-4-E2B-it-GGUF" \
MMPROJ_GLOB="*mmproj*Q8_0*.gguf" \
scripts/download_models.sh
```

验收：

```bash
ls -lh /mnt/nvme/models/gemma4-e2b
cat /mnt/nvme/models/gemma4-e2b/manifest.lock
```

如果 HF 上文件版本变化，以实际 `manifest.lock` 为准，并把它附到部署记录里。

## 6. 启动 llama-server

开第一个终端：

```bash
cd ~/WearEdge-Pro
scripts/run_llama_server.sh
```

开第二个终端做文本冒烟：

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma4",
    "messages": [{"role":"user","content":"你好，做一个一句话自检"}],
    "chat_template_kwargs": {"enable_thinking": true},
    "max_tokens": 64
  }' | jq .
```

验收：返回 JSON，且 `choices[0].message.content` 有文本。

## 7. 启动 FastAPI 网关

再开一个终端：

```bash
cd ~/WearEdge-Pro
source .venv/bin/activate
scripts/run_fastapi.sh
```

局域网内打开：

```text
http://JETSON_IP:8081
```

或者直接测试：

```bash
curl -s http://127.0.0.1:8081/healthz | jq .
```

## 8. 图片上传闭环

先不用 M400，先拿一张本地 JPEG 测：

```bash
export DEMO_TOKEN=你的.env里同一个token
export TEST_IMAGE=/path/to/test.jpg
scripts/smoke_test.sh
```

验收：

- `/healthz` 正常
- llama-server 文本自检正常
- `/v1/infer` 返回 `ok: true`、`answer`、`scene`、`risk`、`action`
- `contract.ok` 为 `true`；如果 `contract.repaired` 为 `true`，说明网关自动修正过一次模型输出格式
- `scripts/smoke_test.sh` 会自动校验 `scene/risk/action` 和 `contract.violations`，不合格会直接失败退出
- 如果 `.env` 设置了 `WEAREDGE_EVENT_LOG`，响应中的 `audit.logged` 应为 `true`

推荐演示 Prompt：

```text
Return exactly this format and nothing else:
- Scene: <one short phrase>
- Risk: <one short hazard>
- Action: <one safe next action>

Rules:
Scene must describe the place.
Risk must name a hazard.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be more than 15 words.
Do not add any introduction.
```

## 9. M400 接入

第一阶段先让 M400 和 Jetson 在同一 Wi-Fi 或 Jetson 热点下：

```text
Jetson: http://JETSON_IP:8081/v1/infer
Header: Authorization: Bearer <DEMO_TOKEN>
Form:
  prompt=<你的问题>
  image=@frame.jpg
  device_id=m400-demo-01
  frame_ts=<M400采图时间>
  location_hint=<现场位置>
  capture_mode=manual-trigger
```

M400 APK 只需要先完成三件事：

1. Camera2 拍一张 1280x720 JPEG。
2. 用 HTTP multipart 上传到 `/v1/infer`。
3. 读取返回 JSON 里的 `scene`、`risk`、`action`、`request_id`。
4. 先把 `action` 显示出来。

等这条链路稳定后，再加语音触发或骨传导播报。

## 10. 安装 systemd 服务

确认手动启动稳定后再安装服务：

```bash
sudo cp deploy/systemd/wearedge-llama.service /etc/systemd/system/
sudo cp deploy/systemd/wearedge-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wearedge-llama.service
sudo systemctl enable --now wearedge-gateway.service
systemctl status wearedge-llama.service
systemctl status wearedge-gateway.service
```

如果你的仓库不在 `/home/jetson/WearEdge-Pro`，先改两个 service 文件里的路径。

## 11. 公网演示

开发期临时预览：

```bash
cloudflared tunnel --url http://localhost:8081
```

正式演示建议使用命名隧道：

```bash
sudo cloudflared service install <TUNNEL_TOKEN>
systemctl status cloudflared
```

公网暴露前务必确认：

- `.env` 里设置了强 `DEMO_TOKEN`
- 没有开启 `WEAREDGE_AUTH_DISABLED=true`
- demo 页面只暴露上传和推理，不暴露本地目录

## 12. 每次演示前的检查顺序

```bash
df -h /mnt/nvme
free -h
tegrastats
systemctl status wearedge-llama.service
systemctl status wearedge-gateway.service
curl -s http://127.0.0.1:8081/healthz | jq .
```

然后用 `scripts/smoke_test.sh` 跑一张固定测试图。

如需记录隐私优先推理审计日志，可在 `.env` 追加：

```bash
WEAREDGE_EVENT_LOG=/home/ryn/WearEdge-Pro/runtime/inference-events.jsonl
```

然后重启网关：

```bash
sudo systemctl restart wearedge-gateway.service
```

查看最新事件：

```bash
tail -n 3 /home/ryn/WearEdge-Pro/runtime/inference-events.jsonl | jq .
```

也可以通过受 token 保护的网关接口查看最近事件：

```bash
curl -s "http://127.0.0.1:8081/v1/audit/recent?limit=3" \
  -H "Authorization: Bearer $DEMO_TOKEN" | jq .
```

实测时，HTTP 响应与 JSONL 日志中出现同一个 `request_id=5b33c68044d748dda77b2a5546968c8f`，且 `saved_path=null`，证明系统可以追踪推理事件但默认不保存图片本体。

验收通过后，应该看到：

```text
llama-server text health passed.
Gateway output contract passed.
```

这两句可以直接作为现场展示的工程证据：第一句证明模型服务可见输出正常，第二句证明图片推理结果满足 `scene/risk/action` 输出契约。

## 参考资料

- Jetson AI Lab: https://www.jetson-ai-lab.com/tutorials/gemma4-on-jetson/
- Jetson AI Lab E2B model page: https://www.jetson-ai-lab.com/models/gemma4-e2b
- NVIDIA JetPack 6.2.1 release notes: https://docs.nvidia.com/jetson/jetpack/release-notes/index.html
- llama.cpp multimodal docs: https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md
- FastAPI request files: https://fastapi.tiangolo.com/tutorial/request-files/
- Vuzix M400 technical details: https://support.vuzix.com/docs/m400-m4000-technical-details
- Vuzix M400 camera docs: https://support.vuzix.com/docs/camera
- Cloudflare Tunnel setup: https://developers.cloudflare.com/tunnel/setup/
