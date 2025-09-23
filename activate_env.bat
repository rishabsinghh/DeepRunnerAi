@echo off
echo Activating CLM Environment...
call clm_env\Scripts\activate
echo.
echo Environment activated! You can now run:
echo   python main.py --mode chatbot
echo   python demo.py
echo   streamlit run chatbot_interface.py
echo.
echo To deactivate, type: deactivate



