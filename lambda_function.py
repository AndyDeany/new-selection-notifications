import sys
import traceback

from main import loop, log


def lambda_handler(event, context):
    """Handle the execution of the lambda function."""
    log(f"[INFO] Received event {event} with context {context}.")

    status_code = 200

    try:
        loop()
    except Exception:
        status_code = 500
        log("[ERROR] Exception caught whilst running loop().")
        traceback.print_exc(file=sys.stdout)
        print("")

    return {"statusCode": status_code}
