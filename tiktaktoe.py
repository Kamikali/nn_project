import numpy as np
from enum import Enum
import torch
import torch.nn as nn
import random

class PlayerNr(Enum):
    """
    Define an enumeration for player numbers bound to more reasonable names.
    """

    X = 1
    O = -1


class Player():
    """
    Represents a player in the game. 
    There are always exactly two players, Player X and 0 required for a game to launch.

    Attributes:

        fields_taken:
            Fields in the TikTakToe matrix picked by the corresponding player.

        player_nr:
            An identifier whether a player is playing as X or O.

    Methods:
        take_field:
        Takes a given field in the game matrix if it is free.
    """

    def __init__(self) -> None:
        self.fields_taken = list()
        self.player_nr = None

    def take_field(self, game, field) -> bool:
        """
        Makes a move in a given game

        Parameters:
            game:
                A game object of TikTakToe

            field:
                The field a player is trying to occupy with his move.
        """
        if field not in range(0, 9):
            raise Exception("Only fields 0 to 8 exist.")
        game.occupy_field(self, self.player_nr, field)

class InputPlayer(Player):

    """
    A player that asks for user input every turn.
    """

    def take_field(self, game) -> bool:
        """
        Makes a random legal move in a given game

        Parameters:
            game:
                A game object of TikTakToe
        """

        
        field = int(input("Take a field, 0 - 8: "))

        while field not in range(0, 9):
            field = int(input("Wrong input. Take a field, 0 - 8: "))
        game.occupy_field(self, self.player_nr, field)


class NNPlayer(Player):

    """
    A player that uses a NN to make a decision.
    """

    def __init__(self, model) -> None:
        super().__init__()
        self.model = model  

    def get_best_action(self,model_output, available_fields):
        model_output = model_output.squeeze(0)  

        # Create a mask filled with negative infinity
        mask = torch.full_like(model_output, float('-inf'))  # Shape should match model_output
        
        mask[available_fields] = model_output[available_fields]  

        # Get the index of the maximum value in the masked output
        best_action = torch.argmax(mask)
        
        return best_action

    def take_field(self, game, moves_made=list(), epsilon=0.0) -> bool:
        """
        Makes a random legal move in a given game

        Parameters:
            game:
                A game object of TikTakToe
        """
        input = game.get_nn_input(self.player_nr)
        input = input.unsqueeze(0)
        
        output = self.model(input)
        
        available_fields = game.get_available_fields() # returns a list with available fields
        
        best_action = self.get_best_action(output, available_fields)

        # chance epsilon
        if epsilon > random.random():
            best_action = random.choice(available_fields)

        moves_made.append((self.player_nr, input, best_action))
        game.occupy_field(self, self.player_nr, best_action)



##############################################################################
# I USED CHATGPT TO HAVE THE PYTORCH BOILERPLATE CODE BELOW FOR A NN CREATED #
##############################################################################

# from there i modified it manually 

class NN(nn.Module):
    def __init__(self):
        super(NN, self).__init__()
        
        # Define the layers
        self.flatten = nn.Flatten()  # 3x9 tensor needs to be flattened
        self.fc1 = nn.Linear(27, 216) 
        self.fc2 = nn.Linear(216, 108)  
        self.fc3 = nn.Linear(108, 54)  
        self.fc4 = nn.Linear(54, 9)  
        
        # Activation function 
        self.relu = nn.ReLU()

    def forward(self, x):
        # Forward pass through the network
        x = self.flatten(x)  # Flatten input (if necessary)
        x = self.relu(self.fc1(x)) 
        x = self.relu(self.fc2(x))  
        x = self.relu(self.fc3(x)) 
        x = self.fc4(x)  
        return x


