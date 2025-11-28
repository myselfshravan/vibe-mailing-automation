# VibeMailing - Agentic Development Guide

## Project Overview

**VibeMailing** is a multi-account Gmail automation system that uses LLMs to generate personalized emails for outreach campaigns. The system emphasizes simplicity, maintainability, and safety.

### Core Philosophy
- **DRY** (Don't Repeat Yourself)
- **KISS** (Keep It Simple, Stupid)
- **Modular** architecture for easy maintenance
- **Side project** scope - just working enough, not enterprise-grade

---

## Project Requirements

### Functional Requirements

1. **Multi-Account Support**
   - Support multiple Gmail accounts
   - User selects account at runtime via CLI
   - Each account uses isolated Chrome profile
   - One campaign = one account (no mixing)

2. **Authentication Strategy**
   - Chrome profile persistence (NOT raw cookies)
   - Manual login once per account (handles 2FA)
   - Browser always visible (configurable in settings)
   - Fallback: prompt user to re-login if session expires

3. **Email Personalization**
   - CSV-based contact list with fields: name, company, email, linkedin
   - Multiple email templates supported
   - Same outer structure, 1-5 lines vary per recipient
   - LLM-generated content using universal provider support

4. **LLM Integration**
   - Universal base_url + API key configuration
   - Support for: OpenAI, Claude, Gemini, Groq, Kimi, DeepSeek, Mistral, TogetherAI
   - System prompt and template stored in YAML
   - Future-proof for LinkedIn context injection

5. **Operation Modes**
   - **Fully Autonomous**: Generate → Send → Next
   - **Semi-Automated**: Generate → Preview → User Confirms → Send → Next

6. **Safety & Rate-Limiting**
   - Configurable cooldown between emails (min/max seconds)
   - Random jitter to avoid bot detection
   - Progress checkpointing for resume capability
   - Detailed logging to .log file

7. **User Experience**
   - CLI-based interface
   - Account selection at startup
   - CSV file selection (provided each run)
   - Campaign progress tracking
   - Summary report at completion

---

## Technical Stack

### Core Technologies
- **Python 3.10+** with `uv` for dependency management
- **Selenium >= 4.38.0** for browser automation
- **Chrome** browser with persistent profiles
- **YAML** for configuration files
- **JSON** for checkpointing

### Key Dependencies
```
selenium>=4.38.0
pyyaml
requests (for LLM API calls)
```

---

## Project Structure

```
email_sender/
│
├── config/
│   ├── settings.yaml          # Core settings: headless, cooldown, LLM config
│   ├── accounts.yaml          # Gmail accounts + profile directories
│   ├── prompts.yaml           # LLM system prompt + message templates
│
├── profiles/
│   ├── profile_email1/        # Chrome user profile for account 1
│   ├── profile_email2/        # Chrome user profile for account 2
│   └── ...
│
├── core/
│   ├── __init__.py
│   ├── browser.py             # Launch Chrome with specific profile
│   ├── login_checker.py       # Verify login status, prompt re-login
│   ├── csv_loader.py          # Load CSV + handle checkpointing
│   ├── email_generator.py     # LLM-based email generation
│   ├── email_preview.py       # Preview logic for semi-auto mode
│   ├── email_sender.py        # Selenium automation for sending
│   ├── cooldown.py            # Rate-limiting & cooldown logic
│   ├── tracker.py             # Progress tracking per row
│   ├── logger.py              # Logging to .log file
│
├── workflows/
│   ├── __init__.py
│   ├── run_campaign.py        # Main campaign orchestration
│   ├── first_time_login.py    # Initial profile setup workflow
│
├── logs/
│   ├── app.log                # Master log file
│   └── campaign_history/      # Per-campaign summaries
│
├── checkpoints/
│   └── campaign_checkpoint.json   # Resume state
│
├── main.py                    # Entry point
├── pyproject.toml             # uv project file
└── README.md                  # Project documentation
```

---

## Configuration Files

### 1. config/settings.yaml

```yaml
# Browser Configuration
browser:
  headless: false                    # Always visible (user preference)
  profile_base_dir: "./profiles"     # Where Chrome profiles are stored

# Workflow Mode
mode: "semi"                         # Options: "autonomous" | "semi"

# LLM Configuration
llm:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o"
  api_key: "ENV:LLM_API_KEY"         # Read from environment variable

# Email Campaign Settings
campaign:
  cooldown:
    min_seconds: 20
    max_seconds: 45
    jitter: true

# Logging
logging:
  log_file: "./logs/app.log"
  level: "INFO"                      # DEBUG | INFO | WARNING | ERROR
```

### 2. config/accounts.yaml

```yaml
accounts:
  - id: email1
    email: email1@gmail.com
    profile_dir: profile_email1

  - id: email2
    email: email2@gmail.com
    profile_dir: profile_email2
```

### 3. config/prompts.yaml

```yaml
# System prompt for LLM
system_prompt: |
  You are an expert email writer specializing in professional outreach.
  Write concise, personalized, and engaging emails that feel genuine.
  Keep emails under 150 words.
  Avoid corporate jargon.

# Email templates
templates:
  - name: default_outreach
    subject_template: "Quick question about {company}"
    body_template: |
      Hi {name},
      
      I noticed your work at {company} and was impressed by [specific detail].
      
      I'm reaching out because [reason for contact].
      
      Would you be open to a brief conversation about [topic]?
      
      Best regards,
      [Your Name]
    
    # Personalization instructions for LLM
    personalization_prompt: |
      Personalize this email for {name} who works at {company}.
      LinkedIn: {linkedin}
      
      Make it feel genuine and specific to their background.
      Change 1-3 sentences to reference their industry or recent work.

  - name: follow_up
    subject_template: "Following up - {company}"
    body_template: |
      Hi {name},
      
      I wanted to follow up on my previous email about [topic].
      
      [New angle or additional value proposition]
      
      Let me know if you're interested!
      
      Best,
      [Your Name]
    
    personalization_prompt: |
      Create a follow-up email for {name} at {company}.
      Keep it brief and add value.
```

---

## Module Specifications

### core/browser.py

**Purpose**: Manage Chrome browser lifecycle with profile support

**Key Functions**:
- `create_browser(profile_dir: str, headless: bool) -> WebDriver`
  - Launch Chrome with specified profile directory
  - Apply headless setting from config
  - Set up browser options (window size, etc.)
  - Return WebDriver instance

**Implementation Notes**:
- Use `--user-data-dir` Chrome argument for profile
- Ensure profile directory exists before launching
- Handle ChromeDriver path configuration

---

### core/login_checker.py

**Purpose**: Verify Gmail login status and handle re-login

**Key Functions**:
- `check_login_status(driver: WebDriver) -> bool`
  - Navigate to Gmail
  - Check if user is logged in
  - Return True if logged in, False otherwise

- `prompt_manual_login(driver: WebDriver) -> None`
  - Display message: "Please log in manually"
  - Open Gmail login page
  - Wait for user input to continue
  - Verify successful login

**Implementation Notes**:
- Check for Gmail inbox elements to verify login
- Handle 2FA gracefully (user completes manually)
- Don't automate password entry (security + 2FA issues)

---

### core/csv_loader.py

**Purpose**: Load CSV contacts and manage checkpointing

**Key Functions**:
- `load_csv(file_path: str) -> List[Dict]`
  - Read CSV with required columns: name, company, email, linkedin
  - Validate all required fields present
  - Return list of contact dictionaries

- `get_checkpoint() -> Optional[Dict]`
  - Load checkpoint file if exists
  - Return last completed row index and campaign state

- `save_checkpoint(campaign_state: Dict) -> None`
  - Save current progress to checkpoint file
  - Include: CSV path, current row index, timestamp

- `should_resume_campaign() -> bool`
  - Check if checkpoint exists
  - Prompt user: "Resume previous campaign? (y/n)"
  - Return user decision

**Implementation Notes**:
- Use standard CSV library
- Checkpoint format: JSON with fields {csv_path, current_row, timestamp, account_used}
- Validate CSV structure before processing

---

### core/email_generator.py

**Purpose**: Generate personalized emails using LLM

**Key Functions**:
- `load_llm_config() -> Dict`
  - Read LLM settings from config
  - Load system prompt and templates from prompts.yaml
  - Handle environment variables for API keys

- `generate_email(contact: Dict, template_name: str) -> Dict[str, str]`
  - Inject contact data into template
  - Build LLM prompt with system + user template
  - Call LLM API (universal base_url support)
  - Return {subject, body}

- `call_llm_api(prompt: str) -> str`
  - Make HTTP request to LLM provider
  - Handle different provider response formats
  - Include error handling and retries

**Implementation Notes**:
- Use requests library for API calls
- Support OpenAI-compatible API format (most providers support this)
- Template variables: {name}, {company}, {email}, {linkedin}
- Future: Add {linkedin_context} for scraped data

---

### core/email_preview.py

**Purpose**: Display email preview and get user confirmation (semi-auto mode)

**Key Functions**:
- `preview_email(subject: str, body: str, recipient: str) -> str`
  - Display formatted email in terminal
  - Show: To, Subject, Body
  - Prompt: "Send this email? (y/n/edit)"
  - Return user choice

- `edit_email(body: str) -> str`
  - Allow inline editing if user chooses 'edit'
  - Return modified body

**Implementation Notes**:
- Clear terminal display for readability
- Color coding for better UX (optional)
- Only used when mode="semi" in settings

---

### core/email_sender.py

**Purpose**: Automate email sending through Gmail web interface

**Key Functions**:
- `send_email(driver: WebDriver, to: str, subject: str, body: str) -> bool`
  - Navigate to Gmail compose
  - Fill recipient, subject, body
  - Click send button
  - Wait for confirmation
  - Return success status

**Implementation Notes**:
- Use explicit waits for element loading
- Handle Gmail's dynamic UI
- Verify email sent (check for sent confirmation)
- Robust error handling for element not found

**Gmail Selectors** (may need updating):
- Compose button: `//div[@gh='cm']` or similar
- To field: `name='to'`
- Subject: `name='subjectbox'`
- Body: `div[aria-label='Message Body']`
- Send: `div[@aria-label*='Send']`

---

### core/cooldown.py

**Purpose**: Implement rate-limiting between email sends

**Key Functions**:
- `apply_cooldown(min_sec: int, max_sec: int, jitter: bool) -> None`
  - Calculate wait time (random between min and max)
  - Apply jitter if enabled (small random adjustment)
  - Sleep for calculated duration
  - Log cooldown duration

**Implementation Notes**:
- Use random.uniform() for random wait
- Jitter adds ±10% variation
- Display countdown in terminal (optional)

---

### core/tracker.py

**Purpose**: Track campaign progress and maintain state

**Key Functions**:
- `log_email_attempt(contact: Dict, status: str, details: Dict) -> None`
  - Log each email send attempt
  - Include: timestamp, contact email, status, error if failed

- `update_checkpoint(row_index: int) -> None`
  - Update checkpoint file with current progress

- `generate_summary() -> Dict`
  - Count successful sends, failures
  - Calculate total time
  - Return summary statistics

**Implementation Notes**:
- Write to both app.log and checkpoint file
- Maintain running counts in memory
- Flush logs after each email

---

### core/logger.py

**Purpose**: Centralized logging utility

**Key Functions**:
- `setup_logger(log_file: str, level: str) -> logging.Logger`
  - Configure Python logging
  - Set up file handler
  - Format: timestamp, level, message

- `log_info(message: str) -> None`
- `log_error(message: str, exception: Exception = None) -> None`
- `log_debug(message: str) -> None`

**Implementation Notes**:
- Use Python's built-in logging module
- Rotate logs if they get too large (optional)
- Include exception tracebacks for errors

---

### workflows/run_campaign.py

**Purpose**: Main campaign orchestration

**Workflow Steps**:
1. Load configuration
2. Select Gmail account (user input)
3. Launch Chrome with selected profile
4. Check login status (prompt if needed)
5. Check for existing checkpoint
6. Select CSV file (user input)
7. Load CSV and get starting row
8. Select email template (user input or default)
9. **For each contact**:
   - Generate personalized email
   - Preview (if semi-auto mode)
   - Send email
   - Update tracker
   - Save checkpoint
   - Apply cooldown
10. Generate and display summary
11. Clean up (close browser)

**Error Handling**:
- Graceful shutdown on interrupt (Ctrl+C)
- Save progress before exit
- Log all errors

---

### workflows/first_time_login.py

**Purpose**: Set up new Gmail account profile

**Workflow Steps**:
1. Select account from accounts.yaml
2. Check if profile already exists
3. Launch Chrome with new profile directory
4. Navigate to Gmail
5. Display: "Please log in manually"
6. Wait for user confirmation
7. Verify login successful
8. Save profile for future use

---

## Implementation Guidelines

### Development Approach

1. **Start Simple**
   - Implement basic browser launch first
   - Add login checking
   - Build up functionality incrementally

2. **Testing Strategy**
   - Test with single contact first
   - Use test Gmail account
   - Verify profile persistence
   - Test resume from checkpoint

3. **Error Handling**
   - Graceful degradation
   - Clear error messages
   - Log all errors
   - Don't crash on single failure

4. **Code Quality**
   - Type hints for all functions
   - Docstrings for public methods
   - Keep functions small (<50 lines)
   - One module = one responsibility

### Security Considerations

1. **Credentials**
   - NEVER hardcode API keys or passwords
   - Use environment variables
   - Add .env to .gitignore

2. **Rate Limiting**
   - Respect Gmail's sending limits
   - Default: 20-45 second cooldown
   - Consider daily limits (500 emails for free accounts)

3. **Profile Storage**
   - Profiles contain sensitive data
   - Add profiles/ to .gitignore
   - Warn users about sharing profiles

### Future Enhancements (Out of Scope for v1)

- LinkedIn profile scraping for enriched context
- A/B testing different templates
- Email scheduling
- Response tracking
- Web dashboard UI
- Batch operations
- Email analytics

---

## CLI User Experience

### Startup Flow

```
=== VibeMailing ===

Select Gmail account:
1. email1@gmail.com
2. email2@gmail.com
3. Add new account

Your choice: 1

Loading Chrome profile for email1@gmail.com...
Checking login status...
✓ Logged in successfully

Resume previous campaign? (y/n): n

Enter path to CSV file: ./contacts.csv
✓ Loaded 50 contacts

Select email template:
1. default_outreach
2. follow_up

Your choice: 1

Mode: Semi-Automated (preview before sending)
Cooldown: 20-45 seconds between emails

Starting campaign...
```

### Email Preview (Semi-Auto Mode)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email Preview [1/50]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To: john.doe@example.com
Subject: Quick question about Acme Corp

Body:
Hi John,

I noticed your work at Acme Corp and was impressed by 
your recent product launch. The integration features 
look innovative.

I'm reaching out because I'm working on similar 
challenges in the B2B space and would love to hear 
your perspective.

Would you be open to a brief conversation about 
product development strategies?

Best regards,
Jane

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Send this email? (y/n/edit): y

✓ Email sent successfully
⏳ Cooling down for 37 seconds...
```

### Campaign Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Campaign Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total contacts: 50
Emails sent: 48
Failed: 2
Duration: 42 minutes

Success rate: 96%

Failed contacts:
- invalid@example.com (invalid email)
- blocked@example.com (sending error)

Logs saved to: ./logs/app.log
Campaign history: ./logs/campaign_history/2024-11-25.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Getting Started (for Developers)

### Initial Setup

```bash
# Clone repository
cd email_sender

# Initialize uv project (already done)
# uv init

# Add dependencies
uv add selenium pyyaml requests

# Create directory structure
mkdir -p config profiles core workflows logs checkpoints logs/campaign_history

# Download ChromeDriver (if not in PATH)
# Place in system PATH or specify in settings
```

### Configuration

1. Copy example configs:
   ```bash
   cp config/settings.example.yaml config/settings.yaml
   cp config/accounts.example.yaml config/accounts.yaml
   cp config/prompts.example.yaml config/prompts.yaml
   ```

2. Edit `config/accounts.yaml` - add your Gmail accounts

3. Set environment variable for LLM API key:
   ```bash
   export LLM_API_KEY="your-api-key-here"
   ```

4. Adjust `config/settings.yaml` as needed

### First Run

```bash
# Run first-time login for each account
python main.py --setup

# Run a campaign
python main.py --campaign
```

---

## Testing Checklist

Before considering the project complete, test:

- ✅ Browser launches with correct profile
- ✅ Login check works (both logged in and logged out states)
- ✅ Manual login prompt appears when needed
- ✅ CSV loads correctly with all required fields
- ✅ LLM generates reasonable personalized emails
- ✅ Email preview displays correctly (semi-auto mode)
- ✅ Emails send successfully through Gmail
- ✅ Cooldown applies between emails
- ✅ Checkpoint saves and resumes work
- ✅ Logs write to file correctly
- ✅ Campaign summary displays accurate statistics
- ✅ Errors are handled gracefully
- ✅ Multiple accounts can be used (separately)
- ✅ Different templates can be selected
- ✅ Both autonomous and semi modes work

---

## Common Issues & Solutions

### Issue: ChromeDriver not found
**Solution**: Download ChromeDriver and add to PATH, or specify path in settings

### Issue: Login keeps expiring
**Solution**: Ensure profile directory persists, check Chrome isn't in incognito mode

### Issue: Gmail UI elements not found
**Solution**: Update selectors in email_sender.py - Gmail's UI changes occasionally

### Issue: LLM API calls failing
**Solution**: Verify API key, check base_url format, ensure provider is online

### Issue: Emails not sending
**Solution**: Check Gmail sending limits, verify account not blocked, check error logs

---

## Project Philosophy Reminder

This is a **side project** focused on:
- ✅ Working functionality
- ✅ Simple, maintainable code
- ✅ Easy to understand and modify
- ✅ Good enough for personal use

NOT focused on:
- ❌ Production-grade scale
- ❌ Complex architectures
- ❌ Over-engineering
- ❌ Perfect code coverage

Keep it simple. Make it work. Ship it. 🚀

---

## Success Criteria

The project is successful when:

1. You can select a Gmail account and it stays logged in
2. You can load a CSV of contacts
3. LLM generates personalized emails that sound natural
4. Emails send through Gmail successfully
5. You can preview emails before sending (semi mode)
6. Progress saves and you can resume if interrupted
7. Logs help you track what happened
8. The code is easy to understand and modify

That's it. Don't overcomplicate.

---

## Final Notes for Agentic Developer

- **Read the config files first** - they define the structure
- **Start with browser.py and login_checker.py** - foundation
- **Build incrementally** - get one piece working before moving on
- **Test frequently** - use a test account and small CSV
- **Ask clarifying questions** - if requirements seem ambiguous
- **Keep functions small** - easier to understand and debug
- **Use type hints** - helps catch errors early
- **Log generously** - but keep logs readable
- **Handle errors gracefully** - user experience matters

Remember: This is a side project for personal use. Prioritize working over perfect.

Good luck! 🎯