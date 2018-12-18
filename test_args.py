import argparse
from email.message import EmailMessage

parser = argparse.ArgumentParser()

parser.add_argument('addresses', help='The addresses to send the file to',
                    nargs=argparse.REMAINDER)

args = parser.parse_args()

print(type(args.addresses))
print(args.addresses)

msg = EmailMessage()

msg['To'] = args.addresses

print(msg['To'])


