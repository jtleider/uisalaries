import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Span, Label
from bokeh.models.widgets import Select, Div, Slider
from bokeh.layouts import row, column
from bokeh.io import curdoc

salaries = pd.read_csv('salaries.csv', index_col=0)
assert all(salaries.groupby('dept')['college'].nunique() == 1)
assert all(salaries.groupby('college')['campus'].nunique() == 1)

selectVariable = Select(title='Variable', options=['Current Salary', 'Previous Salary'])
selectCampus = Select(title='Campus', value='Chicago', options=['Chicago', 'Springfield', 'Urbana-Champaign', 'System'])
selectCollege = Select(title='College')
selectDept = Select(title='Department')

excludeSlider = Slider(start=0, end=5, value=0, step=1, title="Exclude top")

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
	if excludeSlider.value > 0: exclude = slice(None, -excludeSlider.value)
	else: exclude = slice(None)
	df = salaries.loc[(salaries.campus == campus) & (salaries.college == college) & (salaries.dept == dept), 
		['empname', 'empdepttitle', var]].rename(columns={var: 'value'})
	df['Rank'] = df['value'].rank(ascending=False)
	df['ylabel'] = df.apply(lambda row: '{:g} {}'.format(row['Rank'], row['empname']), axis=1)
	df['value_scaled'] = df['value']/1000
	return df.sort_values('value', na_position='first', ascending=True).iloc[exclude], df['value_scaled'].quantile(0.5)

def update():
	df, median = selection()
	source = ColumnDataSource(df)
	newfigure = figure(plot_width=1200, plot_height=60+len(df)*15, y_range=df['ylabel'], x_axis_label='Salary in 1000s', tooltips=TOOLTIPS, tools='hover,save')
	newfigure.title.text_font_size = '20pt'
	newfigure.xaxis.axis_label_text_font_size = '16pt'
	newfigure.yaxis.major_label_text_font_size = '11pt'
	newfigure.hbar(y='ylabel', height=0.9, right='value_scaled', source=source)
	newfigure.add_layout(Span(location=median, dimension='height', line_dash='dashed', line_width=3))
	newfigure.add_layout(Label(x=median+2, y=(len(df)-1)/2, text='Median (no exclusions)'))
	layout.children[1] = newfigure

def selectCampusUpdate():
	selectCollege.options = sorted(list(set(salaries.loc[salaries.campus == selectCampus.value, 'college'])))
	selectCollege.value = selectCollege.options[0]

def selectCollegeUpdate():
	selectDept.options = sorted(list(set(salaries.loc[(salaries.campus == selectCampus.value) & (salaries.college == selectCollege.value), 'dept'])))
	selectDept.value = selectDept.options[0]

def selectDeptUpdate():
	if excludeSlider.value > 0: excludeSlider.value = 0
	else: update()

selectVariable.on_change('value', lambda attr, old, new: update())
selectCampus.on_change('value', lambda attr, old, new: selectCampusUpdate())
selectCollege.on_change('value', lambda attr, old, new: selectCollegeUpdate())
selectDept.on_change('value', lambda attr, old, new: selectDeptUpdate())
excludeSlider.on_change('value', lambda attr, old, new: update())

layout = row(
	column(
		Div(text='<font size="3"><b>Report on Salaries by Department</b></font>'),
		selectVariable,
		selectCampus,
		selectCollege,
		selectDept,
		excludeSlider,
		Div(text='Salaries per 1.0 FTE are shown to allow comparisons for employees not on a standard full-time appointment.'),
	),
	figure())
selectCampusUpdate()
curdoc().add_root(layout)

