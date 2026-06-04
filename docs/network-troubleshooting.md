# Jetson 网络问题分析与解决记录

本文档记录 WearEdge Pro 在 Jetson Orin Nano 部署过程中遇到的网络问题、根因判断和固定处理办法。它的目标是把一次性的排障经验变成后续可复用的工程流程。

## Windows Android Gradle 依赖解析

在 Windows 上验证 `clients/m400/android` 时，Android Studio 可以完成项目同步，但命令行首次执行：

```powershell
.\gradlew.bat :app:assembleDebug --no-daemon
```

曾遇到：

```text
Could not GET https://repo.maven.apache.org/...
UnknownHostException: repo.maven.apache.org
```

诊断结果：

- `repo.maven.apache.org` DNS 解析失败。
- `maven.aliyun.com` 可访问，并且能返回 Kotlin 和 Android Gradle Plugin 依赖。

处理方式：

- `clients/m400/android/settings.gradle.kts` 中加入 Aliyun Maven 镜像优先。
- 官方 `google()`、`mavenCentral()`、`gradlePluginPortal()` 仍保留为兜底源。

这样国内网络下可以优先走可达镜像，海外或 CI 环境仍可回落到官方源。

## 现象总览

| 问题 | 现场表现 | 根因判断 | 已采用解决办法 |
| --- | --- | --- | --- |
| SSH 连错地址 | Windows 执行 `ssh ryn@127.0.1.1` 返回 `Connection refused` | `127.x.x.x` 是本机回环地址，不是 Jetson 地址 | 在 Jetson 上用 `ip addr` 找到 Wi-Fi 地址 `192.168.0.155`，Windows 改为 `ssh ryn@192.168.0.155` |
| Jetson 外网不稳定 | `ping github.com` 有丢包，`ping 8.8.8.8` 也有丢包 | Wi-Fi 链路可用但质量不稳定，可能受路由器、信道、地区链路影响 | 关键下载不依赖 Jetson 在线完成，改为 Windows 下载后 `scp` 传入 |
| Hugging Face 不通 | `hf auth login` 报 `[Errno 101] Network is unreachable`，`curl https://huggingface.co` 失败 | Jetson 到 Hugging Face 的 HTTPS 链路不稳定或被中间网络阻断 | 在 Windows 浏览器手动下载 GGUF 模型和 `mmproj`，通过 `scp` 传到 Jetson |
| HF 镜像也不稳定 | `hf-mirror.com` 首次连接超时，部分仓库页面能返回 200 | 镜像站可达性不稳定，不适合作为唯一自动化依赖 | 保留镜像作为备选，不把它作为首版部署主路径 |
| GitHub clone 失败 | `git clone llama.cpp` 报 HTTP2 framing / GnuTLS TLS termination | Git over HTTPS 长连接在当前网络下不稳定 | 设置 `git config --global http.version HTTP/1.1`，必要时用 Windows 下载 zip 后传入 Jetson |
| Windows PowerShell profile 报错 | PowerShell 启动时提示 `profile.ps1` 禁止运行脚本 | Windows 执行策略问题，不影响 SSH/SCP/Git 本身 | 忽略该提示，或后续用 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 修复 |

## 固定诊断脚本

Jetson 上可以运行：

```bash
cd ~/WearEdge-Pro
chmod +x scripts/network_diagnostics.sh
scripts/network_diagnostics.sh
```

脚本会输出：

- 网卡和 IP
- 默认路由
- DNS 配置
- 网关 ping
- `8.8.8.8`、GitHub、Hugging Face ping
- GitHub、Hugging Face、HF Mirror HTTPS 探测
- Git 全局 HTTP 配置

## 推荐的稳定 Git 配置

在 Jetson 上执行：

```bash
git config --global http.version HTTP/1.1
git config --global http.postBuffer 524288000
```

这不能解决所有网络问题，但能降低 GitHub HTTP/2 / TLS 中断导致 clone 失败的概率。

## 模型下载策略

首选路径：

```text
Windows 浏览器下载模型
  -> 校验文件名和大小
  -> scp 到 Jetson
  -> .env 指向本地模型路径
```

已验证的本地模型路径：

```text
/home/ryn/WearEdge-Pro/models/gemma4-e2b/gemma-4-E2B-it-Q4_K_S.gguf
/home/ryn/WearEdge-Pro/models/gemma4-e2b/mmproj-F16.gguf
```

原因：模型文件较大，Jetson 当前 Wi-Fi 链路对 Hugging Face 大文件下载不够稳定；Windows 下载和断点续传体验更可控。

## llama.cpp 获取策略

优先尝试：

```bash
git config --global http.version HTTP/1.1
git clone --depth 1 https://github.com/ggml-org/llama.cpp.git ~/llama.cpp
```

如果仍失败：

1. Windows 浏览器下载 `llama.cpp` zip。
2. 用 `scp` 传到 Jetson。
3. Jetson 解压到 `~/llama.cpp`。
4. 继续执行 CMake 编译。

这就是本次成功采用的路径：绕开不稳定 clone，把编译链路留在 Jetson 本地完成。

## 如何判断问题类型

| 判断命令 | 结论 |
| --- | --- |
| `ping <router-ip>` 失败 | Wi-Fi 或路由器连接问题 |
| `ping 8.8.8.8` 成功但 `ping github.com` 失败 | DNS 问题 |
| `ping github.com` 成功但 `curl https://github.com` 失败 | HTTPS/TLS 或代理链路问题 |
| GitHub 可用但 Hugging Face 不可用 | HF 站点链路或区域访问问题 |
| 小文件可下载，大文件中断 | 长连接稳定性问题，使用 Windows 下载 + `scp` |

## 当前结论

本项目已经规避了部署中最容易卡住的网络路径：

- Jetson 运行推理不依赖 Hugging Face 在线访问。
- Gemma 4 E2B 模型和 `mmproj` 已在本地。
- `llama.cpp` 已在本地构建完成。
- 后续演示只需要局域网内访问 `http://JETSON_IP:8081`。
- 若需要重新部署，可先运行 `scripts/network_diagnostics.sh` 决定走在线下载还是 Windows 下载 + `scp`。
