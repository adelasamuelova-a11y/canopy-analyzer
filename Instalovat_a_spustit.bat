@echo off
title Canopy Analyzer - Instalace a spusteni
echo ========================================================
echo   Canopy Analyzer - Automaticka priprava a spusteni
echo ========================================================
echo.
echo 1/2 Instaluji potrebne knihovny (OpenCV, Pillow, NumPy)...
python -m pip install -r requirements.txt
echo.
echo 2/2 Spoustim Canopy Analyzer...
python CanopyAnalyzer.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Doslo k chybe pri spousteni. Ujistete se, ze mate nainstalovany Python.
    pause
)
