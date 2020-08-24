# classes to perform integer/float conversions.
import math
import numpy

class ResistanceConversion:
    @staticmethod
    def Convert(adc, v_ref, v_full, r1, r2, bit_depth):
        v_adc = adc * v_full / (2 ** bit_depth)
        if r2 == 0 and r1 != 0:
            r = r1 * ((v_ref / v_adc) - 1.0)
        elif r1 == 0 and r2 != 0:
            r = r2 * (v_adc / v_ref)/(1.0 - (v_adc/v_ref))
        else:
            r = (r1 * r2) / ((((v_ref / v_adc) - 1.0) * r1) - r2)
        return r

    @staticmethod
    def Invert(r, v_ref, v_full, r1, r2, bit_depth):
        if r2 == 0 and r1 != 0:
            v_adc = v_ref / ((r / r1) + 1.0)
        elif r2 != 0 and r1 == 0:
            v_adc = v_ref / ((r2 / r) + 1.0)
        else:
            v_adc = v_ref / (((r1 * r2) + (r2 * r))/(r1 * r) + 1.0)
        return int(v_adc * (2 ** bit_depth) / v_full)

class SteinhartHartConversion:
    @staticmethod
    def Convert(raw, a, b, c, d, r0, v_ref, v_full, r1, r2, bit_depth):
        r = ResistanceConversion.Convert(raw, v_ref, v_full, r1, r2, bit_depth)
        x = math.log(r / r0)
        temp_k = 1.0 / (a + b * x + c * (x ** 2) + d * (x ** 3))
        temp_c = temp_k - 273.15
        return temp_c

    @staticmethod
    def Invert(temp_c, a, b, c, d, r0, v_ref, v_full, r1, r2, bit_depth):
        temp_k = temp_c + 273.15
        roots = numpy.roots([d, c, b, a - (1.0 / temp_k)])
        if numpy.iscomplex(roots[-1]):
            raise # inversion did not work
        return ResistanceConversion.Invert(r0 * math.exp(roots[-1]),
                                           v_ref, v_full, r1, r2, bit_depth)

class CallendarVanDusenConversion:# Platinum RTD
    @staticmethod
    def Convert(raw, a, b, c, r0, v_ref, v_full, r1, r2, bit_depth):
        r = ResistanceConversion.Convert(raw, v_ref, v_full, r1, r2, bit_depth)
        if r > r0:
            return (-a + math.sqrt(a**2 - 4 * b * (1.0 - (r / r0)))) / (2 * b)
        t = ((r / r0) - 1.0) / (a + (100.0 * b))
        for i in range(3): # up to 3 iterations
            tn = t - ((1 + a * t + b * (t ** 2) + c * (t ** 3) * (t - 100) - (res / r0)) /
                      (a + 2 * b * t - 300 * c * (t**2) + 4 * c * (t**3)))
            if abs(tn - t) < 3.0: # arbitrary threshold to determine convergence
                return tn
            t = tn
        return t

    @staticmethod
    def Invert(temp_c, a, b, c, r0, v_ref, v_full, r1, r2, bit_depth):
        if temp_c > 0:
            r = r0 * (1 + a * temp_c + b * (temp_c ** 2))
        else:
            r = r0 * (1 + a * temp_c + b * (temp_c ** 2) + c * (temp_c ** 3) * (temp_c - 100))
        return ResistanceConversion.Invert(r, v_ref, v_full, r1, r2, bit_depth)
