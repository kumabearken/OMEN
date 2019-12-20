import functions
import time

"""set true if want to hardcode admin email"""
AUTO = True
HARDSET = "insert email"

status = {}

"""Hardcoded admin email"""
if AUTO:
    admin = HARDSET
else:
    admin = functions.set_admin()

while True:
    status = functions.get_status()
    if functions.test(status=status):
        pass
    else:
        print("DETECTED PROBLEM")
        time.sleep(5)
        dns, key_name = functions.create_instance()
        functions.transfer(dns=dns, key_name=key_name)
        time.sleep(5)
        functions.notify(email=admin, dns=dns, key_name=key_name)
        time.sleep(5)
        functions.shutdown()
    time.sleep(5)
