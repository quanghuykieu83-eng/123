---
name: montage-vlog-compiler
description: 用户要做情绪混剪 Vlog 时使用——以第一人称口播为时间主轴、由零散生活素材拼成、靠情绪推进的叙事型片子，题材包括母婴、亲子、旅行、成长、关系等。用于分析参考片剪法、按口播语义匹配画面、整理大量本地素材、生成逐镜剪辑执行单与可编辑初剪的执行器指令、或把剪辑反馈沉淀成个人风格。不适用于知识口播、产品测评、教程、访谈、纯音乐卡点。
---

# 情绪混剪 Vlog 剪辑编译器

## 目标

把“我喜欢这种感觉”翻译为可执行、可验证、可继续修改的剪辑方案。生成可编辑初剪，不承诺无需观看的一键终稿。

始终把原始素材视为只读。只处理用户指定范围；未经明确授权，不扫描其他私人目录、不发布、不发送、不删除、不覆盖旧时间线。

## 适用范围

**情绪混剪 Vlog**：以第一人称旁白为时间主轴、由多条零散生活素材拼成、靠情绪推进的片子。

不适用于知识口播、产品测评、教程、访谈实录、赛事集锦、纯音乐卡点——这些题材的画面不由口播语义决定，或干脆没有口播可作时间主轴。

### 验证范围

规则全部来自母婴题材的真实剪辑和用户修改记录，**已验证范围仅限该题材**。

其他情绪混剪题材（旅行、成长、关系、宠物、品牌情绪等）原理相通，但没有实测证据。用在这些题材上时，把结论按 `hypothesis` 对待，不要当成已验证规则。

**「未验证」不等于「不适用」，两者不得混写。**

### 换题材时的处理

| 层 | 处理方式 |
|---|---|
| 证据状态机、偏好状态机、素材只读与授权边界、时间四态 | **直接沿用。** 与题材无关。 |
| 镜长档位、叙事状态划分、声场与转场设计 | **必须重做。** 用该题材自己的参考片重新推导，不要沿用本包的数值。 |
| 风格档案 | **必须自己建。** 它是题材和个人审美的产物，不可继承。 |

## 选择任务路线

- 只有参考片：学习参考风格，读取 [references/style-learning.md](references/style-learning.md)。
- 有真实口播和 SRT：使用语义锚点模式，读取 [references/semantic-anchor-method.md](references/semantic-anchor-method.md)。
- 有文案、素材和风格档案：编译素材匹配与逐镜执行单。
- 要交给剪辑产品执行：读取 [references/executor-contract.md](references/executor-contract.md)，生成对应执行器指令。
- 已有初剪或用户修改：读取 [references/preference-learning.md](references/preference-learning.md)，先生成候选偏好。

输入足够时直接执行当前阶段。只有缺失项会改变口播主版本、授权范围、叙事目标或关键语义落点时才暂停确认。

## 使用证据状态

为关键结论标记一种状态：

- `verified_source`：文案、SRT、风格档案等文本输入已直接读取。
- `verified_meta`：已用工具读取媒体属性（时长、实际显示方向、音轨是否存在、哈希）。
- `verified_still`：已看过该素材的静帧。
- `verified_motion`：已连续播放看过该素材的动态画面。
- `verified_audio`：已试听过该素材的声音。
- `verified_executor`：从执行器时间线、画面、声音或产物直接读回。
- `user_feedback`：用户观看或修改后的明确判断。
- `confirmed_preference`：用户确认可以跨项目复用的偏好。
- `hypothesis`：下一轮可测试，但尚未证实。
- `pending_validation`：缺少连续播放、试听、动态画面或其他直接验证。

每种读取方式只能支撑它真正看得到的结论，能力边界见 [references/evidence-safety.md](references/evidence-safety.md)。静帧看不出动作起落，有音轨不等于听过。工具自报、轨道存在和用户验收是不同证据，不得互相代替。

## 工作流

### 1. 建立输入边界

1. 登记参考片、口播、SRT、文案、素材目录、指定素材、平台、画幅、授权和隐私限制。
2. 用 `scripts/media_inventory.py` 扫描明确授权的素材目录，输出媒体清单；不要手写猜测时长、方向、音轨或哈希。
3. 让用户确认可用于当前项目的素材范围。
4. 对高风险素材降险。高风险指画面中出现：未成年人的裸露或泳装；可辨识的第三方人物，尤其是儿童；私人屏幕、证件、住址、门牌或车牌；烧录的第三方水印、贴纸或品牌标识。
   优先用收紧入出点避开风险内容。只有风险无法通过入出点避开时，才另存一份安全片段——写到独立目录，保存“安全片段 → 原片 → 入出点”映射，原片本身不动。派生副本不等于修改原始素材。
5. 只有本地素材存在明确语义缺口时才补外部素材；保存原始页面、作者、许可证、下载日期和用途。

### 2. 学习参考风格

逐条分析用户指定的全部参考片，分别提取叙事、情绪、文案—画面关系、镜头语言、镜长档位、人物关系、字幕、音乐和环境声。

