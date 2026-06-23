# Current Project State

本文档描述当前代码实现的真实状态。后续开发以本文件和 `reimbursement_data.py` 为准。

## 当前状态模型

当前报销记录使用 4 状态模型：

| status | 含义 |
|---|---|
| `pending_receipt` | 待补票 |
| `pending_submit` | 待提交 |
| `submitted` | 已提交 |
| `error` | 异常 |

旧模型中的以下字段或状态已废弃：

- `ai_check_result`
- `sync_status`
- `need_supplement`
- `sync_failed`
- 旧 5 状态组合模型

## 当前 Demo 主流程

```text
pending_receipt
  → 上传票据
  → pending_submit
  → 立即提交
  → submitted

异常记录使用：

error

用于展示支付失败、同步失败或其他异常态。

## 当前开发原则

- 不要恢复旧 5 状态模型。
- 不要在业务逻辑中重新引入 `ai_check_result` + `sync_status` 双状态源。
- H5、Chat、Sidebar 都应以 `record.status` 为主状态源。
- 新测试应基于 4 状态模型编写。
- 旧文档如与本文件冲突，以本文件为准。
