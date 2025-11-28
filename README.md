# VibeMailing

**Multi-Account Gmail Automation with LLM-Powered Email Personalization**

VibeMailing is a side-project email automation tool that generates personalized emails using LLMs (via Groq) and sends them through Gmail with proper rate limiting and safety features.

## Features

- **Multi-Account Support**: Manage multiple Gmail accounts with isolated Chrome profiles
- **LLM-Powered Personalization**: Generate genuinely personalized emails using Groq's LLM
- **Two Operation Modes**:
  - **Semi-Automated**: Preview and edit each email before sending
  - **Autonomous**: Auto-send without manual intervention
- **Resume Capability**: Automatic checkpointing allows resuming interrupted campaigns
- **Rate Limiting**: Configurable cooldown with jitter to avoid Gmail blocking
- **CSV-Based Contacts**: Simple contact management via CSV files
- **Comprehensive Logging**: Track every action with detailed logs

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd vibe-mailing-automation

# Install dependencies using uv
uv sync

# Or with pip
pip install selenium pyyaml requests python-dotenv openai
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your-api-key-here
```

Edit `config/accounts.yaml` to add your Gmail account:

```yaml
accounts:
  - id: my_account
    email: your-email@gmail.com
    profile_dir: profile_your_email
    display_name: "My Account"
```

### 3. First-Time Setup

Run the setup command to configure your Gmail account:

```bash
python main.py setup
```

This will:

1. Launch Chrome browser
2. Prompt you to log in to Gmail
3. Handle 2FA authentication
4. Save your session for future use

### 4. Prepare Your Contact List

Create a CSV file with these columns:

- `name` - Contact name
- `company` - Company name
- `email` - Email address
- `linkedin` - LinkedIn profile URL

Example (`contacts.csv`):

```csv
name,company,email,linkedin
John Doe,Acme Corp,john@acme.com,https://linkedin.com/in/johndoe
Jane Smith,Tech Startup,jane@techstartup.com,https://linkedin.com/in/janesmith
```

See `tests/sample_contacts.csv` for a working example.

### 5. Run Your First Campaign

```bash
# Interactive mode (recommended for first time)
python main.py campaign

# Or specify CSV directly
python main.py campaign --csv contacts.csv
```

## Usage

### Commands

```bash
# First-time account setup
python main.py setup

# Run campaign (interactive)
python main.py campaign

# Run campaign with specific CSV
python main.py campaign --csv contacts.csv

# Run in autonomous mode (no preview)
python main.py campaign --csv contacts.csv --mode autonomous

# Use specific template
python main.py campaign --csv contacts.csv --template follow_up

# Help
python main.py --help
python main.py campaign --help
```

### Operation Modes

**Semi-Automated Mode** (Default, Recommended)

- Preview each email before sending
- Edit subject or body if needed
- Skip contacts individually
- Full control over what gets sent

**Autonomous Mode**

- Auto-generate and send without preview
- Faster for large campaigns
- Best when you trust your template and LLM output

## Configuration

### settings.yaml

```yaml
# Browser settings
browser:
  headless: false # Always visible (recommended)
  profile_base_dir: "./profiles"

# Operation mode
mode: "semi" # Options: "autonomous" | "semi"

# LLM configuration (Groq)
llm:
  base_url: "https://api.groq.com/openai/v1"
  model: "llama-3.3-70b-versatile"
  api_key: "ENV:GROQ_API_KEY" # Reads from .env file
  temperature: 0.7
  max_tokens: 500

# Campaign settings
campaign:
  cooldown:
    min_seconds: 20 # Minimum wait between emails
    max_seconds: 45 # Maximum wait between emails
    jitter: true # Add random variation
```

### prompts.yaml

Define email templates and personalization instructions:

```yaml
system_prompt: |
  You are an expert email writer specializing in professional outreach.
  Write concise, personalized, and engaging emails that feel genuine.
  Keep emails under 150 words.
  Avoid corporate jargon and overly salesy language.

