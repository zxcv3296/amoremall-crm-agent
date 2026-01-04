@echo off
cd /d C:\Users\MSI\AISystem-2402\AISystem-2402\notion
python test_ollama.py > test_output.txt 2>&1
type test_output.txt
