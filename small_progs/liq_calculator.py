import math

def price_normalize(P, x10 = 0, level = '', pr = 0):
    tick = math.log(P) / math.log(1.0001)
    if x10:
        tick = tick / 10
    if level == 'l':
        tick = math.floor(tick)
    elif level == 'h':
        tick = math.ceil(tick)
    else:
        tick = round(tick)
    if x10:
        tick = tick * 10
    if pr:
        print('Price:', P, 'Tick:', tick)
    return 1.0001 ** tick

def calc_ammount_1(P_max, P_min, P, ammount_0): 
    L = ammount_0 / ((math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P)))
    ammount_1 = L * (math.sqrt(P) - math.sqrt(P_min))
    return ammount_1

def calc_ammount_0(P_max, P_min, P, ammount_1): 
    L = ammount_1 / (math.sqrt(P) - math.sqrt(P_min))
    ammount_0 = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
    return ammount_0

def calc_range_min(P_max, P, ammount_0, ammount_1):
    sqrt_P = math.sqrt(P)
    sqrt_P_max = math.sqrt(P_max)
    L = ammount_0 / ((sqrt_P_max - sqrt_P) / (sqrt_P_max * sqrt_P))
    # L = ammount_1 / (math.sqrt(P) - math.sqrt(P_min))
    P_min = (sqrt_P - ammount_1 / L) ** 2
    return P_min

def calc_range_max(P_min, P, ammount_0, ammount_1):
    sqrt_P = math.sqrt(P)
    sqrt_P_min= math.sqrt(P_min)
    L = ammount_1 / (sqrt_P - sqrt_P_min)
    # ammount_0 = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
    # ammount_0 / L = (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
    # math.sqrt(P_max) * math.sqrt(P) * (ammount_0 / L) = math.sqrt(P_max) - math.sqrt(P)
    # math.sqrt(P_max) - math.sqrt(P_max) * math.sqrt(P) * (ammount_0 / L) = math.sqrt(P)
    # math.sqrt(P_max) * (1 - math.sqrt(P) * (ammount_0 / L)) = math.sqrt(P)
    # math.sqrt(P_max) = math.sqrt(P) / (1 - math.sqrt(P) * (ammount_0 / L))
    P_max = (sqrt_P / (1 - sqrt_P * (ammount_0 / L))) ** 2
    return P_max



# TEST calc range
'''
am_0 = 4.96753813  # LINK
am_1 = 465.033004  # WMATI
P_max = 100.059971
P_min = 28.5550103
P = 62.0005454

# TEST calc_range_min
a = calc_range_min(P_max, P, am_0, am_1)
b = price_normalize(a, 1, 'l')  # okay for amm0
c = price_normalize(a, 1, 'h') # okay for amm1
print('Min:', a, 'corrected low:', b, 'corrected high:', c)
result1a = calc_ammount_1(P_max, b, P, am_0)
result2a = calc_ammount_1(P_max, c, P, am_0)
result1b = calc_ammount_0(P_max, b, P, am_1)
result2b = calc_ammount_0(P_max, c, P, am_1)
print('Ammount 1:', result1a, result2a)
print('Ammount 0:', result1b, result2b)

# TEST calc_range_max
a = calc_range_max(P_min, P, am_0, am_1)
b = price_normalize(a, 1, 'l')  # okay for amm0
c = price_normalize(a, 1, 'h') # okay for amm1
print('Max:', a, 'corrected low:', b, 'corrected high:', c)
result1a = calc_ammount_1(b, P_min, P, am_0)
result2a = calc_ammount_1(c, P_min, P, am_0)
result1b = calc_ammount_0(b, P_min, P, am_1)
result2b = calc_ammount_0(c, P_min, P, am_1)
print('Ammount 1:', result1a, result2a)
print('Ammount 0:', result1b, result2b)
'''






# Start values
am_0 = 0  # weth
am_1 = 1000 # usdc
P = P_max = P_min = 1800

# params
qty_shift = 0.3 
range_shift = 100
range_inc = 0
range_dec = 0
last_dir = 1

# Step swap and move up
if last_dir:
    am_0 = qty_shift * am_1 / P
    am_1 = am_1 * (1 - qty_shift)
    P_max = P_max + range_shift
    P_min = calc_range_min(P_max, P, am_0, am_1)
else:
    am_1 = qty_shift * am_0 * P
    am_0 = am_0 * (1 - qty_shift)
    P_min = P_min - range_shift
    P_max = calc_range_max(P_min, P, am_0, am_1)

print('Entering to pool')
print('P_min:', P_min)
print('P:', P)
print('P_max:', P_max)
print('Ammount0:', am_0, ' |  Ammount1:', am_1)
print()
print('Exiting from pool')

L = am_1 / (math.sqrt(P) - math.sqrt(P_min))

new_dir = 1     # random fn or waiting for price change
if new_dir:
    P = P_max
    am_1 = L * (math.sqrt(P) - math.sqrt(P_min))
    am_0 = 0
    print('Autoexit by max level.')
else:
    P = P_min
    am_0 = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
    am_1 = 0
    print('Autoexit by min level.')
if new_dir == last_dir:
    range_shift = range_shift + range_inc
else:
    range_shift = range_shift - range_dec
last_dir = new_dir
print('Ammount0:', am_0, ' |  Ammount1:', am_1)


# TEST pool moving
'''
# Get L from am
L = am_1 / (math.sqrt(P) - math.sqrt(P_min))
am_0 = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))

print('L:', L)
print()
am_0_test = am_0 + am_1 / P
am_1_test = am_1 + am_0 * P
print( 'Ammount0:', am_0, ' |  Ammount1:', am_1)
print('T0:', am_0_test, 'T1:', am_1_test)
print()

# price gone down
P_new = P_min
am_0_new = L * (math.sqrt(P_max) - math.sqrt(P_new)) / (math.sqrt(P_max) * math.sqrt(P_new))
am_1_new = L * (math.sqrt(P_new) - math.sqrt(P_min))
print('Ammount0:', am_0_new, ' |  T1:', am_0_new * P_new)
# price gone up
P_new = P_max
am_0_new = L * (math.sqrt(P_max) - math.sqrt(P_new)) / (math.sqrt(P_max) * math.sqrt(P_new))
am_1_new = L * (math.sqrt(P_new) - math.sqrt(P_min))
print('T0:', am_1_new / P_new, ' |  Ammount1:', am_1_new)
'''
