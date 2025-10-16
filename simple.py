import math



def clc_amm(P_min, P_max, ammount_in, target):
    if target:
        L = ammount_in / ((math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min)))
        ammount_out = L * (math.sqrt(P_max) - math.sqrt(P_min))
    else:
        L = ammount_in / (math.sqrt(P_max) - math.sqrt(P_min))
        ammount_out = L * (math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min))
    return ammount_out




print(clc_amm(4056.140771, 4204.814476, 17.22527066, 0))
print(clc_amm(3912.723866, 4056.140771, 16.61622005, 0))
print(clc_amm(3774.377892, 3912.723866, 16.31981853, 0))
print(clc_amm(3640.923551, 3774.377892, 15.74278287, 0))









# print(clc_amm(4518.710081, 4684.33879325251, 0.003881222, 1))
# print(clc_amm(4684.33879325251, 4856.03845667503, 0.00374399, 1))



