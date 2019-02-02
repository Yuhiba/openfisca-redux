from pytest import approx

import numpy as np
import inspect

class Simulation:
	def __init__(self):
		self.functions = {}
	def use(self, function):
		self.functions[function.__name__] = function
	def calculate(self, variable_name, inputs):
		if variable_name in inputs:
			return inputs[variable_name]
		if variable_name in self.functions:
			func = self.functions[variable_name]
			args = {param: self.calculate(param, inputs) for param in inspect.signature(func).parameters}
			return func(**args)

# OpenFisca's core mission is to calculate. If you give it
# some inputs, it can calculate them for you (by just giving
# them back.)

def test_calculate():
	simulation = Simulation()
	inputs = {"salaire_net": np.array([800.0, 1600.0])}
	result = simulation.calculate("salaire_net", inputs)
	assert result == approx(np.array([800.0, 1600.0]))

# Besides inputs, OpenFisca can handle formulas; they
# prescribe what inputs they need and transform them into
# values

def test_calculate_formula():
	simulation = Simulation()
	def salaire_net(salaire_brut):
		return salaire_brut * 0.8
	simulation.use(salaire_net)
	inputs = {"salaire_brut": np.array([1000.0, 2000.0])}
	result = simulation.calculate("salaire_net", inputs)
	assert result == approx(np.array([800.0, 1600.0]))
