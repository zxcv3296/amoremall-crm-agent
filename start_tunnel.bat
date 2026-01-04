@echo off
echo Starting Cloudflare Tunnel for Ollama...
echo.
echo This will create a temporary public URL for your local Ollama server.
echo Press Ctrl+C to stop the tunnel.
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:11434
pause
