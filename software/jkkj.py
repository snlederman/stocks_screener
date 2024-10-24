from ib_insync import *
import os
import xml.etree.ElementTree as ET
import requests
from lxml import html
import re
from datetime import datetime
from finvizfinance.quote import finvizfinance
import pandas as pd

ticker='NVDA'

# Set a fixed date for calculations
fixed_date = datetime.strptime('2024-05-30', '%Y-%m-%d')

# URL of the page to scrape
url = 'https://fintel.io/so/us/tsla?d=2023-03-31'

# Set up the connection parameters
host = os.getenv('IB_HOST', 'host.docker.internal')
port = int(os.getenv('IB_PORT', '4001'))

# Initialize IB and connect
ib = IB()
ib.connect(host, port, clientId=1)

# Define the contract
contract = Stock(ticker, 'SMART', 'USD')

# Request and parse fundamental data
fundamental_data = ib.reqFundamentalData(contract, 'ReportsFinSummary')
estimates_data = ib.reqFundamentalData(contract, 'RESC')
x = ib.reqFundamentalData(contract, 'ReportsOwnership')

root = ET.fromstring(fundamental_data)
rootx = ET.fromstring(estimates_data)
xroot = ET.fromstring(x)

# Extracting data
data = []
for owner in xroot.findall('Owner'):
    owner_id = owner.get('ownerId')
    owner_type = owner.find('type').text
    name_date = owner.find('name').attrib['asofDate']
    name = owner.find('name').text
    quantity_date = owner.find('quantity').attrib['asofDate']
    quantity = float(owner.find('quantity').text)

    data.append({
        'ownerId': owner_id,
        'type': owner_type,
        'name_date': name_date,
        'name': name,
        'quantity_date': quantity_date,
        'quantity': quantity
    })

# Creating DataFrame
df = pd.DataFrame(data)

df['quantity_date'] = pd.to_datetime(df['quantity_date'])

# Sorting the DataFrame by name and date
df = df.sort_values(by=['name', 'quantity_date'])

# Calculating 3-month variations
df['variations'] = df.groupby('name')['quantity'].diff()

df.groupby('variations')

print(df)
df = df.sort_values(by=['name', 'quantity_date'])

# Calculating 3-month variations
df['3_month_variation'] = df.groupby('name')['quantity'].diff(periods=3)

# Grouping by 'name' and 'type'
grouped_df = df.groupby(['type', 'quantity_date']).sum().reset_index()

# Ordering by 'name_date' and 'quantity_date'
grouped_df = grouped_df.sort_values(by=['quantity_date'])

# Displaying the grouped and ordered DataFrame
grouped_df = grouped_df[(grouped_df['type'] == '3')]

# Function to find the most recent and the second most recent value for a given period and date
def find_recent_values(root, tag, period, type, fixed_date):
    values = []
    for elem in root.findall(f'.//{tag}'):
        if elem.get('period') == period and elem.get('reportType') == type:
            date = datetime.strptime(elem.get('asofDate'), '%Y-%m-%d')
            if date <= fixed_date:
                values.append((date, float(elem.text)))
    values.sort(key=lambda x: x[0], reverse=True)
    return [values[0], values[4]]

# Function to extract EPS values (actual and estimates) from rootx
def extract_eps_values(rootx, year, value_type='ActValue'):
    if value_type == 'ActValue':
        for elem in rootx.findall('.//FYActual[@type="EPS"]//FYPeriod'):
            if elem.get('fYear') == str(year) and elem.get('periodType') == 'A':
                value_elem = elem.find('.//ActValue')
                if value_elem is not None:
                    return float(value_elem.text)
    elif value_type == 'ConsValue':
        for elem in rootx.findall('.//FYEstimate[@type="EPS"]//FYPeriod'):
            if elem.get('fYear') == str(year) and elem.get('periodType') == 'A':
                value_elem = elem.find('.//ConsEstimate[@type="Mean"]//ConsValue[@dateType="CURR"]')
                if value_elem is not None:
                    return float(value_elem.text)
    return None