class QPlayer(Player):

    """
    A player that relies on a qtable to make a decision.
    """

    def __init__(self, qtable: dict, epsilon) -> None:
        super().__init__()
        self.qtable = qtable
        self.epsilon = epsilon

    def take_field(self, game, game_log, change_epsilon=True):
        """
        Parameters:
            game:
                A game object of TikTakToe
            qtable:
                A qtable the player uses to make a decision.
        """


        available_fields = game.get_available_fields() # returns a list with available fields

        if game.get_qtable_entry(self.player_nr) not in self.qtable:
            self.qtable[game.get_qtable_entry(self.player_nr)] = [(field, 0.0) for field in available_fields] # initiates list of tuples with (field, qvalue=0)
            #self.qtable[game.get_qtable_entry(self.player_nr)] = [(field, 0.0) for field in available_fields] # initiates list of tuples with (field, qvalue=0)
            field = random.choice(self.qtable[game.get_qtable_entry(self.player_nr)])[0]
        
        if random.random() < self.epsilon and change_epsilon:
            field = random.choice(self.qtable[game.get_qtable_entry(self.player_nr)])[0]
        else:
            state_values = self.qtable[game.get_qtable_entry(self.player_nr)]
            max_value = max(state_values, key=lambda item: item[1])
            max_values = [item for item in state_values if item[1] == max_value[1]]
            field = random.choice(max_values)[0]

        game_log.append((self.player_nr, game.get_qtable_entry(self.player_nr), field))
        #game_log.append((self.player_nr, {game.get_qtable_entry(self.player_nr): field}))


        game.occupy_field(self, self.player_nr, field)


class RandomPlayer(Player):

    """
    A player which will always take a random free field on the game matrix.
    """

    def take_field(self, game) -> bool:
        """
        Makes a random legal move in a given game

        Parameters:
            game:
                A game object of TikTakToe
        """

        import random
        field = random.randint(0, 8)

        taken_fields = []
        for field in game.player_x.fields_taken:
            taken_fields.append(field)
        for field in game.player_o.fields_taken:
            taken_fields.append(field)

        while field in taken_fields:
            field = random.randint(0, 8)

        if field not in range(0, 9):
            raise Exception("Only fields 0 to 8 exist.")
        game.occupy_field(self, self.player_nr, field)


