from selenium import webdriver
import smtplib, ssl, time, email, os, csv
from sys import platform
from email import encoders
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from selenium.webdriver.common.by import By
from datetime import datetime

def listener(driver, url, selector):
    print("visiting " + url)
    driver.get(url)
    if url == "https://www.cardhaus.com/":
        img = driver.find_element(By.CSS_SELECTOR, "img[title='daily-deal-generic-rectangle.png']")
        href = img.find_element_by_xpath('..').click()
        location = driver.current_url

        deal = driver.find_element_by_css_selector(selector).text
    else:
        deal = driver.find_element_by_css_selector(selector).text
        location = url

    return deal, location


def email(website, deal, pic):
    print("emailing for " + website)

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
        <br><img src="cid:image1"><br>
        </p>
    </body>
    </html>
    """.format(website, siteName, deal)

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    # Open PDF file in binary mode
    with open(pic, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        msgImage = MIMEImage(attachment.read())
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    message.attach(msgImage)

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        "attachment; filename= %s" % pic,
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def update_csv(update):
    print("updating csv")
    with open("sites.csv", "w+") as file:
        writer = csv.writer(file, delimiter= ",")
        for line in update:
            writer.writerow(line)

def main():
    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    print("starting deal collection at " + current_time)

    if platform == "darwin":
        path = "/usr/local/bin/phantomjs"
    else:
        path = "./node_modules/phantomjs-prebuilt/bin/phantomjs"

    driver = webdriver.PhantomJS(executable_path=path, service_log_path=os.path.devnull) # or add to your PATH
    driver.set_window_size(1024, 768) # optional

    update = [["site", "css_selector", "lastdeal"]]
    needs_update = False

    with open("sites.csv") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        row = 1 # skip header in update

        for site, css_selector, lastdeal in reader:
            update.append([site, css_selector, lastdeal])

            returnedName, location = listener(driver, site, css_selector)
            picName = location.split(".")[1] + 'deal.png'

            if returnedName and lastdeal != returnedName:
                needs_update = True
                driver.save_screenshot(picName) # save a screenshot to disk
                update[row][2] = returnedName # update current deal's name

                print("Sending email")
                email(location, returnedName, picName)

            row += 1

    if needs_update:
        update_csv(update)

    driver.quit ()
    print("finished deal collection")


main()