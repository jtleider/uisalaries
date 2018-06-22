import pandas as pd
import numpy as np

# Read HTML table into pandas DataFrame
data = pd.read_html('http://www.trustees.uillinois.edu/trustees/resources/17-18-Graybook/FY.html')
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
	data[col] = data[col].str.replace('$', '', regex=False)
	data[col] = data[col].str.replace(',', '', regex=False)
	data[col] = pd.to_numeric(data[col])

# Create DataFrame with one row per employee giving their total proposed salary, together with college and department
data['employee_nrow'] = data.groupby('Employee Name')['Employee Name'].transform(lambda s: sum(s.duplicated())+1)
actualcomptotal = data[['Employee Name']].copy() # DataFrame for comparing totals shown in data to actual totals we compute from the data
actualcomptotal.set_index('Employee Name', inplace=True)
for j in ['Present FTE', 'Proposed FTE', 'Present Salary', 'Proposed Salary']:
	data['comptotal_'+j] = data[j].where(data['Job Title'] == 'Employee Total for All Jobs...')
	data['comptotal_'+j] = data.groupby('Employee Name')['comptotal_'+j].transform(np.max)
	data.loc[data['employee_nrow'] == 1, 'comptotal_'+j] = data[j]
	actualcomptotal['Computed total: '+j] = data.loc[data['Job Title'] != 'Employee Total for All Jobs...'].groupby('Employee Name')[j].sum()
	actualcomptotal['Total shown in data: '+j] = data[['Employee Name', 'comptotal_'+j]].drop_duplicates().set_index('Employee Name')

salaries = data[['Employee Name', 'comptotal_Present FTE', 'comptotal_Proposed FTE', 'comptotal_Present Salary', 'comptotal_Proposed Salary']]
salaries = salaries.drop(salaries.loc[salaries.duplicated()].index)
salaries = salaries.rename({'Employee Name': 'empname', 'comptotal_Present FTE': 'curfte', 'comptotal_Proposed FTE': 'newfte',
	'comptotal_Present Salary': 'cursalary', 'comptotal_Proposed Salary': 'newsalary'}, axis=1)

