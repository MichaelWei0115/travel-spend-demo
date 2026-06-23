# Travel Spend AI Skill Demo ✈️

一个可运行的 AI 差旅支出助手 Demo，同时也是轻量 AI 应用练习场。

## 功能概览

### 产品演示
- 支付成功后自动生成补票任务
- 支付失败后 AI 解释原因（含政策引用）
- 上传票据后识别字段
- 自动匹配票据和交易（高/低置信度）
- 恶意票据注入防护
- 用户口头修改锁定字段的防护

### AI Lab 练习场
- Prompt 版本管理（v1/v2 切换）
- 上下文裁剪（compact/verbose）
- 前缀稳定性与 KV Cache 友好度估算
- 工作记忆 [WORKING_NOTES]
- 工具调用日志与边界
- JSON 输出校验和 fallback
- 工具误导实验（simulate_tool_error）
- 间接提示注入检测
- 多轮用户修改系统事实防护

### 评估与观测
- 评估用例 pass/fail 报告
- Token 估算、延迟、fallback 次数
- 匹配置信度、人工确认次数
- 异常告警：token 突增、连续 fallback、低置信率过高

## 安装

```bash
cd 差旅支出助手
pip install -r requirements.txt
```

## 运行

```bash
streamlit run app.py
```

浏览器打开 http://localhost:8501

## 无 API Key 演示

本项目**无需 API Key** 即可完整运行。所有 AI 响应均使用模板 fallback 生成，保证演示链路稳定。

如果设置了 `OPENAI_API_KEY` 环境变量，未来可接入真实 LLM 调用。

## 演示脚本

按以下顺序操作产品演示 Tab：

1. **场景1** - 选择 "Tokyo Hotel 支付成功 ($820)"，点击触发 → 看到补票提醒卡片
2. **场景2** - 选择 "上传 Tokyo Hotel 票据 (高置信匹配)" → 看到自动匹配成功
3. **场景3** - 选择 "Tokyo Hotel 支付失败 ($1500)" → 看到限额解释
4. **场景4** - 选择 "Sushi Restaurant 低置信匹配" → 看到差异分析和建议
5. **场景5** - 选择 "恶意票据 (注入攻击)" → 看到安全拦截
6. **场景6** - 选择 "用户口头修改金额" → 看到锁定字段保护

## 项目结构

```
├── app.py                         # Streamlit 主应用
├── requirements.txt               # Python 依赖
├── README.md                      # 本文件
├── AGENTS.md                      # Agent 协作说明
├── data/
│   ├── transactions.json          # 交易 mock 数据
│   ├── receipts_mock.json         # 票据 mock 数据
│   ├── policies.json              # 公司政策配置
│   └── eval_cases.json            # 评估用例
├── prompts/
│   ├── system_skill_prompt.txt    # 系统 Prompt
│   ├── failure_explanation_v1.txt # 失败解释 v1
│   ├── failure_explanation_v2.txt # 失败解释 v2（增强版）
│   ├── receipt_match_v1.txt       # 票据匹配 v1
│   └── receipt_match_v2.txt       # 票据匹配 v2（增强版）
├── services/
│   ├── ai_client.py               # AI 调用层（含 fallback）
│   ├── event_handler.py           # 事件路由与处理
│   ├── receipt_parser.py          # 票据解析
│   ├── matcher.py                 # 票据-交易匹配
│   ├── tools.py                   # 工具注册与执行
│   ├── guardrails.py              # 安全护栏
│   ├── evaluator.py               # 评估运行器
│   ├── observability.py           # 观测指标
│   └── memory.py                  # 工作记忆
└── skills/
    └── travel_spend_assistant.md  # Skill 定义文档
```

## 技术栈

- Python 3.10+
- Streamlit
- Pydantic（数据校验）
- tiktoken（Token 估算）
- 本地 JSON mock 数据

## AI 练习概念

| 概念 | 在哪体验 |
|------|---------|
| Prompt 版本管理 | AI Lab → Prompt 查看 |
| 上下文裁剪 | AI Lab → compact/verbose 切换 |
| 前缀稳定性 | AI Lab → 缓存友好度 |
| 工作记忆 | AI Lab → [WORKING_NOTES] |
| 工具调用边界 | AI Lab → 工具列表 + 产品演示判断依据 |
| JSON 校验 + fallback | AI Lab → JSON 校验 |
| 注入防护 | AI Lab → 安全测试 |
| 覆盖防护 | AI Lab → 安全测试 |
| 过度自信校准 | Prompt v2 置信度上限 0.95 |
| 观测指标 | 评估与观测 Tab |
