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

