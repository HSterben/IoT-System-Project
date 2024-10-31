import smtplib
import ssl
import imaplib
import email
from email.message import EmailMessage

class Email:
    EMAIL = "liamgroupiot@gmail.com"
    PASSWORD = "unip eiah qvyn bjbp"
    SERVER = 'smtp.gmail.com'

    def send_email(self, temp, email_receiver):
        # Variable with email sender
        email_sender = self.EMAIL
        email_password = self.PASSWORD
        temp_str = str(temp)

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = "Temperature Is Getting High"
        em.set_content(
            f"Hello, the current temperature is {temp_str}. Please reply 'YES' to this email if you wish to turn the fan on."
        )

        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.SERVER, 465, context=context) as smtp:  # Use port 465 for SMTP_SSL
            # Login into the sender email
            smtp.login(email_sender, email_password)
            # Send the email
            smtp.sendmail(email_sender, email_receiver, em.as_string())

    def receive_email(self, sender_email):
        # Connect to the server and go to its inbox
        mail = imaplib.IMAP4_SSL(self.SERVER)
        mail.login(self.EMAIL, self.PASSWORD)
        # Choose the inbox
        mail.select('inbox')

        # Search for unseen emails from the specified sender with the specified subject
        status, data = mail.search(None, 'UNSEEN', f'HEADER SUBJECT "Temperature Is Getting High"', f'HEADER FROM "{sender_email}"')

        mail_ids = []
        for block in data:
            # Transform the bytes into a list using white spaces as separator
            mail_ids += block.split()

        # Fetch each email by ID
        for i in mail_ids:
            # Fetch the email given its ID and desired format
            status, data = mail.fetch(i, '(RFC822)')

            for response_part in data:
                if isinstance(response_part, tuple):
                    # Extract the email message
                    message = email.message_from_bytes(response_part[1])
                    mail_from = message['from']
                    mail_subject = message['subject']

                    # Extract the email content
                    if message.is_multipart():
                        mail_content = ''
                        for part in message.get_payload():
                            if part.get_content_type() == 'text/plain':
                                mail_content += part.get_payload(decode=True).decode()
                    else:
                        mail_content = message.get_payload(decode=True).decode()

                    return "yes" in mail_content.lower()

def main():
    email_client = Email()
    email_client.send_email(25)  # Send an email with the temperature of 25 degrees

    for count in range(4):
        if not email_client.receive_email("websterliam25@gmail.com"):  # Check for a response
            time.sleep(10)
            print(count)
        else:
            print("Fan has been turned on!")
            break


if __name__ == "__main__":
    main()  # Run the main function