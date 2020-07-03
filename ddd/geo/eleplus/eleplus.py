# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import numpy as np
from scipy.optimize import basinhopping

func = lambda x: np.sum(np.square(x - 7)) #np.sum(np.abs(x)) + (abs(x[3] - 1)) * 1000
#x0=[-5]  #[-5, -1, 1, 1]
x0 = np.array([[-3] * 2500])

minimizer_kwargs = {"method": "BFGS"}
ret = basinhopping(func, x0, minimizer_kwargs=minimizer_kwargs, niter=0)

print("global minimum: x = %s, f(x0) = %.4f" % (ret.x, ret.fun))



import numpy as np
from scipy.optimize import basinhopping
import matplotlib.pyplot as plt
import random

func = lambda x: np.sum(np.square(np.reshape(x, (-1, 2))[:,0] ** 2 + np.reshape(x, (-1, 2))[:,1] ** 2 - 1)) #np.sum(np.abs(x)) + (abs(x[3] - 1)) * 1000
#x0=[-5]  #[-5, -1, 1, 1]
x0 = np.array([random.uniform(-10, 10) for i in range(2 * 250)])
#x0 = np.reshape(x0, (50, 2))
print(x0)

minimizer_kwargs = {"method": "BFGS"}
ret = basinhopping(func, x0, minimizer_kwargs=minimizer_kwargs, niter=200)

print("global minimum: x = %s, f(x0) = %.4f" % (ret.x, ret.fun))


x = np.reshape(ret.x, (-1, 2))
print(x)

plt.scatter(x[:,0], x[:,1])
plt.show()
