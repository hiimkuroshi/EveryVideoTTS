@echo off
chcp 65001 >nul
title EveryVideoTTS Studio - Fast Launcher
cd /d "%~dp0"

echo ===========================================================
echo   ⚡ EveryVideoTTS Studio - Fast Launcher
echo   Tác giả: Tyr
echo ===========================================================
echo.
echo [1/2] Đang khởi động trực tiếp từ môi trường Python (.venv)...

:: Tự động mở trình duyệt vào Web UI sau 2 giây
start /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:7860"

echo [2/2] Web UI: http://127.0.0.1:7860
echo.
echo 💡 Nhấn Ctrl+C để dừng app bất kỳ lúc nào.
echo ===========================================================
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m apps.gradio_main
) else (
    uv run --no-sync python -m apps.gradio_main
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Ứng dụng đã dừng lại do lỗi.
    pause
)
