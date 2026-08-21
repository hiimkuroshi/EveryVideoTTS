@echo off
chcp 65001 >nul
title EveryVideoTTS Studio Launcher
cd /d "%~dp0"

echo ===========================================================
echo   🎬 EveryVideoTTS Studio - Fast Launcher
echo   Tác giả: Tyr
echo ===========================================================
echo.
echo [1/2] Đang kiểm tra môi trường và khởi động server...

:: Tự động mở trình duyệt sau 3 giây khi server sẵn sàng
start /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:7860"

echo [2/2] Đang nạp EveryVideoTTS Web UI...
echo       Địa chỉ Web: http://127.0.0.1:7860
echo.
echo 💡 Nhấn Ctrl+C để dừng app bất kỳ lúc nào.
echo ===========================================================
echo.

uv run vieneu-web

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Đã xảy ra lỗi khi chạy bằng lệnh vieneu-web, đang thử lại bằng python module...
    uv run python -m apps.gradio_main
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Ứng dụng đã dừng lại do lỗi.
    pause
)
