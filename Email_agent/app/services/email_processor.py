import time
import logging

from app.services.email_service import fetch_unread_emails, send_auto_reply, extract_customer_name
from app.services.ticket_service import (
    create_ticket, update_ticket_with_processing,
    find_conv_id_by_message_id, get_conversation_history
)
from app.services.agent_service import process_email_with_agent
from app.services.audit_service import log_action
from app.utils.helpers import retry_function
from app.database.connection import init_ticket_db

logger = logging.getLogger(__name__)


def process_all_emails():
    start_time = time.time()
    init_ticket_db()

    try:
        emails = retry_function(fetch_unread_emails, max_retries=3, initial_delay=1.0)
        log_action(action="emails_fetched", request_data={"count": len(emails)},
                   duration_ms=(time.time() - start_time) * 1000)
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        log_action(action="emails_fetch_failed", error_message=str(e),
                   duration_ms=(time.time() - start_time) * 1000)
        return

    if not emails:
        print("[-] No new emails.")
        return

    for email_data in emails:
        email_start = time.time()
        try:
            in_reply_to = email_data.get("in_reply_to")
            conversation_id = find_conv_id_by_message_id(in_reply_to) if in_reply_to else None

            ticket_id, conv_id = create_ticket(email_data, conversation_id)
            log_action(action="ticket_created",
                       request_data={"ticket_id": ticket_id, "conversation_id": conv_id},
                       duration_ms=(time.time() - email_start) * 1000)

            full_history = get_conversation_history(conv_id)
            customer_name = extract_customer_name(email_data.get("from", ""), email_data.get("body", ""))

            agent_start = time.time()
            agent_response = retry_function(
                process_email_with_agent, max_retries=2, initial_delay=2.0,
                email_content=full_history, subject=email_data.get("subject", "")
            )

            if agent_response == "SPAM":
                update_ticket_with_processing(ticket_id, "N/A", "SPAM", "Email classified as unrelated spam.")
                log_action(action="email_classified_spam", request_data={"ticket_id": ticket_id},
                           duration_ms=(time.time() - agent_start) * 1000)
                continue

            update_ticket_with_processing(ticket_id, "Mail Agent", "Processed by Agent", agent_response)

            send_auto_reply(
                email_data["from"], email_data["subject"], agent_response,
                original_message_id=email_data.get("message_id"),
                in_reply_to=email_data.get("in_reply_to"),
                customer_name=customer_name
            )
            log_action(action="email_reply_sent",
                       request_data={"ticket_id": ticket_id, "to": email_data["from"]},
                       duration_ms=(time.time() - email_start) * 1000)

        except Exception as e:
            logger.error(f"Error processing email: {e}", exc_info=True)
            log_action(action="email_processing_error", error_message=str(e),
                       duration_ms=(time.time() - email_start) * 1000)
