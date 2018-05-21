def dew_point_calculate(humidity, temperature, isCelsius=True,
                        isReturnTypeCelsius=True):
    '''calculate dew_point based on temperature and relative humidity'''
    temp = temperature

    humi = humidity
    ans = (temp - (14.55 + 0.114 * temp) * (1 - (0.01 * humi)) - pow(((2.5 +
           0.007 * temp) * (1 - (0.01 * humi))), 3) - (15.9 + 0.117 * temp) *
           pow((1 - (0.01 * humi)), 14))

    return ans  # returns dew Point in Celsius


def compare(x, y):
    if x > y:
        return 1
    elif x < y:
        return -1
    elif x == y:
        return 0
