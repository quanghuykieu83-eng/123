# 当前云环境安装说明

- 来源：https://github.com/Vincentwei1021/video-talkcraft
- 固定提交：a7c29edfb2404612dde6a5a1c8aa94232e85625b
- 安装位置：项目级 `.agents/skills/video-talkcraft/`；保留 LICENSE、THIRD_PARTY_NOTICES.md 和素材归属说明。
- 许可是 PolyForm Noncommercial，作者要求商业使用先授权。安装不表示已取得商业授权；酒店营销等商用制作前须先解决授权。

## 运行环境

Node.js 24；FFmpeg；Remotion 4.0.519（上游 runtime 锁文件）；Python 3.12 独立环境 `/workspace/123/.venv-talkcraft/`，固定依赖记录在仓库根目录 requirements-talkcraft.txt。与 motion-explainer 的 .venv 分离。

```bash
cd /workspace/123
source .venv-talkcraft/bin/activate
export XDG_CACHE_HOME=/workspace/123/.cache
```

本机已有 `/usr/bin/chromium`。已验证的渲染自检（从技能目录运行）：

```bash
runtime/node_modules/.bin/remotion still runtime/smoke/index.ts Smoke /tmp/video-talkcraft-smoke.png --frame=5 --browser-executable=/usr/bin/chromium --concurrency=1
```

本环境启动 Chromium 需允许浏览器子进程运行的执行模式。不要以关闭 TLS 校验解决启动问题。上游 check-runtime.sh 会另下载无头浏览器；这里复用系统 Chromium，以显式 --browser-executable 参数执行。未运行自动版本升级，制作时保持当前依赖版本一致。

本地安装适配：排除上游 workbench/node_modules 指向作者 macOS 的绝对链接，改为 `../runtime/node_modules`；补建 `gallery/media/`，解决上游 `workbench/public/cardpreviews` 指向不存在目录而导致的构建错误。未下载该目录的可选画廊视频；动态卡片和 HTML demo 源码均已保留。

## 工作台

```bash
cd /workspace/123/.agents/skills/video-talkcraft/workbench
npm run dev -- --host 127.0.0.1 --port 5179 --strictPort
```

启动后检查页面标题包含 `TalkCraft Workbench`，并确认 `/src/main.tsx` 能编译响应。当前安装测试结束后已停止临时服务。没有绑定实际口播工程，工作台以 kbsrc-stub 方式运行；制作新片时按上游契约接入真实项目。当前聊天不提供该本地服务的网页预览。

## 验证范围

- 25 项 Fish Audio 离线回归测试通过；使用模拟响应，无真实 API 调用。
- 23 项 render_shots 流程测试通过，无跳过。
- 实际 Chromium 渲染测试帧成功。
- 工作台 TypeScript/Vite 生产构建成功，页面标题及 Vite 入口请求验证成功。构建仍有未接工程的音效别名警告及大包提示，不阻塞构建。
- 已安装 FireRedASR2-CTC int8 模型，位置 `.cache/models/sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25/`。官方压缩包约 497MiB，模型文件约 740MiB；已记录并校验 SHA-256。官方样例真实 CPU 推理产出 23 个带时间的 token；另用本地合成英语短句跑通识别、文本对齐及 Remotion timing 转换，match=1.00（文本映射检查，不等于人工确认识别精度）。
- 已按用户要求准备 Fish Audio 接入：依赖和调用入口已安装，云环境草稿登记 FISH_AUDIO_API_KEY，并添加 api.fish.audio。当前环境仍无密钥，真实 API 尚未启用或调用；用户需在环境设置中安全填写密钥、保存并发布，再验证配音请求。无需启动本地配音守护进程。
- 安装不等于完成视频制作或取得商业授权。项目级技能自动发现可能需新会话，当前会话可直接读取 SKILL.md。

## 模型与外部配音入口

在仓库根目录执行：

```bash
# 下载/校验模型（模型和压缩包均在 Git 忽略目录）
bash scripts/download-talkcraft-model.sh
# 成品配音 + 逐字一致的稿件 → 时间戳
bash scripts/talkcraft-align.sh audio/full.wav script.json audio/timestamps.json
# 设置中安全配置 FISH_AUDIO_API_KEY 生效后：生成配音和时间戳
bash scripts/talkcraft-tts.sh script.json audio/full.wav audio/timestamps.json
```

输出使用新文件名，避免覆盖现有音频。Fish Audio 配音可能消耗账户额度，模型可用性和价格由服务商决定；当前没有调用真实服务。默认模型沿用上游 s2.1-pro-free。模型权重不推送 GitHub；下载脚本和校验值会提交。
