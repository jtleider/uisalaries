import time
import pandas as pd
import numpy as np
import requests

pd.set_option('display.max_rows', None)
debug = False

def collegeSalaries(campus, code, sleep=30):
	"""Return pandas DataFrame with 2017-2018 Gray Book Information for given college of the University of Illinois.

	Args:
		campus (str): Campus of which college is a part. This is noted in the returned DataFrame but is not used for downloading the data.
		code (str): Code indicating college for which to download data.
		sleep (int): Number of seconds to sleep after making network request. Only applies where data not already cached.

	Returns:
		pandas DataFrame with all Gray Book information for the given college.

	Examples::
		collegeSalaries('Chicago', 'FY') # Returns DataFrame with information for University of Illinois, Chicago Campus, FY - School of Public Health.
	"""
	# Read HTML table into pandas DataFrame
	try:
		data = pd.read_html('data/{}.html'.format(code))
	except ValueError:
		if debug: print('Downloading data for campus {}, college {}'.format(campus, code))
		r = requests.get('http://www.trustees.uillinois.edu/trustees/resources/17-18-Graybook/{}.html'.format(code))
		with open('data/{}.html'.format(code), 'x') as fp:
			fp.write(r.text)
		time.sleep(sleep)
		data = pd.read_html(r.text)
	assert len(data) == 1
	data = data[0]

	# Handle 'Employee Total for All Jobs...' properly; by default values are being placed in the wrong columns here
	totalrow = (data['Employee Name'] == 'Employee Total for All Jobs...')
	assert len(data.columns) == 8
	for col in range(-3, 0):
		assert all(data.loc[totalrow].iloc[:, col].isnull())
	for col in range(-1, -4-1, -1):
		data.loc[totalrow, data.columns[col]] = data.loc[totalrow, data.columns[col-3]]
		data.loc[totalrow, data.columns[col-3]] = np.nan
	assert all(data.loc[totalrow, 'Job Title'].isnull())
	data.loc[totalrow, 'Job Title'] = 'Employee Total for All Jobs...'
	data.loc[totalrow, 'Employee Name'] = np.nan

	# Need to fix read-in of rows for the same person but different job title; values are being placed in the wrong columns
	addltitlerow = (data['Proposed Salary'].isnull() & ~data['Present Salary'].isnull())
	assert data.columns[-1] == 'Proposed Salary'
	for col in range(len(data.columns)-1, 0, -1):
		data.loc[addltitlerow, data.columns[col]] = data.loc[addltitlerow, data.columns[col-1]]
	data.loc[addltitlerow, data.columns[0]] = np.nan

	# Copy down employee names
	data['Employee Name'] = data['Employee Name'].fillna(method='ffill')

	# Integrate subheaders into the data
	data['Campus'] = campus
	data['College'] = data.iloc[0, 0]
	data['Dept'] = data['Employee Name'].where(data['Job Title'].isnull())
	data['Dept'] = data['Dept'].fillna(method='ffill')
	data = data.drop(data.loc[data['Job Title'].isnull()].index)

	# Convert numeric columns
	for col in ['Present FTE', 'Proposed FTE', 'Present Salary', 'Proposed Salary']:
		try:
			data[col] = data[col].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
		except AttributeError:
			pass
		finally:
			data[col] = pd.to_numeric(data[col])

	return data

# Pull salary data for each University of Illinois college
colleges = {
	'Urbana-Champaign': 'KL KY LD NQ LT LN NA NT KM KT NU KW KN MY KP NN KR KS LQ KU KV LB NS NB LM NH LF LP LG LL NC LR NJ LC NP NE',
	'Chicago': 'JV GF FR JY FL JP JA FZ GA FV GE GC GS FN FM FP FQ JM FS JD GH GT JT FT GQ FW JS FX JB JU FY GL JK GN JL GP HY JW JE JX JC JJ JF',
	'Springfield': 'SC SG PE PL SA PG SF PJ PH SB PF SE PK',
	'System': 'AF AH AA AR AM AD AN AP AJ',
}
uiData = []
for campus in colleges:
	for college in colleges[campus].split():
		uiData.append(collegeSalaries(campus, college))