只把跨样本重复出现且有定位证据的特征写入参考风格。把单片特征、用户偏好和未验证假设分开保存。不要预装某位创作者、题材比例、固定 BPM 或平均镜长公式。

输出 [assets/style-profile-template.md](assets/style-profile-template.md)。

### 3. 编译语义与素材

先划分人物状态、时间、空间和行动目标，再逐句匹配素材。为每个状态标记允许场景、允许声场、边界动作和禁止无提示返回的旧状态。

有真实口播和 SRT 时，以真实口播决定总时长、停顿和重音，以 SRT 作为语义与字幕索引。生成 [assets/semantic-anchor-table-template.md](assets/semantic-anchor-table-template.md)：

- 口播语义决定画面。
- 情绪变化决定速度。
- 关键动作决定卡点。
- 空间变化决定声音和转场。

抽象表达必须转译为具体动作、人物反应或环境变化。漂亮但无关的空镜不能替代语义证据。

素材匹配同时检查同源重复距离、场景变化、远中近景、主体完整、动作起落、裁切损失和相邻镜头功能。

素材卡、自动标签和它们自带的置信度分值只能用于候选召回，**不能用于排序**，也不能替代真实画面检查、授权与隐私判断。实测中高置信度的卡片描述照样出错。

### 4. 生成剪辑执行单

使用 [assets/editing-order-template.md](assets/editing-order-template.md)。每镜至少记录：目标时间、原文、叙事功能、情绪、语义锚点、素材路径、原片入出点、剪辑动作、转场、声音、字幕、备选和人工检查。

时间状态只使用：

- `text_only`：只有文案，没有任何音频，时间按字数推算。
- `estimated`：已有初步口播或粗录音，据此估算。
- `audio_aligned`：已读取真实口播并生成目标时间，但尚未在执行器连续复核。
- `audio_locked`：已在实际时间线完成口播、字幕与画面的连续同步复核。

不要仅因已有真实音频或执行器自报就写 `audio_locked`。

### 5. 交给执行器

保持执行单工具无关。通用提示词见 [assets/executor-prompt-template.md](assets/executor-prompt-template.md)；接入具体执行器时只做格式适配，不得改变核心语义和证据契约。

要求执行器：

- 只使用确认过的素材包。
- 保持视频、口播、字幕、音乐和效果可编辑。
- 大幅修改前复制并命名新时间线。
- 回报实际素材、入出点、时间线位置、空隙、重叠、黑场、声音、字幕、人工修改和未遵守项。
- 未经明确要求不导出、不发布、不压平时间线。

### 6. 验收和偏好学习

从头到尾连续播放，分别检查结构、动态画面、字幕和声音。使用 [assets/review-template.md](assets/review-template.md)；没有执行的检查标为 `pending_validation`。

用户修改后，使用 [assets/preference-candidate-template.md](assets/preference-candidate-template.md) 保存修改前后、位置、用户原话、原因、候选规则、适用边界和反例。只有用户明确确认跨项目复用时才写入长期风格；单片修改、项目偏好、合规修正和否定不得混入长期审美。

## 分级停止

缺少输入时不要整体停下。按下表判断哪一步可以继续、哪一步必须停。

| 缺少 | 仍可执行 | 禁止执行 |
|---|---|---|
| 真实口播或 SRT | 语义锚点表、素材匹配、执行单，时间状态 `text_only` | 声称任何卡点已与语音对齐；把时间状态升到 `estimated` 以上 |
| 动态画面与试听 | 依据媒体属性和静帧的候选排序、执行单草稿 | 写出动作起落、抖动、失焦、转场余量、声音听感的结论 |
| 用户确认素材范围 | 候选清单与人工复核项 | 生成执行器指令，或把素材交给执行器 |
| 初剪或用户修改 | — | 产出验收记录或偏好候选 |

写进缺口表可以继续；把缺口当成已解决不可以。

以下情况必须整体停止：

- 授权范围不明确，或需要读取用户未指定的目录。
- 执行器无法保持可编辑结构，或无法返回必要证据。
- 用户要求停止，或继续微调的收益已明显低于成本。

停止时保存当前输入、产物、失败点和恢复条件，不把计划写成完成。

## 可复用资源

- [examples/worked-example.md](examples/worked-example.md)：填写样例，说明每一栏的粒度与三处常见错填。**首次使用先读这个。**

- [references/style-learning.md](references/style-learning.md)：参考片学习与风格证据。
- [references/semantic-anchor-method.md](references/semantic-anchor-method.md)：语义锚点驱动的口播混剪法。
- [references/evidence-safety.md](references/evidence-safety.md)：证据、授权、隐私和状态边界。
- [references/preference-learning.md](references/preference-learning.md)：候选偏好与长期风格状态机。
- [references/executor-contract.md](references/executor-contract.md)：执行器输入、回报和验收契约。
- [references/originality-and-release.md](references/originality-and-release.md)：原创边界、来源记录和公开发布前检查。
- `scripts/media_inventory.py`：生成素材媒体清单。
- `scripts/verify_inventory.py`：复核素材是否缺失、被替换或混入清单外文件。
