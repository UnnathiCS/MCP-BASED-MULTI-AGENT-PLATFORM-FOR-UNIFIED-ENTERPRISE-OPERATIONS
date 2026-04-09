from email_fetcher import fetch_unread_emails
from ticket_manager import (
    init_ticket_db, create_ticket, update_ticket_with_processing,
    find_conv_id_by_message_id, get_conversation_history
)
from responder import send_auto_reply, extract_customer_name
from gemini_agent import process_email_with_agent
from retry_logic import retry_function
from audit_logger import log_action
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    start_time = time.time()
    print("[+] Initializing ticket DB...")
    init_ticket_db()

    print("[+] Fetching unread emails...")
    try:
        # Retry email fetching with exponential backoff
        emails = retry_function(
            fetch_unread_emails,
            max_retries=3,
            initial_delay=1.0
        )
        print(f"[+] {len(emails)} unread email(s) found.")
        
        log_action(
            action="emails_fetched",
            request_data={"count": len(emails)},
            duration_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        log_action(
            action="emails_fetch_failed",
            error_message=str(e),
            duration_ms=(time.time() - start_time) * 1000
        )
        return
    
    if not emails:
        print("[-] No new emails. Exiting.")
        return

    for email_data in emails:
        email_start_time = time.time()
        try:
            in_reply_to = email_data.get("in_reply_to")
            conversation_id = None

            # Check if this email is a reply to an existing thread
            if in_reply_to:
                conversation_id = find_conv_id_by_message_id(in_reply_to)

            # Create a new ticket, passing the existing conversation_id if found
            ticket_id, conv_id = create_ticket(email_data, conversation_id)
            print(f"\n[+] Created ticket: {ticket_id} (Conv ID: {conv_id})")
            
            log_action(
                action="ticket_created",
                request_data={"ticket_id": ticket_id, "conversation_id": conv_id},
                duration_ms=(time.time() - email_start_time) * 1000
            )

            # Get the full conversation history to provide context to the agent
            full_history = get_conversation_history(conv_id)
            
            # Extract customer name for personalization
            customer_name = extract_customer_name(
                email_data.get("from", ""),
                email_data.get("body", "")
            )
            
            print(f"[*] Processing with Agent for ticket {ticket_id}...")
            agent_start_time = time.time()
            
            # Retry agent processing with subject for better intent classification
            agent_response_text = retry_function(
                process_email_with_agent,
                max_retries=2,
                initial_delay=2.0,
                email_content=full_history,
                subject=email_data.get("subject", "")
            )
            
            agent_duration = (time.time() - agent_start_time) * 1000
            
            # Check if the agent classified the email as SPAM
            if agent_response_text == "SPAM":
                print("[!] Agent classified email as SPAM. No reply will be sent.")
                update_ticket_with_processing(
                    ticket_id,
                    "N/A",
                    "SPAM",
                    "Email classified as unrelated spam."
                )
                log_action(
                    action="email_classified_spam",
                    request_data={"ticket_id": ticket_id},
                    duration_ms=agent_duration
                )
                continue

            print("\n====== AGENT RESPONSE ======")
            print(agent_response_text)
            print("============================\n")

            update_ticket_with_processing(
                ticket_id,
                "Mail Agent",
                "Processed by Agent",
                agent_response_text
            )
            print(f"[✔] Updated ticket: {ticket_id} with agent response.")

            # Send reply with customer name for personalization
            send_start_time = time.time()
            send_auto_reply(
                email_data["from"], 
                email_data["subject"], 
                agent_response_text,
                original_message_id=email_data.get("message_id"),
                in_reply_to=email_data.get("in_reply_to"),
                customer_name=customer_name
            )
            send_duration = (time.time() - send_start_time) * 1000
            print(f"[↩] Sent auto-reply to: {email_data['from']}")
            
            log_action(
                action="email_reply_sent",
                request_data={"ticket_id": ticket_id, "to": email_data["from"]},
                duration_ms=send_duration
            )
            
        except Exception as e:
            logger.error(f"Error processing email: {e}", exc_info=True)
            log_action(
                action="email_processing_error",
                error_message=str(e),
                duration_ms=(time.time() - email_start_time) * 1000
            )
            continue

if __name__ == "__main__":
    main()