uiData = pd.concat(uiData)
uiData.reset_index(drop=True, inplace=True)

# Compute total salary and FTE for each employee
uiData['employee_nrow'] = uiData.groupby('Employee Name')['Employee Name'].transform(lambda s: sum(s.duplicated())+1)
actualcomptotal = uiData[['Employee Name']].copy() # DataFrame for comparing totals shown in uiData to actual totals we compute from the uiData
actualcomptotal.set_index('Employee Name', inplace=True)
for j in ['Present FTE', 'Proposed FTE', 'Present Salary', 'Proposed Salary']:
	uiData['comptotal_'+j] = uiData[j].where(uiData['Job Title'] == 'Employee Total for All Jobs...')
	uiData['comptotal_'+j] = uiData.groupby('Employee Name')['comptotal_'+j].transform(np.max)
	uiData.loc[uiData['employee_nrow'] == 1, 'comptotal_'+j] = uiData[j]
	actualcomptotal['Total computed from data: '+j] = uiData.loc[uiData['Job Title'] != 'Employee Total for All Jobs...'].groupby('Employee Name')[j].sum()
	actualcomptotal['Total shown in data: '+j] = uiData[['Employee Name', 'comptotal_'+j]].drop_duplicates().set_index('Employee Name')
	if debug: print(actualcomptotal.loc[abs(actualcomptotal['Total computed from data: '+j] - actualcomptotal['Total shown in data: '+j])>.01,
		['Total computed from data: '+j, 'Total shown in data: '+j]])
# Some of the totals shown in the data simply don't add up, and it's not clear why not. In at least some cases, it looks like there may be more than one person with the same name.
# In the absence of information to correct the totals shown, and given there are relatively few discrepancies, we will continue with the totals shown in the data.
del actualcomptotal

# Compute list of job titles for each employee
assert all(uiData['Job Title'].notnull())
uiData['comptotal_Job Title'] = uiData['Job Title'].where(uiData['Job Title'] != 'Employee Total for All Jobs...', '')
uiData['comptotal_Job Title'] = uiData.groupby(['Employee Name', 'Campus', 'College', 'Dept'])['comptotal_Job Title'].transform(lambda s: '; '.join(si for si in s if si != ''))

# Create DataFrame with one row per employee x college/department giving their total salary and FTE (across all colleges/departments, where employee has multiple appointments)
salaries = uiData[['Employee Name', 'comptotal_Job Title',
	'comptotal_Present FTE', 'comptotal_Proposed FTE', 'comptotal_Present Salary', 'comptotal_Proposed Salary', 'Campus', 'College', 'Dept']]
salaries = salaries.drop(salaries.loc[salaries.duplicated()].index)
salaries = salaries.rename({'Employee Name': 'empname', 'comptotal_Job Title': 'empdepttitle', 'comptotal_Present FTE': 'curfte', 'comptotal_Proposed FTE': 'newfte',
	'comptotal_Present Salary': 'cursalary', 'comptotal_Proposed Salary': 'newsalary', 'Campus': 'campus', 'College': 'college', 'Dept': 'dept'}, axis=1)
assert any(salaries[['empname', 'campus', 'college', 'dept']].duplicated()) == False

# Compute salary/FTE
salaries['cursalaryperfte'] = salaries['cursalary'] / salaries['curfte']
salaries.loc[salaries['curfte'] == 0, 'cursalaryperfte'] = np.nan
salaries['newsalaryperfte'] = salaries['newsalary'] / salaries['newfte']
salaries.loc[salaries['newfte'] == 0, 'newsalaryperfte'] = np.nan

# Export datasets to CSV
uiData.to_csv('uiData.csv') # includes all information in raw data
salaries.to_csv('salaries.csv') # includes summary data per employee

