import unittest


modelSuite = unittest.TestLoader().discover('tests')
runner = unittest.TextTestRunner()
runner.run(modelSuite)
