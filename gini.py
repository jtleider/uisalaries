import pandas as pd

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

