import math
import random
import matplotlib.pyplot as plt

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









# params
qty_shift = 0.3 
range_inc = 30
range_dec = 20
range_max = 500
range_min = 30






# cycle params
avrg = 0
avrg_i = 1
j = 50


for i in range(avrg_i):                         # Repeat for collect average loss

    range_shift = 100                           # Initial calculations for start
    last_dir = 1
    am_0 = 0 # weth
    am_1 = 1500 # usdc
    P = 2000
    P_start = P
    am_1_start = am_1
    am_0 = qty_shift * am_1 / P
    am_1 = am_1 * (1 - qty_shift)
    print('Ammount0:', am_0, ' |  Ammount1:', am_1)
    P_max = P + range_shift
    P_min = calc_range_min(P_max, P, am_0, am_1)
    L = am_1 / (math.sqrt(P) - math.sqrt(P_min))
    prices_max = [P_max]
    prices_min = [P_min]
    prices = [P]
    count = 0

    while count < j:
        if (P - P_start) / P_start * 100 > 100:         # Correct, if random walk goes too far
            x = -0.001                                  #
        elif (P - P_start) / P_start * 100 < -50:       #
            x = 0.001                                   #
        else:                                           #
            x = 0                                       #
        P *= (1 + random.gauss(x, 0.005))               # Price generate block end

        if P > P_max:                                   # Control price to upper limit
            if last_dir:                                    # Review range swift values
                range_shift = range_shift - range_dec
                if range_shift < range_min:
                    range_shift = range_min
            else:
                range_shift = range_shift + range_inc
                if range_shift > range_max:
                    range_shift = range_max
            last_dir = 1

            am_1 = L * (math.sqrt(P_max) - math.sqrt(P_min))
            am_0 = 0                                            # Exit from pool
            print('Autoexit by max level.')
            am_0 = qty_shift * am_1 / P                         # Rebalance ammounts
            am_1 = am_1 * (1 - qty_shift)
            P_max = P + range_shift                             # Set new range
            P_min = calc_range_min(P_max, P, am_0, am_1)

        elif P < P_min:                                 # Control price to lower limit
            if last_dir:                                    # Review range swift values
                range_shift = range_shift + range_inc
                if range_shift > range_max:
                    range_shift = range_max
            else:
                range_shift = range_shift - range_dec
                if range_shift < range_min:
                    range_shift = range_min
            last_dir = 0
            
            am_0 = L * (math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min))
            am_1 = 0                                            # Exit from pool
            print('Autoexit by min level.')
            am_1 = qty_shift * am_0 * P                         # Rebalance ammounts  
            am_0 = am_0 * (1 - qty_shift)
            P_min = P - range_shift                             # Set new range
            P_max = calc_range_max(P_min, P, am_0, am_1)
        else:
            continue                                            # Repeat if price in range

        L = am_1 / (math.sqrt(P) - math.sqrt(P_min))            # Calculate new liquidity

        bal_change = ((am_1 + am_0 * P) - am_1_start) / am_1_start * 100
        print('Entering to pool')                               # Prepare statistics
        print('P_min:', P_min, 'P:', P, 'P_max:', P_max)
        print('Ammount0:', am_0, ' |  Ammount1:', am_1)
        print('P start:', P_start, 'P now:', P, '========================>>> P change:', (P - P_start) / P_start * 100, '%')
        print('Interation:', count + 1, 'Epoch:', i + 1)
        print('Balance in start:', am_1_start, 'Balance now:', am_1 + am_0 * P, '========================>>> Change:', bal_change, '%')
        print('-----------------------------------------------------------------------------')
        count += 1 

        if avrg_i == i + 1:                                     # Save statistics in last iteration for curve
            prices_max.append(P_max)
            prices_min.append(P_min)
            prices.append(P)

    avrg += bal_change
print('Average:', avrg / avrg_i, '%')



plt.figure(figsize=(12, 6))
plt.plot(prices_max, 'o', label="Max")
plt.plot(prices_min, 'o', label="Min")
plt.plot(prices, label="P")
plt.title("Emulated ranges movement")
plt.xlabel("Interations")
plt.ylabel("Price")
plt.grid(True)
plt.legend()
plt.savefig('pictures/pool_sim_' + str(random.randint(1000, 9999)) + '.png')

# TESTED 1500>>>3500    profit 136..140 /1000   13.5%
# TESTED 3500>>>1500    profit 0.09 /0.667      13.5%
# TESTED 3500<><>, 1500<><>          ???        -15.7%

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
