from bs4 import BeautifulSoup
import argparse
import pandas as pd
import requests
import datetime

# Create a empty Dataframe for data storage
df = pd.DataFrame(columns=('Date', 'Time', 'Currency', 'Impact', 'Event', 'Actual', 'Forecast', 'Previous'))

# Set up arguments for user to specify date range of data, output file type (excel or csv) and file name
parser = argparse.ArgumentParser()
parser.add_argument('--datefrom', type=str, help='starting date of website data with format YYYYMMDD')
parser.add_argument('--dateto', type=str, help='ending date of website data with format YYYYMMDD')
parser.add_argument('--outfile', type=str, help='file name and outfile document type, filename.csv or filename.xlsx')
args = parser.parse_args()


# Transfer user input date from argument into the format of URL
def format_user_date(input_date):
    year = input_date[:4]
    day = str(int(input_date[6:8]))
    choices = {'01': 'jan', '02': 'feb', '03': 'mar', '04': 'apr', '05': 'may', '06': 'jun', '07': 'jul', '08': 'aug', '09': 'sep', '10': 'oct', '11': 'nov', '12': 'dec'}
    month = choices.get(input_date[4:6], 'default')
    output = 'calendar.php?day=' + month + day + '.' + year
    return output


# Retrieve date from URL
def retrieve_link_date(input_date):
    date_in_process = str(input_date).split('=')[1].split('.')
    month = date_in_process[0][0].upper() + date_in_process[0][1:3]
    day = date_in_process[0][3:]
    year = date_in_process[1]
    output = month + " " + day + ", " + year
    return output


# It is not required for user to enter end date of data retrieval. By default, the program will get the data until current date
def get_end_date():
    if args.dateto is not None:
        return format_user_date(args.dateto)
    else:
        curr_date = datetime.date.today()
        return 'calendar.php?day=' + curr_date.strftime('%b').lower()[:3] + str(int(curr_date.strftime('%d'))) + '.' + str(curr_date.year)


# Depending on the argument input from the user, the program will generate different types of file. If the user enters 'filename.csv', the program will
# generate csv file. If the user enters 'filename.xlsx', the program will generate excel file. The user can enter whatever filename he wants
def get_file(filename):
    if filename.split('.')[1] == 'csv':
        df.to_csv(filename, encoding='utf-8', index=False)
    else:
        writer = pd.ExcelWriter(filename)
        df.to_excel(writer, 'output', index=False)
        writer.save()


# Retrieve calendar from forexfactory.com with start date and end date specified
def get_calendar(start, end):
    base_url = 'https://www.forexfactory.com/'
    response = requests.get(base_url + start)  # visit the website of start date and retrieve html
    soup = BeautifulSoup(response.text, 'lxml')  # parsing with lxml

    # get the data for each columns
    time = soup.find_all('td', class_='calendar__cell calendar__time time')
    curr = soup.find_all('td', class_='calendar__cell calendar__currency currency ')
    impact = soup.find_all('div', class_='calendar__impact-icon calendar__impact-icon--screen')
    event = soup.find_all('span', class_='calendar__event-title')
    actual = soup.find_all('td', class_='calendar__cell calendar__actual actual')
    forecast = soup.find_all('td', class_='calendar__cell calendar__forecast forecast')
    previous = soup.find_all('td', class_='calendar__cell calendar__previous previous')

    date = retrieve_link_date(start)
    num_of_event = len(curr)
    format_time = []
    following = soup.find('li', class_='left pagination shadow').a['href']  # get date part of URL for the next date to visit

    # put data of the date into Dataframe
    if curr[0].text.strip() != '':  # check if there is no data for the date
        for i in range(num_of_event):
            # In the economic calendar, if multiple events happen at the same time, it will only show time only for the first one appearing.
            # The following code deals with this issue
            if str(time[i].text) == '':
                format_time.append(format_time[i-1])
            else:
                format_time.append(time[i].text)
            # each row stands for a single event, which will be insert into the Dataframe
            input_row = [date, format_time[i], curr[i].text.strip(), impact[i].span['class'][0], event[i].text, actual[i].text, forecast[i].text, previous[i].text]
            df.loc[-1] = input_row
            df.index = df.index + 1

    # If the start date equals the end date, the program will terminate the recursion
    if start == end:
        return

    # retrieve data for the following date
    get_calendar(following, end)


if __name__ == '__main__':
    get_calendar(format_user_date(args.datefrom), get_end_date())
    get_file(args.outfile)