Set WshShell = CreateObject("WScript.Shell")
Set Shortcut = WshShell.CreateShortcut(WshShell.SpecialFolders("Startup") & "\Ollama.lnk")
Shortcut.TargetPath = "C:\Users\MSI\AppData\Local\Programs\Ollama\ollama.exe"
Shortcut.Arguments = "serve"
Shortcut.WindowStyle = 7
Shortcut.Save
WScript.Echo "Ollama 시작프로그램 등록 완료!"
