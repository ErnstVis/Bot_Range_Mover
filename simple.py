import math



def clc_amm(P_min, P_max, ammount_in, target):
    if target:
        L = ammount_in / ((math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min)))
        ammount_out = L * (math.sqrt(P_max) - math.sqrt(P_min))
    else:
        L = ammount_in / (math.sqrt(P_max) - math.sqrt(P_min))
        ammount_out = L * (math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min))
    print('L', L)
    return ammount_out




print(clc_amm(3819, 4113, 48, 0))









# print(clc_amm(4518.710081, 4684.33879325251, 0.003881222, 1))
# print(clc_amm(4684.33879325251, 4856.03845667503, 0.00374399, 1))



