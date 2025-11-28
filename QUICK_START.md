# VibeMailing - Quick Start Guide

## Prerequisites

- Python 3.13 installed
- Chrome browser (version 142 or compatible)
- Groq API key ([Get one here](https://console.groq.com/keys))
- Gmail account for testing: `vibemailingtest@gmail.com`

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd vibe-mailing-automation
uv sync
```

### 2. Configure API Key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
nano .env
```

Add this line:
```
GROQ_API_KEY=your-actual-groq-api-key-here
```

### 3. First-Time Gmail Setup

```bash
python main.py setup
```

**What happens:**
1. Chrome browser will open
2. You'll be prompted to log in to `vibemailingtest@gmail.com`
3. Complete 2FA if prompted
4. Wait for inbox to load
5. Press Enter when done

**Your login session is saved!** You won't need to login again.

## Running Your First Campaign

### Test with Sample Contacts

```bash
python main.py campaign --csv tests/sample_contacts.csv
```

**The system will:**
1. Ask you to select an account (choose `vibemailingtest@gmail.com`)
2. Load the CSV (2 contacts: your emails)
3. Ask you to select a template (choose `default_outreach`)
4. Show campaign summary
5. Ask you to press Enter to start

### Preview Mode (Recommended for First Run)

For each contact, you'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email Preview [1/2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Contact:  Shravan Revanna (Personal)
To:       shravanrevanna@gmail.com
Subject:  Quick question about Personal

Body:
---------------------------------------------------------
Hi Shravan,

I noticed your work at Personal and was impressed by your
background...

---------------------------------------------------------

Options:
  [s] Send this email
  [k] Skip this contact
  [e] Edit email body
  [a] Abort campaign

Your choice (s/k/e/a):
```

**Choose:**
- `s` - Send the email
- `k` - Skip this person
- `e` - Edit the email text
- `a` - Stop the campaign

### After Sending

You'll see:
```
✓ [1/2] Email sent to shravanrevanna@gmail.com

⏳ Cooling down: 37 seconds remaining...
```

The system waits 20-45 seconds (random) between emails to avoid Gmail blocking.

## Campaign Complete

When done, you'll see a summary:

```
============================================================
CAMPAIGN SUMMARY
============================================================

Account:          vibemailingtest@gmail.com
Template:         default_outreach
Mode:             semi
CSV File:         sample_contacts.csv

Total Contacts:   2
Processed:        2
  ✓ Sent:         2
  ✗ Failed:       0
  ⊘ Skipped:      0
Remaining:        0

Success Rate:     100.0%
Duration:         1.2 minutes

============================================================
```

## What Just Happened?

1. **LLM Generated Personalized Emails**
   - Used Groq's `llama-3.3-70b-versatile` model
   - Took your template and made it unique for each person
   - Kept the structure but personalized the content

2. **Sent Through Gmail**
   - Automated browser interaction
   - Real Gmail web interface
   - Looks like you sent it manually

3. **Saved Progress**
   - Every email saved to checkpoint
   - Can resume if interrupted (Ctrl+C)
   - Full logs in `logs/app.log`

## Next Steps

### Run a Real Campaign

1. **Create your contacts CSV:**

```csv
name,company,email,linkedin
John Doe,Acme Corp,john@acme.com,https://linkedin.com/in/johndoe
Jane Smith,TechCo,jane@techco.com,https://linkedin.com/in/janesmith
```

2. **Customize your template** in `config/prompts.yaml`

3. **Run campaign:**

```bash
python main.py campaign --csv your_contacts.csv
```

### Autonomous Mode (No Preview)

Once you trust the system:

```bash
python main.py campaign --csv contacts.csv --mode autonomous
```

This will auto-send all emails without asking for confirmation.

## Common Commands

```bash
# Show help
python main.py --help

# First-time setup (do once per account)
python main.py setup

# Run campaign (interactive)
python main.py campaign

# Run with specific CSV
python main.py campaign --csv mycontacts.csv

# Autonomous mode (no preview)
python main.py campaign --csv mycontacts.csv --mode autonomous

# Use different template
python main.py campaign --csv mycontacts.csv --template follow_up
```

## Troubleshooting

### "ChromeDriver not found"
- Make sure Chrome browser is installed
- System will try to use built-in ChromeDriver

### "Not logged in"
- Run `python main.py setup` again
- Make sure you completed the login fully
- Check that inbox was visible before pressing Enter

### "LLM API error"
- Check `.env` has correct `GROQ_API_KEY`
- Verify you have API credits at console.groq.com
- Check internet connection

### "Email not sending"
- Check `logs/app.log` for detailed error
- Gmail might have changed UI (update selectors in `core/email_sender.py`)
- Account may be rate-limited (wait 24 hours)

## Where Things Are

```
├── config/
│   ├── settings.yaml      # Browser, LLM, cooldown settings
│   ├── accounts.yaml      # Your Gmail accounts
│   └── prompts.yaml       # Email templates
│
├── logs/
│   └── app.log            # Everything that happens
│
├── checkpoints/           # Resume state if interrupted
│
└── profiles/              # Chrome login sessions
```

## Safety Features

- **20-45 second cooldown** between emails (random)
- **Progress saved** after every email
- **Can resume** if you stop (Ctrl+C)
- **Comprehensive logs** of everything
- **Preview mode** to check before sending

## Tips

1. **Test first** with `tests/sample_contacts.csv` (your own emails)
2. **Use semi mode** until you trust the templates
3. **Check logs** if anything goes wrong
4. **Respect limits** - Gmail allows ~500 emails/day for free accounts
5. **Be genuine** - personalize templates, don't spam

## Support

- Check `logs/app.log` for detailed errors
- Read `README.md` for full documentation
- See `CLAUDE.md` for development details

---

That's it! You're ready to send personalized emails at scale. 🚀

Start with the test campaign and work your way up to real outreach.
