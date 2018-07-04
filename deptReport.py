import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.io import curdoc

# Report by department
def deptReport(salaries, dept, var='newsalaryperfte', varlabel='Salary', showFigure=False):
	"""Generate report by department (within college).

	Args:
		salaries: pandas DataFrame with salary data.
		dept (str): Department for which to produce report.
		var (str): Variable on which to produce report.
		varlabel (str): Label for variable on which to produce report (for figure).
		showFigure (bool): Plot bar chart of salaries.

	Returns:
		pandas DataFrame with report for department.
	"""
	ranks = salaries.loc[salaries.dept == dept, var].rank(ascending=False)
	ranks.name = 'Rank'
	d = pd.concat([salaries.loc[salaries.dept == dept, ['campus', 'college', 'dept', 'empname', 'empdepttitle', var]], ranks], axis=1).sort_values(var, ascending=True).copy()
	if showFigure:
		d[var+'_scaled'] = d[var]/1000
		d['ylabel'] = d.apply(lambda row: '{:g} {}'.format(row['Rank'], row['empname']), axis=1)
		source = ColumnDataSource(d)
		TOOLTIPS = [
			('Employee', '@empname'),
			('Titles in Department', '@empdepttitle'),
			(varlabel, "@{}{{0,0.00}}".format(var)),
		]
		p = figure(y_range=d['ylabel'], plot_height = len(d)*15, plot_width=1200,
			x_axis_label='{} in 1000s'.format(varlabel), title='{} Range in Department {}'.format(varlabel, dept), tooltips=TOOLTIPS)
		p.title.text_font_size = '20pt'
		p.xaxis.axis_label_text_font_size = '16pt'
		p.yaxis.major_label_text_font_size = '11pt'
		p.hbar(y='ylabel', height=0.9, right=var+'_scaled', source=source)
		curdoc().add_root(p)
		d.drop([var+'_scaled', 'ylabel'], axis=1, inplace=True)
	return d.sort_values(var, ascending=False)
salaries = pd.read_csv('salaries.csv', index_col=0)
d = deptReport(salaries, '846 - Managerial Studies', showFigure=True)
print(d)