# Extract EPS values for the relevant periods
eps_12m_values = find_recent_values(root, 'EPS', '12M', 'TTM', fixed_date)
eps_3m_values = find_recent_values(root, 'EPS', '3M', 'A', fixed_date)

# Extract revenue values for the relevant periods
revenue_3m_values = find_recent_values(root, 'TotalRevenue', '3M', 'A', fixed_date)

# Determine the current year and next two years from the fixed date
current_year = fixed_date.year
next_year = current_year + 1
year_after_next = current_year + 2

# Extract EPS values (actual and estimates) for the current, next, and year after next
eps_actual_current_year = extract_eps_values(rootx, current_year, value_type='ActValue')
eps_estimate_next_year = extract_eps_values(rootx, next_year, value_type='ConsValue')
eps_estimate_year_after_next = extract_eps_values(rootx, year_after_next, value_type='ConsValue')

# Calculate EPS growth quarter over quarter (3M period)
if len(eps_3m_values) == 2:
    eps_growth_qtr_qtr = (eps_3m_values[0][1] - eps_3m_values[1][1]) / abs(eps_3m_values[1][1]) * 100
else:
    eps_growth_qtr_qtr = None

# Calculate sales growth quarter over quarter (3M period)
if len(revenue_3m_values) == 2:
    sales_growth_qtr_qtr = (revenue_3m_values[0][1] - revenue_3m_values[1][1]) / abs(revenue_3m_values[1][1]) * 100
else:
    sales_growth_qtr_qtr = None

# Calculate EPS growth this year using actual and next year estimate data
if eps_actual_current_year is not None and eps_estimate_next_year is not None:
    eps_growth_this_year_estimate = (eps_estimate_next_year - eps_actual_current_year) / abs(eps_actual_current_year) * 100
else:
    eps_growth_this_year_estimate = None

# Calculate EPS growth next year using next year and year after next estimate data
if eps_estimate_next_year is not None and eps_estimate_year_after_next is not None:
    eps_growth_next_year_estimate = (eps_estimate_year_after_next - eps_estimate_next_year) / abs(eps_estimate_next_year) * 100
else:
    eps_growth_next_year_estimate = None

# Make the request to fetch the page content
html_content = requests.get(url).content

# Parse the page content using lxml
tree = html.fromstring(html_content)

# Use XPath to locate the data
# This example assumes you want the first row's second column data
xpath_expression = '//*[@id="main-content"]/div/div[1]/div/div/div[2]/table/tbody/tr[1]/td[2]/text()'
amount = tree.xpath(xpath_expression)

match = re.search(r'-\s(\d+\.?\d*)%', amount[0])
percentage = float(match.group(1))/100

# Print results
print(f"EPS Growth This Year: {eps_growth_this_year_estimate:.2f}%" if eps_growth_this_year_estimate is not None else
      f"EPS Growth This Year: {finvizfinance(ticker).ticker_fundament()['EPS this Y']}" if current_year==datetime.now().year
      else "EPS Growth This Year: Not enough data")
print(f"EPS Growth Next Year: {eps_growth_next_year_estimate:.2f}%" if eps_growth_next_year_estimate is not None else
      "EPS Growth Next Year: Not enough data")
print(f"EPS Growth Quarter over Quarter: {eps_growth_qtr_qtr:.2f}%" if eps_growth_qtr_qtr is not None else
      "EPS Growth Quarter over Quarter: Not enough data")
print(f"Sales Growth Quarter over Quarter: {sales_growth_qtr_qtr:.2f}%" if sales_growth_qtr_qtr is not None else
      "Sales Growth Quarter over Quarter: Not enough data")
print(f"Institutional Transactions: {percentage:.2f}%" if percentage is not None else
      "Institutional Transactions: Not enough data")
