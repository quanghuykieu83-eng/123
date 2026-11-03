# 安装记录

- 来源：https://github.com/jeszhou/weread-reading-note-skill
- 上游提交：96b4fe5ccdfb985d5669891caef5602d44315415
- 许可：MIT，保留 LICENSE。
- 原仓库的 skill/ 内容安装到本目录，并附带 scripts/、examples/、README.md 和 config.example.yaml；上游内容未修改。
- 无第三方软件包或 API 密钥要求，配置工具仅使用 Python 3 标准库。

## 使用

对 Codex 说：`用 weread-reading-note 整理这份微信读书导出 Markdown：<文件路径>`，并提供读书笔记、语义卡的输出目录。读取 SKILL.md 后按其流程处理。

首次使用时确定 Obsidian vault、输入和输出路径；本次安装未创建实际 vault 或用户配置。需要手动配置时可运行：

```bash
python3 /workspace/123/.agents/skills/weread-reading-note/scripts/setup_config.py --vault /你的/vault
```

该脚本会写入（若存在则覆盖）vault 根目录的 weread-reading-note.config.yaml；已有配置请先阅读并保留。不要直接执行在未经确认的用户目录。

已验证技能本地文档链接完整、配置工具可在临时目录正确保存四个中文路径。尚未对用户真实笔记执行整理；安装不代表已经连接微信读书或 Obsidian。自动发现项目级技能可能需新会话，当前会话可直接读取 SKILL.md。
