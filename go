#!/bin/bash
# Whole WhatsApp capture setup on this Mac, step by step. Run: bash <(curl -sL aiwithsoulofficial.github.io/wa-capture-setup/go)
B=https://aiwithsoulofficial.github.io/wa-capture-setup
echo
echo "STEP 1 of 4 - finding the job groups (can take a minute)..."
python3 <(curl -sL $B/find_jobs.py)
echo
read -p "STEP 2 of 4 - when the list is checked and saved with Cmd + S, press Enter here (or Ctrl + C to stop)... "
echo "First save of the job groups (can take a while)..."
python3 ~/.gill-whatsapp/wa_capture.py file
echo
P="$(python3 -c 'import os,sys;print(os.path.realpath(sys.executable))')"
printf "%s" "$P" | pbcopy
echo "STEP 3 of 4 - Full Disk Access for Python (for the automatic saving)."
echo "Python path (already copied): $P"
echo "In the window that opens: click +, press Cmd + Shift + G, press Cmd + V, Enter, click Open, make sure it is ON."
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
read -p "Press Enter when done... "
echo
echo "STEP 4 of 4 - switching on automatic saving every 15 minutes..."
launchctl load ~/Library/LaunchAgents/au.com.gillgroup.whatsapp-capture.plist 2>&1
launchctl start au.com.gillgroup.whatsapp-capture 2>/dev/null
sleep 20
echo "Last runs:"
tail -5 ~/.gill-whatsapp/capture.log
echo
echo "DONE on this Mac. Last thing: Finder > OneDrive > right-click WhatsApp-Jobs > Share > add Kelly with edit access."
