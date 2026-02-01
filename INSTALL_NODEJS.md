# Installing Node.js on Windows

Node.js includes npm (Node Package Manager) which is needed to install Firebase CLI.

## Method 1: Direct Download (Recommended)

1. **Go to:** https://nodejs.org/
2. **Download the LTS version** (Long Term Support - recommended)
   - Click the big green button that says "LTS" (usually on the left)
   - This will download a `.msi` installer file
3. **Run the installer:**
   - Double-click the downloaded `.msi` file
   - Click "Next" through the installation wizard
   - **Important:** Make sure "Add to PATH" is checked (it should be by default)
   - Click "Install"
   - Wait for installation to complete
   - Click "Finish"
4. **Restart PowerShell:**
   - Close your current PowerShell window
   - Open a new PowerShell window
5. **Verify installation:**
   ```powershell
   node --version
   npm --version
   ```
   You should see version numbers (e.g., `v20.10.0` and `10.2.3`)

## Method 2: Using Chocolatey (If you have it)

If you have Chocolatey package manager installed:
```powershell
choco install nodejs-lts
```

## Method 3: Using Winget (Windows 11)

If you have Windows 11 with winget:
```powershell
winget install OpenJS.NodeJS.LTS
```

## After Installation

Once Node.js is installed, you can proceed with installing Firebase CLI:

```powershell
npm install -g firebase-tools
```

## Troubleshooting

### "npm is not recognized" after installation
1. **Restart PowerShell** - Close and reopen your terminal
2. **Check PATH:**
   ```powershell
   $env:PATH
   ```
   Should include something like `C:\Program Files\nodejs\`
3. **If not in PATH, add it manually:**
   - Search for "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Program Files\nodejs\`
   - Restart PowerShell

### Still having issues?
Try installing from the official website: https://nodejs.org/
