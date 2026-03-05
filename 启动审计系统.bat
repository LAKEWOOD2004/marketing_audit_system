@echo off
chcp 65001 >nul
echo ====================================================
echo 营销审计多智能体系统启动器
 echo ====================================================
echo.
echo 正在启动审计系统...
echo.
echo 请稍候，系统正在初始化...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 运行GUI界面
python "%~dp0audit_ui.py"

pause
