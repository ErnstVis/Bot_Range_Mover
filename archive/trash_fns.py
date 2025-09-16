    


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