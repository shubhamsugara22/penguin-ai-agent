# 🚀 How to Run the GitHub Maintainer Agent

## ✅ Setup Complete!

Your verification passed! Now let's run the agent.

---

## 📋 Before You Start

Make sure you have:
1. ✅ Virtual environment activated: `source venv/Scripts/activate` (Git Bash)
2. ✅ Created `.env` file with your credentials
3. ✅ Set PYTHONPATH (see below)

---

## 🔧 Set PYTHONPATH (Required Every Time)

### **Git Bash:**
```bash
export PYTHONPATH="$(pwd)"
```

### **PowerShell:**
```powershell
$env:PYTHONPATH = $PWD
```

### **Command Prompt:**
```cmd
set PYTHONPATH=%CD%
```

Or use the helper scripts:
```bash
# Git Bash
source setup_env.sh

# Command Prompt
setup_env.bat
```

---

## 🎯 Run the Agent

### **Step 1: Create Your .env File**

If you haven't already:

```bash
cp .env.example .env
nano .env  # or use notepad .env
```

Add your credentials:
```env
GITHUB_TOKEN=ghp_your_actual_token_here
GEMINI_API_KEY=AIza_your_actual_key_here
```

### **Step 2: Verify Setup**

```bash
export PYTHONPATH="$(pwd)"
python scripts/verify/verify_setup.py
```

You should see: `✓ All checks passed!`

### **Step 3: Run Your First Analysis**

```bash
# Basic usage - analyze all your repos
python main.py analyze YOUR_GITHUB_USERNAME

# Example with filters
python main.py analyze YOUR_GITHUB_USERNAME \
  --language Python \
  --updated-after 2024-01-01 \
  --automation manual

# Focus on specific areas
python main.py analyze YOUR_GITHUB_USERNAME \
  --focus tests,docs,security
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

---

## 📝 Complete Example Session

```bash
# 1. Navigate to project
cd ~/OneDrive/Desktop/penguin-ai-agent/penguin-ai-agent

# 2. Activate virtual environment
source venv/Scripts/activate

# 3. Set PYTHONPATH
export PYTHONPATH="$(pwd)"

# 4. Run the agent
python main.py analyze octocat --language Python
```

---

## 🎨 Usage Examples

### Analyze All Repositories
```bash
python main.py analyze YOUR_USERNAME
```

### Filter by Language
```bash
python main.py analyze YOUR_USERNAME --language Python
python main.py analyze YOUR_USERNAME --language JavaScript
```

### Filter by Date
```bash
# Only repos updated after Jan 1, 2024
python main.py analyze YOUR_USERNAME --updated-after 2024-01-01
```

### Focus on Specific Areas
```bash
# Focus on tests and documentation
python main.py analyze YOUR_USERNAME --focus tests,docs

# Focus on security
python main.py analyze YOUR_USERNAME --focus security
```

### Exclude Repositories
```bash
python main.py analyze YOUR_USERNAME --exclude old-repo,archived-project
```

### Auto-Approve Mode
```bash
# Automatically create issues without asking
python main.py analyze YOUR_USERNAME --automation auto
```

### Combine Options
```bash
python main.py analyze YOUR_USERNAME \
  --language Python \
  --updated-after 2024-01-01 \
  --focus tests,docs \
  --exclude archived-repo \
  --automation manual
```

---

## 🔍 What Happens During Analysis?

1. **🚀 Initialization**: Sets up session and loads preferences
2. **📥 Fetching**: Retrieves your repositories from GitHub
3. **🔍 Analyzing**: Examines each repo's health (tests, docs, CI/CD, etc.)
4. **💡 Generating**: AI creates maintenance suggestions
5. **✋ Approval**: You review and approve suggestions
6. **📝 Creating**: Approved suggestions become GitHub issues
7. **✅ Complete**: Shows summary with issue URLs

---

## 📊 Example Output

```
🚀 Starting GitHub Maintainer Agent...

📥 Fetching repositories for user: octocat
   Found 5 repositories

🔍 Analyzing repositories...
   [1/5] octocat/Hello-World ✓
   [2/5] octocat/Spoon-Knife ✓
   [3/5] octocat/test-repo ✓
   [4/5] octocat/my-project ✓
   [5/5] octocat/awesome-app ✓

💡 Generated 12 maintenance suggestions

✋ Review suggestions? [y/n]: y

Repository: octocat/Hello-World
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Add unit tests for core module
   Category: enhancement | Priority: high | Effort: medium
   
   Rationale: No test files detected. Adding tests will improve code quality
   and catch bugs early.
   
   Create issue? [y/n]: y

2. Update README with setup instructions
   Category: documentation | Priority: medium | Effort: small
   
   Rationale: README is minimal. Adding setup instructions will help new
   contributors get started.
   
   Create issue? [y/n]: y

...

📝 Creating GitHub issues...
   ✓ Created: octocat/Hello-World#123
   ✓ Created: octocat/Hello-World#124

✅ Analysis Complete!

Session ID: abc123-def456
Repositories Analyzed: 5
Suggestions Generated: 12
Issues Created: 8

Created Issues:
  ✓ octocat/Hello-World#123: Add unit tests for core module
    https://github.com/octocat/Hello-World/issues/123
  ✓ octocat/Hello-World#124: Update README with setup instructions
    https://github.com/octocat/Hello-World/issues/124
  ...
```

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'src'"
**Solution**: Set PYTHONPATH
```bash
export PYTHONPATH="$(pwd)"
```

### "Authentication failed"
**Solution**: Check your `.env` file has valid tokens
```bash
cat .env  # Verify tokens are set
```

### "Rate limit exceeded"
**Solution**: Wait for rate limit to reset, or use filters to analyze fewer repos
```bash
python main.py analyze YOUR_USERNAME --language Python  # Analyze fewer repos
```

### "Gemini API error"
**Solution**: Verify your API key at https://makersuite.google.com/app/apikey

---

## 💡 Pro Tips

1. **Start small**: Use `--language` filter to test with fewer repos first
2. **Use manual mode**: Review suggestions before creating issues
3. **Check logs**: Add `--log-level DEBUG` for detailed output
4. **Save time**: Use `--automation auto` once you trust the suggestions
5. **Focus areas**: Use `--focus` to get targeted suggestions

---

## 📚 More Help

- **CLI Usage**: See [CLI_USAGE.md](CLI_USAGE.md)
- **Credentials**: See [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md)
- **Quick Start**: See [QUICK_START.md](QUICK_START.md)
- **Evaluation**: See [docs/EVALUATION.md](docs/EVALUATION.md)

---

## 🎉 You're Ready!

Run your first analysis:

```bash
export PYTHONPATH="$(pwd)"
python main.py analyze YOUR_GITHUB_USERNAME
```

Happy maintaining! 🚀
