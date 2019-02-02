from pytest import approx

import numpy as np

class Simulation:
	def calculate(self, variable_name, inputs):
		return inputs[variable_name]

# OpenFisca's core mission is to calculate. If you give it
# some inputs, it can calculate them for you (by just giving
# them back.)

def test_calculate():
	simulation = Simulation()
	inputs = {"salaire_net": np.array([800.0, 1600.0])}
	result = simulation.calculate("salaire_net", inputs)
	assert result == approx(np.array([800.0, 1600.0]))