templates:
  - name: default_outreach
    subject_template: "Quick question about {company}"
    body_template: |
      Hi {name},

      I noticed your work at {company} and was impressed by your background.

      I'm reaching out because I believe we might have some interesting
      opportunities to collaborate.

      Would you be open to a brief conversation?

      Best regards,
      Shravan

    personalization_prompt: |
      Personalize this email for {name} who works at {company}.
      Make it feel genuine and specific to their background.
      Keep the same structure but make it authentic, not templated.
```

## Safety Features

- **Rate Limiting**: 20-45 second cooldown between emails (configurable)
- **Random Jitter**: Adds variation to avoid bot detection
- **Checkpointing**: Automatic progress saving every email
- **Resume Capability**: Pick up where you left off if interrupted
- **Comprehensive Logging**: Every action is logged to `logs/app.log`
- **Daily Limits**: Respects Gmail's sending limits (~500/day for free accounts)

## Project Structure

```yaml
vibe-mailing-automation/
  config/                 # Configuration files
    settings.yaml      # Main settings
    accounts.yaml      # Gmail accounts
    prompts.yaml       # Email templates
  core/                   # Core modules
    browser.py         # Chrome automation
    login_checker.py   # Gmail login verification
    csv_loader.py      # Contact list loading
    checkpoint.py      # Progress checkpointing
    tracker.py         # Campaign tracking
    llm_client.py      # LLM integration (Groq)
    email_sender.py    # Gmail sending automation
    email_preview.py   # Preview interface
    cooldown.py        # Rate limiting
  workflows/              # Orchestration
    first_time_login.py
    run_campaign.py
  profiles/               # Chrome user profiles (gitignored)
  logs/                   # Log files (gitignored)
  checkpoints/            # Campaign state (gitignored)
  tests/                  # Test data
    sample_contacts.csv
  main.py                 # Entry point
```

## Troubleshooting

### "ChromeDriver not found"

Make sure Chrome browser is installed and up to date. The script will attempt to use the system ChromeDriver.

### "Gmail selectors not working"

Gmail's UI changes frequently. If email sending fails:

1. Check `logs/app.log` for details
2. Gmail selectors in `core/email_sender.py` may need updating
3. Open an issue with the error details

### "Profile not persisting login"

Ensure:

- Profile directory exists and has write permissions
- You're not running in headless mode during first-time setup
- Chrome isn't in incognito mode

### "LLM API errors"

Check:

- Your Groq API key in `.env` is correct
- You have API credits available
- Network connectivity

### "Email not sending"

- Verify you're logged in (`python main.py setup`)
- Check `logs/app.log` for specific errors
- Gmail may have rate-limited your account (wait 24 hours)

## Campaign Statistics

After each campaign, you'll see a summary:

```
CAMPAIGN SUMMARY
============================================================

Account:          vibemailingtest@gmail.com
Template:         default_outreach
Mode:             semi
CSV File:         contacts.csv

Total Contacts:   50
Processed:        50
   Sent:          48
   Failed:        2
   Skipped:       0
Remaining:        0

Success Rate:     96.0%
Duration:         42.1 minutes
Avg Time/Email:   50.5 seconds

Started:          2024-11-28T10:30:00
Completed:        2024-11-28T11:12:00

============================================================
```

## Contributing

This is a side project for personal use. Feel free to fork and customize for your needs.

## Disclaimer

Use responsibly and respect email best practices:

- Only contact people you have a legitimate reason to reach
- Respect opt-out requests immediately
- Don't spam
- Follow CAN-SPAM Act and GDPR regulations
- Use reasonable sending volumes

The authors are not responsible for misuse of this tool.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [Selenium](https://www.selenium.dev/)
- LLM powered by [Groq](https://groq.com/)
- Inspired by the need for genuine personalization at scale

---

**Made by Shravan Revanna**
