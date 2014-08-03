from distutils.core import setup
from distutils.extension import Extension

setup(name='SIMPLEchangepoint',
        version='1.0',
        description='SIMultaneous Penalized Likelihood Estimation of changepoints',
        long_description='Detects simultaneous changepoints in multiple sequential observables by solving a penalized maximum Laplace-likelihood optimization problem',
        author='Zhou Fan',
        author_email='Zhou.Fan@deshawresearch.com',
        url='http://www.deshawresearch.com/resources.html',
        packages=['SIMPLEchangepoint'],
        platforms=['Linux'],
        ext_modules=[Extension('SIMPLEchangepoint._univariate_changes',
            ['src/_univariate_changes.cpp'])],
        scripts=['scripts/ComputeSIMPLEChanges']
        )
