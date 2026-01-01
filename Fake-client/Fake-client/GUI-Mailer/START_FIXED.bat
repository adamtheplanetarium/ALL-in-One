@echo off
echo ======================================================================
echo CRITICAL BUG FIXES - QUICK START
echo ======================================================================
echo.
echo This will fix the 2 critical bugs:
echo   1. IMAP duplicate email fetching
echo   2. FROM addresses crash (3M emails, 197MB config)
echo.
echo ======================================================================
echo STEP 1: Cleaning config file...
echo ======================================================================
python cleanup_config.py
echo.
echo ======================================================================
echo STEP 2: Starting GUI...
echo ======================================================================
echo.
python gui_mailer.py
