name: VibeMailing
description: >
  A multi-account Gmail automation system that uses LLMs to generate
  personalized emails for outreach campaigns. Supports multiple templates,
  CLI operation, progress checkpointing, and safe rate-limited sending.

agents:
  - name: AccountManager
    role: >
      Handles Gmail account selection, Chrome profile loading, and
      ensures the user is logged in. If cookies/session expired,
      prompts user to login manually.
    capabilities:
      - list_available_accounts
      - select_account
      - launch_chrome_profile
      - check_login_status
      - prompt_manual_login
      - track_active_account

  - name: CSVManager
    role: >
      Loads the target CSV file, reads rows, and maintains checkpoints
      so campaigns can resume if interrupted.
    capabilities:
      - select_csv_file
      - load_csv_rows
      - mark_checkpoint
      - resume_from_checkpoint

  - name: TemplateManager
    role: >
      Loads email templates and injects row-specific personalization
      data into placeholders. Supports multiple templates per campaign.
    capabilities:
      - load_templates_yaml
      - select_template
      - inject_csv_data
      - generate_final_prompt

  - name: LLMManager
    role: >
      Generates personalized email content using configured LLM provider.
      Can support multiple LLM providers using a universal base_url and API key.
    capabilities:
      - load_system_prompt
      - load_user_template
      - generate_email_content
      - support_multiple_llm_providers

  - name: EmailComposer
    role: >
      Receives the generated email content, composes it in Gmail via Chrome,
      supports two modes: fully autonomous and semi-automated preview mode.
    capabilities:
      - open_gmail_compose
      - fill_recipient_email
      - fill_subject
      - fill_body_content
      - preview_email (semi-auto)
      - send_email
      - log_sent_email

  - name: CooldownManager
    role: >
      Ensures a safe random wait between email sends to avoid Gmail restrictions.
    capabilities:
      - calculate_random_wait
      - enforce_wait
      - optional_jitter

  - name: TrackerManager
    role: >
      Tracks campaign progress, stores logs in app.log and campaign-specific logs,
      and maintains row-level state for checkpointing.
    capabilities:
      - log_email_status
      - log_errors
      - maintain_campaign_checkpoint
      - generate_summary_report

workflow:
  description: >
    The main orchestration workflow for VibeMailing. Handles the end-to-end process
    from selecting account, loading CSV, generating emails, previewing/sending, 
    cooldown, and logging.

  steps:
    - step: Select Gmail Account
      agent: AccountManager
      action: select_account

    - step: Launch Chrome with profile
      agent: AccountManager
      action: launch_chrome_profile

    - step: Check login & prompt if expired
      agent: AccountManager
      action: check_login_status

    - step: Select CSV File
      agent: CSVManager
      action: select_csv_file

    - step: Load CSV rows & checkpoint
      agent: CSVManager
      action: load_csv_rows

    - step: For each contact row:
      loop: csv_rows
      steps:
        - step: Select Template
          agent: TemplateManager
          action: select_template

        - step: Inject personalization data
          agent: TemplateManager
          action: inject_csv_data

        - step: Generate email content
          agent: LLMManager
          action: generate_email_content

        - step: Preview email if semi-auto
          agent: EmailComposer
          action: preview_email
          condition: workflow_mode == "semi-auto"

        - step: Send email
          agent: EmailComposer
          action: send_email

        - step: Log progress & update checkpoint
          agent: TrackerManager
          action: log_email_status

        - step: Apply cooldown
          agent: CooldownManager
          action: enforce_wait

    - step: Campaign Summary
      agent: TrackerManager
      action: generate_summary_report
