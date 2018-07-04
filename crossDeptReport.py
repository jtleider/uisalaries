import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter
from bokeh.io import curdoc

def gini(y):
	"""Calculate Gini coefficient for a pandas Series. Computation method from https://numbersandshapes.net/2017/09/the-gini-coefficient-and-income-inequality-in-australia/

	Args:
		y: pandas Series

	Returns:
		float: Gini coefficient of Series
	"""
	y = y.loc[y.notnull()].sort_values()
	w = pd.concat([pd.Series([0]), y.cumsum()/y.sum()])
	n = len(y)
	return 1 - sum((1/float(n)) * (w.iloc[i] + w.iloc[i+1]) for i in range(n))
assert abs(gini(pd.Series([1])) == 0)
assert abs(gini(pd.Series([0, 100])) == 0.5)
assert abs(gini(pd.Series([998000, 20000, 17500, 70000, 23500, 45200])) - .7202) < .00005 # http://www.peterrosenmai.com/lorenz-curve-graphing-tool-and-gini-coefficient-calculator?
assert abs(gini(pd.Series([1, 1, 2, 2])) - .167) < .0005 # http://shlegeris.com/gini

def crossDeptReport(salaries, var='newsalaryperfte', varlabel='Salary', showFigure=False):
	"""Generate report by department (within college).

	Args:
		salaries: pandas DataFrame with salary data.
		var (str): Variable on which to produce report.
		varlabel (str): Label for variable on which to produce report (for figure).
		showFigure (bool): Plot bar chart of salaries.

	Returns:
		pandas DataFrame with report across departments.
	"""
	d = salaries.groupby(['campus', 'college', 'dept'])['newsalaryperfte'].agg(['size', 'count', 'min', 'mean', 'max', gini])
	if showFigure:
		source = ColumnDataSource(d)
		# data table
	return d


salaries = pd.read_csv('salaries.csv', index_col=0)
d = crossDeptReport(salaries, showFigure=True)
d.reset_index(inplace=True)
print(d)

columns = [
	TableColumn(field='campus', title='Campus'),
	TableColumn(field='college', title='College'),
	TableColumn(field='dept', title='Department'),
	TableColumn(field='size', title='# of Employees'),
	TableColumn(field='count', title='# with Data'),
	TableColumn(field='min', title='Min', formatter=NumberFormatter(format="$0,0")),
	TableColumn(field='mean', title='Mean', formatter=NumberFormatter(format="$0,0")),
	TableColumn(field='max', title='Max', formatter=NumberFormatter(format="$0,0")),
	TableColumn(field='gini', title='Gini Coefficient', formatter=NumberFormatter(format="0.000")),
]
source = ColumnDataSource(d)
dtable = DataTable(source=source, columns=columns, width=1600)

curdoc().add_root(dtable)

# Create plot for this


