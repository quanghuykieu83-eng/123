# 视频剪辑工作约定

- 用户明确要求 video-talkcraft 或口播配音视频时，先读 `.agents/skills/video-talkcraft/INSTALLATION.md` 和 SKILL.md。复用独立 `.venv-talkcraft`、锁定 runtime 及系统 Chromium 的本地适配。该工具是非商业许可，酒店营销等商用前需处理作者授权；本地 ASR 模型已安装，入口 scripts/talkcraft-align.sh。用户已要求启用 Fish Audio，调用入口 scripts/talkcraft-tts.sh；当前缺少密钥时提示在环境设置中安全配置，不向聊天索取密钥。

- 用户要求 token 体检时，先读 `.agents/skills/token-checkup/SKILL.md` 和 `reference/narrative-rules.md`，再按 INSTALLATION.md 检查已知限制。安装不等于授权扫描真实日志；输出写入 `output/token-checkup/`，不能把合成测试当成真实用量。

- 用户要求整理微信读书导出的 Markdown、生成读书笔记或语义卡时，先读 `.agents/skills/weread-reading-note/SKILL.md`。先确定用户实际 vault 和输出路径，不自动创建默认笔记目录；保留已有语义卡中的用户理解。

- 用户要求情绪混剪 Vlog、参考片风格学习或按口播匹配生活素材时，先读 `.agents/skills/montage-vlog-compiler/SKILL.md` 和 `examples/worked-example.md`。该技能输出剪辑方案；不要声称已经创建可编辑时间线或成片，除非实际执行并验证。

- 用户要求将文案或要点制作成动效短片时，先读 `.agents/skills/motion-explainer/SKILL.md`，再按该技能执行。环境使用方法见该目录的 `INSTALLATION.md`。普通素材剪辑仍使用 FFmpeg。

- 使用现有工作目录；每个云任务已有隔离环境，无需另建 Git worktree。
- 优先使用 FFmpeg / FFprobe 和 Python 标准库；新增依赖前说明用途。
- 开始剪辑前用 FFprobe 检查素材的时长、尺寸、帧率和音轨。
- 原始素材放在 media/，成片放在 output/，字幕放在 subtitles/，剪辑方案放在 projects/。
- 保留原始素材。禁止直接覆盖输入文件；FFmpeg 默认使用 -n，输出使用新文件名。
- 素材和成片默认不进入 Git；不要提交凭据或私人媒体。
- 默认导出 MP4、H.264、yuv420p、AAC 和 +faststart；保持源视频比例，除非用户指定横屏或竖屏。
- 批量转码前先处理短片段，确认参数、字体和声音；控制 CPU 并行度。
- 完成后完整解码检查成片，并用 FFprobe 核对时长、分辨率和音轨。实际观看/试听尚未执行时需如实说明。
- 环境检查：bash scripts/check.sh；功能检查：bash scripts/smoke.sh。
