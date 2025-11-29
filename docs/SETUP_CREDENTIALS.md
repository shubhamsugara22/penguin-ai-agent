# 🔑 Credentials Setup Guide

## Where to Add Your Credentials

Your credentials go in the `.env` file in the `penguin-ai-agent` directory.

```
penguin-ai-agent/
├── .env  ← YOUR CREDENTIALS GO HERE
├── .env.example  ← Template (don't edit this)
├── main.py
└── ...
```

## Step-by-Step Instructions

### 1️⃣ Create Your .env File

**Windows (Command Prompt):**
```cmd
cd penguin-ai-agent
copy .env.example .env
notepad .env
```

**Windows (PowerShell):**
```powershell
cd penguin-ai-agent
Copy-Item .env.example .env
notepad .env
```

**Mac/Linux:**
```bash
cd penguin-ai-agent
cp .env.example .env
nano .env
```

### 2️⃣ Get GitHub Token

1. Open: https://github.com/settings/tokens
2. Click: **"Generate new token (classic)"**
3. Name: `GitHub Maintainer Agent`
4. Select scopes:
   ```
   ✅ repo
   ✅ read:user
   ✅ read:org
   ```
5. Click: **"Generate token"**
6. **Copy the token** (starts with `ghp_`)

### 3️⃣ Get Gemini API Key

1. Open: https://makersuite.google.com/app/apikey
2. Click: **"Create API Key"**
3. **Copy the key**

### 4️⃣ Edit Your .env File

Open the `.env` file and replace the placeholders:

**BEFORE:**
```env
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**AFTER:**
```env
GITHUB_TOKEN=ghp_abc123xyz789yourActualTokenHere
GEMINI_API_KEY=AIzaSyD_yourActualGeminiKeyHere
```

### 5️⃣ Save the File

- **Notepad**: File → Save (or Ctrl+S)
- **Nano**: Ctrl+O, Enter, Ctrl+X
- **VS Code**: Ctrl+S (or Cmd+S on Mac)

## ✅ Verify Your Setup

Run this command to check everything is working:

```bash
python verify_setup.py
```

You should see:
```
✅ Python version: 3.11.x
✅ All required packages installed
✅ Environment variables loaded
✅ GitHub token is valid
✅ Gemini API key is valid

🎉 Setup complete! You're ready to go!
```

## 🚀 Run Your First Analysis

```bash
python main.py analyze YOUR_GITHUB_USERNAME
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username (e.g., `octocat`)

## 🔒 Security Notes

### ⚠️ IMPORTANT: Keep Your Credentials Secret!

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Don't share your tokens** - They give full access to your GitHub account
3. **Rotate tokens regularly** - Generate new ones every few months
4. **Use environment-specific tokens** - Different tokens for dev/prod

### Check Your .gitignore

Make sure `.env` is listed in `.gitignore`:

```bash
# Check if .env is ignored
cat .gitignore | grep .env
```

You should see:
```
.env
```

## 🆘 Troubleshooting

### "File not found: .env"
- Make sure you created the `.env` file (not `.env.txt`)
- Check you're in the `penguin-ai-agent` directory
- On Windows, make sure file extensions are visible

### "Invalid GitHub token"
- Check the token starts with `ghp_`
- Make sure you copied the entire token
- Verify the token has the required scopes
- Try generating a new token

### "Gemini API error"
- Check the key starts with `AIza`
- Make sure you copied the entire key
- Verify the key is active at https://makersuite.google.com/app/apikey

### "Environment variable not found"
- Make sure the `.env` file is in the `penguin-ai-agent` directory
- Check there are no spaces around the `=` sign
- Restart your terminal after creating `.env`

## 📝 Example .env File

Here's what a complete `.env` file looks like:

```env
# GitHub API Configuration
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz

# Gemini API Configuration
GEMINI_API_KEY=AIzaSyD_abcdefghijklmnopqrstuvwxyz1234567

# Optional: Logging Configuration
LOG_LEVEL=INFO

# Optional: Performance Configuration
MAX_PARALLEL_REPOS=5
```

## 🎯 Quick Reference

| Credential | Where to Get It | Format |
|------------|----------------|--------|
| GitHub Token | https://github.com/settings/tokens | `ghp_...` |
| Gemini API Key | https://makersuite.google.com/app/apikey | `AIza...` |

## ✨ You're All Set!

Once your `.env` file is configured, you can:

1. ✅ Analyze your repositories
2. ✅ Generate maintenance suggestions
3. ✅ Create GitHub issues automatically
4. ✅ Track repository health over time

**Next**: Read [QUICK_START.md](QUICK_START.md) for usage examples!
