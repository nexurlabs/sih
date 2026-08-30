#!/usr/bin/env python3
"""Write the 8 demo .eml files. Crafted samples only — do not send."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "samples"


def w(name: str, content: str) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / name).write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    w(
        "01_clean.eml",
        """\
Return-Path: <tutor@pec.edu.in>
Received: from mail.pec.edu.in (mail.pec.edu.in [103.25.60.12])
	by mx.example.net with ESMTPS id a1; Sun, 30 Aug 2026 10:01:00 +0530
Authentication-Results: mx.example.net; spf=pass smtp.mailfrom=pec.edu.in; dkim=pass header.d=pec.edu.in; dmarc=pass header.from=pec.edu.in
Received-SPF: pass (pec.edu.in: 103.25.60.12 designated)
From: "KOM Tutor" <tutor@pec.edu.in>
To: student@pec.edu.in
Subject: Tutorial 11 — instantaneous centres
Message-ID: <clean-001@pec.edu.in>
Date: Sun, 30 Aug 2026 10:00:00 +0530
Content-Type: text/plain; charset=utf-8

Bring assignment 1 and 2. Class test Monday. No attachments required.
""",
    )
    w(
        "02_display_spoof.eml",
        """\
Return-Path: <bounce@mail-secure.net>
Received: from ec2-18-184.eu-central-1.compute.amazonaws.com (ec2-18-184.eu-central-1.compute.amazonaws.com [18.184.10.20])
	by mx.google.com with ESMTPS id b2; Sun, 30 Aug 2026 12:10:00 +0530
Authentication-Results: mx.google.com; spf=fail smtp.mailfrom=mail-secure.net; dkim=none; dmarc=fail header.from=gmail.com
Received-SPF: fail (gmail.com: 18.184.10.20 not designated)
From: "PEC Principal" <random.account@gmail.com>
Reply-To: verify-now@mail-secure.net
To: student@pec.edu.in
Subject: Urgent circular — fee waiver
Message-ID: <spoof-002@mail-secure.net>
Date: Sun, 30 Aug 2026 12:09:00 +0530
Content-Type: text/plain; charset=utf-8

Office of the Principal. Submit documents immediately.
""",
    )
    w(
        "03_lookalike.eml",
        """\
Return-Path: <pay@paypa1.com>
Received: from unknown (unknown [52.94.76.10])
	by mx.example.net with ESMTP id c3; Sun, 30 Aug 2026 13:00:00 +0000
Authentication-Results: mx.example.net; spf=fail smtp.mailfrom=paypa1.com; dkim=fail; dmarc=fail
From: "Accounts" <service@paypa1.com>
To: student@pec.edu.in
Subject: Invoice unpaid
Message-ID: <look-003@paypa1.com>
Content-Type: text/plain; charset=utf-8

Pay at https://paypa1.com/invoice/77 to avoid suspension.
""",
    )
    w(
        "04_spf_fail.eml",
        """\
Return-Path: <notice@pec.edu.in>
Received: from rogue.example (rogue.example [18.184.10.20])
	by mx.example.net with ESMTP id d4; Sun, 30 Aug 2026 14:00:00 +0000
Authentication-Results: mx.example.net; spf=fail smtp.mailfrom=pec.edu.in; dkim=fail header.d=pec.edu.in; dmarc=fail
Received-SPF: fail (pec.edu.in: 18.184.10.20 not designated)
From: "Exam Cell" <notice@pec.edu.in>
To: student@pec.edu.in
Subject: Seating plan
Message-ID: <spf-004@rogue.example>
Content-Type: text/plain; charset=utf-8

Seating plan attached as a link. Ignore if already received.
""",
    )
    w(
        "05_bec_invoice.eml",
        """\
Return-Path: <finance@mail-secure.net>
Received: from ec2-18-184.eu-central-1.compute.amazonaws.com ([18.184.10.20])
	by mx.example.net with ESMTP id e5
Authentication-Results: mx.example.net; spf=fail; dkim=none; dmarc=fail
From: "Director (Admin)" <director@pec.edu.in>
Reply-To: payments@mail-secure.net
To: accounts@pec.edu.in
Subject: Change of account — pay vendor today
Message-ID: <bec-005@mail-secure.net>
Content-Type: text/plain; charset=utf-8

I am in a meeting. Wire the amount to the new bank account in the note.
Urgent payment. Do not call.
""",
    )
    w(
        "06_cred_phish.eml",
        """\
Return-Path: <bot@mail-secure.net>
Received: from ec2-18-184.eu-central-1.compute.amazonaws.com ([18.184.10.20])
	by mx.example.net with ESMTP id f6
Authentication-Results: mx.example.net; spf=fail; dkim=fail; dmarc=fail
From: "IT Helpdesk" <it@pec-edu.in>
To: student@pec.edu.in
Subject: Mailbox will be suspended
Message-ID: <phish-006@pec-edu.in>
Content-Type: text/plain; charset=utf-8

Your mailbox is suspended. Verify your password immediately:
http://192.168.1.100/login
""",
    )
    w(
        "07_cloud_hops.eml",
        """\
Return-Path: <camp@mail-secure.net>
Received: from mx.google.com (mx.google.com [8.8.8.8])
	by mailbox.pec.edu.in with ESMTPS id g7a
Received: from mail-relay.example.net (mail-relay.example.net [185.199.108.153])
	by mx.google.com with ESMTPS id g7b
Received: from ec2-18-184.eu-central-1.compute.amazonaws.com (ec2-18-184.eu-central-1.compute.amazonaws.com [18.184.10.20])
	by mail-relay.example.net with ESMTP id g7c
Authentication-Results: mx.google.com; spf=fail smtp.mailfrom=mail-secure.net; dkim=none; dmarc=fail
From: "Campaign Desk" <desk@mail-secure.net>
Reply-To: camp@mail-secure.net
To: student@pec.edu.in
Subject: Shared campaign A
Message-ID: <cloud-007@mail-secure.net>
Content-Type: text/plain; charset=utf-8

First notice. Ignore if this is a drill sample.
""",
    )
    w(
        "08_campaign_twin.eml",
        """\
Return-Path: <camp@mail-secure.net>
Received: from mx.google.com (mx.google.com [8.8.8.8])
	by mailbox.pec.edu.in with ESMTPS id h8a
Received: from ec2-18-184.eu-central-1.compute.amazonaws.com (ec2-18-184.eu-central-1.compute.amazonaws.com [18.184.10.20])
	by mx.google.com with ESMTPS id h8b
Authentication-Results: mx.google.com; spf=fail smtp.mailfrom=mail-secure.net; dkim=none; dmarc=fail
From: "Campaign Desk" <followup@mail-secure.net>
Reply-To: camp@mail-secure.net
To: student@pec.edu.in
Subject: Shared campaign B
Message-ID: <cloud-008@mail-secure.net>
Content-Type: text/plain; charset=utf-8

Second notice from the same reply-to and hop. This is the graph twin.
""",
    )
    print("wrote", sorted(p.name for p in ROOT.glob("*.eml")))


if __name__ == "__main__":
    main()
