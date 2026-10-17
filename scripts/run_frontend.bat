@echo off
echo Starting AUTOSAR HLD Streamlit Frontend...
python -m streamlit run frontend/app.py --server.port 8501
pause
