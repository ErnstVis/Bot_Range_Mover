    


# OLD PART OF BOTPOS CLASS



# def p_actuate(self, mode, hlp = 0):
#     if mode == 'rnd':                                   # Random price change
#         if (1.0001 ** self.P_act - self.reference_price) / self.reference_price * 100 > 100:
#             x = -0.001
#         elif (1.0001 ** self.P_act - self.reference_price) / self.reference_price * 100 < -50:
#             x = 0.001
#         else:
#             x = 0                                   # hold movement in reality
#         if hlp:                                     # hour or tick randomize
#             y = 0.0001
#         else:
#             y = 0.005
#         self.P_act_normal *= (1 + random.gauss(x, y))
#         self.P_act = self.prc_norm(self.P_act_normal)
#     elif mode == 'man':
#         if hlp:
#             self.P_act = self.P_max_tick
#             self.P_act_normal = 1.0001 ** self.P_max_tick
#         else:
#             self.P_act = self.P_min_tick
#             self.P_act_normal = 1.0001 ** self.P_min_tick
#     else:
#         self.amm0 = self.chain.get_balance_token(0)
#         self.amm1 = self.chain.get_balance_token(1)
#         self.P_act_tick, self.P_act = self.chain.get_current_tick()

# def stat_put(self, time):
#     self.prices_max.append(self.P_max)
#     self.prices_min.append(self.P_min)
#     self.prices.append(self.P_act_normal)
#     self.balances.append((self.amm1 + self.amm0 * self.P_act_normal) + (self.amm1_lock + self.amm0_lock * self.P_act_normal))
#     self.balances_alt.append((self.amm0 + self.amm1 / self.P_act_normal) + (self.amm0_lock + self.amm1_lock / self.P_act_normal))
#     self.times.append(float(time))





















        # if mode == 'UT' or mode == 'UF':
        #     self.k0 = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, 1, 0)
        #     self.amm0_get = (self.k0 * self.amm1) / (1 + self.k0 * self.P_act)
        #     print("Needed to get per one token:", self.k0)
        #     print('Limit:', self.amm0_get * self.P_act * (1 + self.slippage))
        #     print('Need to output token:', self.amm0_get)
        #     x, x0, x1 = self.chain.get_swap_ammount_router(self.amm0_get, self.amm0_get * self.P_act * (1 + self.slippage), 0, by='Q')
        #     # self.amm1 -= self.amm0_get * self.P_act
        #     # self.amm0 += self.amm0_get
        #     # am0new = k * am1 / (1 + k * p)                            FORMULA
        # elif mode == 'DT' or mode == 'DF':
        #     self.k1 = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, 1, 1)
        #     self.amm1_get = (self.k1 * self.amm0 * self.P_act) / (self.k1 + self.P_act)
        #     x, x0, x1 = self.chain.get_swap_ammount_router(self.amm1_get, self.amm1_get / self.P_act * (1 - self.slippage), 1, by='Q')
        #     # self.amm0 -= self.amm1_get / self.P_act
        #     # self.amm1 += self.amm1_get  
        #     # am1new = (k * am0 * p) / (k + p)                          FORMULA