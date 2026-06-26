# readybuilderone/skills

Personal skills collection for Claude Code.

## Installation

```bash
npx skills@latest add readybuilderone/skills
```

This will install all promoted skills into your local Claude Code environment.

## Usage

Skills are triggered automatically by Claude Code when your prompt matches a skill's trigger words. You can also invoke them explicitly:

```
/yh-codebase-onboarding  # 摸清一个陌生代码库，产出导览文档
/yh-study         # 交互式深度学习一个新概念
/yh-grill-me      # 对你的方案进行追问压力测试
/yh-meta-learn-skill  # 快速了解某个已安装的 skill
```

Or describe your intent naturally:

- "帮我摸清这个 repo" → triggers `yh-codebase-onboarding`
- "帮我讲讲 Raft 协议" → triggers `yh-study`
- "grill me on this design" → triggers `yh-grill-me`
- "学习一下 tdd 这个 skill" → triggers `yh-meta-learn-skill`

## Skills

### Engineering

- [yh-codebase-onboarding](skills/engineering/yh-codebase-onboarding/SKILL.md) — 摸清陌生代码库，产出决策者视角的导览（功能/场景/架构/外部依赖），不碰 CLAUDE.md

### Productivity

- [yh-meta-learn-skill](skills/productivity/yh-meta-learn-skill/SKILL.md) — 快速学习任意已安装 Skill 的元技能，生成速读卡
- [yh-grill-me](skills/productivity/yh-grill-me/SKILL.md) — 逐问追问压力测试你的设计/计划（fork of mattpocock/grill-me）
- [yh-study](skills/productivity/yh-study/SKILL.md) — 深度学习新概念的交互式引导，逐层讲解直到完全理解

### Misc

_No skills yet._

## Uninstall

```bash
npx skills@latest remove readybuilderone/skills
```
