from time import sleep
import sys
import traceback
import re
import imaplib
import email

import yaml

from notify import notify


INTERVAL = 5.0

with open("credentials.yml") as credentials_yaml:
    credentials = yaml.safe_load(credentials_yaml)

EMAIL_ADDRESS = credentials["email"]
PASSWORD = credentials["password"]
IMAP_ADDRESS = "imap.gmail.com"
IMAP_PORT = 993


SUBJECT_REGEX = r"PROFORM (?P<type>NEW\-SELECTION|NON\-RUNNER|SWAP BET) \((?P<horse>[a-zA-Z ]+)\-(?P<time>[0-9]{2}\:[0-9]{2})\-(?P<course>[a-zA-Z ]+)\)"
SYSTEM_REGEX = r"JR\-TN2|JR\-DTR|JR\-MR3\.2|JR - LT6R|JR &gt;=3D6 \+ jo=ckey"
BODY_REGEX = r"NREP System: +(?P<system>{})".format(SYSTEM_REGEX)
SWAP_BET_BODY_REGEX = r"NREP TO +NEW System\: (?P<new_system>{0}), FROM +OLD System\: (?P<old_system>{0})".format(SYSTEM_REGEX)

mail = imaplib.IMAP4_SSL(IMAP_ADDRESS)
mail.login(EMAIL_ADDRESS, PASSWORD)


def retrieve_emails():
    mail.select("inbox")
    response_code, data = mail.search(None, "UNSEEN")

    if not response_code == "OK":
        raise Exception("Failed to retrieve emails.")

    return data


def notify_from_email(subject, body):
    """Send a Discord notification about the information in the given email."""
    subject_match = re.match(SUBJECT_REGEX, subject)
    notification_type = subject_match["type"]
    horse = subject_match["horse"]
    course = subject_match["course"]
    time = subject_match["time"]

    if notification_type == "SWAP BET":
        body_match = re.match(SWAP_BET_BODY_REGEX, body)
        old_system = tidied(body_match["old_system"])
        new_system = tidied(body_match["new_system"])
        notify(f"Swap bet ({old_system} -> {new_system}): {horse} ({time} {course})")
        return

    body_match = re.match(BODY_REGEX, body)
    system = tidied(body_match["system"])

    if notification_type == "NEW-SELECTION":
        notify(f"<@&757791393035845742> New selection ({system}): **{horse}** ({time} {course})")
    elif notification_type == "NON-RUNNER":
        notify(f"Non-runner ({system}): {horse} ({time} {course})")
    else:
        notify(f"<@203581825451425792> Unknown email format! Send help.")


def get_email_and_notify(email_id):
    print(f"[INFO] Processing email with {email_id=}...")
    response_code, data = mail.fetch(email_id, "(RFC822)")
    if not response_code == "OK":
        raise Exception(f"Failed to retrieve email with id={email_id}.")

    message = email.message_from_bytes(data[0][1])
    subject = message["subject"]
    if message.is_multipart():
        body = message.get_payload()[0].get_payload()
    else:
        body = re.sub(r"<[^>]+>", "", message.get_payload())    # Removing html tags

    body = body.replace("\r\n", "")

    notify_from_email(subject, body)
    print(f"[INFO] Processing of email with {email_id=} complete.\n")


def tidied(system):
    """Return the tidy version of the given system name."""
    if system == "JR-TN2":
        return "TN2"
    elif system == "JR-DTR":
        return "DTR"
    elif system == "JR-MR3" or system == "JR-MR3.2":
        return "MR3"
    elif system == "JR - LT6R":
        return "LT6R"
    elif system == "JR &gt;=3D6 + jo=ckey":
        return "6LTO"
    else:
        raise ValueError(f"Unknown system: '{system}'.")


def loop():
    data = retrieve_emails()
    email_ids = data[0].split()

    for email_id in email_ids:
        try:
            get_email_and_notify(email_id)
        except Exception:
            print(f"[WARNING] Exception caught whilst processing email with {email_id=}.")
            traceback.print_exc(file=sys.stdout)
            print("")


def main():
    while True:
        try:
            loop()
        except Exception:
            print("[ERROR] Exception caught whilst running loop().")
            traceback.print_exc(file=sys.stdout)
            print("")
        sleep(INTERVAL)


if __name__ == "__main__":
    main()
