import logging
from datetime import datetime
from dotenv import load_dotenv
from imaplib import IMAP4_SSL
import email
import os
from bs4 import BeautifulSoup
import requests
import threading

class EmailParser:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__file__)
        self.username = None
        self.password = None
        self.mail_server = None

    def __enter__(self):
        self._setup_env()
        return self
    
    def _setup_env(self):
        self._setup_logging()
        load_dotenv()
        self.username = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.connect_to_email()
    
    def _setup_logging(self):
        self.logger.setLevel(logging.DEBUG)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logfile_{timestamp}.log"
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _cleanup(self):
        self.mail_server.logout()

    def  __exit__(self):
        self._cleanup()

    def extract_links_from_html(self, html_content: str):
        soup = BeautifulSoup(html_content, "html.parser")
        links = [link["href"] for link in soup.find_all("a", href=True) if "unsubscribe" in link["href"].lower()]
        return links

    def connect_to_email(self) -> IMAP4_SSL:
        if not self.mail_server:
            self.mail_server = IMAP4_SSL("imap.gmail.com")
            self.mail_server.login(self.username, self.password)
        else:
            self.logger.info("Already connected to server")
    
    def _read_msg(self, msg):
        # TODO process each message here
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    content = part.get_payload(decode=True).decode()
                    return self.extract_links_from_html(content)
        else:
            content = msg.get_payload(decode=True).decode()
            return self.extract_links_from_html(content)

    def _process_msg_parts(self, part):
        pass

    def save_links(self, links: list) -> None:
        with open("links.txt", 'w') as f:
            f.write("\n".join())

    def unsubscribe(self, link: str) -> str:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                self.logger.info(f"unsubscribed link {link}")
            else:
                print(f"unable to unsubscibe link with status {response.status_code}")
        except Exception as e:
            self.logger.error(f"got error with {e}")

    def get_unsubscribe_links(self, folder:  str = "inbox") -> list:
            unsubscribe_links = []
            self.mail_server.select(folder)
            _, searched_data = self.mail_server.search(None, '(BODY "UNSUBSCRIBE")')
            data = searched_data[0].split()
            for num in data:
                _, data = self.mail_server.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                unsubscribe_links.extend(self._read_msg(msg))
            return unsubscribe_links

def main():
    with EmailParser() as ep:
        links = ep.get_unsubscribe_links()
        for link in links:
            ep.unsubscribe(link)
            ep.save_links(links)

main()

