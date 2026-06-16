# Publishing To GitHub

This directory is intended to become its own GitHub repository.

From this directory:

```powershell
cd C:\Users\georg\Codex_Projects\luckfox-lyra\publish\luckfox-lyra-picocalc
git init
git add .
git commit -m "Initial Luckfox Lyra PicoCalc project"
git branch -M main
```

Then create an empty GitHub repository and push:

```powershell
git remote add origin https://github.com/YOUR_USER/luckfox-lyra-picocalc.git
git push -u origin main
```

Before pushing, choose a license if you want others to reuse the code under
clear terms. The root README currently records that no license has been selected
yet.
