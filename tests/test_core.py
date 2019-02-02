from pytest import approx, mark

import numpy as np
import inspect

def previous(period):
	return str(int(period)-1)

class Simulation:
	def __init__(self):
		self.functions = {}
	def use(self, function, when = None):
		self.functions[function.__name__] = (self.functions.get(function.__name__) or []) + [(function, when)]
	def offset(self, parameter, period):
		if parameter.annotation is not parameter.empty:
			return eval(parameter.annotation, {"previous":previous}, {"period":period})
		else:
			return period
	def calculate(self, variable_name, period, inputs):
		if variable_name in inputs:
			return inputs[variable_name][period]
		if variable_name in self.functions:
			candidates = [function for (function, when) in self.functions[variable_name] if ((not when) or (when[0] <= period < when[1]))]
			func = candidates[0]
			parameters = inspect.signature(func).parameters
			args = {parameter: self.calculate(parameter, self.offset(parameters.get(parameter), period), inputs) for parameter in parameters}
			return func(**args)

# OpenFisca's core mission is to calculate. If you give it
# some inputs, it can calculate them for you (by just giving
# them back.) Inputs and calculations are relative to a given
# time period, for reasons to be discussed further.

def test_calculate():
	simulation = Simulation()
	inputs = {"salaire_net": {"2016": np.array([800.0, 1600.0])}}
	result = simulation.calculate("salaire_net", "2016", inputs)
	assert result == approx(np.array([800.0, 1600.0]))

# Besides inputs, OpenFisca can handle formulas; they
# prescribe what inputs they need and transform them into
# values.

def test_calculate_formula():
	simulation = Simulation()
	def salaire_net(salaire_brut):
		return salaire_brut * 0.8
	simulation.use(salaire_net)
	inputs = {"salaire_brut": {"2016": np.array([1000.0, 2000.0])}}
	result = simulation.calculate("salaire_net", "2016", inputs)
	assert result == approx(np.array([800.0, 1600.0]))

# OpenFisca is concerned with computable law, and one
# defining characteristic of law is that it changes over
# time; we therefore want to associate formulas with time
# periods.

def test_calculate_by_period():
	simulation = Simulation()
	def salaire_net(salaire_brut):
		return salaire_brut * 0.8
	simulation.use(salaire_net, ("2016", "2017"))
	def salaire_net(salaire_brut):
		return salaire_brut * 0.7
	simulation.use(salaire_net, ("2017", "2018"))
	inputs = {"salaire_brut": {"2016": np.array([1000.0, 2000.0]), "2017": np.array([1000.0, 2000.0])}}
	result = simulation.calculate("salaire_net", "2017", inputs)
	assert result == approx(np.array([700.0, 1400.0]))
	result = simulation.calculate("salaire_net", "2016", inputs)
	assert result == approx(np.array([800.0, 1600.0]))

# Sometimes we want to use values from an earlier period

def test_calculate_by_period():
	simulation = Simulation()
	inputs = {"rfr": {"2016": np.array([1000.0, 2000.0])}}
	def allocation(rfr : "previous(period)"):
		return rfr * 0.01
	simulation.use(allocation)
	result = simulation.calculate("allocation", "2017", inputs)
	assert result == approx(np.array([10.0, 20.0]))
