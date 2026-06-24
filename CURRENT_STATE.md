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

## 当前稳定云端 Demo 状态

更新时间：2026-06-24

当前 Demo 已完成云端部署与手机端适配验证。

### 稳定状态

- Streamlit Cloud 云端 App 可访问
- PC 浏览器访问正常
- PC 无痕模式访问正常
- 手机浏览器访问正常
- 不带参数访问会显示 Demo 口令页
- 输入口令后进入 Demo
- 刷新后不会重复要求输入口令
- 页面跳转过程中 `demo_authed=1` 会被保留
- 手机端不再出现白屏或灰屏
- 手机端不再显示 AI Lab / 评估与观测开发面板
- 首页布局已适配手机端
- 详情页底部按钮已恢复显示
- 报销记录列表、费用详情、票据上传、立即提交、差旅政策页流程可正常演示

### 已修复的关键问题

1. 云端部署依赖和配置问题；
2. Demo 口令刷新后丢失问题；
3. 页面跳转覆盖 `demo_authed=1` 问题；
4. 手机端 `100vh + overflow:hidden` 导致白屏问题；
5. `tab-panel:nth-child + display:none` 导致移动端灰屏问题；
6. 手机端 AI Lab / 评估与观测开发面板外露问题；
7. 手机端首页底部区域位置异常问题；
8. 手机端详情页底部 CTA 按钮不显示问题；
9. 待补票、上传票据、立即提交、状态回写等演示流程问题。

### 当前不建议继续开发的事项

为了保持 Demo 稳定，暂时不要继续加入：

- 真实 OpenAI API
- 真实 OCR
- 真实报销系统同步
- 多用户隔离
- 正式账号系统
- 复杂 cookie auth
- 生产级权限系统
- 大规模 UI 重构
- 状态机重构

当前目标是稳定演示与验收，不是继续扩展生产功能。


---

## demo-cloud-v2-cleanup1 released

Base:

- demo-cloud-v2
- 7251f2b

Summary:

- Aligned deprecated documents with the current 4-state reimbursement model.
- Marked phone_shell.py as legacy / fallback.
- Moved unused legacy modules (action_map.py, ui_components.py) out of the active root path.
- Fixed prompt variable injection gaps in services/event_handler.py (v1 and v2 templates).
- Added prompt rendering regression tests to prevent unresolved placeholders.
- Configured pytest to exclude legacy and visual/manual test folders.
- Added .gitignore coverage for *.bak* backup file patterns.
- Updated DEPLOYMENT.md troubleshooting to reflect phone_shell.py legacy status.

Test result:

- 153 passed / 0 failed

Notes:

- No changes to the 4-state reimbursement state machine.
- No changes to authentication logic.
- No changes to core page interaction flow.
- No changes to mobile CSS layout rules.
- Cloud and mobile manual smoke testing passed on 2026-06-24.
  - Desktop: 8/8 checks passed (PC 首页、无痕模式、口令认证、报销列表、费用详情、上传票据、立即提交、差旅政策页均正常).
  - Mobile: 10/10 checks passed (无白屏/灰屏、AI Lab 未外露、底部布局正常、列表可滚动、CTA 可见、状态流转正常、demo_authed=1 保留).
