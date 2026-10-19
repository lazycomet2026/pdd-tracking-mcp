#!/data/data/com.termux/files/usr/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$1" == "--doctor" ]; then
    echo "🩺 正在运行环境体检与修复 (PDD-doctor)..."
    pkg update -y
    pkg install python sqlite x11-repo chromium -y
    pip install --no-deps DrissionPage -i https://mirrors.aliyun.com/pypi/simple/
    pip install requests cssselect DrissionGet DrissionRecord websocket-client click tldextract -i https://mirrors.aliyun.com/pypi/simple/ --timeout 15 || true
    pkg reinstall libc++ -y
    echo "✅ 环境修复完毕！"
    exit 0
fi

echo "正在初始化环境..."
if ! command -v python3 >/dev/null 2>&1; then pkg install python -y; fi
if ! python3 -c "import sqlite3" >/dev/null 2>&1; then pkg install sqlite -y; fi
if ! command -v chromium-browser >/dev/null 2>&1; then pkg install chromium -y; fi
if ! command -v termux-x11 >/dev/null 2>&1; then pkg install x11-repo -y; pkg install termux-x11-nightly -y; fi

if ! python3 -c "import DrissionPage" >/dev/null 2>&1; then 
    echo "📦 正在安装 DrissionPage 核心依赖..."
    pip cache purge > /dev/null 2>&1
    pip install --no-deps DrissionPage -i https://mirrors.aliyun.com/pypi/simple/
    pip install requests cssselect DrissionGet DrissionRecord websocket-client click tldextract -i https://mirrors.aliyun.com/pypi/simple/ --timeout 15 || true
fi
pkg reinstall libc++ -y > /dev/null 2>&1

# 写入 PDD-run
echo "cd $DIR" > "$PREFIX/bin/PDD-run"
echo "python3 server.py" >> "$PREFIX/bin/PDD-run"
chmod +x "$PREFIX/bin/PDD-run"

# 写入 PDD-doctor
echo "bash $DIR/install.sh --doctor" > "$PREFIX/bin/PDD-doctor"
chmod +x "$PREFIX/bin/PDD-doctor"

# 写入 PDD-help（使用本地文件中转，彻底解决手机终端长行截断问题）
cat > "$DIR/help_tmp.txt" << 'HELPTEXT'
#!/data/data/com.termux/files/usr/bin/bash
echo "=================================================="
echo "👋 欢迎使用 拼多多订单 MCP 工具"
echo "=================================================="
echo "可用命令列表："
echo "  👉 PDD-run      启动服务 (拉起 X11 和后台服务)"
echo "  👉 PDD-doctor   一键修复环境 (解决依赖丢失或运行崩溃)"
echo "  👉 PDD-help     查看本帮助文档"
echo "=================================================="
echo "使用说明："
echo "  1. 首次运行请执行 PDD-run，并在弹出的 X11 界面中扫码登录。"
echo "  2. 在 MCP 客户端配置接口: http://127.0.0.1:8000/get_orders"
echo "  3. 免责声明：因拼多多前端混淆机制，查询准确率非 100%。"
echo "=================================================="
HELPTEXT
mv "$DIR/help_tmp.txt" "$PREFIX/bin/PDD-help"
chmod +x "$PREFIX/bin/PDD-help"

echo "✅ 安装完成！输入 PDD-help 查看命令列表"
