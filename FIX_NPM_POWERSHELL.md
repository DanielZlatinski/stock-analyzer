# Fix npm PowerShell Execution Policy Issue

## Quick Fix

Run this command in PowerShell **as Administrator**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then type `Y` when prompted.

## Verify It Works

After running the command above, test npm:

```powershell
npm --version
```

You should see a version number (e.g., `10.8.2`).

## Alternative: Run Without Changing Policy

If you don't want to change the execution policy, you can bypass it for a single command:

```powershell
powershell -ExecutionPolicy Bypass -Command "npm --version"
```

Or use cmd.exe instead:
```cmd
npm --version
```

## Then Install Firebase CLI

Once npm works, install Firebase CLI:

```powershell
npm install -g firebase-tools
```
