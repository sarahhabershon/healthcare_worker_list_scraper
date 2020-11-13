import pandas as pd 
import requests_cache
import requests
import csv
requests_cache.install_cache('cache')
from bs4 import BeautifulSoup

#sources - note that the Russian list can't be translated before scraping; translate the page and then copy and paste the lists (there are two, one of Russian deaths and one of deaths outside Russia) into text files - russia.txt and outsideofrussia.txt
medscape = "https://www.medscape.com/viewarticle/927976"
italian_list = "https://portale.fnomceo.it/elenco-dei-medici-caduti-nel-corso-dellepidemia-di-covid-19/"
# russian_list = "https://sites.google.com/view/covid-memory/home?authuser=0"



#scrape medscape list, remove extraneous rows, create df
arr = []
page = requests.get(medscape)
soup = BeautifulSoup(page.text, "html.parser")
names = soup.find('div', attrs = {'id':'article-content'})
output = names.findAll('a', href=True)
for x in output:
	this = x.parent.text.replace("\n", "").split(',')
	arr.append(this)
arr_len = len(arr)-6
arr_start = 29
clipped_arr = arr[arr_start:arr_len]
clean_arr = []
for x in clipped_arr:
	derp = len(x)-1
	output = [x[0], x[1], x[derp]]
	clean_arr.append(output)

in_memoriam = pd.DataFrame(clean_arr, columns = ['Name', 'Age', 'Country'])
in_memoriam.rename(columns = {'Country':'country', 'Name':'name', 'Age':'age'}, inplace = True) 
in_memoriam["source"] = "Medscape"
in_memoriam["country"] = in_memoriam["country"].str.strip()


## scrape italian list, split and create df
itlian_arr = []
page = requests.get(italian_list)
soup = BeautifulSoup(page.text, "html.parser")
names = soup.find('ol')
output = names.findAll('li')
for x in output:
	itlian_arr.append(x.text.replace("\n", '†').split('†'))

italian_doctors = pd.DataFrame(itlian_arr, columns=["name", "date_reported", "notes"])
italian_doctors["country"]="Italy"
italian_doctors["source"]="Italian list"


## russian list - comes from txt files pasted from translated site. Gross, I know.
outside_rus = []
with open('outsideofrussia.txt', 'r') as f:
	for line in f:
		line = line.split(",")
		tableentry = [line[0].strip(), line[1].strip(), line.pop()]
		tableentry[2] = tableentry[2].rstrip()
		outside_rus.append(tableentry)

rus = []
with open('russia.txt', 'r', encoding="utf8") as f:
	for line in f:
		line = line.split(",")
		tableentry = [line[0].strip(), line[1].strip()]
		rus.append(tableentry)

outside_russia = pd.DataFrame(outside_rus, columns=["name", "age", "country"])
outside_russia["source"] = "Russian_list"

russia = pd.DataFrame(rus, columns=["name", "age"])
russia['country'] = 'Russia'
russia["source"] = "Russian_list"


#attach all the dfs together
total = in_memoriam.append(italian_doctors).append(outside_russia).append(russia)

#identify US states
states = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"]

total["USA"] = total["country"].isin(states)
total["country_or_us_state"] = total["country"]
total.loc[total.USA == True, "country"] = "USA"

#horrible hardcoded cleanup
total["country"] = total["country"].str.partition('(')
total["country"] = total["country"].str.strip()

total.loc[total['country_or_us_state'].str.contains("Mold"),'country'] = 'Moldova'
total.loc[total['country_or_us_state'].str.contains("Dominic"),'country'] = "Dominican Republic"
total.loc[total['country_or_us_state'].str.contains("England"),'country'] = 'England'
# total.loc[total['country_or_us_state'].str.contains("New York"),'country'] = 'USA'
total.loc[total['country_or_us_state'].str.contains("xico"),'country'] = 'Mexico'
total.loc[total['country_or_us_state'].str.contains("ppines"),'country'] = 'Philippines'
total.loc[total['country_or_us_state'].str.contains("Indon"),'country'] = 'Indonesia'



#check for duplicates, remove, keep as separate file for checking
duplicates = total.loc[total[['name', 'age', 'country']].duplicated(), :]
total = total.drop_duplicates(subset = ['name', 'age', 'country'])

#count
grouped = total.groupby(['country'])['name'].agg('count')

#create csv output
duplicates.to_csv('duplicates.csv')
grouped.to_csv("country_count.csv")
total.to_csv("merged_crowdsourced_lists.csv")
