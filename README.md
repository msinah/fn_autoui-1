```bash
# 环境
uv init my-project
cd my-project
# 2. 添加依赖（自动更新 lock 文件）
uv add requests pandas
# 3. 运行脚本（自动使用项目虚拟环境）
uv run main.py
# 或先激活再运行
uv sync
python main.py
```

基于playwright+pytest的BDD框架
```bash
# 安装playwright
uv add playwright
# 安装pytest
uv add pytest-playwright
# 安装浏览器驱动
playwright install
# 安装驱动时默认带录制工具ffmepg,Codegen
# 脚本录制命令
playwright codegen https://www.baidu.com



# 安装yaml
uv add pyyaml
# 日志颜色安装
uv add colorlog
```


