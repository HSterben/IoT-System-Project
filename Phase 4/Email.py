import smtplib
from email.message import EmailMessage

class EmailManager:
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"  # App password
        self.SERVER = 'smtp.gmail.com'
        
    def send_temp_email(self, temp, email_receiver):
        temp_str = str(temp)
        em = EmailMessage()
        em['From'] = self.EMAIL
        em['To'] = email_receiver
        em['Subject'] = "Temperature Is Getting High"
        em.set_content(
            f"Hello, the current temperature is {temp_str}°C. Please reply 'YES' to this email if you wish to turn the fan on."
        )

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.SERVER, 465, context=context) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.sendmail(self.EMAIL, email_receiver, em.as_string())

    def receive_temp_email(self, sender_email):
        mail = imaplib.IMAP4_SSL(self.SERVER)
        mail.login(self.EMAIL, self.PASSWORD)
        mail.select('inbox')

        status, data = mail.search(None, 'UNSEEN', f'HEADER SUBJECT "Temperature Is Getting High"', f'HEADER FROM "{sender_email}"')
        
        mail_ids = []
        for block in data:
            mail_ids += block.split()

        for i in mail_ids:
            status, data = mail.fetch(i, '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1])
                    mail_content = ''
                    if message.is_multipart():
                        for part in message.get_payload():
                            if part.get_content_type() == 'text/plain':
                                mail_content += part.get_payload(decode=True).decode()
                    else:
                        mail_content = message.get_payload(decode=True).decode()

                    return "yes" in mail_content.lower()
        return False

    def send_light_email(self, intensity):
        c = datetime.now()
        current_time = c.strftime('%H:%M')
        email_content = f"Light intensity is low. LED was turned on at {current_time}."
        msg = EmailMessage()
        msg["From"] = self.EMAIL
        msg["To"] = "wliam2525@gmail.com"
        msg["Subject"] = "Light Intensity Alert"
        msg.set_content(email_content)

        with smtplib.SMTP_SSL(self.SERVER, 465) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.send_message(msg)


    def send_user_email(self, user):
        c = datetime.now()
        current_time = c.strftime('%H:%M')
        email_content = f"User {user} logged in to the dashboard at {current_time}."
        msg = EmailMessage()
        msg["From"] = self.EMAIL
        msg["To"] = "wliam2525@gmail.com"
        msg["Subject"] = "User Log On"
        msg.set_content(email_content)

        with smtplib.SMTP_SSL(self.SERVER, 465) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.send_message(msg)
            
# email_thread = threading.Thread(target=email_manager.send_email, args=(light_intensity,))
# email_thread.start()