@echo off
echo Installing required packages...
pip install tf-keras
pip install sentence-transformers --upgrade
pip install langchain-huggingface
pip install langchain-community
pip install faiss-cpu
echo.
echo Done! Now run: streamlit run app.py
pause
