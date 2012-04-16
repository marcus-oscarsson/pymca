import unittest
import os
import numpy    

class testGefit(unittest.TestCase):
    def setUp(self):
        """
        import the module
        """
        try:
            from PyMca import Gefit
            self.gefit = Gefit
        except:
            self.gefit = None

    def gaussianPlusLinearBackground(self, param, t):
        dummy = 2.3548200450309493 * (t - param[3])/ param[4]
        return param[0] + param[1] * t +\
               param[2] * numpy.exp(-0.5 * dummy * dummy)

    def testGefitImport(self):
        self.assertIsNotNone(self.gefit)

    def testGefitLeastSquares(self):
        self.testGefitImport()
        x = numpy.arange(500.)
        originalParameters = numpy.array([10.5, 2, 1000.0, 200., 100],
                                         numpy.float)
        fitFunction = self.gaussianPlusLinearBackground
        y = fitFunction(originalParameters, x)

        startingParameters = [0.0 ,1.0,900.0, 150., 90]
        fittedpar, chisq, sigmapar =self.gefit.LeastSquaresFit(fitFunction,
                                                     startingParameters,
                                                     xdata=x,
                                                     ydata=y,
                                                     sigmadata=None)
        for i in range(len(originalParameters)):
            self.assertTrue(abs(fittedpar[i] - originalParameters[i]) < 0.01)

def getSuite(auto=True):
    testSuite = unittest.TestSuite()
    if auto:
        testSuite.addTest(\
            unittest.TestLoader().loadTestsFromTestCase(testGefit))
    else:
        # use a predefined order
        testSuite.addTest(testGefit("testGefitImport"))
        testSuite.addTest(testGefit("testGefitLeastSquares"))
    return testSuite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(getSuite(auto=False))
