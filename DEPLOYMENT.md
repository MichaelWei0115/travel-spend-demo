# Deployment Guide — Streamlit Community Cloud

## Prerequisites

- GitHub account
- Project pushed to a **private** GitHub repository
- Streamlit Community Cloud account ([share.streamlit.io](https://share.streamlit.io))

## System packages

当前 Demo 不依赖额外系统级 apt 包，因此 `packages.txt` 为空。

## Deploy Steps

1. **Push to GitHub (private repo)**

   ```bash
   git remote add origin git@github.com:<your-username>/travel-spend-demo.git
   git push -u origin main
   ```

2. **Log in to Streamlit Community Cloud**

   打开 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 账号登录。

3. **New app → From existing repo**

   - Repository: `<your-username>/travel-spend-demo`
   - Branch: `main`
   - Main file path: `app.py`
   - 点击 **Deploy**

4. **配置 Secrets（可选：设口令保护）**

   部署完成后，进入 App → Settings → Secrets，添加：

   ```toml
   DEMO_PASSWORD = "your-chosen-password"
   ```

   不设置或留空则跳过口令页面。

5. **分享链接**

   部署完成后获得 `https://<app-name>.streamlit.app` 链接，分发给体验者。

## Demo 注意事项

当前版本使用 mock data，不接真实报销系统，不接真实 OCR，不支持多用户隔离。请勿上传真实票据或敏感数据。

## Pre-deploy Check

```bash
./scripts/predeploy_check.sh
```

## 本地验证

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，确认 Tab1/Tab2/Tab3 均可正常交互。

## Troubleshooting

| 问题 | 解决方案 |
|------|---------|
| Tab1 手机壳空白 | 检查 `phone_ui.py` 和 `phone_shell.py` 是否正确 import |
| 评估用例加载失败 | 确认 `data/eval_cases.json` 在 git tracking 中 |
| 口令页面不出现 | 确认 `DEMO_PASSWORD` 在 Streamlit Cloud Secrets 中设为非空字符串 |
| Import Error | 本地运行 `pip install -r requirements.txt` 后重新部署 |
