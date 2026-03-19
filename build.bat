@echo off
chcp 65001 >nul
echo ========================================
echo GatewayMapper 打包脚本
echo ========================================
echo.

echo [1/3] 清理旧的构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo 清理完成!

echo.
echo [2/3] 开始打包...
pyinstaller build.spec --noconfirm

echo.
echo [3/3] 检查打包结果...
if exist "dist\GatewayMapper.exe" (
    echo.
    echo ========================================
    echo 打包成功!
    echo 可执行文件位置：dist\GatewayMapper.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 打包失败!请检查错误信息
    echo ========================================
    pause
    exit /b 1
)

pause
