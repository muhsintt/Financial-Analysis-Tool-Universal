# INSTALLATION GUIDE - Expense Tracker

**Time Required**: 5-10 minutes  
**Difficulty**: Easy (No programming knowledge needed)

---

## STEP 1: Install Python

Your computer needs Python to run this application.

### For Windows:

1. Go to https://www.python.org/downloads/
2. Click the big **"Download Python 3.11"** button (or latest version)
3. Open the downloaded installer
4. **IMPORTANT**: Check the box that says **"Add Python to PATH"**
   - This is at the bottom of the first screen
5. Click **"Install Now"**
6. Wait for installation to complete
7. Click **"Close"**

### For macOS:

1. Go to https://www.python.org/downloads/
2. Click **"Download Python 3.11"** for macOS
3. Open the downloaded `.pkg` file
4. Follow the installer steps
5. Python is now installed

### For Linux:

Most Linux systems have Python already. Open Terminal and type:
```bash
python3 --version
```

If not installed, use:
```bash
# Ubuntu/Debian
sudo apt-get install python3

# Fedora
sudo dnf install python3
```

---

## STEP 2: Verify Python Installation

### Windows:
1. Open **Command Prompt** (Press `Win + R`, type `cmd`, press Enter)
2. Type: `python --version`
3. You should see: `Python 3.x.x` (version number)

### macOS/Linux:
1. Open **Terminal**
2. Type: `python3 --version`
3. You should see: `Python 3.x.x` (version number)

---

## STEP 3: Run the Application

### For Windows:

**Method 1 (Easiest):**
1. Go to your **"Financial analysis software"** folder
2. Open the **"expense_tracker"** subfolder
3. **Double-click** the file named **`start.bat`**
4. A window will open and show installation progress
5. After a few seconds, your browser will open with the application
6. Done! You can now use the app

**Method 2 (Using Command Prompt):**
1. Open **Command Prompt**
2. Type: `cd C:\Users\YourUsername\Documents\Financial analysis software\expense_tracker`
   - Replace "YourUsername" with your actual Windows username
3. Type: `start.bat`
4. The application will start

### For macOS/Linux:

1. Open **Terminal**
2. Type:
```bash
cd ~/Documents/Financial\ analysis\ software/expense_tracker
```
3. Make the start script executable:
```bash
chmod +x start.sh
```
4. Type: `./start.sh`
5. The application will start and open in your browser

---

## What Happens on First Run

When you run `start.bat` or `start.sh` for the first time:

1. **Virtual Environment Created** - A folder called `venv` is created (this is normal)
2. **Dependencies Installed** - Required Python packages are downloaded and installed
3. **Database Created** - `expense_tracker.db` file is created to store your data
4. **Default Categories Added** - Standard expense categories are created
5. **Application Started** - The app runs on `http://localhost:5000`
6. **Browser Opens** - Your browser automatically opens to the application

This takes 2-5 minutes on first run (faster on subsequent runs).

---

## Accessing the Application

After startup, your browser will automatically open to:
```
http://localhost:5000
```

If it doesn't open automatically:
1. Open any web browser (Chrome, Firefox, Safari, Edge, etc.)
2. Type in the address bar: `http://localhost:5000`
3. Press Enter

---

## Stopping the Application

### To Stop the Application:

**Windows:**
- In Command Prompt window, press `Ctrl + C`
- Or close the window

**macOS/Linux:**
- In Terminal, press `Ctrl + C`
- Or close the window

**Warning**: Do NOT simply close the browser. You need to stop the actual application in the Command Prompt/Terminal.

---

## Restarting the Application

To use the app again:
- Simply run `start.bat` (Windows) or `./start.sh` (macOS/Linux) again
- Your data is automatically saved

---

## Troubleshooting Installation

### Problem: "Python is not recognized"

