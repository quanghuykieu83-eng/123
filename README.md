# 视频剪辑工作区

已安装 **video-talkcraft**：口播配音驱动的 Remotion 动效视频及多轨工作台。[安装与使用说明](.agents/skills/video-talkcraft/INSTALLATION.md)。已验证渲染、工作台和本地 ASR 对齐；Fish Audio 接入已准备，需在云环境设置中安全配置 FISH_AUDIO_API_KEY 后才能调用。注意：该技能使用非商业许可，商用需作者授权。

已安装 **token-checkup**：本地分析 Claude Code / Codex 日志并生成用量 HTML 报告，无额外依赖。[使用说明与上游限制](.agents/skills/token-checkup/INSTALLATION.md)。本次仅完成合成数据验证，未扫描真实对话。

已安装 **weread-reading-note**：整理已导出的微信读书 Markdown，生成读书笔记与跨书关联语义卡。[使用说明](.agents/skills/weread-reading-note/INSTALLATION.md)。首次使用需指定笔记文件及输出目录，无需登录微信读书。

已安装 **montage-vlog-compiler**：用于参考片风格分析、口播语义与生活素材匹配、逐镜剪辑执行单。详见[安装和使用说明](.agents/skills/montage-vlog-compiler/INSTALLATION.md)。示例：`用 montage-vlog-compiler 根据我的参考片、口播和指定素材目录，整理一份旅行 Vlog 剪辑方案。` 可编辑初剪需另接执行器。

已安装项目级 **motion-explainer** 技能，可将文案制作成有配乐的竖版或横版动效短片。使用方式和依赖见 [.agents/skills/motion-explainer/INSTALLATION.md](.agents/skills/motion-explainer/INSTALLATION.md)。例如：`用 motion-explainer 把这段文案做成 30 秒竖版视频，无口播：……`。

通过 Codex 调用 FFmpeg 和 FFprobe 进行视频裁剪、拼接、转码、音频处理及中文字幕烧录。当前配置适合脚本剪辑，没有网页时间线界面，也不包含自动语音识别模型。

## 目录

| 路径 | 用途 |
| --- | --- |
| `media/` | 原始素材，默认不提交 Git |
| `output/` | 成片，默认不提交 Git |
| `subtitles/` | SRT / ASS 字幕 |
| `projects/` | 剪辑要求、时间点、导出参数 |
| `scripts/` | 环境及功能验证 |

## 环境

需要 Bash、Python 3、FFmpeg（含 libx264、AAC、libass）及中文字体（推荐 Noto CJK）。当前云环境已经提供这些工具，无额外 Python 包、API 密钥或后台服务要求。

```bash
cd /workspace/123
bash scripts/check.sh
bash scripts/smoke.sh
```

功能检查在临时目录生成测试视频，验证裁剪、拼接、字幕烧录、成片完整解码及媒体参数，结束后自动清理。

## 开始剪辑

将素材放入 `media/`，然后告诉 Codex，例如：

> 把 media/input.mp4 的第 10 至 25 秒剪出来，保留声音，输出到 output/clip.mp4。

> 把两个视频按顺序拼接，统一分辨率和帧率，添加 subtitles/captions.srt 中文字幕，输出 MP4。

也可以直接执行以下命令（示例文件需要自行提供）：

```bash
# 查看素材信息
ffprobe -v error -show_format -show_streams -of json media/input.mp4

# 从第 10 秒开始剪 15 秒；重新编码以获得准确剪辑点
ffmpeg -n -ss 10 -i media/input.mp4 -t 15 \
  -c:v libx264 -threads 2 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart output/clip.mp4

# 烧录已有 SRT 字幕（先检查字幕时间和中文字体）
ffmpeg -n -i media/input.mp4 \
  -vf "subtitles=subtitles/captions.srt:force_style='FontName=Noto Sans CJK SC'" \
  -c:v libx264 -threads 2 -crf 20 -pix_fmt yuv420p \
  -c:a aac -movflags +faststart output/captioned.mp4

# 检查成片是否能够完整解码
ffmpeg -v error -i output/clip.mp4 -f null -
```

保留原始素材；输出文件已存在时请换名称。不要将大视频、私人素材或密钥提交 Git。技能来源、固定版本和本地适配记录见各技能目录的 INSTALLATION.md。
