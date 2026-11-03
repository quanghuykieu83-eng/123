# 安装记录

- 来源：https://github.com/jeszhou/token-checkup
- 上游提交：17d9658fdfd8b403edcee858aaec64d57d43c6ce
- 许可：MIT，保留 LICENSE；上游代码未修改。
- 安装范围：当前仓库的项目级技能。
- 依赖：Python 3.8+ 标准库，无额外包、API 密钥或后台服务。

## 使用

用户要求「用 token-checkup 做一次 token 体检」时，先读 SKILL.md 和 reference/narrative-rules.md。仅分析实际可访问的本机日志；当前云环境不等于用户电脑，不能自动看到用户电脑上的历史。

建议在独立、被 Git 忽略的报告目录运行，避免统计文件进入版本库。例如从仓库根目录执行：

```bash
mkdir -p output/token-checkup
cd output/token-checkup
python3 ../../.agents/skills/token-checkup/scripts/scan.py -o facts.json
```

后续报告和基线步骤按 SKILL.md 执行。首次真实体检需要由用户选择操作阈值；安装阶段不设置阈值，也不改状态栏。

## 验证与限制

- 已使用隔离的 60 轮合成 Claude 日志验证扫描，独立核对输入 token 和缓存读取 token 总数。
- 在含工具调用的合成数据上验证完整 HTML、趋势 HTML 和同日基线去重；合成数据不表示用户真实用量或真实趋势。
- 未扫描用户真实对话，也没有生成真实体检基线。
- 上游 scan.py 在没有 ~/.claude/projects 时直接退出，即使存在 Codex 日志。仅 Codex 数据的完整体检目前受此限制；不要用假数据绕过真实统计。
- 上游 render_report.py 在工具调用数为零时会对空 error_rate_pct 做数值格式化并报 TypeError。该边界缺陷尚未修改；遇到时如实报告，不伪造工具调用或把缺失值改为零。
- 项目级技能自动发现可能需要新会话，当前会话可直接读取 SKILL.md。
