import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import Select, Div
from bokeh.layouts import row, column
from bokeh.io import curdoc

salaries = pd.read_csv('salaries.csv', index_col=0)

selectVariable = Select(title='Variable', options=['Current Salary', 'Previous Salary'])
selectCampus = Select(title='Campus', value='Chicago', options=['Chicago', 'Springfield', 'Urbana-Champaign', 'System'])
selectCollege = Select(title='College')
selectDept = Select(title='Department')

TOOLTIPS = [
	('Employee', '@empname'),
	('Titles in Department', '@empdepttitle'),
	('Salary', '@value{0,0.00}'),
]

def selection():
	var = 'newsalaryperfte'
	if selectVariable.value == 'Previous Salary': var = 'cursalaryperfte'
	campus = selectCampus.value
	college = selectCollege.value
	dept = selectDept.value
	df = salaries.loc[(salaries.campus == campus) & (salaries.college == college) & (salaries.dept == dept), 
		['empname', 'empdepttitle', var]].rename(columns={var: 'value'})
	df['Rank'] = df['value'].rank(ascending=False)
	df['ylabel'] = df.apply(lambda row: '{:g} {}'.format(row['Rank'], row['empname']), axis=1)
	df['value_scaled'] = df['value']/1000
	return df.sort_values('value', ascending=True)

def update():
	df = selection()
	source = ColumnDataSource(df)
	newfigure = figure(plot_width=1200, plot_height=60+len(df)*15, y_range=df['ylabel'], x_axis_label='Salary in 1000s', tooltips=TOOLTIPS)
	newfigure.title.text_font_size = '20pt'
	newfigure.xaxis.axis_label_text_font_size = '16pt'
	newfigure.yaxis.major_label_text_font_size = '11pt'
	newfigure.hbar(y='ylabel', height=0.9, right='value_scaled', source=source)
	layout.children[1] = newfigure

def selectCampusUpdate():
	selectCollege.options = sorted(list(set(salaries.loc[salaries.campus == selectCampus.value, 'college'])))
	selectCollege.value = selectCollege.options[0]

def selectCollegeUpdate():
	selectDept.options = sorted(list(set(salaries.loc[(salaries.campus == selectCampus.value) & (salaries.college == selectCollege.value), 'dept'])))
	selectDept.value = selectDept.options[0]

selectVariable.on_change('value', lambda attr, old, new: update())
selectCampus.on_change('value', lambda attr, old, new: selectCampusUpdate())
selectCollege.on_change('value', lambda attr, old, new: selectCollegeUpdate())
selectDept.on_change('value', lambda attr, old, new: update())

layout = row(
	column(
		Div(text='<font size="3"><b>Report on Salaries by Department</b></font>'),
		selectVariable,
		selectCampus,
		selectCollege,
		selectDept,
		Div(text='Salaries per 1.0 FTE are shown to allow comparisons for employees not on a standard full-time appointment.'),
	),
	figure())
selectCampusUpdate()
curdoc().add_root(layout)

