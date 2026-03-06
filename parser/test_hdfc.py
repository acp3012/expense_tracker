# test_hdfc.py
from parser import parse_email

body1 = """Dear Customer, Rs.560.00 has been debited from account 8891 to VPA 
paytm.s1e43i7@pty mariya protein centre on 01-03-26. Your UPI transaction 
reference number is 927283492221."""
body = """
Dear Customer, Rs.98.00 has been debited from account 8891 to VPA 9600321792@okbizicici KONDAL V on 01-03-26. Your UPI transaction reference number is 324342052884. If you did not authorize this transaction, please report it immediately by calling 18002586161 Or SMS BLOCK UPI to 7308080808. Warm Regards, HDFC Bank
"""
result = parse_email(body, sender="alerts@hdfcbank.bank.in", subject="UPI Transaction Alert", email_id="acp3012@gmail.com")
print(result)
