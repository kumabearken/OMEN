import psutil
import boto3
import time
import random
import os
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

"""Put true if testing to fail the hardware check
false if using for real"""
TEST = True


def create_instance():
    print("CREATING INSTANCE...")
    ec2 = boto3.resource('ec2')
    ec2_info = boto3.client('ec2')
    response = ec2_info.describe_instances()
    ami = response['Reservations'][0]['Instances'][0]['ImageId']

    """Find security group name"""
    security_groups = []
    counter = 0
    while response['Reservations'][counter]['Instances'][0]['State']['Name'] == 'terminated':
        counter = counter + 1
    security_groups.append(
        response['Reservations'][counter]['Instances'][0]['NetworkInterfaces'][0]['Groups'][0]['GroupName'])

    """Create random key of 10 letters"""
    key = random_string(10)
    outfile = open(key + ".pem", 'w')
    key_name = key

    """Pair keys"""
    key_pair = ec2.create_key_pair(KeyName=key_name)
    key_pair_out = str(key_pair.key_material)
    outfile.write(key_pair_out)

    """Create instance with parameters"""
    inst = ec2.create_instances(
        ImageId=ami,
        MinCount=1,
        MaxCount=1,
        KeyName=key_name,
        InstanceType='t2.micro',
        SecurityGroups=security_groups)
    print("CREATED INSTANCE")
    instance = inst[0]
    print("STARTING UP INSTANCE")

    """wait til instance fully setup or else transfer will fail"""
    instance.wait_until_running()
    waiter = ec2_info.get_waiter('instance_status_ok')
    waiter.wait()
    print("FINISHED LOADING")
    instance.load()
    return instance.public_dns_name, key_name + ".pem"


def debug():
    print("DETECTED PROBLEM")
    time.sleep(5)
    ec2 = boto3.resource('ec2')
    ec2_info = boto3.client('ec2')
    response = ec2_info.describe_instances()

    dns, key_name = create_instance()
    transfer(key_name=key_name, dns=dns)
    notify('insert email', dns=dns, key_name=key_name)
    # ec2_info.start_instances(InstanceIds=[brain])
    # ec2_info.stop_instances(InstanceIds=[brain])
    print("Stopping")
    time.sleep(10)
    exit(0)


def get_status():
    """Get Temps"""
    return psutil.sensors_temperatures()


def notify(email, dns, key_name):
    print("SENDING EMAIL")
    fromaddr = "insert gmail for server"
    toaddr = email

    # instance of MIMEMultipart
    msg = MIMEMultipart()

    # storing the senders email address
    msg['From'] = fromaddr

    # storing the receivers email address
    msg['To'] = toaddr

    # storing the subject
    msg['Subject'] = "SERVER FAILURE"

    # string to store the body of the mail
    body = "SERVER FAILURE\n" + \
           "DNS IS " + dns + '\n' + \
        "KEY PEM IS ATTACHED AT BOTTOM"

    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    # open the file to be sent
    filename = key_name
    attachment = open(filename, "rb")

    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')

    # To change the payload into encoded form
    p.set_payload((attachment).read())

    # encode into base64
    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    # attach the instance 'p' to instance 'msg'
    msg.attach(p)

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(fromaddr, "insert password for server gmail")

    # Converts the Multipart msg into a string
    text = msg.as_string()

    # sending the mail
    s.sendmail(fromaddr, toaddr, text)

    # terminating the session
    s.quit()
    print("EMAIL SENT")


def random_string(stringlength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringlength))


def set_admin():
    """get email address for admin"""
    print("Insert admin email:")
    return input()


def shutdown():
    print("shutting down")
    exit(0)
    """Turn off computer"""
    #os.system('systemctl poweroff')

def test(status):
    """if purposely failing"""
    if TEST:
        safe = False
    else:
        safe = True

    """loop through cores and test if dangerous temp"""
    for items in status['coretemp']:
        print(str(items[0]) + " " + str(items[1]))
        if items[1] >= 100.0:
            safe = False

    return safe


def transfer(key_name, dns):
    """change key permissions"""
    os.system("chmod 400 " + key_name)

    """get paths for files"""
    key_name = './' + key_name
    file2trans = "insert filename and path"

    """add host to known hosts to bypass prompt"""
    print("WAITING TO INITIALIZE")
    os.system("ssh-keyscan -H " + dns + " >> ~/.ssh/known_hosts")

    """start transfer"""
    command = "scp -i " + key_name + " " + file2trans + " " + "ubuntu@" + dns + ":~"
    print("STARTING TRANSFER")
    os.system(command)
    print("TRANSFER COMPLETE")
