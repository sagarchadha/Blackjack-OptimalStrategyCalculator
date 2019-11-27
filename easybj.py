#!/usr/bin/python3
#
# easybj.py
#
# Calculate optimal strategy for the game of Easy Blackjack
#

from table import Table
from collections import defaultdict
#from numpy import inf

# code names for all the hard hands
HARD_CODE = [ '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', 
    '15', '16', '17', '18', '19', '20']

# code names for all the soft hands
SOFT_CODE = [ 'AA', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9' ]

# code names for all the hands that can be split
SPLIT_CODE = [ '22', '33', '44', '55', '66', '77', '88', '99', 'TT', 'AA' ]

# code names for all the hands that cannot be split
NON_SPLIT_CODE = HARD_CODE + SOFT_CODE

# code names for standing
STAND_CODE = HARD_CODE + ['21'] + SOFT_CODE
   
# code names for all the y-labels in the strategy table
PLAYER_CODE = HARD_CODE + SPLIT_CODE + SOFT_CODE[1:]

# code names for all the x-labels in all the tables
DEALER_CODE = HARD_CODE + SOFT_CODE[:6]

# code names for all the initial player starting hands
# (hard 4 is always 22, and hard 20 is always TT)
INITIAL_CODE = HARD_CODE[1:-1] + SPLIT_CODE + SOFT_CODE[1:] + ['BJ']

# 
# Returns whether a and b are close enough in floating point value
# Note: use this to debug your code
#
def isclose(a, b=1., rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)  

# use the numeral value 0 to represent a busted hand (makes it easier to
# compare using integer comparison)
BUST = 0

# list of distinct card values
DISTINCT = [ 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T' ]

# number of cards with 10 points
NUM_FACES = 4

# number of ranks in a French deck
NUM_RANKS = 13

# return the probability of receiving this card
def probability(card):
    return (1 if card != 'T' else NUM_FACES) / NUM_RANKS

#
# Represents a Blackjack hand (owned by either player or dealer)
#
# Note: you should make BIG changes to this class
#
class Hand:
    def __init__(self, x, y, dealer=False):
        self.cards = [x, y]
        self.is_dealer = dealer
        #Added by us
        self.value = 0
        self.soft = False
        self.bust = False
        self.can_split = True

    # probability of receiving this hand
    def probability(self):
        p = 1.
        for c in self.cards:
            p *= probability(c)
        return p
  
    # the code which represents this hand
    def code(self, nosplit=False):

        # TODO: implement me
        if self.value == 21 and self.can_split == True:
            return 'BJ'
        elif self.soft and self.value != 21:
            if (self.is_dealer == True and self.value < 18) or self.is_dealer == False:
                return SOFT_CODE[self.value - 12]
        elif self.cards[0] == self.cards[1] and len(self.cards) == 2 and self.is_dealer == False and self.can_split == True:
            return SPLIT_CODE[self.value//2 - 2]
        elif self.value == 0 and self.is_dealer == False:
            return '0'
        
        #All of the possible values
        POSSIBLE_VALUES = HARD_CODE + ['21']
        return POSSIBLE_VALUES[self.value - 4]
    
    # calculates the value of the hand
    def calculate_value(self):
        num_aces = 0
        self.value = 0

        for i in range(len(self.cards)):
            if self.cards[i] == 'A':
                num_aces += 1
            elif self.cards[i] == 'T':
                self.value += 10
            else :
                self.value += int(self.cards[i])
        
        while num_aces > 1:
            self.value += 1
            num_aces -= 1
        
        self.soft = False
        if num_aces == 1 and (self.value + 11 <= 21):
            self.value += 11
            self.soft = True
        elif num_aces == 1:
            self.value += 1
        
        if self.value > 21:
            self.bust = True
            self.value = 0
        
        return
    
    #Adding a card to the hand
    def add_card(self, card):
        self.cards.append(card)
    
    #Removing a card from the hand
    def remove_card(self):
        self.cards.pop()

#
# Singleton class to store all the results. 
#
# Note: you should make HUGE changes to this class
#
class Calculator:
    def __init__(self): 
        self.initprob = Table(float, DEALER_CODE + ['BJ'], INITIAL_CODE, unit='%')
        self.dealprob = defaultdict(dict)
        self.stand_ev = Table(float, DEALER_CODE, STAND_CODE)
        self.hit_ev = Table(float, DEALER_CODE, NON_SPLIT_CODE)
        self.double_ev = Table(float, DEALER_CODE, NON_SPLIT_CODE)
        self.split_ev = Table(float, DEALER_CODE, SPLIT_CODE)
        self.optimal_ev = Table(float, DEALER_CODE, PLAYER_CODE)
        self.strategy = Table(str, DEALER_CODE, PLAYER_CODE)
        self.advantage = 0.
        self.resplit_list = [Table(float, DEALER_CODE, STAND_CODE), 
            Table(float, DEALER_CODE, SPLIT_CODE[:-1]), 
            Table(float, DEALER_CODE, SPLIT_CODE[:-1])] 
    
    # make each cell of the initial probability table      
    def make_initial_cell(self, player, dealer):
        table = self.initprob
        dc = dealer.code()  
        pc = player.code()
        prob = dealer.probability() * player.probability()
        if table[pc,dc] is None:
            table[pc,dc] = prob
        else:
            table[pc,dc] += prob
    
    # make the initial probability table            
    def make_initial_table(self):
        #
        # TODO: refactor so that other table building functions can use it
        #
        for i in DISTINCT:
            for j in DISTINCT:
                for x in DISTINCT:
                    for y in DISTINCT:
                        dealer = Hand(i, j, dealer=True)
                        player = Hand(x, y)
                        dealer.calculate_value()
                        player.calculate_value()
                        self.make_initial_cell(player, dealer)
    
    # verify sum of initial table is close to 1    
    def verify_initial_table(self):
        total = 0.
        for x in self.initprob.xlabels:
            for y in self.initprob.ylabels:
                total += self.initprob[y,x]
        assert(isclose(total))
    
    def make_dealer_tables_sub(self, table_index):  
        #The dealer table for this value is empty
        if not self.dealprob[DEALER_CODE[table_index]]:
            #Initialize the table values
            self.dealprob[DEALER_CODE[table_index]] = {'17':0, '18':0, '19':0, '20':0, '21':0, '0':0}

            #Checks if there is a soft hand, and then creates a hand
            if len(HARD_CODE) <= table_index:
                #First card is ace, second card is the value - 11
                temp_hand = Hand(DISTINCT[0], DISTINCT[int((table_index - len(HARD_CODE)))], False)
            else:
                #First card is half of the value, second card is the remaining value
                temp_hand = Hand(DISTINCT[table_index + 4 - int((table_index + 4)/2)-1], DISTINCT[int((table_index + 4)/2)-1], False)
            temp_hand.calculate_value()
            
            #Looping through all of the possible cards (A-K)
            for card in range(1,14):
                #If the card is J, Q, K consider it as a 10 to reference the card in the distinct list
                if card > 10:
                    card_index = 9
                else:
                    card_index = card - 1

                #Add the new card that we are considering and calculate its value
                temp_hand.add_card(DISTINCT[card_index])
                temp_hand.calculate_value()
                
                #The new hand hand has not busted
                if temp_hand.value < 21 and temp_hand.value != 0:
                    #If it is a soft hand that the dealer can have then get the values for the new hand
                    if temp_hand.soft and temp_hand.value <= 17:
                        temp_dict = self.make_dealer_tables_sub(temp_hand.value + 5)
                    
                    # if temp_hand.code in DEALER_CODE[17:]: #or temp_hand.soft:
                    #     temp_dict = self.make_dealer_tables_sub(temp_hand.value + 5)
                    #If the hand is based on value, then get the index from the distinct list
                    else:
                        temp_dict = self.make_dealer_tables_sub(temp_hand.value - 4)
                    
                    if '17' in temp_dict:
                        self.dealprob[DEALER_CODE[table_index]]['17'] += (1/13)*temp_dict['17']
                    if '18' in temp_dict:
                        self.dealprob[DEALER_CODE[table_index]]['18'] += (1/13)*temp_dict['18']
                    if '19' in temp_dict:    
                        self.dealprob[DEALER_CODE[table_index]]['19'] += (1/13)*temp_dict['19']
                    if '20' in temp_dict:
                        self.dealprob[DEALER_CODE[table_index]]['20'] += (1/13)*temp_dict['20']
                    if '21' in temp_dict:
                        self.dealprob[DEALER_CODE[table_index]]['21'] += (1/13)*temp_dict['21']
                        # self.dealprob[HARD_CODE[table_index]]['0'] += (1/13)*temp_dict['0']
                elif temp_hand.value == 21:
                    self.dealprob[DEALER_CODE[table_index]]['21'] += (1/13)
                # else:
                #     self.dealprob[HARD_CODE[table_index]]['0'] += (1/13)
                temp_hand.remove_card()
                
            # self.dealprob[HARD_CODE[table_index]]['0'] = 0
            self.dealprob[DEALER_CODE[table_index]]['0'] = 1 - sum(self.dealprob[DEALER_CODE[table_index]].values())

        else :
            return self.dealprob[DEALER_CODE[table_index]]
        
    def make_dealer_tables(self):
        #Intialize the dealer tables: 17-20 are initialized to 1 and the rest are empty
        for i in HARD_CODE[13:]:
            self.dealprob[i] = {i:1}

        #Creating the dealer tables: 4-16
        for i in range(12, 2, -1):
            self.make_dealer_tables_sub(i)
        for i in range(len(DEALER_CODE)):
             self.make_dealer_tables_sub(len(DEALER_CODE) - 1 - i)
        return
    
    def make_stand_table_helper(self, player_hand, dealer_hand):
        expected_value = 0.0

        dealer_prob = self.dealprob[dealer_hand]
        for key, prob_value in dealer_prob.items():
            #Obtain the value of the player's hand based on index
            if STAND_CODE.index(player_hand) <= 17:
                player_value = STAND_CODE.index(player_hand) + 4
            else :
                player_value = STAND_CODE.index(player_hand) - 6

            #Obtain the value of the dealer's hand
            dealer_value = int(key)
            # if player's hand is greater, increment EV by +1 * prob(dealer_value)
            if dealer_value == 0:
                expected_value += float(prob_value)
            #if the player's hand score is lower to the dealer's potential hand (17, 18, 19, 20, 21, bust)
            #decrement EV by -1 * prob(dealer_value) 
            elif player_value < dealer_value:
                expected_value -= float(prob_value)
            # if dealer's hand is busted, player wins (increment by +1 * prob(dealer bust))
            elif player_value > dealer_value:
                expected_value += float(prob_value)
            
        return expected_value

    def make_stand_table(self):
        for i in DEALER_CODE:
            for j in STAND_CODE:
                self.stand_ev.__setitem__((j,i), self.make_stand_table_helper(j, i))

    def make_double_table_helper(self, player_hand_str, dealer_hand_str):
        
        expected_value = 0
        #If the hand is hard
        if NON_SPLIT_CODE.index(player_hand_str) < 17:
            player_value = NON_SPLIT_CODE.index(player_hand_str) + 4
            player_hand = Hand(DISTINCT[int(player_value/2) - 1], DISTINCT[int(player_value - int(player_value/2) - 1)], False)
        else:
            player_value = NON_SPLIT_CODE.index(player_hand_str) - 5
            player_hand = Hand(DISTINCT[0], DISTINCT[int(player_value - 11 - 1)], False)
        player_hand.can_split = False
        
        for card in range(1,14):
            #If the card is J, Q, K consider it as a 10 to reference the card in the distinct list
            if card > 10:
                card_index = 9
            else:
                card_index = card - 1

            #Add the new card that we are considering and calculate its value
            player_hand.add_card(DISTINCT[card_index])
            player_hand.calculate_value()

            if player_hand.value != 0:
                expected_value += 2*(1/13)*self.make_stand_table_helper(player_hand.code(), dealer_hand_str)
            else :
                expected_value -= 2*(1/13)
            player_hand.remove_card()

        return expected_value
    
    def make_double_table(self):
        for i in DEALER_CODE:
            for j in NON_SPLIT_CODE:
                self.double_ev.__setitem__((j,i), self.make_double_table_helper(j, i))
    
    def make_hit_table_helper(self, player_hand_str, dealer_hand_str):
        expected_value = 0
        if not self.hit_ev.__getitem__((player_hand_str, dealer_hand_str)):
            if NON_SPLIT_CODE.index(player_hand_str) < 17:
                player_value = NON_SPLIT_CODE.index(player_hand_str) + 4
                player_hand = Hand(DISTINCT[int(player_value/2) - 1], DISTINCT[int(player_value - int(player_value/2) - 1)], False)
            else:
                player_value = NON_SPLIT_CODE.index(player_hand_str) - 5
                player_hand = Hand(DISTINCT[0], DISTINCT[int(player_value - 11 - 1)], False)
            player_hand.can_split = False

            for card in range(1,14):
                #If the card is J, Q, K consider it as a 10 to reference the card in the distinct list
                if card > 10:
                    card_index = 9
                else:
                    card_index = card - 1

                #Add the new card that we are considering and calculate its value
                player_hand.add_card(DISTINCT[card_index])
                player_hand.calculate_value()

                if player_hand.value != 0 and player_hand.value != 21:
                    stand_value = self.make_stand_table_helper(player_hand.code(), dealer_hand_str)
                    hit_value = self.make_hit_table_helper(player_hand.code(), dealer_hand_str)
                    if stand_value >= hit_value:
                        expected_value += (1/13)*stand_value
                    else:
                        expected_value += (1/13)*hit_value
                elif player_hand.value == 21:
                    expected_value += (1/13)*self.make_stand_table_helper(player_hand.code(), dealer_hand_str)
                else :
                    expected_value -= (1/13)
                player_hand.remove_card()
        else:
            return self.hit_ev.__getitem__((player_hand_str, dealer_hand_str))
        return expected_value

    def make_hit_table(self):
        for i in DEALER_CODE:
            for j in NON_SPLIT_CODE[16:3:-1]:
                self.hit_ev.__setitem__((j,i), self.make_hit_table_helper(j, i))
        
        for i in DEALER_CODE:
            for j in reversed(NON_SPLIT_CODE):
                self.hit_ev.__setitem__((j,i), self.make_hit_table_helper(j, i))
        
        # for i in range(16, 2, -1):
        #     self.make_hit_table_helper(i)
        # for i in range(len(NON_SPLIT_CODE)):
        #      self.make_hit_table_helper(len(NON_SPLIT_CODE) - 1 - i)
        return

    def make_split0_table(self):
        for i in DEALER_CODE:
            for j in STAND_CODE:
                if j == '21':
                    max_value = self.stand_ev.__getitem__((j,i))
                else:
                    hit_value = self.hit_ev.__getitem__((j,i))
                    stand_value = self.stand_ev.__getitem__((j,i))
                    double_value = self.double_ev.__getitem__((j,i))
                    list_of_values = [hit_value, stand_value, double_value]
                    max_value = max(list_of_values)

                self.resplit_list[0].__setitem__((j,i), max_value)
        return

    def make_split1_table_helper(self, player_hand_str, dealer_hand_str):
        expected_value = 0
        for card1 in range(1,14):
            if card1 > 10:
                card_index1 = 9
            else:
                card_index1 = card1 - 1

            for card2 in range(1,14):
                #If the card is J, Q, K consider it as a 10 to reference the card in the distinct list
                if card2 > 10:
                    card_index2 = 9
                else:
                    card_index2 = card2 - 1
 
                player_hand1 = Hand(player_hand_str[0], DISTINCT[card_index1], False)
                player_hand2 = Hand(player_hand_str[0], DISTINCT[card_index2], False)
                player_hand1.calculate_value()
                player_hand2.calculate_value()
                player_hand1.can_split = False
                player_hand2.can_split = False
                
                if player_hand1.value != 0 and player_hand2.value != 0:
                    expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))
                        + self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str)))
                elif player_hand1.value != 0:
                    expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))-1/13)
                elif player_hand2.value != 0:
                    expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str))-1/13)
                else:
                    expected_value -= (1/13)*(1/13)

        return expected_value

    def make_split1_table(self):
        for i in DEALER_CODE:
            for j in SPLIT_CODE[:9]:
                self.resplit_list[1].__setitem__((j,i), self.make_split1_table_helper(j,i))

    def make_split2_table_helper(self, player_hand_str, dealer_hand_str):
        expected_value = 0
        for card1 in range(1,14):
            if card1 > 10:
                card_index1 = 9
            else:
                card_index1 = card1 - 1

            for card2 in range(1,14):
                #If the card is J, Q, K consider it as a 10 to reference the card in the distinct list
                if card2 > 10:
                    card_index2 = 9
                else:
                    card_index2 = card2 - 1
 
                player_hand1 = Hand(player_hand_str[0], DISTINCT[card_index1], False)
                player_hand2 = Hand(player_hand_str[0], DISTINCT[card_index2], False)
                player_hand1.calculate_value()
                player_hand2.calculate_value()

                #Case 1: both values do not bust
                if player_hand1.value != 0 and player_hand2.value != 0:
                    #Case 1A: where hand1 is able to split regardless of hand2
                    if player_hand1.code() in SPLIT_CODE:
                        player_hand2.can_split = False
                        expected_value += (1/13)*(1/13)*(self.resplit_list[1].__getitem__((player_hand1.code(), dealer_hand_str))
                        + self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str)))
                    #Case 1B: where hand2 is able to split and hand1 is not
                    elif player_hand2.code() in SPLIT_CODE:
                        player_hand1.can_split = False
                        expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))
                        + self.resplit_list[1].__getitem__((player_hand2.code(), dealer_hand_str)))
                    #Case 1C: where neither can split
                    else:
                        player_hand1.can_split = False
                        player_hand2.can_split = False
                        expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))
                        + self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str)))
                
                #Case 2:hand2 has busted
                elif player_hand1.value != 0:
                    #Case 2A: hand2 can split
                    if player_hand1.code() in SPLIT_CODE:
                        expected_value += (1/13)*(1/13)*(self.resplit_list[1].__getitem__((player_hand1.code(), dealer_hand_str))-1/13)    
                    #Case 2B: hand2 cannot split
                    else:
                        player_hand1.can_split = False
                        expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))-1/13)
                
                #Case 3:hand1 has busted
                elif player_hand2.value != 0:
                    #Case 3A: hand2 can split
                    if player_hand2.code() in SPLIT_CODE:
                        expected_value += (1/13)*(1/13)*(self.resplit_list[1].__getitem__((player_hand2.code(), dealer_hand_str))-1/13)
                    #Case 3B: hand2 cannot split
                    else:
                        player_hand2.can_split = False
                        expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str))-1/13)
                else:
                    expected_value -= (1/13)*(1/13)

        return expected_value

    def make_split2_table(self):
        for i in DEALER_CODE:
            for j in SPLIT_CODE[:9]:
                self.resplit_list[2].__setitem__((j,i), self.make_split2_table_helper(j,i))

    def make_split3_table_helper(self, player_hand_str, dealer_hand_str):
        expected_value = 0
        for card1 in range(1,14):
            if card1 > 10:
                card_index1 = 9
            else:
                card_index1 = card1 - 1

            for card2 in range(1,14):
                #If the card is J, Q, K consider it as a 10 to reference the card in the distinct list
                if card2 > 10:
                    card_index2 = 9
                else:
                    card_index2 = card2 - 1
 
                player_hand1 = Hand(player_hand_str[0], DISTINCT[card_index1], False)
                player_hand2 = Hand(player_hand_str[0], DISTINCT[card_index2], False)
                player_hand1.calculate_value()
                player_hand2.calculate_value()

                if player_hand_str[0] == 'A':
                    player_hand1.can_split = False
                    player_hand2.can_split = False
                    expected_value += (1/13)*(1/13)*(self.stand_ev.__getitem__((player_hand1.code(), dealer_hand_str))
                        + self.stand_ev.__getitem__((player_hand2.code(), dealer_hand_str)))
                else:
                    #Case 1: both values do not bust
                    if player_hand1.value != 0 and player_hand2.value != 0:
                        #Case 1A: both hands can be split
                        if player_hand1.code() in SPLIT_CODE and player_hand2.code() in SPLIT_CODE:
                            expected_value += (1/13)*(1/13)*(self.resplit_list[1].__getitem__((player_hand1.code(), dealer_hand_str))
                            + self.resplit_list[1].__getitem__((player_hand2.code(), dealer_hand_str)))
                            
                        #Case 1B: where hand1 is able to split and hand2 is not
                        elif player_hand1.code() in SPLIT_CODE:
                            player_hand2.can_split = False
                            expected_value += (1/13)*(1/13)*(self.resplit_list[2].__getitem__((player_hand1.code(), dealer_hand_str))
                            + self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str)))
                        #Case 1C: where hand2 is able to split and hand1 is not
                        elif player_hand2.code() in SPLIT_CODE:
                            player_hand1.can_split = False
                            expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))
                            + self.resplit_list[2].__getitem__((player_hand2.code(), dealer_hand_str)))
                        #Case 1D: where neither can split
                        else:
                            player_hand1.can_split = False
                            player_hand2.can_split = False
                            expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))
                            + self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str)))
                    
                    #Case 2:hand2 has busted
                    elif player_hand1.value != 0:
                        #Case 2A: hand2 can split
                        if player_hand1.code() in SPLIT_CODE:
                            expected_value += (1/13)*(1/13)*(self.resplit_list[2].__getitem__((player_hand1.code(), dealer_hand_str))-1/13)    
                        #Case 2B: hand2 cannot split
                        else:
                            player_hand1.can_split = False
                            expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand1.code(), dealer_hand_str))-1/13)
                    
                    #Case 3:hand1 has busted
                    elif player_hand2.value != 0:
                        #Case 3A: hand2 can split
                        if player_hand2.code() in SPLIT_CODE:
                            expected_value += (1/13)*(1/13)*(self.resplit_list[2].__getitem__((player_hand2.code(), dealer_hand_str))-1/13)
                        #Case 3B: hand2 cannot split
                        else:
                            player_hand2.can_split = False
                            expected_value += (1/13)*(1/13)*(self.resplit_list[0].__getitem__((player_hand2.code(), dealer_hand_str))-1/13)
                    else:
                        expected_value -= (1/13)*(1/13)

        return expected_value

    def make_split3_table(self):
        for i in DEALER_CODE:
            for j in SPLIT_CODE:
                self.split_ev.__setitem__((j,i), self.make_split3_table_helper(j,i))

    def make_optimal_table(self):
        for i in DEALER_CODE:
            for j in PLAYER_CODE:
                f = j
                if j in self.split_ev.ylabels and i in self.split_ev.xlabels:
                    split_ev = self.split_ev.__getitem__((j,i))
                else:
                    split_ev = -1*float('inf')
                
                if j in SPLIT_CODE:
                    temp_hand = Hand(j[0], j[1], False)
                    temp_hand.calculate_value()
                    temp_hand.can_split = False
                    j = temp_hand.code()
                    
                if j in self.stand_ev.ylabels and i in self.stand_ev.xlabels:
                    stand_ev = self.stand_ev.__getitem__((j,i))
                else:
                    stand_ev = -1*float('inf')
                if j in self.hit_ev.ylabels and i in self.hit_ev.xlabels:
                    hit_ev = self.hit_ev.__getitem__((j,i))
                else:
                    hit_ev = -1*float('inf')
                if j in self.double_ev.ylabels and i in self.double_ev.xlabels:
                    double_ev = self.double_ev.__getitem__((j,i))
                else:
                    double_ev = -1*float('inf')
                
                surrender_ev = -0.5
                ev_list = [stand_ev, hit_ev, double_ev, split_ev, surrender_ev]
                max_ev = max(ev_list)
                self.optimal_ev.__setitem__((f,i), max_ev)

                max_ev_id = ev_list.index(max_ev)

                if max_ev_id == 0:
                    move = 'S'
                elif max_ev_id == 1:
                    move = 'H'    
                elif max_ev_id == 2:
                    move = "D"
                    if ev_list[0] < ev_list[1]:
                        move += "h"
                    else:
                        move += "s"
                elif max_ev_id == 3:
                    move = 'P'
                elif max_ev_id == 4:
                    move = "R"
                    if ev_list[0] < ev_list[1]:
                        move += "h"
                    else:
                        move += "s"
                self.strategy.__setitem__((f,i), move)

    def calculate_advantage(self):
        for i in self.initprob.xlabels:
            for j in self.initprob.ylabels:
                if i == 'BJ' and j == 'BJ':
                    self.advantage += 0
                elif i == 'BJ' and j != 'BJ':
                    self.advantage -= self.initprob.__getitem__((j,i))
                elif j == 'BJ' and i != 'BJ':
                    self.advantage += self.initprob.__getitem__((j,i))*1.5
                else:
                    self.advantage += self.initprob.__getitem__((j,i))*self.optimal_ev.__getitem__((j,i))
           
# Calculate all the ev tables and the final strategy table and return them
# all in a dictionary
#      
def calculate():
    calc = Calculator()   
    
    calc.make_initial_table()
    
    # TODO: uncomment once you finished your table implementation
    #       and Hand.code implementation
    calc.verify_initial_table()
    
    # TODO: calculate all other tables and numbers
    calc.make_dealer_tables()
    calc.make_stand_table()
    calc.make_double_table()
    calc.make_hit_table()
    calc.make_split0_table()
    calc.make_split1_table()
    calc.make_split2_table()
    calc.make_split3_table()
    calc.make_optimal_table()
    calc.calculate_advantage()
    
    
    return {
        'initial' : calc.initprob,
        'dealer' : calc.dealprob,
        'stand' : calc.stand_ev,
        'hit' : calc.hit_ev,
        'double' : calc.double_ev,
        'split' : calc.split_ev,
        'optimal' : calc.optimal_ev,
        'strategy' : calc.strategy,
        'advantage' : calc.advantage,
        'resplit' : calc.resplit_list,
    }

