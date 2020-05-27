from selenium import webdriver
import smtplib, ssl, time, email, os, csv
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

def listener(driver, url, selector):
    driver.get(url)
    return driver.find_element_by_css_selector(selector)


def email(website, deal, pic):

    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "devdavid968@gmail.com"  # Enter your address
    receiver_email = "noshameever@gmail.com"  # Enter receiver address
    password = ""
    siteName = website.split(".")[1]

    with open("passcode.txt", "r") as file:
        password = file.readline()

    message = MIMEMultipart("alternative")
    message["Subject"] = "DEAL " + siteName + " " + deal
    message["From"] = sender_email
    message["To"] = receiver_email

    text = """\
    {}""".format(website)

    html = """\
    <html>
    <body>
        <p>Deal of the day at
        <a href="{}">{}</a>
        is {}
        </p>
    </body>
    </html>
    """.format(website, siteName, deal)

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    filename = pic  # In same directory as script

    # Open PDF file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        "attachment; filename= %s" % filename,
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def main():
    while True:
        driver = webdriver.PhantomJS(executable_path="./node_modules/phantomjs-prebuilt/bin/phantomjs") # or add to your PATH
        driver.set_window_size(1024, 768) # optional

        with open("sites.csv") as file:
            row_count = sum(1 for row in file) - 1
            name = [""] * row_count


        with open("sites.csv") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            row = 0

            for site, css_selector in reader:
                website = site

                returnedName = listener(driver, website, css_selector)
                picName = website.split(".")[1] + 'deal.png'

                if returnedName.text and name[row] != returnedName.text:
                    driver.save_screenshot(picName) # save a screenshot to disk

                    email(website, returnedName.text, picName)

                name[row] = returnedName
                row += 1

        driver.close()
        time.sleep(600)


main()