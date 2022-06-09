import requests
import datetime as dt
import smtplib
import creds

#!Need STOCKS_API_KEY and NEWS_API_KEY (from creds.py file)

STOCK = "TM"
COMPANY_NAME = "Toyota Motor Corp"
STOCKS_URL = "https://www.alphavantage.co/query?"
NEWS_URL = "https://newsapi.org/v2/everything"

stocks_parameters = {
    "function":"TIME_SERIES_DAILY",
    "symbol":STOCK,
    "interval":"5min",
    "apikey": creds.STOCKS_API_KEY
}
news_parameters = {
    "apiKey": creds.NEWS_API_KEY,
    "qInTitle": "Toyota"
}


def createNews(news_data)->list:
    #!Could've done list comprehension instead of helper function,
    #!but author was sometimes "None" so wanted to change it
    news_list = []
    list_index = 0
    completed_entries = 0
    while completed_entries < 3: 
        title = news_data[list_index]["title"]
        author = news_data[list_index]["author"]
        if not author or author == "None":
            author = "Unknown"
        description = news_data[list_index]["content"]
        url = news_data[list_index]["url"]

        news_block = f"{title}\nBy {author}\n{description}\nLink to article - {url}"
        
        news_list.append(news_block)
        list_index += 1
        completed_entries += 1
        
    return news_list



#------------------------ Main Driver --------------------------------#  
#Utilize stocks api for gathering stocks information
response = requests.get(url=STOCKS_URL, params=stocks_parameters)
response.raise_for_status()
stocks_data = response.json()

day_tracker = 1

curr_day = dt.date(year=2022, month=5, day=27)
prev_day = dt.date(year=curr_day.year, month=curr_day.month, day=curr_day.day-day_tracker)
curr_day_str = str(curr_day)
prev_day_str = str(prev_day)

curr_day_close_price = round(float(stocks_data["Time Series (Daily)"][curr_day_str]['4. close']), 2)
prev_day_close_price = round(float(stocks_data["Time Series (Daily)"][prev_day_str]['4. close']), 2)
delta = round(100*((curr_day_close_price - prev_day_close_price)/curr_day_close_price), 2)

any_news = False
#checks 20 days before current date (including closed market days)
while day_tracker < 20:
    prev_day = curr_day - dt.timedelta(days=day_tracker)
    prev_day_str = str(prev_day)
    if prev_day_str in stocks_data["Time Series (Daily)"]:
        prev_day_close_price = round(float(stocks_data["Time Series (Daily)"][prev_day_str]['4. close']), 2)
        delta = round(100*((curr_day_close_price - prev_day_close_price)/curr_day_close_price), 2)
        if abs(delta) > 5:
            #sends request to news api about the company
            news_response = requests.get(url=NEWS_URL, params=news_parameters)
            news_response.raise_for_status()
            data = news_response.json()["articles"][:3]
            up_down = "🔺" if delta > 0 else "🔻"

            #!List Comprehension Method
            # formatted_articles = [f"{STOCK_NAME}: {up_down}{diff_percent}%\nHeadline: {article['title']}. \nBrief: {article['content']}" for article in three_articles]
            news_articles = createNews(data)
            
            with smtplib.SMTP("smtp.mail.yahoo.com", port=587) as connection:
                connection.starttls()
                connection.login(user=creds.EMAIL_LOGIN, password=creds.EMAIL_PASSWORD)
                connection.sendmail(
                    from_addr=creds.EMAIL_LOGIN,
                    to_addrs=creds.RECEIVING_EMAIL,
                    msg=f"Subject:{COMPANY_NAME} Breaking News!\n\n{curr_day_str}\n\n{COMPANY_NAME}'s stock has changed at a drastic rate recently! {delta}{up_down}\n\n{news_articles[0]}\n\n{news_articles[1]}\n\n{news_articles[2]}".encode('utf8'))

            any_news = True
            break
        curr_day = prev_day
        curr_day_str = prev_day_str
        curr_day_close_price = prev_day_close_price
    day_tracker += 1

if any_news:
    print("There was news!")
print("Program successful!")