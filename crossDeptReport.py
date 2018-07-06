import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter, Select, Div
from bokeh.layouts import layout
from bokeh.io import curdoc
from gini import gini

salaries = pd.read_csv('salaries.csv', index_col=0)

selectVariable = Select(title='Variable', options=['Current Salary', 'Previous Salary'])
selectCampus = Select(title='Campus', value='All', options=['All', 'Chicago', 'Springfield', 'Urbana-Champaign', 'System'])
selectCollege = Select(title='College')

def update():
	var = 'newsalaryperfte'
	if selectVariable.value == 'Previous Salary': var = 'cursalaryperfte'
	campus = selectCampus.value
	if campus == 'All': campusSelection = (salaries.campus == salaries.campus)
	else: campusSelection = (salaries.campus == campus)
	college = selectCollege.value
	if college == 'All': collegeSelection = (salaries.college == salaries.college)
	else: collegeSelection = (salaries.college == college)
	df = salaries.loc[campusSelection & collegeSelection].groupby(
		['campus', 'college', 'dept'])[var].agg(
		['size', 'count', 'min', 'mean', 'max', gini]).reset_index()
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
	l.children[2] = DataTable(source=ColumnDataSource(df), columns=columns, height=650, width=1600, selectable=True, scroll_to_selection=True)

def selectCampusUpdate():
	if selectCampus.value == 'All': selectCollege.options = ['All']
	else: selectCollege.options = ['All'] + sorted(list(set(list(salaries.loc[salaries.campus == selectCampus.value, 'college']))))
	selectCollege.value = 'All'
	update()

selectVariable.on_change('value', lambda attr, old, new: update())
selectCampus.on_change('value', lambda attr, old, new: selectCampusUpdate())
selectCollege.on_change('value', lambda attr, old, new: update())

l = layout([
	[Div(text='<font size="3"><b>Report on Salaries across Departments</b></font>', width=500)],
	[selectVariable, selectCampus, selectCollege],
	[DataTable()],
	[Div(text='Data on salaries per 1.0 FTE are shown to allow comparisons for employees not on a standard full-time appointment.', width=1000)],
])
selectCampusUpdate()
curdoc().add_root(l)

