---
name: noterx-diagnosis
description: |
  小红书笔记诊断技能 - 基于 874 条真实笔记训练的多 Agent 分析系统。
  支持图片封面诊断（使用 sn-image-recognize）、标题结构分析、品类权重评分、
  钩子检测（3个最优，超过4个崩塌）、黄金发布时段建议（17:00）、改写方案生成。
  
  触发关键词：诊断笔记、分析小红书、优化笔记、检查标题、封面图诊断、图片分析
allowed-tools:
  - read
  - write
  - edit
  - exec
allowed-edit-paths:
  - ~/.openclaw/skills/noterx-diagnosis
---

# NoteRx - 小红书笔记诊断技能

基于 874 条真实笔记 + 2465 条评论训练的数据驱动分析系统。

## 核心能力

| 功能 | 说明 |
|------|------|
| 标题诊断 | 评估标题结构（数字+情感+悬念） |
| **封面图分析** | **使用 sn-image-recognize 进行 VLM 视觉诊断** |
| 品类判断 | 根据内容判断美食/穿搭/科技/旅游/生活 |
| 权重评分 | 基于品类差异化权重打分 |
| 钩子检查 | 评估钩子数量（3个最优，超过4个崩塌） |
| 评论预测 | 基于6种画像模拟真实评论区 |
| 优化改写 | 生成3个高分改写方案 |
| 黄金时段 | 17:00发布建议 |

## 图像分析（关键功能）

当用户发送图片时，使用 `sn-image-recognize` 进行封面诊断。

### 调用方式

```bash
python3 ~/.openclaw/skills/sn-image-base/scripts/sn_agent_runner.py sn-image-recognize \
  --user-prompt "请分析这张小红书封面图的视觉质量：1) 构图是否吸引人 2) 光线是否到位 3) 主体是否突出 4) 色彩搭配如何 5) 是否有视觉冲击力 6) 预估互动潜力（高/中/低）" \
  --images "图片路径或URL" \
  --api-key "$SN_API_KEY" \
  --base-url "$SN_BASE_URL" \
  --model "$SN_CHAT_MODEL"
```

### 视觉评分转换

| VLM评估 | 视觉得分 |
|---------|----------|
| 优质、专业、吸引人 | 22-25 |
| 不错、良好 | 17-21 |
| 一般、有改进空间 | 10-16 |
| 差、模糊、无吸引力 | 1-9 |

## 使用流程

1. 用户发送笔记内容/标题/图片
2. 图片使用 sn-image-recognize 分析封面质量
3. 文字分析标题结构、钩子、品类
4. 结合视觉+文字计算综合评分
5. 生成优化建议 + 改写方案
6. 预测评论区反应

## 品类权重（核心数据）

详见 `references/category-weights.md`

## 评分维度

详见 `references/scoring-dimensions.md`

## 重写规则

详见 `references/rewrite-rules.md`

## 评论画像

详见 `references/comment-personas.md`

## 数据来源

- 874 条真实小红书笔记（美食183/穿搭278/科技235/旅游130/生活48）
- 2465 条评论分析
- Spearman 相关、线性回归、K-Means 聚类验证