# a dynamically registered class to perform a linear conversion.
class LineConversion:
    @staticmethod
    def Convert(x, m, b):
        ret = m*x + b
        #print("%f = %f * %f + %f" % (ret, m, x, b))
        return ret
    def Invert(y, m, b):
        ret = (y-b)/m
        #print("%f = (%f - %f) / %f" % (ret, y, b, m))
        return int(ret)
