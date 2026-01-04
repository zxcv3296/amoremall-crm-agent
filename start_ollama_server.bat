@echo off
echo Setting OLLAMA_HOST to allow external connections...
set OLLAMA_HOST=0.0.0.0

echo Starting Ollama server...
echo.
echo Ollama is now accessible from external networks.
echo Local: http://localhost:11434
echo.
"C:\Users\MSI\AppData\Local\Programs\Ollama\ollama.exe" serve
pause
