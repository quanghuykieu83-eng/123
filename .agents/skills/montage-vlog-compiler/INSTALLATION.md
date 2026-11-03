# 安装记录

- 来源：https://github.com/jeszhou/montage-vlog-compiler
- 上游提交：a8fe4f5df7586fb6d6cf8d8cef811b0ef8fbe56a
- 许可：MIT，保留 LICENSE。
- 安装范围：当前仓库的项目级技能，上游文件未修改。
- 依赖：Python 3 和 FFprobe，当前环境已有，无需额外包或 API 密钥。

## 使用

先读 SKILL.md 和 examples/worked-example.md。仅在用户明确指定的素材目录中建清单。以下在仓库根目录执行，替换示例目录为实际授权路径；使用新的清单文件名避免覆盖。

```bash
python3 .agents/skills/montage-vlog-compiler/scripts/media_inventory.py media/ --output projects/inventory.json
python3 .agents/skills/montage-vlog-compiler/scripts/verify_inventory.py projects/inventory.json
```

已用临时生成的视频验证：媒体属性、音轨、时长、SHA-256、未变更通过，以及变更、丢失、新增素材时返回失败。未扫描用户私人素材。

技能生成风格档案、语义锚点和逐镜执行单；可编辑时间线需要另接执行器或手动剪辑。没有安装具体剪辑软件适配器。项目级技能自动发现可能需要新会话，当前会话可直接读取 SKILL.md 使用。
