import time
import pandas as pd
import numpy as np
import requests

debug = False

def collegeSalaries(code, sleep=30):
	"""Return pandas DataFrame with 2017-2018 Gray Book Information for given college of the University of Illinois.

	Args:
		code (str): Code indicating college for which to download data.
		sleep (int): Number of seconds to sleep after making network request. Only applies where data not already cached.

	Returns:
		pandas DataFrame with all Gray Book information for the given college.

	Examples::
		collegeSalaries('FY') # Returns DataFrame with information for University of Illinois, Chicago Campus, FY - School of Public Health.
	"""
	# Read HTML table into pandas DataFrame
	try:
		data = pd.read_html('data/{}.html'.format(code))
	except ValueError:
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

# Pull salary data for each UIC college
uicData = []
for college in 'JV GF FR JY FL JP JA FZ GA FV GE GC GS FN FM FP FQ JM FS JD GH GT JT FT GQ FW JS FX JB JU FY GL JK GN JL GP HY JW JE JX JC JJ JF'.split():
	uicData.append(collegeSalaries(college))
uicData = pd.concat(uicData)
uicData.reset_index(drop=True, inplace=True)

# Compute total salary and FTE for each employee
uicData['employee_nrow'] = uicData.groupby('Employee Name')['Employee Name'].transform(lambda s: sum(s.duplicated())+1)
actualcomptotal = uicData[['Employee Name']].copy() # DataFrame for comparing totals shown in uicData to actual totals we compute from the uicData
actualcomptotal.set_index('Employee Name', inplace=True)
for j in ['Present FTE', 'Proposed FTE', 'Present Salary', 'Proposed Salary']:
	uicData['comptotal_'+j] = uicData[j].where(uicData['Job Title'] == 'Employee Total for All Jobs...')
	uicData['comptotal_'+j] = uicData.groupby('Employee Name')['comptotal_'+j].transform(np.max)
	uicData.loc[uicData['employee_nrow'] == 1, 'comptotal_'+j] = uicData[j]
	actualcomptotal['Total computed from data: '+j] = uicData.loc[uicData['Job Title'] != 'Employee Total for All Jobs...'].groupby('Employee Name')[j].sum()
	actualcomptotal['Total shown in data: '+j] = uicData[['Employee Name', 'comptotal_'+j]].drop_duplicates().set_index('Employee Name')
	if debug: print(actualcomptotal.loc[abs(actualcomptotal['Total computed from data: '+j] - actualcomptotal['Total shown in data: '+j])>.01,
		['Total computed from data: '+j, 'Total shown in data: '+j]])
# Discrepancies between totals shown in data and totals computed from data appear to be due to appointments outside of UIC, in particular, System Offices appointments
# Continue with totals shown in data
del actualcomptotal

# Create DataFrame with one row per employee x college/department giving their total salary and FTE (across all colleges/departments, where employee has multiple appointments)
salaries = uicData[['Employee Name', 'comptotal_Present FTE', 'comptotal_Proposed FTE', 'comptotal_Present Salary', 'comptotal_Proposed Salary', 'College', 'Dept']]
salaries = salaries.drop(salaries.loc[salaries.duplicated()].index)
salaries = salaries.rename({'Employee Name': 'empname', 'comptotal_Present FTE': 'curfte', 'comptotal_Proposed FTE': 'newfte',
	'comptotal_Present Salary': 'cursalary', 'comptotal_Proposed Salary': 'newsalary', 'College': 'college', 'Dept': 'dept'}, axis=1)
assert any(salaries[['empname', 'college', 'dept']].duplicated()) == False

# Compute salary/FTE
salaries['cursalaryperfte'] = salaries['cursalary'] / salaries['curfte']
salaries['newsalaryperfte'] = salaries['newsalary'] / salaries['newfte']

def deptReport(salaries, dept, var='newsalaryperfte'):
	"""Generate report by department (within college).

	Args:
		salaries: pandas DataFrame with salary data.
		dept (str): Department for which to produce report.
		var (str): Variable on which to produce report.

	Returns:
		None
	"""
	ranks = salaries.loc[salaries.dept == dept, var].sort_values(ascending=False).rank()
	ranks.name = 'Rank'
	print(pd.concat([salaries[salaries.dept == dept].sort_values(var, ascending=False)[['college', 'dept', 'empname', var]], ranks], axis=1))
deptReport(salaries, '846 - Managerial Studies')


