# 本工作区安装记录

来源：https://github.com/jeszhou/motion-explainer

上游提交：a18b7919a0b4421902b49b73831c68a140351e66（MIT，保留 LICENSE）。

安装在项目级 `.agents/skills/motion-explainer/`。本地适配：模板 `engine/lib.mjs` 的 macOS 字体改为 Noto CJK / DejaVu；建项目脚本的 skia-canvas 固定为 4.0.0；其余上游文件保持原样。

使用前在仓库根目录运行：

```bash
source .venv/bin/activate
export XDG_CACHE_HOME=/workspace/123/.cache
bash .agents/skills/motion-explainer/scripts/new_project.sh projects/my-film 9:16
```

目标必须是新目录：上游建项目脚本会覆盖同名模板文件。随后阅读本技能 SKILL.md，按其流程制作。依赖是 NumPy 2.4.2、skia-canvas 4.0.0、Node.js、FFmpeg 和中文字体。建新项目需要 npm 网络访问；本机已安装可运行的示例在 `.cache/motion-demo/`。

当前会话可以直接读取技能文件；项目级技能的自动发现可能需要新建会话。已有材料裁剪继续使用仓库原本的 FFmpeg 工作流。
