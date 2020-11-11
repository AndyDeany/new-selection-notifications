from time import sleep
from datetime import datetime
import sys
import traceback
import re
import imaplib
import email
import codecs

import yaml

from notify import notify


INTERVAL = 5.0

with open("credentials.yml") as credentials_yaml:
    credentials = yaml.safe_load(credentials_yaml)

EMAIL_ADDRESS = credentials["email"]
PASSWORD = credentials["password"]
IMAP_ADDRESS = "imap.gmail.com"
IMAP_PORT = 993


SYSTEM_TN2 = "JR-TN2"
SYSTEM_DTR = "JR-DTR"
SYSTEM_MR3 = "JR-MR3.2"
SYSTEM_LT6R = "JR - LT6R"
SYSTEM_PnJ = "jockey+pace"
SYSTEM_ACCAS = "JR - ACCAS"
SYSTEM_JLT2 = "JR-JLT2"
SYSTEM_6LTO = "JR &gt;=6 + jockey"
SYSTEMS = (SYSTEM_TN2, SYSTEM_DTR, SYSTEM_MR3, SYSTEM_LT6R, SYSTEM_PnJ, SYSTEM_ACCAS, SYSTEM_JLT2, SYSTEM_6LTO)

SUBJECT_REGEX = r"PROFORM (?P<type>NEW\-SELECTION|NON\-RUNNER|SWAP BET) \((?P<horse>[a-zA-Z ']+)\-(?P<time>[0-9]{2}\:[0-9]{2})\-(?P<course>[a-zA-Z \-]+)\)"
SYSTEM_REGEX = r"|".join((system.replace(r".", r"\.").replace(r"+", r"\+") for system in SYSTEMS))
BODY_REGEX = r"NREP System: +(?P<system>{})".format(SYSTEM_REGEX)
SWAP_BET_BODY_REGEX = r"NREP TO +NEW System\: (?P<new_system>{0}), FROM +=?OLD System\: (?P<old_system>{0})".format(SYSTEM_REGEX)

mail = imaplib.IMAP4_SSL(IMAP_ADDRESS)
mail.login(EMAIL_ADDRESS, PASSWORD)


def log(string):
    """Write the given string to log."""
    print(f"[{datetime.now().isoformat()}] {string}")


def handle_error(message):
    """Log the given error and notify the relevant people."""
    log(message)
    traceback.print_exc(file=sys.stdout)
    notify(f"<@203581825451425792> <@256567031481106433> {message}")
    print("")


def tidied(system):
    """Return the tidy version of the given system name."""
    try:
        return {
            SYSTEM_TN2: "TN2",
            SYSTEM_DTR: "DTR",
            SYSTEM_MR3: "MR3",
            SYSTEM_LT6R: "LT6R",
            SYSTEM_PnJ: "PnJ",
            SYSTEM_ACCAS: "ACCAS",
            SYSTEM_JLT2: "JLT2",
            SYSTEM_6LTO: "6LTO"
        }[system]
    except KeyError:
        raise ValueError(f"Unknown system: '{system}'.")


def retrieve_emails():
    mail.select("inbox")
    response_code, data = mail.search(None, "UNSEEN")

    if not response_code == "OK":
        raise Exception("Failed to retrieve emails.")

    return data


def notify_from_email(subject, body):
    """Send a Discord notification about the information in the given email."""
    log(f"[INFO] Subject: {subject}\nBody: {body}")
    subject_match = re.match(SUBJECT_REGEX, subject)
    notification_type = subject_match["type"]
    horse = subject_match["horse"]
    course = subject_match["course"]
    time = subject_match["time"]

    if notification_type == "SWAP BET":
        body_match = re.match(SWAP_BET_BODY_REGEX, body)
        old_system = tidied(body_match["old_system"])
        new_system = tidied(body_match["new_system"])
        notify(f":warning: <@&757791393035845742> Swap bet ({old_system} -> {new_system}): {horse} ({time} {course}) :warning:")
        return

    body_match = re.match(BODY_REGEX, body)
    system = tidied(body_match["system"])
    if system == "JLT2": return     # Remove this line when we want JLT2 picks.

    if notification_type == "NEW-SELECTION":
        if system == "6LTO":
            role = "761914927127593000"     # @BSP
        else:
            role = "757791393035845742"     # @Notifications
        notify(f"<@&{role}> New selection ({system}): **{horse}** ({time} {course})")
    elif notification_type == "NON-RUNNER":
        notify(f"Non-runner ({system}): {horse} ({time} {course})")
    else:
        notify(f"<@203581825451425792> Unknown email format! Send help.")


def get_email_and_notify(email_id):
    log(f"[INFO] Processing email with {email_id=}...")
    response_code, data = mail.fetch(email_id, "(RFC822)")
    if not response_code == "OK":
        raise Exception(f"Failed to retrieve email with id={email_id}.")

    message = email.message_from_bytes(data[0][1])
    subject = message["subject"]
    if message.is_multipart():
        body = message.get_payload()[0].get_payload()
    else:
        body = re.sub(r"<[^>]+>", "", message.get_payload())    # Removing html tags

    body = codecs.decode(bytes(body, "utf-8"), "quopri").decode("utf-8")    # Properly decode body
    body = body.replace("\r\n", "")     # Remove newlines

    notify_from_email(subject, body)
    log(f"[INFO] Processing of email with {email_id=} complete.\n")


def loop():
    try:
        data = retrieve_emails()
        email_ids = data[0].split()
    except Exception:
        handle_error("[ERROR] Failed to retrieve emails.")

    for email_id in email_ids:
        try:
            get_email_and_notify(email_id)
        except Exception:
            handle_error(f"[WARNING] Exception caught whilst processing email with {email_id=}.")


def main():
    while True:
        try:
            loop()
        except Exception:
            handle_error("[ERROR] Exception caught whilst running loop().")
        sleep(INTERVAL)


if __name__ == "__main__":
    main()
