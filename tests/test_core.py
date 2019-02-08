from pytest import approx, mark, raises

import numpy as np
import inspect

def previous(period):
	return str(int(period)-1)

class Simulation:
	def __init__(self):
		self.functions = {}
		self.defaults = {}

	def use(self, function, when = None):
		self.functions[function.__name__] = (self.functions.get(function.__name__) or []) + [(function, when)]

	def period(self, parameter, period):
		if parameter.annotation is "previous":
			return previous(period)
		else:
			return period

	def value(self, parameter, period):
		if parameter.annotation is "previous":
			return previous(period)
		else:
			return period

	def evaluate(self, parameters, parameter, period, inputs):
		p = parameters.get(parameter)
		if p.annotation is "formula":
			return self.formula(parameter, period)
		else:
			return self.calculate(parameter, self.period(p, period), inputs)

	def formula(self, variable_name, period):
		candidates = [function for (function, when) in self.functions[variable_name] if ((not when) or (when[0] <= period < when[1]))]
		return candidates[0]

	def calculate(self, variable_name, period, inputs):
		if variable_name in inputs:
			return inputs[variable_name][period]
		elif variable_name in self.defaults:
			return self.defaults[variable_name]
		elif variable_name in self.functions:
			func = self.formula(variable_name, period)
			parameters = inspect.signature(func).parameters
			args = {parameter: self.evaluate(parameters, parameter, period, inputs) for parameter in parameters}
			return func(**args)
		raise Exception()

	def use_default(self, variable_name, value):
		self.defaults[variable_name] = value


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

def test_calculate_with_value_from_previous_value():
	simulation = Simulation()
	inputs = {"rfr": {"2016": np.array([1000.0, 2000.0])}}
	def allocation(rfr : "previous"):
		return rfr * 0.01
	simulation.use(allocation)
	result = simulation.calculate("allocation", "2017", inputs)
	assert result == approx(np.array([10.0, 20.0]))


def test_calculate_without_input():
	simulation = Simulation()
	inputs = {}
	def allocation(rfr : "previous"):
		return rfr * 0.01
	simulation.use(allocation)
	simulation.use_default("rfr", 0.0)
	result = simulation.calculate("allocation", "2017", inputs)
	assert result == approx(np.array([0.0, 0.0]))

def test_calculate_without_default():
	simulation = Simulation()
	inputs = {}
	def allocation(rfr : "previous"):
		return rfr * 0.01
	simulation.use(allocation)
	with raises(Exception):
		result = simulation.calculate("allocation", "2017", inputs)