**Solution:**
1. Python is installed but not in PATH
2. Uninstall Python (Control Panel → Programs → Uninstall)
3. Reinstall Python from https://www.python.org/
4. **During installation, MUST check "Add Python to PATH"**
5. Restart your computer
6. Try again

### Problem: Port 5000 Already in Use

**Error Message:**
```
OSError: [WinError 10048] Only one usage of each socket address
```

**Solution:**
1. Another application is using port 5000
2. Stop that application
3. Or restart your computer
4. Try running the app again

### Problem: Dependencies Won't Install

**Error Message:**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution:**
1. Check internet connection
2. Try running `start.bat` again
3. Check that firewall allows Python access
4. If on corporate network, you may need to configure proxy settings

### Problem: Browser Won't Open

**Solution:**
1. Check Command Prompt/Terminal window for errors
2. Manually open browser to `http://localhost:5000`
3. If still blank, application may be starting
4. Wait 10 seconds and refresh browser (press F5)

### Problem: Application Crashes After Starting

**Solution:**
1. Check that `expense_tracker.db` file exists in `backend/data/` folder
2. If not, delete the entire `backend/data/` folder
3. Run the application again (it will recreate the database)
4. This will reset your data, but fixes the issue

---

## File Structure After Installation

After running the app, you'll see:

```
Financial analysis software/
└── expense_tracker/
    ├── backend/
    │   ├── app/
    │   ├── data/
    │   │   ├── expense_tracker.db    ← Your data (DO NOT DELETE)
    │   │   └── uploads/
    │   ├── venv/                     ← Virtual environment (created on first run)
    │   ├── run.py
    │   └── requirements.txt
    ├── frontend/
    │   ├── static/
    │   └── templates/
    ├── start.bat
    ├── start.sh
    ├── README.md
    ├── QUICK_START.md
    └── verify_setup.bat
```

---

## Next Steps

Once the application is running:

1. **Read QUICK_START.md** - Fast overview of basic features
2. **Add Your First Transaction** - Practice adding an expense
3. **Create a Budget** - Set up a budget for a category
4. **Upload a Bank Statement** - Try importing a CSV/Excel file
5. **View Reports** - Check out the analytics and charts

---

## Getting Help

### Check These Resources:

1. **QUICK_START.md** - Quick feature overview
2. **README.md** - Complete documentation
3. **This Installation Guide** - You're reading it!

### Common Questions:

**Q: Can I have multiple instances running?**
A: Not easily on the same port. Close one before starting another.

**Q: Where are my files stored?**
A: All data in `backend/data/expense_tracker.db` on your computer.

**Q: Is there a cloud version?**
A: Currently local only. You can backup the `.db` file.

**Q: Can I uninstall/reinstall?**
A: Yes. Just delete the entire `expense_tracker` folder and start over.

**Q: How do I update?**
A: A new version would replace the old folder. Backup `expense_tracker.db` first.

---

## Important Notes

✅ **Data is Private** - All data stays on your computer
✅ **No Internet Needed** - Works completely offline  
✅ **Always Backup** - Copy `expense_tracker.db` regularly
✅ **First Run Takes Time** - Dependencies need to install
✅ **Keep Port 5000 Free** - Used by the application

---

## System Requirements Verification

Before installation, make sure you have:

- [ ] Windows, macOS, or Linux operating system
- [ ] At least 100MB free disk space
- [ ] Python 3.8 or higher
- [ ] 512MB RAM (recommended: 1GB+)
- [ ] Internet connection (for first-time setup only)
- [ ] Any modern web browser

---

## Support Checklist

If you have issues:

- [ ] Python is version 3.8 or higher
- [ ] "Add Python to PATH" was checked during installation
- [ ] All files are in the correct folder structure
- [ ] Port 5000 is not in use
- [ ] Internet connection is active (for first run)
- [ ] Firewall allows Python
- [ ] No error messages in Command Prompt/Terminal

---

**Congratulations! Your Expense Tracker is ready to use! 🎉**

For detailed features and usage, see README.md or QUICK_START.md
