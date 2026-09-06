@echo off
echo ==============================================
echo   Building Audio Splitter Pro (.exe)
echo ==============================================

pyinstaller --noconfirm --onefile --windowed ^
    --name "AudioSplitterPro" ^
    main.py

echo.
echo Done! Find your EXE inside the "dist" folder:
echo    dist\AudioSplitterPro.exe
pause
