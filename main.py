from time import sleep
import re
import imaplib
import email

from notify import notify


EMAIL_ADDRESS = "newselectionnotifications@gmail.com"
PASSWORD = "OverwhelmingDustStorm14&"
IMAP_ADDRESS = "imap.gmail.com"
IMAP_PORT = 993

SUBJECT_REGEX = r"PROFORM (?P<type>NEW\-SELECTION|NON\-RUNNER|SWAP BET) \((?P<horse>[a-zA-Z ]+)\-(?P<time>[0-9]{2}\:[0-9]{2})\-(?P<course>[a-zA-Z ]+)\)"
BODY_REGEX = r"NREP System: +(?P<system>JR\-TN2|JR\-DTR|JR\-MR3\.2|JR - LT6R)"

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

    body_match = re.match(BODY_REGEX, body)

    notification_type = subject_match["type"]
    system = body_match["system"]
    horse = subject_match["horse"]
    course = subject_match["course"]
    time = subject_match["time"]

    if system == "JR-TN2":
        system = "TN2"
    elif system == "JR-DTR":
        system = "DTR"
    elif system == "JR-MR3":
        system = "MR3"
    elif system == "JR - LT6R":
        system = "LT6R"

    if notification_type == "NEW-SELECTION":
        notify(f"<@203581825451425792> New selection ({system}): {horse} ({time} {course})")
    elif notification_type == "NON-RUNNER":
        notify(f"Non-runner: ({system}): {horse} ({time} {course})")
    else:
        notify(f"<@203581825451425792> Unknown email format! Send help.")


def loop():
    data = retrieve_emails()
    email_ids = data[0].split()

    for email_id in email_ids:
        response_code, data = mail.fetch(email_id, "(RFC822)")
        if not response_code == "OK":
            raise Exception(f"Failed to retrieve email with id={email_id}.")

        message = email.message_from_bytes(data[0][1])
        subject = message["subject"]
        body = message.get_payload()[0].get_payload().replace("\r\n", "")

        notify_from_email(subject, body)


def main():
    while True:
        loop()
        sleep(5)


if __name__ == "__main__":
    main()
