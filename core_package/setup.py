from distutils.core import setup
from distutils.extension import Extension

setup(name='SIMPLEchangepoint',
        version='1.0',
        description='SIMultaneous Penalized Likelihood Estimation of changepoints',
        long_description='Detects simultaneous changepoints in multiple sequential observables by solving a penalized maximum Laplace-likelihood optimization problem',
        author='Zhou Fan',
        author_email='zhoufan@stanford.edu',
        url='https://github.com/DEShawResearch/SIMPLEchangepoint',
        packages=['SIMPLEchangepoint'],
        platforms=['Linux'],
        ext_modules=[Extension('SIMPLEchangepoint._univariate_changes',
            ['src/_univariate_changes.cpp'])],
        scripts=['scripts/ComputeSIMPLEChanges']
        )
