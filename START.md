# 🚀 启动说明

## ✅ 问题已修复！

PyCharm 调试器兼容性问题已解决。现在您有三种启动方式可选：

---

## 方式1：使用启动脚本（推荐）

```bash
python run_server.py
```

✅ **优点**：最简单，兼容所有环境

---

## 方式2：在 PyCharm 中直接运行

在 PyCharm 中右键运行 `src/api/main.py`

✅ **优点**：支持断点调试
✅ **已修复**：自动检测调试器环境，避免冲突

---

## 方式3：使用 uvicorn 命令

```bash
# 开发模式（带热重载）
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

✅ **优点**：最灵活，可自定义参数

---

## 访问系统

启动成功后，在浏览器中打开：

- **主页面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 🎯 快速测试

```bash
# 1. 启动服务器
python run_server.py

# 2. 在另一个终端测试API
curl http://localhost:8000/health

# 预期输出：
# {"status":"healthy","database":"connected","detector":"ready"}
```

---

## ⚠️ 常见问题

### 端口被占用

如果8000端口已被占用，可以修改端口：

```bash
# 使用其他端口
uvicorn src.api.main:app --host 0.0.0.0 --port 8080
```

或修改 `config/api_settings.py` 中的 `PORT` 配置。

### 摄像头权限

浏览器首次访问会请求摄像头权限，请点击"允许"。

---

**现在可以正常启动了！** 🎉
