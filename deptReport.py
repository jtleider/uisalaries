# Report by department

import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Span, Label
from bokeh.models.widgets import Select, Div, Slider
from bokeh.layouts import row, column
from bokeh.io import curdoc
from gini import gini

# Read in salary data, make sure departments nest within colleges and colleges nest within campuses, as we assume this later in deciding how to update plot.
salaries = pd.read_csv('salaries.csv', index_col=0)
assert all(salaries.groupby('dept')['college'].nunique() == 1)
assert all(salaries.groupby('college')['campus'].nunique() == 1)

# User controls
selectVariable = Select(title='Variable', options=['Current Salary', 'Previous Salary'])
selectCampus = Select(title='Campus', value='Chicago', options=['Chicago', 'Springfield', 'Urbana-Champaign', 'System'])
selectCollege = Select(title='College')
selectDept = Select(title='Department')
excludeSlider = Slider(start=0, end=5, value=0, step=1, title="Exclude top")

# Return selection of salary data
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
	return df.sort_values('value', na_position='first', ascending=True).iloc[exclude], df['value_scaled'].quantile(0.5), gini(df['value_scaled'])

# Update plot
def update():
	df, median, giniValue = selection()
	source = ColumnDataSource(df)
	# We have to replace the plot each time because that's the only way to update the plot height based on the number of employees shown.
	newfigure = figure(plot_width=1200, plot_height=60+len(df)*15, y_range=df['ylabel'], x_axis_label='Salary in 1000s',
		tooltips=[('Employee', '@empname'), ('Titles in Department', '@empdepttitle'), ('Salary', '@value{0,0.00}')], tools='hover,save')
	newfigure.title.text_font_size = '20pt'
	newfigure.xaxis.axis_label_text_font_size = '16pt'
	newfigure.yaxis.major_label_text_font_size = '11pt'
	newfigure.hbar(y='ylabel', height=0.9, right='value_scaled', source=source)
	newfigure.add_layout(Span(location=median, dimension='height', line_dash='dashed', line_width=3))
	newfigure.add_layout(Label(x=median+2, y=(len(df)-1)/2, text='Median (no exclusions)'))
	newfigure.add_layout(Label(x=630, y=0, x_units='screen', text='Gini coefficient = {:.3f} (no exclusions)'.format(giniValue)))
	layout.children[1] = newfigure

# Handle changes to user controls
def selectCampusUpdate():
	selectCollege.options = sorted(list(set(salaries.loc[salaries.campus == selectCampus.value, 'college'])))
	selectCollege.value = selectCollege.options[0] # updating the college will cascade down

def selectCollegeUpdate():
	selectDept.options = sorted(list(set(salaries.loc[(salaries.campus == selectCampus.value) & (salaries.college == selectCollege.value), 'dept'])))
	selectDept.value = selectDept.options[0] # updating the department will cascade down

def selectDeptUpdate():
	# If we update the slider, that will cascade down to update the plot; otherwise, update the plot here.
	if excludeSlider.value > 0: excludeSlider.value = 0
	else: update()

selectVariable.on_change('value', lambda attr, old, new: update())
selectCampus.on_change('value', lambda attr, old, new: selectCampusUpdate())
selectCollege.on_change('value', lambda attr, old, new: selectCollegeUpdate())
selectDept.on_change('value', lambda attr, old, new: selectDeptUpdate())
excludeSlider.on_change('value', lambda attr, old, new: update())

# Layout
layout = row(
	column(
		Div(text='<font size="3"><b>Report on Salaries by Department</b></font>'),
		selectVariable,
		selectCampus,
		selectCollege,
		selectDept,
		excludeSlider,
		Div(text='Total salary shown (including any salary from other departments). Salaries per 1.0 FTE are shown to allow comparisons for employees not on a standard full-time appointment.'),
	),
	figure())
selectCampusUpdate()
curdoc().add_root(layout)

