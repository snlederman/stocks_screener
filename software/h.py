import requests
from lxml import html
import re

# URL of the page to scrape
url = 'https://fintel.io/so/us/tsla?d=2023-03-31'

# Make the request to fetch the page content
response = requests.get(url)
html_content = response.content

# Parse the page content using lxml
tree = html.fromstring(html_content)

# Use XPath to locate the data
# This example assumes you want the first row's second column data
xpath_expression = '//*[@id="main-content"]/div/div[1]/div/div/div[2]/table/tbody/tr[1]/td[2]/text()'
amount = tree.xpath(xpath_expression)

match = re.search(r'-\s(\d+\.?\d*)%', amount[0])
percentage = float(match.group(1))/100
print(percentage)