"""Build the bundled NLP corpus and train the local classifier."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CORPUS = DATA / "nlp_corpus.json"


def corpus() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    clean = [
        "Seating plan attached as a link. Ignore if already received.",
        "Weekly newsletter: campus library hours this week.",
        "Your package was delivered to the front desk.",
        "Minutes of yesterday's faculty meeting are in the shared folder.",
        "Please find the course outline for next semester attached.",
        "Thank you for attending the seminar. Slides are on the portal.",
        "The lab will be closed on Friday for maintenance.",
        "Reminder: submit the assignment on the LMS by Friday evening.",
        "Office hours moved to Tuesday 3pm in room 204.",
        "Happy birthday. The team lunch is at the cafeteria at 1pm.",
        "Weather update: light rain expected tomorrow morning.",
        "Your print job is ready for pickup at the help desk.",
        "Concert tickets are at will-call. Enjoy the show.",
        "The invoice for last month's licensed software was paid.",
        "Welcome to the mailing list. You can unsubscribe at any time.",
        "Sports club practice is cancelled due to the ground being wet.",
        "Here is the agenda for the curriculum committee.",
        "Please review the attached policy draft and send comments.",
        "Your appointment with the counsellor is confirmed for Monday.",
        "The hostel mess menu for this week is now posted.",
        "Project status: all unit tests passed on the staging branch.",
        "FYI the projector in LT-3 has been repaired.",
        "Shared notes from the industrial visit are in this folder.",
        "Please confirm attendance for the alumni meet.",
        "The bus schedule is unchanged this week.",
        "Good morning. The registrar office opens at 9:30.",
        "Please use the official portal to download your grade sheet.",
        "This is a receipt for the workshop registration fee already paid.",
        "Class rescheduled to 11am in the same lecture hall.",
        "Attached: harmless meeting notes from 30 August.",
    ]
    for i, text in enumerate(clean):
        rows.append({"label": "clean", "text": text})
        rows.append({"label": "clean", "text": text.lower()})
        if i % 2 == 0:
            rows.append({"label": "clean", "text": f"Subject: Update. {text}"})

    cred = [
        "Verify your password immediately to keep your mailbox.",
        "Confirm your password or the account will be suspended.",
        "Login to continue and unlock your webmail quota.",
        "Your mailbox is full. Sign in now to verify credentials.",
        "Unusual sign-in. Reset your password at this link today.",
        "Click here to confirm your password for the student portal.",
        "We locked your account. Enter username and password to resume.",
        "Update billing: login to continue or access will stop.",
        "Security alert. Re-enter your password on this page.",
        "Your session expired. Login to continue using campus mail.",
        "Password expiry in 1 hour. Confirm your password now.",
        "Validate your credentials to prevent mailbox deletion.",
        "Account review required. Submit password to the form.",
        "Phishing style: enter your password to view the document.",
        "Re-authenticate. Type the account password to proceed.",
        "Webmail quota exceeded. Login and confirm password.",
        "Stolen access theme: verify password to restore inbox.",
        "Credential harvest: confirm password for Office 365 webmail.",
        "Sign in to the lookalike portal and save your password.",
        "IT helpdesk: we need you to confirm your password today.",
    ]
    for text in cred:
        rows.append({"label": "credential_harvest", "text": text})
        rows.append({"label": "credential_harvest", "text": text.replace("password", "passwd")})

    pay = [
        "Please wire the amount to the new bank account today.",
        "Urgent payment: change of account for the vendor invoice.",
        "Accounts payable: send the funds to this new bank account.",
        "The director asked you to wire the amount before noon.",
        "Invoice attached. Use the new bank account for payment.",
        "Do not use the old account. Urgent payment on the new IBAN.",
        "Change of account details. Process the supplier payment now.",
        "BEC style request: wire the amount to the treasury account.",
        "Payroll redirect: new bank account for this week's salaries.",
        "Vendor changed banks. Urgent payment required this afternoon.",
        "Finance impersonation: wire the remaining invoice immediately.",
        "Pay the attached invoice using the updated bank details.",
        "Hold all other work. Wire the amount to the account below.",
        "New bank account for the contractor. Process payment today.",
        "The CFO is travelling. Wire the amount and reply done.",
    ]
    for text in pay:
        rows.append({"label": "payment_fraud", "text": text})
        rows.append({"label": "payment_fraud", "text": text + " Treat as confidential."})

    urg = [
        "Your mailbox will be suspended. Act now.",
        "Urgent: respond immediately or access is revoked.",
        "Act now. This is your final warning from IT.",
        "Immediately confirm or the account is suspended.",
        "Urgent action required on your student account.",
        "Final notice. Mailbox suspended at midnight unless you act now.",
        "Immediately update the profile or you lose access.",
        "Act now to keep the exam portal from being suspended.",
        "Urgent: dean's office needs a reply immediately.",
        "Suspended access in 30 minutes unless you continue.",
    ]
    for text in urg:
        rows.append({"label": "impersonation_urgency", "text": text})
        rows.append({"label": "impersonation_urgency", "text": "URGENT. " + text})

    return rows


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows = corpus()
    CORPUS.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    from mailtrace.nlp_model import train

    stats = train()
    print(f"wrote {CORPUS} n={len(rows)} trained={stats}")


if __name__ == "__main__":
    main()
