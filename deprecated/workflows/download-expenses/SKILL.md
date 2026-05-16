---
name: download-expenses
description: |
  浏览器自动化邮箱发票下载。扫描 Gmail/163 邮箱，AI 识别发票邮件，下载并分类归档。
  触发词：下载发票、报销整理、expense download。
  建议每月执行 1-2 次。
version: 1.0.0
platforms: [linux]
depends_on: [setup-chrome]
frequency: monthly
estimated_time: 15-30min
metadata:
  openclaw:
    emoji: "🧾"
    requires:
      bins: [python3, curl]
  hermes:
    category: workflow
    tags: [automation, finance, browser]
---

# Download Expenses — 发票自动下载

## When to Use

- 每月报销前整理发票
- 用户说"下载发票"、"整理报销"
- 需要从邮箱批量提取发票/水单

## Input

- 用户已登录的 Chrome 浏览器（Gmail/163 邮箱会话）
- CDP 端口可用（9222 或 18800）
- 可选：搜索日期范围（默认上月）

## Output

- 发票文件下载到 `~/Expenses/YYYY-MM/`
- 命名格式：`YYYYMMDD_类型_金额_地点_供应商.pdf`
- 分类子目录：交通/住宿/餐饮/通讯/办公/其他
- 汇总报告：`summary.md`

## Procedure

### Phase 1: 环境检查

```bash
# 确认 CDP 可用
curl -s http://127.0.0.1:9222/json/version >/dev/null 2>&1 || \
curl -s http://127.0.0.1:18800/json/version >/dev/null 2>&1 || \
{ echo "❌ CDP 不可用，请先执行 setup-chrome"; exit 1; }

# 确认邮箱 tab 存在
# 检查是否有 mail.google.com 或 mail.163.com 的标签页
```

### Phase 2: 扫描邮件列表

通过 CDP 操作邮箱：

```
1. 定位邮箱标签页
2. 使用搜索关键词过滤（发票/invoice/receipt/水单/报销）
3. 设置日期范围
4. 获取邮件列表（标题、发件人、日期）
```

搜索关键词体系：
- 中文：发票、电子发票、报销、水单、收据、账单
- 英文：invoice、receipt、billing、statement
- 平台：滴滴出行、航旅纵横、12306、美团、饿了么

### Phase 3: AI 语义识别

对每封邮件判断是否为发票邮件：

```
输入：邮件标题 + 发件人 + 摘要
判断：是否包含可下载的发票/收据？

决策树：
- 有 PDF 附件且文件名含"发票" → 直接下载
- 有链接指向发票平台 → 打开链接下载
- 有二维码 → 截图保存（手动扫码）
- 仅通知类（无附件无链接） → 跳过
```

### Phase 4: 下载与分类

```
对每个确认的发票：
1. 下载 PDF/图片
2. AI OCR 提取字段（日期、金额、供应商、类型）
3. 重命名：YYYYMMDD_类型_金额_地点_供应商.pdf
4. 移入分类目录
```

分类规则：
| 类型 | 关键词 |
|------|--------|
| 交通 | 滴滴、出租、地铁、机票、火车 |
| 住宿 | 酒店、hotel、民宿 |
| 餐饮 | 美团、饿了么、餐厅 |
| 通讯 | 中国移动、联通、电信 |
| 办公 | 文具、打印、快递 |

### Phase 5: 生成汇总

```markdown
# 发票汇总 — YYYY年MM月

## 统计
- 总计: XX 张发票，¥XXXX.XX
- 交通: X 张，¥XXX
- 住宿: X 张，¥XXX
- ...

## 明细
| 日期 | 类型 | 金额 | 供应商 | 文件 |
|------|------|------|--------|------|
| ... |
```

## Verification

- [ ] 发票文件已下载到 `~/Expenses/YYYY-MM/`
- [ ] 文件名符合规范
- [ ] `summary.md` 已生成
- [ ] 无遗漏（与邮箱中的发票邮件数对比）

## Pitfalls

| 问题 | 解决 |
|------|------|
| Gmail 登录过期 | 提示用户在浏览器中重新登录 |
| 防盗链下载失败 | 在浏览器上下文中 fetch |
| 发票平台需要验证码 | 截图通知用户手动处理 |
| PDF 加密无法 OCR | 保留原文件名，标记为"待手动处理" |
