#!/usr/bin/env python3
"""测试前端页面是否正确加载和执行JavaScript"""

# 检查HTML文件
with open("src/web/templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 检查关键元素ID
required_ids = ["goodCount", "warningCount", "badCount", "totalRecords"]
missing_ids = [elem_id for elem_id in required_ids if f'id="{elem_id}"' not in html]

if missing_ids:
    print(f"❌ HTML中缺少元素ID: {missing_ids}")
else:
    print(f"✅ HTML中包含所有必需的元素ID: {required_ids}")

# 检查JavaScript文件
with open("src/web/static/js/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# 检查关键函数
checks = [
    ("loadWeeklyStats", "loadWeeklyStats函数"),
    ("displayWeeklyStats", "displayWeeklyStats函数"),
    ("weeklyGoodCount:", "weeklyGoodCount变量"),
    ("weeklyWarningCount:", "weeklyWarningCount变量"),
    ("weeklyBadCount:", "weeklyBadCount变量"),
    ("weeklyTotalRecords:", "weeklyTotalRecords变量"),
    ("await loadWeeklyStats()", "initApp中调用loadWeeklyStats")
]

for check_str, desc in checks:
    if check_str in js:
        print(f"✅ {desc}")
    else:
        print(f"❌ 缺少: {desc}")

print("\n建议：")
print("1. 强制刷新浏览器缓存（Cmd+Shift+R 或 Ctrl+Shift+R）")
print("2. 打开浏览器F12开发者工具 > Console标签")
print("3. 查看是否有JavaScript错误（红色文字）")
print("4. 切换到Network标签，刷新页面")
print("5. 搜索 'statistics' 查看是否有API请求")