class TikTakToe():

    """
    Class that hosts a TikTakToe game.
    Each instantiation of the class is a playble game of player O against player X.

    We encode our 3x3 TikTakToe game matrix as following:
    Empty fields = 0
    Fields chosen by player X = 1
    Fields chosen by player O = 2

    Parameters:
        player_x: a reference to the first player
        player_o: a ference to the second player
        player_turn: Of type PlayerNr. Holds which player can make the next move.
        is_ongoing: boolean whether a game is finished or not
        game_log: list, contains moves made by QPlayers in this form: (player_nr, state, action)


    Methods:
        check_for_win: 
        checks whether a player has won

        print: 
        prettyprints the game matrix

        occupy_field:
        Is called when a player is trying to make a move to take a field in the game matrix.

        reset:
        resets a game into beginning state
    """

    def __init__(self, starting_player_x: Player, second_player_o: Player):
        """
        Creates a game.

        Parameters:
            starting_player_x:
            The first player, using X in the game matrix, represented by a 0.

            second_player_o:
            The second player, using O in the game matrix, represented by a 1.

            player_turn: 
            Stores whose players turn it currently is. Starting with player X.

            #game_matrix:
            #A 3x3 matrix that is used to print the game state for humans.

            is_onging:
            True as long as there is no winner yet or not all nine 
            fields are in the game matrix taken.

            result:
            A string to store a game's end result.
            Possible values are "x_win", "o_win", "draw" and "error".

        """

        if len(starting_player_x.fields_taken) > 0 or len(second_player_o.fields_taken) > 0:
            raise Exception('A given player already has taken fields. Use player.clean_fields.')


        self.player_x = starting_player_x
        self.player_x.player_nr = PlayerNr.X

        self.player_o = second_player_o
        self.player_o.player_nr = PlayerNr.O

        self.player_turn = PlayerNr.X   # player X starts the game

        self.is_ongoing = True
        self.result = None # will be set after game has ended

        self.game_log = list()

    def reset(self):
        self.player_x.fields_taken = list()
        self.player_o.fields_taken = list()
        self.player_turn = PlayerNr.X
        self.is_ongoing = True
        self.game_log = list()

    def get_game_matrix(self) -> list:
        
        game_matrix = [0 for _ in range(3 * 3)] # storing game states as a list

        for field in self.player_x.fields_taken:
            game_matrix[field] = 1
        for field in self.player_o.fields_taken:
            game_matrix[field] = -1

        return game_matrix

    def print(self, raw=False):
        """
        Prettyprints the game matrix, readable for humans.

        # TODO actually pretty print it

        Paramters:
            raw:
                If set to true, print the game_matrix as its original list form.
        """

        game_matrix = self.get_game_matrix()

        if raw:
            print(game_matrix)
        else:
            pretty_matrix = [0 for _ in range(3 * 3)] # using the nice numpy 2d matrix feature here because it prints nicely

            for index, field in enumerate(game_matrix):
                if field == 0:
                    pretty_matrix[index] = '-'
                if field == PlayerNr.X.value:
                    pretty_matrix[index] = 'X'
                if field == PlayerNr.O.value:
                    pretty_matrix[index] = 'O'

            pretty_matrix = np.char.array(pretty_matrix)
            print(pretty_matrix.reshape((3, 3)))

    def get_qtable_entry(self, pov: PlayerNr) -> str:
        
        """
        pov: Used to make the qtables look same for both players, self is x, opponent is o
        """

        qtable_entry = ''
        for field in self.get_game_matrix(): # returns [1, 0, -1, 1, -1, 0, 1, 1, -1]
            if field == 0: 
                qtable_entry += '-'
            if field == pov.value:
                qtable_entry += 'x'
            elif field != 0 and field != pov.value:
                qtable_entry += 'o'

        return qtable_entry
    

    def get_nn_input(self, pov):
        
        input_string = self.get_qtable_entry(pov=pov) # we are using our qtable entry generator here

        # Define the mappings
        mapping = {
            'x': [1, 0, 0],  
            '-': [0, 1, 0], 
            'o': [0, 0, 1]   
        }
        
        if len(input_string) != 9:
            raise ValueError("Input string must have exactly 9 characters.")
        
        tensor_data = [mapping[char] for char in input_string]
        
        tensor = torch.tensor(tensor_data, dtype=torch.float32).reshape(9, 3)
        
        return tensor

    def get_state(self) -> str:
        return str(self.get_game_matrix())
    
    def is_occupied(self, field) -> bool:
        return field in self.player_o.fields_taken or field in self.player_x.fields_taken
    
    def get_available_fields(self):
        available_fields = list()
        for i in range(0, 9):
            if not self.is_occupied(i):
                available_fields.append(i)
        return available_fields

    def occupy_field(self, player: Player, player_nr: PlayerNr, field) -> bool:
        
        # check if player can make a move
        if player_nr != self.player_turn:
            raise Exception(f"It is not this players turn yet. Player: {player.player_nr}")
    
        
        # check if field can be occupied by player
        if field in self.player_o.fields_taken or field in self.player_x.fields_taken:
            raise Exception(f"You are trying to take an occupied field!")
        
        # change turn
        if self.player_turn == PlayerNr.X:
            self.player_turn = PlayerNr.O
        else:
            self.player_turn = PlayerNr.X

        # add field to taken fields
        player.fields_taken.append(field)
        
        # check for win
        if self.check_for_win(player):
            #print(f"Player {player.player_nr} has won the game!")

            if player.player_nr == PlayerNr.X:
                self.result = 'x_win'
            elif player.player_nr == PlayerNr.O:
                self.result = 'o_win'
            else:
                self.result = 'error'
            self.is_ongoing = False
        elif self.check_for_draw():
            #print("Draw! All fields are taken.")
            self.result = 'draw'
            self.is_ongoing = False

        return True

    def check_for_draw(self):
        if len(self.player_x.fields_taken) + len(self.player_o.fields_taken) >= 9:
            return True
        return False

    def check_for_win(self, player: Player) -> bool:
        """
        Has to be called to verify gamne state after every move made by each player.
        Checks, whether a player has won a game of TikTakToe.

        Attributes:
            win_states:
            valid combinations of moves placed on the game matrix that lead to victory.
        """

        win_states = [
            [0, 1, 2], # rows
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6], # cols
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8], # diagonals
            [2, 4, 6],
        ] 

        for win_state in win_states:       # iterate through win conditions
            if win_state[0] in player.fields_taken and win_state[1] in player.fields_taken and win_state[2] in player.fields_taken:
                return True
            
        return False
