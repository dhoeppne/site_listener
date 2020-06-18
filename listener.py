from selenium import webdriver
import smtplib, ssl, time, email, os, csv, json, difflib
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
    try:
        driver.get(url)
        navigated = True
    except:
        print("unable to navigate to site")

    location = url

    if navigated:
        if url == "https://www.cardhaus.com/":
            img = driver.find_element(By.CSS_SELECTOR, "img[title='daily-deal-generic-rectangle.png']")
            href = img.find_element_by_xpath('..').click()
            location = driver.current_url
        elif url == "https://www.coolstuffinc.com/page/1175":
            sale_list = driver.find_elements_by_class_name("breadcrumb-trail")
            href="https://www.coolstuffinc.com/p/294149" # default page is Montmartre

            for sale in sale_list:
                if "Board Games" in sale.text:
                    href = sale.find_element_by_xpath("../../../../div[1]/a").get_attribute("href")

            driver.get(href)
            location = driver.current_url

        deal = driver.find_element_by_css_selector(selector).text
        deal = deal.replace("(Deal of the Day)", "")
        deal = deal.replace("(Add to cart to see price)", "")
    else:
        deal = "Site is down"

    return deal, location


def email(website, deal, pic, rating, bgg_url):
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
        <a href="{}">Link to bgg page</a>. {} has a rating of {}
        <br></br>
        <br><a href="{}"><img src="cid:image1"></a><br>
        </p>
    </body>
    </html>
    """.format(website, siteName, deal, bgg_url, deal, rating, website)

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    # Open PDF file in binary mode
    with open(pic, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        msgImage = MIMEImage(attachment.read())

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    message.attach(msgImage)

    # Convert message to string
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

def bgg_lookup(name):
    corpusname = "/Volumes/Storage/bgg_games/__corpus__.json"

    rating = "rating not found"
    gameId = 1

    try:
        with open(corpusname, 'r') as corpus:
                data = json.load(corpus)
                games = data.keys()
                match = difflib.get_close_matches(name, games)[0]

                if len(match) > 0:
                    index = data[match]

                    with open("/Volumes/Storage/bgg_games/" + str(index) + ".json") as game:
                        game_data = json.load(game)
                        rating = game_data["bggRating"]
                        gameId = game_data["gameId"]

    return rating, "https://boardgamegeek.com/boardgame/" + str(gameId)

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

            bgg_lookup(returnedName)

            if returnedName and lastdeal != returnedName:
                needs_update = True
                driver.save_screenshot(picName) # save a screenshot to disk
                update[row][2] = returnedName # update current deal's name

                # look up bgg data
                rating, bgg_url = bgg_lookup(returnedName)

                print("Sending email")
                email(location, returnedName, picName, rating, bgg_url)

            row += 1

    if needs_update:
        update_csv(update)

    driver.quit ()
    print("finished deal collection")


main()