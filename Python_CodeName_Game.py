#**********************************************************************************************************************
#  Copyright (c) 2019 by Mark Kastelic
#**********************************************************************************************************************
'''
Implementation Notes
---------------------------------------
Hardware:  Game play requires the use of a device with internet connection and web browser.

Software:  Game play requires FTP access to a modifiable web page on the internet.
'''


import copy
from ftplib import FTP
import itertools
import numpy as np
import os
from os import startfile
import PIL.Image
import random
from time import time
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import winsound

class Board:
    '''
    Board class creates the game GUI with a 5x5 layout of cardstock on which words are overlaid.  Each word card is a button which can
    be accessed by an array.
    '''
    def __init__(self, master_window, word_array):
        '''
        Initialize Board object using word_array to create a 5x5 array of active buttons labeled with codewords in a new frame of
        the root window.
        :param master_window:
        :param word_array:
        '''
        self.word_array = word_array
        self.button_identities = []

        #  Create the window within the root which will contain the 5x5 array of codewords.
        frame1 = ttk.Frame(master_window)
        frame1.grid(row=0,column=1)
        frame1.config(height=600, width=400, relief=RIDGE)
        #  Resize font and spacing of codewords based on current screen size being used.
        font_size = round((width_resize + height_resize)/2.0*28)
        padx_size = int(width_resize*10)
        pady_size = round(height_resize*10)

        #  Create individual buttons for each codeword in the word_array passed in and store their identities in a list.
        #  Assign a unique command to each button based on its row and column position.
        for i in range(2,7):
            for j in range(5):
                btn = Button(frame1,text = word_array[0,i-2,j],
                           command=lambda row=i-2, col=j: self.click(frame1,frame,row,col,self.word_array))
                btn.grid(row=i, column=j, padx=padx_size, pady=pady_size)
                btn.img=Cards['CodeName_Card']
                btn.config(image=btn.img)
                btn.config(compound='center')
                btn.config(font=('courier', font_size, 'bold'))
                self.button_identities.append(btn)

        #  Arrange the list of button_identities into a 5x5 array to correspond to the codename word_array.
        self.button_identities = np.array(self.button_identities)
        self.button_identities.shape = 5,5
        
    #
    def Update_Board(self,master_window,word_array):
        '''
        Method for setting the word_array of an active game board.
        :param master_window:
        :param word_array:
        :return:
        '''
        self.word_array = word_array

    def Current_Board(self,master_window):
        '''
        Method for getting the current word_array of an active game board.
        :param master_window:
        :return: self.word_array
        '''
        return self.word_array    

    def click(self, master_window,submaster,row,col,word_array):
        '''
        When a word is clicked, logic is invoked to process the outcome of revealing the contact based on the current team color in play.
        :param master_window:
        :param submaster:
        :param row:
        :param col:
        :param word_array:
        :return:
        '''
        font_size = round((width_resize + height_resize)/2*18)
        
        #  If the game is not paused and it is not the spymaster's turn in "Split" time mode then allow operatives to make contacts.
        if game.pause and not game.master:
            #  A zero at any word_array[2,row,col] means the agent at that codename has not yet been contacted.
            if int(word_array[2,row,col]) == 0:
                choice = messagebox.askokcancel("Confirm Selection",
                                   "Click OK to confirm that {} is the correct word choice".format(word_array[0,row,col]))
            else:
                messagebox.showerror(message='Contact has been revealed and cannot be selected again.')
                choice = False
        elif not game.pause:
            messagebox.showerror(message='Word selections cannot be made when game is paused.')
            choice = False
        else:
            messagebox.showerror(message='Word selections can only be made by operatives.')
            choice = False
        if choice:
            bname = (self.button_identities[row,col])
            bname.config(text='')
            #  After a team confirms codename selection, if it belongs to the Assassin, the opposing team wins (increment score)
            #  and a video of a spy assassination plays.
            if word_array[1,row,col] == 'Assassin':
                bname.img=Cards['Assassin']
                bname.config(image=bname.img)
                if game.team == 'Blue':
                    game.red_score += 1
                    Label(frame, text=str(game.red_score), foreground='red', font=('Courier',font_size, 'bold')).grid(row=9,column=2)
                else:
                    game.blue_score += 1
                    Label(frame, text=str(game.blue_score), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=9,column=1)
                winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                #startfile(Assets_dir + 'MovieClips\\SALT Assassination1.mp4')
                startfile(Assets_dir + str(movie_files[-1]))
                movie_files.pop()
                #  Game is paused and the board is cleared from the browser.  Players can then choose to start a new game.
                game.Pause_Resume()
                BlankHTML()
                choice = messagebox.showerror(message='Game Over:  {} Team Was Assassinated.  Click to start new game.'.format(game.team))
                if choice:
                    game.New_Game()
            #  After a team confirms codename selection, if it belongs to a Bystander, that team's turn ends.
            elif word_array[1,row,col] == 'Yellow':
                bname.img=random.choice([Cards['Bystander_Guy'], Cards['Bystander_Girl']])
                bname.config(image=bname.img)
                word_array[2,row,col] = 1
                game.Next_Turn()
            else:
                #  After a team confirms codename selection, if it belongs to a Red agent, the Red team is credited with a contact made.
                if word_array[1,row,col] == 'Red':
                    bname.img=random.choice([Cards['Red_Spy_Guy'], Cards['Red_Spy_Girl']])
                    bname.config(image=bname.img)
                    word_array[2,row,col] = 1
                    game.red_contacts -= 1
                    Label(submaster, text=str(game.red_contacts), foreground='red', font=('Courier',font_size, 'bold')).grid(row=2,column=2)
                    #  If the Red team has made contact and the Blue team has a double agent assigned, then Blue team is also credited.
                    if word_array[0,row,col] == game.blue_da_codename and game.team == 'Red':
                        game.blue_contacts -= 1
                        Label(submaster, text=str(game.blue_contacts), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=2,column=1)
                    #  Game ends in a tie if both team's contacts simultaneously reach zero.  Game is paused and board is cleared from browser.
                    if game.red_contacts == 0 and game.blue_contacts == 0:
                        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                        game.Pause_Resume()
                        BlankHTML()
                        choice = messagebox.showerror(message='Game Over:  It\' a tie.  Click to start new game.')
                        if choice:
                            game.New_Game()
                    #  If only Red team's contacts reach zero, Red team wins.  Game is paused and board is cleared from browser.
                    elif game.red_contacts == 0:
                        game.red_score += 1
                        Label(frame, text=str(game.red_score), foreground='red', font=('Courier',font_size, 'bold')).grid(row=9,column=2)
                        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                        game.Pause_Resume()
                        BlankHTML()
                        choice = messagebox.showerror(message='Game Over:  Red Team Has Won.  Click to start new game.')
                        if choice:
                            game.New_Game()
                    #  If only Blue team's contacts reach zero, Blue team wins.  Game is paused and board is cleared from browser.
                    elif game.blue_contacts == 0:
                        game.blue_score += 1
                        Label(frame, text=str(game.blue_score), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=9,column=1)
                        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                        game.Pause_Resume()
                        BlankHTML()
                        choice = messagebox.showerror(message='Game Over:  Blue Team Has Won.  Click to start new game.')
                        if choice:
                            game.New_Game()
                    #  If the Blue team made contact with the Red agent, it now becomes Red's turn.
                    if game.team == 'Blue':
                        game.Next_Turn()
                #  If the agent contacted is instead a Blue agent, Blue team is credited with the contact.
                else:
                    bname.img=random.choice([Cards['Blue_Spy_Guy'], Cards['Blue_Spy_Girl']])
                    bname.config(image=bname.img)
                    word_array[2,row,col] = 1
                    game.blue_contacts -= 1
                    Label(submaster, text=str(game.blue_contacts), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=2,column=1)
                    #  If the Blue team has made contact and the Red team has a double agent assigned, then Red team is also credited.
                    if word_array[0,row,col] == game.red_da_codename and game.team == 'Blue':
                        game.red_contacts -= 1
                        Label(submaster, text=str(game.red_contacts), foreground='red', font=('Courier',font_size, 'bold')).grid(row=2,column=2)
                    #  Game ends in a tie if both team's contacts simultaneously reach zero.  Game is paused and board is cleared from browser.
                    if game.red_contacts == 0 and game.blue_contacts == 0:
                        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                        game.Pause_Resume()
                        BlankHTML()
                        choice = messagebox.showerror(message='Game Over:  It\' a tie.  Click to start new game.')
                        if choice:
                            game.New_Game()
                    #  If only Blue team's contacts reach zero, Blue team wins.  Game is paused and board is cleared from browser.
                    if game.blue_contacts == 0:
                        game.blue_score += 1
                        Label(frame, text=str(game.blue_score), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=9,column=1)
                        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                        game.Pause_Resume()
                        BlankHTML()
                        choice = messagebox.showerror(message='Game Over:  Blue Team Has Won.  Click to start new game.')
                        if choice:
                            game.New_Game()
                    #  If only Red team's contacts reach zero, Red team wins.  Game is paused and board is cleared from browser.
                    elif game.red_contacts == 0:
                        game.red_score += 1
                        Label(frame, text=str(game.red_score), foreground='red', font=('Courier',font_size, 'bold')).grid(row=9,column=2)
                        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
                        game.Pause_Resume()
                        BlankHTML()
                        choice = messagebox.showerror(message='Game Over:  Red Team Has Won.  Click to start new game.')
                        if choice:
                            game.New_Game()
                    #  If the Red team made contact with the Blue agent, it now becomes Blue's turn.
                    if game.team == 'Red':
                        game.Next_Turn()


    def DA(self):
        '''
         Allows Spymaster to select one of his opponent's uncontacted agents as a Double Agent.  If on the next turn, the opposing team
        makes contact with this agent, contact points are given to both teams.
        :return:
        '''

        def da_enter_pressed_blue(event):
            gui.Spy_Check(da_setup_window, 'blue', use_board, True)

        def da_enter_pressed_red(event):
            gui.Spy_Check(da_setup_window, 'red', use_board, True)


        da_setup_window = Toplevel()
        #  Setup text entry fields depending on the team in play and confirm the team has double agents to use.
        if game.team == 'Blue' and game.blue_da:
            tc = 'red'
            #team_col = 1                                          # used to specify column of display status for red team
            self.red_entry = ttk.Entry(da_setup_window, width=10)
            self.red_entry.bind("<Return>", da_enter_pressed_red)
            self.red_entry.config(show=' ')
            self.red_entry.grid(row=18, column=1)
        elif game.team == 'Red' and game.red_da:
            tc = 'blue'
            #team_col = 0                                           #  used to specify column of display status for blue team
            self.blue_entry = ttk.Entry(da_setup_window, width=10)
            self.blue_entry.bind("<Return>", da_enter_pressed_blue)
            self.blue_entry.config(show=' ')
            self.blue_entry.grid(row=18, column=1)
        else:
            messagebox.showerror(message='{} Team does not have any double agents left to insert'.format(game.team))
            return

        self.blue_check = False         #  set to True only if the Blue agent selected as a double agent is found on the board and available.
        self.red_check = False          #  set to True only if the Red agent selected as a double agent is found on the board and available.
        da_setup_window.geometry('650x210+600+400')
        Label(da_setup_window, text='Enter double agent\'s insertion code word.', font=('Courier', 18)).grid(row=3, column=0, columnspan=2)
        Label(da_setup_window, text=tc.capitalize(), foreground=tc, font=('Courier', 18, 'bold')).grid(row=5, column=1)

        #  Get the status of the current game board and the initial game board and convert each to lists and compare for changes.
        current_board = self.Current_Board(root)
        cboard = current_board.tolist()
        iboard = game.initial_board.tolist()
        if cboard == iboard:
            use_board = iboard
        else:
            use_board = cboard

        #button1 = ttk.Button(da_setup_window, text='Check', style='my.TButton',
        #                     command=lambda: self.Spy_Check(da_setup_window, tc, use_board)).grid(row=18, column=0, pady=10)
        button3 = ttk.Button(da_setup_window, text='Proceed', style='my.TButton',
                             command=lambda: self.DA_Proceed(da_setup_window, use_board)).grid(row=19, column=0, pady=25)
        button4 = ttk.Button(da_setup_window, text='Cancel', style='my.TButton', command=lambda: self.DA_Cancel(da_setup_window)).grid(row=19, column=1, pady=25)
        da_setup_window.mainloop()

    def DA_Proceed(self, window, c_or_iboard):
        '''
        Once all entries are made to select a Double Agent and verified to be correct, acknowledgement is issued and window closed.
        :param window:
        :param c_or_iboard:
        :return:
        '''

        #  If the spy check for an available red agent passes, then decrement the Blue team's remaining double agents
        #  and indicate successful agent insertion (only 1 insertion allowed per turn).
        if game.team == 'Blue' and self.red_check:
            window.destroy()
            game.blue_da -= 1
            Label(frame, text='{0:1d}'.format(game.blue_da), foreground='blue', font=('Courier', font_size, 'bold'),
                  justify=RIGHT).grid(row=7, column=1, padx=5, pady=5)
            game.double_agent_btn.state(['disabled'])
            messagebox.showinfo(message='Double agent has been inserted.  No need to update browsers.')
        #  If the spy check for an available blue agent passes, then decrement the Red team's remaining double agents
        #  and indicate successful agent insertion (only 1 insertion allowed per turn).
        elif game.team == 'Red' and self.blue_check:
            window.destroy()
            game.red_da -= 1
            Label(frame, text='{0:1d}'.format(game.red_da), foreground='red', font=('Courier', font_size, 'bold'),
                  justify=RIGHT).grid(row=7, column=2, padx=5, pady=5)
            game.double_agent_btn.state(['disabled'])
            messagebox.showinfo(message='Double agent has been inserted.  No need to update browsers.')
        else:
            okay = messagebox.showerror(message='Double agent has not been successfully identified.')
            if okay:
                window.lift(root)

    def DA_Cancel(self, window):
        '''
        Abort the double agent assignment process.
        :param window:
        :return:
        '''
        window.destroy()
        game.blue_da_codename = None
        game.red_da_codename = None

    def Swap(self):

        '''
        Allows Spymaster to exchange one of his/her agent's codename with one of the opponent's.  Typed codename entries for each team's
        agents are checked for accuracy and availability.  Entries are displayed as a series of asterisks to cover identity, and a random
        number of asterisks can be added by players to further disquise the true length of the codename.
        :return:
        '''

        def on_enter_pressed_blue(event):
            gui.Spy_Check(swap_setup_window, 'blue', use_board, False)

        def on_enter_pressed_red(event):
            gui.Spy_Check(swap_setup_window, 'red', use_board, False)

        self.blue_check = False                         #  set to True only if the Blue agent selected as a double agent is found on the board and available.
        self.red_check = False                          #  set to True only if the Red agent selected as a double agent is found on the board and available.

        swap_setup_window = Toplevel()
        swap_setup_window.geometry('750x180+600+400')
        Label(swap_setup_window, text='Enter code words to use in spy swap:', font=('Courier', 18)).grid(row=3, column=0)

        #  Set up text entry fields to allow both blue and red agents to be selected for a potential spy swap.
        self.blue_entry = ttk.Entry(swap_setup_window, width=10)
        self.blue_entry.bind("<Return>", on_enter_pressed_blue)
        self.blue_entry.config(show=' ')
        self.blue_entry.grid(row=4, column=0)
        Label(swap_setup_window, text='Blue', foreground='blue', font=('Courier', 18, 'bold')).grid(row=5, column=0)
        self.red_entry = ttk.Entry(swap_setup_window, width=10)
        self.red_entry.bind("<Return>", on_enter_pressed_red)
        self.red_entry.config(show=' ')
        self.red_entry.grid(row=4, column=1)
        Label(swap_setup_window, text='Red', foreground='red', font=('Courier', 18, 'bold')).grid(row=5, column=1)
        #  Get the status of the current game board and the initial game board and convert each to lists and compare for changes.
        current_board = self.Current_Board(root)
        cboard = current_board.tolist()
        iboard = game.initial_board.tolist()
        if cboard == iboard:
            use_board = iboard
        else:
            use_board = cboard
        #  Create buttons for spymasters to check their typed entries and proceed with spy swap or cancel the process.
        '''
        button1 = ttk.Button(swap_setup_window, text='Check',
                             command=lambda: self.Spy_Check(swap_setup_window, 'blue', use_board)).grid(row=18, column=0,
                                                                                                   pady=10)
        button2 = ttk.Button(swap_setup_window, text='Check',
                             command=lambda: self.Spy_Check(swap_setup_window, 'red', use_board)).grid(row=18, column=1,
                                                                                                  pady=10)
        '''

        button3 = ttk.Button(swap_setup_window, text='Proceed', style='my.TButton',
                             command=lambda: self.Spy_Swap_Proceed(swap_setup_window, use_board)).grid(row=19, column=0,pady=25)
        button4 = ttk.Button(swap_setup_window, text='Cancel', style='my.TButton',
                            command=lambda: swap_setup_window.destroy()).grid(row=19,column=1,pady=25)

        swap_setup_window.mainloop()

    def Spy_Swap_Proceed(self, window, c_or_iboard):
        '''
        Once all entries are correctly made to begin a Spy Swap, a button is clicked to execute the transaction at which time the game board state
        information is updated.
        :param window:
        :param c_or_iboard:
        :return:
        '''
        #  If the spy check for both an available blue and red agent passes, then for the team making the swap, decrement their remaining double agents.
        #  Indicate that a successful agent swap has been made (only 1 insertion allowed per turn) and remind spymasters to update browsers.
        if self.blue_check == True and self.red_check == True:
            window.destroy()
            if game.team == 'Blue':
                game.blue_swaps -= 1
                Label(frame, text='{0:1d}'.format(game.blue_swaps), foreground='blue', font=('Courier', font_size, 'bold'),
                      justify=RIGHT).grid(row=6, column=1, padx=5, pady=5)
                if game.blue_swaps == 0:
                    game.spy_swap_btn.state(['disabled'])
            else:
                game.red_swaps -= 1
                Label(frame, text='{0:1d}'.format(game.red_swaps), foreground='red', font=('Courier', font_size, 'bold'),
                      justify=RIGHT).grid(row=6, column=2, padx=5, pady=5)
                if game.red_swaps == 0:
                    game.spy_swap_btn.state(['disabled'])
            #  Update the current game board with the modified temporary board and send new board HTML to browser.
            swap_board = np.array(c_or_iboard)
            self.Update_Board(root, swap_board)
            BoardHTML(swap_board)
            messagebox.showinfo(message='Spy exchange complete.  Spymasters, please refresh browsers.')
        else:
            okay = messagebox.showerror(message='Need two agents to be cleared for exchange.')
            if okay:
                window.lift(root)

    def Spy_Check(self, window, team_color, c_or_iboard, DA):
        '''
        Performs codename entry check to make sure that it has not been mistyped and is an existing agent which has not yet been contacted.  Results
        are used by both Double Agent (DA) and Spy_Swap (Swap) above.
        :param window:
        :param team_color:
        :param c_or_iboard:
        :return:
        '''

        #  Get the text entry for either team and remove extra '*' spymaster may have typed to provide extra hiding of entry.
        #  Add two LF and convert to upper case to be compatible with display of codewords on the game board.
        if team_color == 'blue':
            b_word = self.blue_entry.get().upper()
            if DA:
                team_col = 1
            else:
                team_col = 0
        else:
            b_word = self.red_entry.get().upper()
            team_col = 1
        #  Check if the entry exists on the board.  If it does, find the row and column it is in.  Then check if the agent has been
        #  contacted and the expected color.  If so, display that there is a "Match."
        w_count = 0
        for word in list(itertools.chain(*c_or_iboard[0])):
            word = word.strip('\n\n')
            if word in b_word:
                w_count+=1
                if w_count > 1:
                    okay = messagebox.showerror(message='Agent is not available or has already been contacted.')
                    Label(window, text=team_color.capitalize(), foreground=team_color, font=('Courier', 18, 'bold')).grid(row=5, column=team_col)
                    if okay:
                        window.lift(root)
                print(word,b_word)
                word = '\n\n' + word
                for i in range(5):
                    if word in c_or_iboard[0][i]:
                        row = i
                        col = c_or_iboard[0][i].index(word)
                if (int(c_or_iboard[2][row][col]) == 0) and (c_or_iboard[1][row][col] == team_color.capitalize()):
                    Label(window, text='Match', foreground='black', font=('Courier', 18, 'bold')).grid(row=5, column=team_col)
                    #  Flag that the spy check was successful and make the spy swap on this copy of the board.  Also set the
                    #  red/blue_da_codename variable to the codename found on the board to track double agent status.
                    '''
                    Note:  red and blue_da_codename is set every time Spycheck is used.  This may create interference problems if DA is used along
                    with Spy Swap.  Added DA switch to SpyCheck so red and blue_da_codename is only set if SpyCheck is being used by DA.
                    '''
                    if team_color == 'blue':
                        self.blue_check = True
                        c_or_iboard[1][row][col] = 'Red'
                        if DA:
                            game.red_da_codename = (c_or_iboard[0][row][col]).upper()
                    else:
                        self.red_check = True
                        c_or_iboard[1][row][col] = 'Blue'
                        if DA:
                            game.blue_da_codename = (c_or_iboard[0][row][col]).upper()
                else:
                    okay = messagebox.showerror(message='Agent is not available or has already been contacted.')
                    Label(window, text='  ' + team_color.capitalize() + '  ', foreground=team_color, font=('Courier', 18, 'bold')).grid(row=5, column=team_col)
                    if okay:
                        window.lift(root)
        if ((team_color == 'blue' and self.blue_check == False) or (team_color == 'red' and self.red_check == False) or (w_count > 1)):
            if team_color == 'blue':
                game.red_da_codename = None
                self.blue_check = False
            else:
                game.blue_da_codename = None
                self.red_check = False
            okay = messagebox.showerror(message='No match found for codename entered')
            Label(window, text='  ' + team_color.capitalize() + '  ', foreground=team_color, font=('Courier', 18, 'bold')).grid(row=5, column=team_col)
            if okay:
                window.destroy()
                #window.lift(root)

    def Mole_Agent(self):
        '''
        Randomly select an uncontacted agent from either team on the current game board and replace the codename with a new and
        different codename.  Update the Spymaster's key card view for their browsers.
        :return:
        '''
        #  Make a copy of the current board and convert to list to search for all row,col pairs which are either blue or red,
        #  and have not been contacted yet.  From this list make a random choice of one row,col pair and assign it a codeword that is
        #  not being used on the current board (this is the mole agent).  Update the button text to display the mole agent's codeword
        #  and send the new HTML file and display a reminder for spymasters to refresh their browsers.
        mole_board = self.Current_Board(root)
        mboard = mole_board.tolist()
        row_col = []
        for i in range(5):
            for j in range(5):
                if (mboard[1][i][j] == 'Red' or mboard[1][i][j] == 'Blue') and mboard[2][i][j] == '0':
                    row_col.append((i, j))
        row_col = random.choice(row_col)
        row, col = row_col
        mole_agent = game.mole_words.pop()
        mole_board[0, row, col] = mole_agent
        self.Update_Board(root, mole_board)
        bname = (gui.button_identities[row, col])
        bname.config(text=mole_agent)
        BoardHTML(mole_board)
        okay = messagebox.showinfo(message='A mole agent has been detected.  Spymasters, please refresh browsers.')
        #  Because mole appearances are random, they could occur while other windows are open (i.e., in the middle of a double agent
        #  operation or spy swap.  Once the mole agent notification above has been acknowledged, both the double agent and spy swap
        #  windows are attempted to be brought back into focus.
        if okay:
            try:
                da_setup_window.focus_set()
            except:
                pass
            try:
                swap_setup_window.focus_set()
            except:
                pass


class Game_Control:

    def __init__ (self):
        '''
        Initialize game control variables at the start of a new session (multiple alternating games between teams)
        and create a randomized list of codewords from the code_words.txt file found in the Assets subdirectory from
        where the program runs.
        '''

        self.first_game = 2                      #  counter to track the number of the game in the session series
        self.blue_score = 0                      #  number of games in the session won by the blue team
        self.red_score = 0                       #  number of games in the session won by the red team
        self.team_time = 170                     #  the total time allotted to a team turn if constraint option is selected
        self.max_spy_swap = 0                    #  the number of spy swaps allowed per team if option is selected
        self.mole_freq = 0                       #  the rate at which random "moles" are generated if option is selected
        self.max_double_agents = 0               #  the number of double agents allowed per team if option is selected
        self.time_config = 0                     #  default is no constraint, "1" for shared time, and "2" for split time
        self.shared_flag = False                 #  set to True if "Shared" time constraint option is selected for teams
        self.split_flag = False                  #  set to True if "Split" time constraint option is selected for teams
        self.split = 0.5                         #  factor by which total team time is divided between spymaster and operatives in "Split" time constraint
        self.saved = False                       #  set to True if game Settings are saved before closing Settings window
        self.master = True                       #  during "Split" time, this flag tracks whether spymaster or operatives are in play
        #self.team = 'blue'                       #  tracks team color in play
        self.blue_contacts = 9                   #  tracks number of contacts remaining for blue team (blue starts first game and so is assigned 9 contacts)
        self.red_contacts = 8                    #  tracks number of contacts remaining for red team


        #  Read all 400 code words stored in a text file to a list and append two newline control characters to each (to allow alignment when overlaid on blank
        #  card stock image).  Randomize the word order of the code_words list and make a copy.
        Assets_dir = os.getcwd() + '\\Assets\\'
        code_words = []
        f = open(Assets_dir + 'code_words.txt', 'r')
        for line in f.readlines():
            line = line.strip()
            line = '\n\n' + line
            code_words.append(line)
        random.shuffle(code_words)
        self.code_words = code_words
        self.code_words_copy = code_words.copy()


    def New_Game(self):
        '''
        Start setup of an individual game within a session.  Check current team color for who goes first in the round.  Setup spies and randomize and re-
        initialize the contact count array.  Select 25 words for the current round.
        :return:
        '''

        global gui

        font_size = round((width_resize + height_resize)/2*18)
        #  Determine which team's turn based on the number of games played within a session.
        if self.first_game % 2 == 0:
            self.team = 'Blue'
            next_turn_btn = ttk.Button(frame,text = 'Blue Turn', style='my.TButton', command=self.Next_Turn)
            next_turn_btn.grid(row=12, column=1, padx=10, pady=10)
        else:
            self.team = 'Red'
            next_turn_btn = ttk.Button(frame,text = 'Red Turn', style='my.TButton', command=self.Next_Turn)
            next_turn_btn.grid(row=12, column=1, padx=padx_size, pady=pady_size)

        start_game_btn.state(['disabled'])
        pause_resume_btn.state(['!disabled'])
        settings_btn.state(['disabled'])
        self.first_game += 1

        #  Initialize the number of agents on the board so that the team going first is assigned one additional agent.
        if self.team == 'Blue':
            spys = np.array(['Red']*8 + ['Blue']*9 + ['Yellow']*7 + ['Assassin'])
            self.red_contacts = 8
            self.blue_contacts = 9
        else:
            spys = np.array(['Red']*9 + ['Blue']*8 + ['Yellow']*7 + ['Assassin'])
            self.red_contacts = 9
            self.blue_contacts = 8

        self.blue_time = 0
        int_blue_time = IntVar(value=self.blue_time)
        text_blue_time.set(str(int_blue_time.get()))
        self.red_time = 0
        int_red_time = IntVar(value=self.red_time)
        text_red_time.set(str(int_red_time.get()))

        #  Display the number of contacts remaining and scores for each team.
        Label(frame, text=str(self.blue_contacts), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=2,column=1)
        Label(frame, text=str(self.red_contacts), foreground='red', font=('Courier',font_size, 'bold')).grid(row=2,column=2)
        Label(frame, text=str(self.blue_score), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=9,column=1)
        Label(frame, text=str(self.red_score), foreground='red', font=('Courier',font_size, 'bold')).grid(row=9,column=2)
        Label(frame, textvariable=text_blue_time, foreground='blue', font=('Courier', font_size, 'bold'),
              justify=RIGHT).grid(row=8, column=1, padx=5, pady=5)
        Label(frame, textvariable=text_red_time, foreground='red', font=('Courier', font_size, 'bold'),
              justify=RIGHT).grid(row=8, column=2, padx=5, pady=5)

        #  Based on which time mode has been selected from the "Settings" window, configure the status display and variables to contain the buttons
        #  and fields needed to control and report the time tracking during play.
        if self.time_config == 2:
            self.operatives_turn_btn = ttk.Button(frame,text = 'Ops Turn',style='my.TButton', command=self.Op_Turn)
            self.operatives_turn_btn.grid(row=12, column=0, padx=10, pady=10)
            self.operatives_turn_btn.state(['!disabled'])
            next_turn_btn.state(['disabled'])
            self.master = True

            Label(frame, text='Master Time', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=4,column=0,padx=5,pady=5)
            Label(frame, text='Ops Time', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=5,column=0,padx=5,pady=5)
            #Label(frame, text='{0:5.0f} s'.format(int(self.Spymaster_time)),foreground='blue',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=4,column=1,padx=5,pady=5)
            #Label(frame, text='{0:5.0f} s'.format(int(self.Operative_time)),foreground='blue',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=5,column=1,padx=5,pady=5)
            #Label(frame, text='{0:5.0f} s'.format(int(self.Spymaster_time)),foreground='red',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=4,column=2,padx=5,pady=5)
            #Label(frame, text='{0:5.0f} s'.format(int(self.Operative_time)),foreground='red',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=5,column=2,padx=5,pady=5)
            Label(frame, textvariable=text_blue_spymaster_remain, foreground='blue',
                  font=('Courier', font_size, 'bold'), justify=RIGHT).grid(row=4, column=1, padx=5, pady=5)
            Label(frame, textvariable=text_blue_operative_remain, foreground='blue',
                  font=('Courier', font_size, 'bold'), justify=RIGHT).grid(row=5, column=1, padx=5, pady=5)
            Label(frame, textvariable=text_red_spymaster_remain, foreground='red',
                  font=('Courier', font_size, 'bold'), justify=RIGHT).grid(row=4, column=2, padx=5, pady=5)
            Label(frame, textvariable=text_red_operative_remain, foreground='red',
                  font=('Courier', font_size, 'bold'), justify=RIGHT).grid(row=5, column=2, padx=5, pady=5)
        elif self.time_config == 1:
            next_turn_btn.state(['!disabled'])
            self.master = False
            Label(frame, text='    Team Time Left', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=4,column=0,padx=5,pady=5)
            #Label(frame, text='{0:5.0f} s'.format(int(self.team_time)),foreground='blue',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=4,column=1,padx=5,pady=5)
            #Label(frame, text='{0:5.0f} s'.format(int(self.team_time)),foreground='red',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=4,column=2,padx=5,pady=5)
            Label(frame, textvariable=text_blue_time_remain, foreground='blue',
                  font=('Courier', font_size, 'bold'), justify=RIGHT).grid(row=4, column=1, padx=5, pady=5)
            Label(frame, textvariable=text_red_time_remain, foreground='red',
                  font=('Courier', font_size, 'bold'), justify=RIGHT).grid(row=4, column=2, padx=5, pady=5)
        else:
            next_turn_btn.state(['!disabled'])
            self.master = False

        #  Randomize the list of Agents, Bystanders, and Assassin and covert to a 5x5 array.
        random.shuffle(spys)
        spys = spys.reshape(5, 5)
        #  Create a 5x5 array initialized to all zeros to track contact status.  If an agent or bystander is contacted, their value is set to "1" in this array.
        contact = np.zeros( (5, 5), dtype=np.int16)

        #  There are initially 400 code words read in from the code_words.txt file.  This allows for only 16 games of play within a session.  So, if the words
        #  are depleted, reset the code_words list with a newly randomized copy of the initially read in list.
        if self.code_words == []:
            random.shuffle(self.code_words_copy)
            self.code_words = self.code_words_copy.copy()
        board_code_words = []

        #  Take 25 words off the top of the code_words list and make a board_code_words 5x5 array for the current game.
        #  Also, make a list of mole_words from a reshuffle of the remaining code_words list.
        for i in range(25):
            board_code_words.append(self.code_words.pop())
        self.mole_words = self.code_words.copy()
        random.shuffle(self.mole_words)

        #  If the last 25 words have been used on the current board, set the mole words list to the reverse of the code_words_copy
        #  to ensure words on the current board will not be present in the mole list.
        if len(self.mole_words) < 25:
            self.mole_words = self.code_words_copy[::-1]
        board_code_words = np.array(board_code_words)
        board_code_words.shape = 5,5
        #  Make a three-dimensional array, by stacking the board_code_words, spies, and contact arrays together.
        board = np.vstack([board_code_words, spys, contact])
        board.shape = 3,5,5
        self.initial_board = copy.deepcopy(board)

        #  Create an HTML layout of the current game board (containing colored labeled rectangles representing blue or red agents, yellow bystanders, and
        #  the black assassin.
        BoardHTML(board)

        #  Create an instance of the current game board to display and interact with players on a computer controlled screen running the program.
        gui = Board(root, board)

        current_board = gui.Current_Board(root)

        #  If the option to allow spy swaps has been selected in the "Settings" menu, configure variables and display to accommodate.
        if self.max_spy_swap != 0:
            self.red_swaps = self.max_spy_swap
            self.blue_swaps = self.max_spy_swap
            Label(frame, text='Spy Swaps', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=6,column=0,padx=5,pady=5)
            Label(frame, text='{0:1d}'.format(self.blue_swaps),foreground='blue',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=6,column=1,padx=5,pady=5)
            Label(frame, text='{0:1d}'.format(self.red_swaps),foreground='red',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=6,column=2,padx=5,pady=5)
            self.spy_swap_btn = ttk.Button(frame,text = 'Spy Swap',style='my.TButton', command=gui.Swap)
            self.spy_swap_btn.grid(row=13, column=0, padx=10, pady=10)
        else:
            self.red_swaps = 0
            self.blue_swaps = 0
            self.spy_swap_btn = ttk.Button(frame)

        #  If the option to allow double agents has been selected in the "Settings" menu, configure variables and display to accommodate.
        if self.max_double_agents != 0:
            self.red_da = self.max_double_agents
            self.blue_da = self.max_double_agents

            Label(frame, text='Double Agents', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=7,column=0,padx=5,pady=5)
            Label(frame, text='{0:1d}'.format(self.blue_da),foreground='blue',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=7,column=1,padx=5,pady=5)
            Label(frame, text='{0:1d}'.format(self.red_da),foreground='red',font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=7,column=2,padx=5,pady=5)
            self.double_agent_btn = ttk.Button(frame,text = 'Double Agent',style='my.TButton', command=gui.DA)
            self.double_agent_btn.grid(row=14, column=0, padx=10, pady=10)
        else:
            self.red_da = 0
            self.blue_da = 0
            self.double_agent_btn = ttk.Button(frame)

        '''
        if self.team == 'Blue':
            self.red_time = 0                    #  tracks time of red team's current turn
        else:
            self.blue_time = 0                   #  tracks time of blue team's current turn
        '''

        try:
            SendFTP()
        except:
            okay = messagebox.showerror(message='FTP connection cannot be made. Re-enter credentials')
            if okay:
                Set_FTP()
                return

        #  These game variables need to be initialized at the start of each new game within a session of play.
        self.pause = 1                           #  set to "0" if game is paused
        self.blue_da_codename = None             #  set to codename that has been selected as a blue double agent
        self.red_da_codename = None              #  set to codename that has been selected as a red double agent
        self.start_time = time()                 #  holds the time when the session was started
        self.start_turn_time = time()            #  holds the time that a team's turn began if constraint option is selected for teams
        self.random_start_time = time()          #  tracks time between random mole appearances if option is selected
        self.event_count = 0                     #  tracks the number of random mole appearances if option is selected
        self.blue_hold_time_remain = 0           #  tracks blue team time when game is paused
        self.blue_time_remain = 0                #  tracks blue team's remaining turn time
        self.red_hold_time_remain = 0            #  tracks red team time when game is paused
        self.red_time_remain = 0                 #  tracks red team's remaining turn time
        self.blue_total = 0                      #  tracks total time blue team has been in play
        self.red_total = 0                       #  tracks total time red team has been in play
        self.play_flag = 0                       #  set to "1" if sound effects play during operative's turn in "Split" time mode
        self.play_flag_2 = 0                     #  set to "1" if sound effects play during spymaster's turn in "Split" time mode


        self.task()
        root.mainloop()

    def Settings(self):
        '''
        Allows users to select the mode of time control for the game:  (1) none, only keeps track of total elapsed time for each team with no limit,
        (2) shared, sets a total time limit for each team's turn which can be used by the Spymaster and Operatives as needed, (3) split, sets a total
        time limit for each team's turn, but Spymaster and Operatives are issued a fixed fraction which when expired forces the Spymaster's role to end
        or the Operative's role to end, completing the team's turn.
        In addition to time control, a few more novel features are added which were not present in the original board version of CodeNames.
        (1) Spy Swaps - allow teams a fixed number of opportunities during the game in which the Spymaster of each team can elect to exchange one of his/her
        field agent's codename with that of the opponent's.
        (2) Random Mole - at a pre-selected frequency, any single non-contacted codename from either team can randomly be assigned to a new codename not
        being used in the current game.
        (3) Double Agent - allows teams a fixed number of opportunities during the game for the Spymaster of each team to select an opponent's non-contacted
        codename on the board.  If in the next turn, the opposing team makes contact, that contact is also awarded to the other team.
        :return:
        '''
        self.man_swap_value = IntVar()                   #  selected number of spy swaps allowed
        self.ran_mole_value = IntVar()                   #  selected random mole frequency
        self.man_double_value = IntVar()                 #  selected number of double agents allowed
        self.split_value = DoubleVar()                   #  fraction of total team turn time allocated to spymaster vs operatives
        self.time_cfg = IntVar()                         #  set to 0,1, or 2 depending on radiobutton selection for time constraint option
        self.time_value = IntVar()                       #  set to total team turn time allowed if constraint selected
        self.setup_window = Toplevel()
        self.setup_window.geometry('480x450+600+400')

        #  Create radiobuttons to allow players to select various time constraint options.
        lbl = Label(self.setup_window, text='Time Tracking', font=('Courier', 10))
        lbl.place(x=10, y=5)
        rb0 = ttk.Radiobutton(self.setup_window, text='No Time Limit', command=self.Update_Time_None, variable=self.time_cfg, value=0)
        rb0.place(x=10, y=25)
        rb1 = ttk.Radiobutton(self.setup_window, text='Shared Time', command=self.Update_Time_Shared, variable=self.time_cfg, value=1)
        rb1.place(x=120, y=25)
        rb2 = ttk.Radiobutton(self.setup_window, text='Split Time', command=self.Update_Time_Split, variable=self.time_cfg, value=2)
        rb2.place(x=230, y=25)
        lbl = Label(self.setup_window, text='Advanced Features', font=('Courier', 10))
        lbl.place(x=10, y=200)

        """
        if not self.saved:                      These are initialized in New_Game
            self.team_time = 170
            self.time_config = 0
            self.max_spy_swap = 0
            self.mole_freq = 0
            self.max_double_agents = 0
            self.shared_flag = False
            self.split_flag = False
        """
        #  When the "Save" button is clicked in the Settings window parameters are saved for the session.  To re-display
        #  the settings when window is re-opened after a save, the radiobuttons must be programmatically invoked (and in
        #  this case, rbo must always be invoked first to make this work).
        if self.saved:
            if self.time_config == 2:
                rb0.invoke()
                rb2.invoke()
            elif self.time_config == 1:
                rb0.invoke()
                rb1.invoke()
            else:
                rb0.invoke()

        #  Create sliding scales for player selection of game variant numerical parameters.
        man_swap_scale = ttk.Scale(self.setup_window, orient=HORIZONTAL, length=400, command=self.Update_Man_Swap,
                                   variable=self.man_swap_value, from_=0, to=8)
        man_swap_scale.place(x=40, y=260)
        man_swap_scale.set(self.max_spy_swap)

        ran_mole_scale = ttk.Scale(self.setup_window, orient=HORIZONTAL, length=400, command=self.Update_Ran_Mole,
                                   variable=self.ran_mole_value, from_=0, to=5)
        ran_mole_scale.place(x=40, y=320)
        ran_mole_scale.set(self.mole_freq)

        man_double_scale = ttk.Scale(self.setup_window, orient=HORIZONTAL, length=400, command=self.Update_Man_Double,
                                     variable=self.man_double_value, from_=0, to=8)
        man_double_scale.place(x=40, y=380)
        man_double_scale.set(self.max_double_agents)

        #  Buttons for saving game setting parameters and cancelling the settings window.
        button1 = ttk.Button(self.setup_window, text='Save', command=lambda: self.Save_Settings(self.setup_window)).place(x=140, y=420)
        button2 = ttk.Button(self.setup_window, text='Cancel', command=lambda: self.Close_Settings(self.setup_window)).place(x=260,
                                                                                                              y=420)
        self.setup_window.mainloop()

    def Update_Man_Swap(self, man_swap_value):
        '''
        Provide real time display update for the number of spy swaps allowed based on slider position.
        :param man_swap_value:
        :return:
        '''
        man_swap_lbl = Label(self.setup_window, text='Manual Spy Swaps Allowed: {0:1d}'.format(int(float(man_swap_value))),
                             font=('Courier', 10))
        man_swap_lbl.place(x=150, y=230)

    def Update_Ran_Mole(self, ran_mole_value):
        '''
        Provide real time display update for the frequency of random mole appearances based on slider position.
        :param ran_mole_value:
        :return:
        '''
        ran_mole_lbl = Label(self.setup_window, text='Random Mole Frequency:  {0:3d}'.format(int(float(ran_mole_value))),
                             font=('Courier', 10))
        ran_mole_lbl.place(x=150, y=290)

    def Update_Man_Double(self, man_double_value):
        '''
        Provide real time display update for the number of double agents allowed based on slider position.
        :param man_double_value:
        :return:
        '''
        man_double_lbl = Label(self.setup_window,
                               text='Manual Double Agents Allowed: {0:1d}'.format(int(float(man_double_value))),
                               font=('Courier', 10))
        man_double_lbl.place(x=150, y=350)

    """
    When radio buttons are selected for "shared" and "split" time options, sliders are displayed to allow users to select values.  If an
    option with fewer sliders displayed was subsequently selected, the sliders would remain.  The functions Update_Time_None,
    Update_Time_Shared, and Update_Time_Split handle these cases.
    """

    def Update_Time_None(self):

        self.shared_flag = False
        self.split_flag = False

        try:
            self.scale_lbl.destroy()
            self.scale.destroy()
        except:
            pass

        self.time_lbl.destroy()
        self.time_scale.destroy()

        blank_time_lbl = Label(self.setup_window,
                               text='                                                                                                                                   ')
        blank_time_lbl.place(x=40, y=60)
        blank_split_lbl = Label(self.setup_window,
                                text='                                                                                                                                     ')
        blank_split_lbl.place(x=40, y=130)

    def Update_Time_Shared(self):

        if not self.saved:
            self.team_time = 170
        self.shared_flag = True
        if not self.split_flag:
            self.time_scale = ttk.Scale(self.setup_window, orient=HORIZONTAL, length=400, command=self.Update_Team_Time,
                                   variable=self.time_value, from_=40, to=300)
            self.time_scale.place(x=40, y=90)
            self.time_scale.set(self.team_time)
        try:
            self.scale_lbl.destroy()
            self.scale.destroy()
        except:
            pass

        blank_split_lbl = Label(self.setup_window,
                                text='                                                                                                                                     ')
        blank_split_lbl.place(x=40, y=130)

    def Update_Time_Split(self):

        self.split_flag = True
        if not self.saved:
            self.team_time = 170
            self.split = 0.5
        if not self.shared_flag:
            self.time_scale = ttk.Scale(self.setup_window, orient=HORIZONTAL, length=400, command=self.Update_Team_Time,
                                   variable=self.time_value, from_=40, to=300)
            self.time_scale.place(x=40, y=90)
            self.time_scale.set(self.team_time)
        self.scale = ttk.Scale(self.setup_window, orient=HORIZONTAL, length=400, command=self.Update_Time_Scale, variable=self.split_value,
                          from_=0.1, to=0.9)
        self.scale.place(x=40, y=170)
        self.scale.set(self.split)


    def Update_Team_Time(self, time_setting):
        '''
        Provides a real time display update for the total team time allowed during a turn based on the position of the slider.
        :param time_setting:
        :return:
        '''
        self.time_lbl = Label(self.setup_window, text='Total Team Time (sec): {0:3d}'.format(int(float(time_setting))),
                         font=('Courier', 10))
        self.time_lbl.place(x=40, y=60)
        if self.time_cfg == 2:
            self.Operative_time = int(float(self.split_value.get()) * int(float(time_setting)))
            self.Spymaster_time = int(int(float(time_setting)) - self.Operative_time)
            self.scale_lbl = Label(self.setup_window,
                              text='Spymaster: {0:3d} sec           Operatives: {1:3d} sec'.format(self.Spymaster_time,
                                                                                                   self.Operative_time),
                              font=('Courier', 10))
            self.scale_lbl.place(x=40, y=130)


    def Update_Time_Scale(self, scale_value):
        '''
        Provides a real time display update for the time allowed during a turn for the Spymaster and Operatives respectively
        based on the position of the slider.
        :param scale_value:
        :return:
        '''
        self.Operative_time = int(float(scale_value) * self.time_value.get())
        self.Spymaster_time = int(self.time_value.get() - self.Operative_time)
        self.scale_lbl = Label(self.setup_window,
                               text='Spymaster: {0:3d} sec           Operatives: {1:3d} sec'.format(self.Spymaster_time,
                                                                                                    self.Operative_time),
                               font=('Courier', 10))
        self.scale_lbl.place(x=40, y=130)


    def Save_Settings(self, window):
        '''
        Clicking "Save" on the Settings window will close it and save all selected parameters for game play.  If the window
        is reopened by clicking "Settings" button again, all previously selected parameter values will still appear.
        :param window:
        :return:
        '''
        self.split = self.split_value.get()
        self.time_config = self.time_cfg.get()
        self.team_time = self.time_value.get()
        self.max_spy_swap = self.man_swap_value.get()
        self.mole_freq = self.ran_mole_value.get()
        self.max_double_agents = self.man_double_value.get()
        self.saved = True
        window.destroy()

    def Close_Settings(self, window):
        '''
        When the "Cancel" button is selected, the Settings window is closed and all parameters revert to default values.
        :param window:
        :return:
        '''
        self.time_config = 0
        self.team_time = 170
        self.split = 0.5
        self.max_spy_swap = 0
        self.mole_freq = 0
        self.max_double_agents = 0
        window.destroy()


    def Pause_Resume(self):
        '''
        Allows game play to be paused/resumed, by saving all time variables for each team.
        :return:
        '''
        if self.team == 'Blue':
            next_turn_btn = ttk.Button(frame, text='Blue Turn', style='my.TButton', command=self.Next_Turn)
        else:
            next_turn_btn = ttk.Button(frame, text='Red Turn', style='my.TButton', command=self.Next_Turn)
        next_turn_btn.grid(row=12, column=1, padx=padx_size, pady=pady_size)
        self.pause = self.pause ^ 1
        if self.pause == 0:
            next_turn_btn.state(['disabled'])
            if self.team == 'Blue':
                self.blue_hold_time_remain = self.blue_time_remain
                if self.time_config == 2:
                    self.last_blue_spymaster_remain = self.blue_spymaster_remain
                    self.last_blue_operative_remain = self.blue_operative_remain
            else:
                self.red_hold_time_remain = self.red_time_remain
                if self.time_config == 2:
                    self.last_red_spymaster_remain = self.red_spymaster_remain
                    self.last_red_operative_remain = self.red_operative_remain
            self.blue_total = self.blue_time
            self.red_total = self.red_time
        else:
            next_turn_btn.state(['!disabled'])
            self.start_time = time()
            self.start_turn_time = time()


    def Next_Turn(self):
        '''
        Puts the selected team color in current play.  Unless a time constraint mode is selected AND time runs out during
        a team's turn, board control is not automatically switched between teams and must be performed manually with this button.
        :return:
        '''
        self.Pause_Resume()

        #  Stop playback of alarm sounds which may have been in progress and reset play flags.
        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
        self.play_flag = 0
        self.play_flag_2 = 0

        #  Switch team in play.  Disallow double agents to be used (disable button) if there are 0 left, or if the
        #  opposing team has < 2 contacts remaining on the board.  Disable spy swaps button if there are 0 left.
        #  Set blue/red_da_codename to False since it may have been set to True in the previous turn when a double agent
        #  was deployed.
        if self.team == 'Red':
            self.team = 'Blue'
            if self.blue_da == 0 or self.red_contacts < 2:
                self.double_agent_btn.state(['disabled'])
            else:
                self.double_agent_btn.state(['!disabled'])
            self.blue_da_codename = None
            if self.blue_swaps == 0:
                self.spy_swap_btn.state(['disabled'])
            else:
                self.spy_swap_btn.state(['!disabled'])
            self.red_total = self.red_time
            self.blue_hold_time_remain = 0
        else:
            self.team = 'Red'
            if self.red_da == 0 or self.blue_contacts < 2:
                self.double_agent_btn.state(['disabled'])
            else:
                self.double_agent_btn.state(['!disabled'])
            self.red_da_codename = None
            if self.red_swaps == 0:
                self.spy_swap_btn.state(['disabled'])
            else:
                self.spy_swap_btn.state(['!disabled'])
            self.blue_total = self.blue_time
            self.red_hold_time_remain = 0

        self.start_turn_time = time()

        self.Pause_Resume()

        #  Update label on Next_Turn button.  If "Split" time was selected, enable operatives_turn_btn to allow switch
        #  from Spymaster to Operative time countdown.  Finally, disable next_turn_btn since team control should not be
        #  switched before operatives have been brought into play.  Set self.master to True to indicate that turn starts
        #  with team's spymaster on the clock.
        next_turn_btn = ttk.Button(frame, text=self.team + ' Turn', style='my.TButton', command=self.Next_Turn)
        next_turn_btn.grid(row=12, column=1, padx=padx_size, pady=pady_size)
        if self.time_config == 2:
            self.operatives_turn_btn.state(['!disabled'])
            next_turn_btn.state(['disabled'])
            self.master = True

    def task(self):
        '''
        Called every 1000 ms, task performs display updates for scores, elapsed time and other status parameters.
        :return:
        '''

        global gui
        
        font_size = round((width_resize + height_resize)/2*18)
        #  If game has been paused (i.e., self.pause = 0), then task does not run.
        if self.pause:
            if self.team == 'Blue':
                self.blue_time = self.blue_total + time() - self.start_time
                int_blue_time = IntVar(value=self.blue_time)
                text_blue_time.set(str(int_blue_time.get()))
                try:
                    if self.blue_hold_time_remain > 0:
                        self.blue_time_remain = (self.start_turn_time - time()) + self.blue_hold_time_remain
                        if self.master:
                            self.blue_spymaster_remain = self.last_blue_spymaster_remain + (self.start_turn_time - time())
                            self.blue_operative_remain = self.Operative_time
                        else:
                            self.blue_spymaster_remain = self.last_blue_spymaster_remain
                            self.blue_operative_remain = self.last_blue_operative_remain + (self.start_turn_time - time())
                    else:
                        self.blue_time_remain = int(self.team_time) + (self.start_turn_time - time())
                        if self.master:
                            self.blue_spymaster_remain = self.Spymaster_time + (self.start_turn_time - time())
                            self.last_blue_spymaster_remain = self.blue_spymaster_remain
                            self.blue_operative_remain = self.Operative_time
                        else:
                            self.blue_spymaster_remain = self.last_blue_spymaster_remain
                            self.blue_operative_remain = self.Operative_time + (self.start_turn_time - time()) + (
                                    self.Spymaster_time - self.last_blue_spymaster_remain)
                except:
                    pass
                #  In "Split" time mode, play alarm sound when spymaster has < 6 seconds remaining.
                if self.time_config == 2:
                    if self.blue_spymaster_remain < 6 and self.play_flag_2 == 0:
                        self.play_flag_2 = 1
                        winsound.PlaySound(Assets_dir + 'Spymaster Timeout.wav',
                                           winsound.SND_FILENAME + winsound.SND_ASYNC)
                    #  When spymaster has < 1 second remaining, automatically switch operatives into play.
                    if self.blue_spymaster_remain < 1 and self.master:
                        self.blue_spymaster_remain = 0
                        self.Op_Turn()
                    #  Play multiple alarm sound when operatives remaining time is < 20 seconds.
                    if self.blue_operative_remain < 20 and self.play_flag == 0:
                        self.play_flag = 1
                        winsound.PlaySound(Assets_dir + 'Multiple_Alarms.wav',
                                           winsound.SND_FILENAME + winsound.SND_ASYNC)
                    #  When operatives have < 1 second remaining, automatically switch teams.
                    if self.blue_operative_remain < 1:
                        self.blue_operative_remain = 0
                        self.Next_Turn()
                    int_blue_spymaster_remain = IntVar(value=self.blue_spymaster_remain)
                    text_blue_spymaster_remain.set(str(int_blue_spymaster_remain.get()))
                    int_blue_operative_remain = IntVar(value=self.blue_operative_remain)
                    text_blue_operative_remain.set(str(int_blue_operative_remain.get()))
                elif self.time_config == 1:
                    #  In "Shared" time mode, play multiple alarm sound when team time remaining is < 20 seconds.
                    if self.blue_time_remain < 20 and self.play_flag == 0:
                        self.play_flag = 1
                        winsound.PlaySound(Assets_dir + 'Multiple_Alarms.wav',
                                           winsound.SND_FILENAME + winsound.SND_ASYNC)
                    #  When team has < 1 second remaining, automatically switch teams.
                    if self.blue_time_remain < 1:
                        self.blue_time_remain = 0
                        self.Next_Turn()
                    int_blue_time_remain = IntVar(value=self.blue_time_remain)
                    text_blue_time_remain.set(str(int_blue_time_remain.get()))
            else:
                self.red_time = self.red_total + time() - self.start_time
                int_red_time = IntVar(value=self.red_time)
                text_red_time.set(str(int_red_time.get()))
                try:
                    if self.red_hold_time_remain > 0:
                        self.red_time_remain = (self.start_turn_time - time()) + self.red_hold_time_remain
                        if self.master:
                            self.red_spymaster_remain = self.last_red_spymaster_remain + (self.start_turn_time - time())
                            self.red_operative_remain = self.Operative_time
                        else:
                            self.red_spymaster_remain = self.last_red_spymaster_remain
                            self.red_operative_remain = self.last_red_operative_remain + (self.start_turn_time - time())
                    else:
                        self.red_time_remain = int(self.team_time) + (self.start_turn_time - time())
                        if self.master:
                            self.red_spymaster_remain = self.Spymaster_time + (self.start_turn_time - time())
                            self.last_red_spymaster_remain = self.red_spymaster_remain
                            self.red_operative_remain = self.Operative_time
                        else:
                            self.red_spymaster_remain = self.last_red_spymaster_remain
                            self.red_operative_remain = self.Operative_time + (self.start_turn_time - time()) + (
                                    self.Spymaster_time - self.last_red_spymaster_remain)
                except:
                    pass
                #  See comments above for "Split" and "Shared" time modes as logic is identical for both teams
                #  TODO: write function for blue/red team operations in task.
                if self.time_config == 2:
                    if self.red_spymaster_remain < 6 and self.play_flag_2 == 0:
                        self.play_flag_2 = 1
                        winsound.PlaySound(Assets_dir + 'Spymaster Timeout.wav',
                                           winsound.SND_FILENAME + winsound.SND_ASYNC)
                    if self.red_spymaster_remain < 1 and self.master:
                        self.red_spymaster_remain = 0
                        self.Op_Turn()
                    if self.red_operative_remain < 20 and self.play_flag == 0:
                        self.play_flag = 1
                        winsound.PlaySound(Assets_dir + 'Multiple_Alarms.wav',
                                           winsound.SND_FILENAME + winsound.SND_ASYNC)
                    if self.red_operative_remain < 1:
                        self.red_operative_remain = 0
                        self.Next_Turn()
                    int_red_spymaster_remain = IntVar(value=self.red_spymaster_remain)
                    text_red_spymaster_remain.set(str(int_red_spymaster_remain.get()))
                    int_red_operative_remain = IntVar(value=self.red_operative_remain)
                    text_red_operative_remain.set(str(int_red_operative_remain.get()))
                elif self.time_config == 1:
                    if self.red_time_remain < 20 and self.play_flag == 0:
                        self.play_flag = 1
                        winsound.PlaySound(Assets_dir + 'Multiple_Alarms.wav',
                                           winsound.SND_FILENAME + winsound.SND_ASYNC)
                    if self.red_time_remain < 1:
                        self.red_time_remain = 0
                        self.Next_Turn()
                    int_red_time_remain = IntVar(value=self.red_time_remain)
                    text_red_time_remain.set(str(int_red_time_remain.get()))

            #  If the random mole option has been selected in the "Settings" menu, call the Mole_Agent() method at a random interval which is not
            #  to be less than 25 seconds and is proportional to the mole frequency selected.  At the highest frequency setting allowed in the
            #  menu, the average mole appearance is about once a minute.  At the lowest frequency it is about . . .
            if self.mole_freq != 0:
                if 10.5 * random.random() > 9.999:
                    time_between_events = time() - self.random_start_time
                    if time_between_events > 25:
                        self.event_count += 1
                        self.random_start_time = time()
                        if self.event_count % (6 - self.mole_freq) == 0:
                            gui.Mole_Agent()

        #  In order to allow the Tkinter GUI to interact with the players (button selections etc. . .), all other programmatic
        #  updates are performed by the task function which is automatically called every 1000 ms.

        root.after(500, self.task)

    def Op_Turn(self):
        '''
        Automatically switch from master to operatives in "Split" time mode when spymaster's time runs out.
        :return:
        '''

        winsound.PlaySound(None, winsound.SND_FILENAME + winsound.SND_ASYNC)
        self.Pause_Resume()
        self.master = False
        self.operatives_turn_btn.state(['disabled'])
        self.Pause_Resume()
        next_turn_btn.state(['!disabled'])


    def Open_File():
        '''
        Display PDF file of supplementary game rules.
        :return:
        '''
        startfile(Assets_dir + "CodeName_New_Rules.pdf")


def Set_FTP():
    '''
    Open interactive window to allow players to enter FTP account information for spy master key card browser display.
    :return:
    '''
    #  Create text entry fields for FTP account parameters and initialize variables.
    FTP_setup_window = Toplevel()
    FTP_domain = ttk.Entry(FTP_setup_window, width=25)
    FTP_domain.grid(row=10, column=1)
    FTP_ID = ttk.Entry(FTP_setup_window, width=25)
    FTP_ID.grid(row=11, column=1)
    FTP_PWD = ttk.Entry(FTP_setup_window, width=25)
    FTP_PWD.grid(row=12, column=1)
    FTP_Folder = ttk.Entry(FTP_setup_window, width=25)
    FTP_Folder.grid(row=13, column=1)
    show_field = IntVar()
    show_field.set(0)
    saved_settings = IntVar()
    saved_settings.set(0)
    FTP_domain.config(show='*')
    FTP_ID.config(show='*')
    FTP_PWD.config(show='*')
    FTP_Folder.config(show='*')
    file_path = os.path.join(os.getcwd(), 'ftp_config.txt')
    FTP_setup_window.geometry('350x200+600+400')
    Label(FTP_setup_window, text='FTP Domain',font=('Courier', 10, 'bold')).grid(row=10, column=0)
    Label(FTP_setup_window, text='Account ID',font=('Courier', 10, 'bold')).grid(row=11, column=0)
    Label(FTP_setup_window, text='Password',font=('Courier', 10, 'bold')).grid(row=12, column=0) 
    Label(FTP_setup_window, text='FTP Directory',font=('Courier', 10, 'bold')).grid(row=13, column=0)


    def FTP_Reset():
        '''
        Function which clears all text entry fields.
        :return:
        '''
        FTP_domain.delete(0, END)
        FTP_ID.delete(0, END)
        FTP_PWD.delete(0, END)
        FTP_Folder.delete(0, END)


    def FTP_Show(window):
        '''
        Function which toggles between showing/hiding text fields depending on state of "Show field entries" checkbutton.
        :param window:
        :return:
        '''
        if show_field.get():
            FTP_domain.config(show='')
            FTP_ID.config(show='')
            FTP_PWD.config(show='')
            FTP_Folder.config(show='')
        else:
            FTP_domain.config(show='*')
            FTP_ID.config(show='*')
            FTP_PWD.config(show='*')
            FTP_Folder.config(show='*')


    def FTP_Saved(window):
        '''
        Function which populates text fields with FTP settings if "Use saved settings" checkbutton is selected.  Note:
    #  unencrypted FTP account settings are simply saved to a text file (ftp_config.txt) in the program directory.
        :param window:
        :return:
        '''
        if saved_settings.get():
            FTP_Reset()
            try:
                with open(file_path, 'r') as f:
                    FTP_domain.insert(0, f.readline().strip())
                    FTP_ID.insert(0, f.readline().strip())
                    FTP_PWD.insert(0, f.readline().strip())
                    FTP_Folder.insert(0, f.readline().strip())
            except:
                okay = messagebox.showerror(message='FTP settings have not yet been saved.  Enter settings and click "Save."')
                if okay:
                    window.lift(root)
        else:
            FTP_Reset()


    def FTP_Save(window):
        '''
        Function which saves FTP text entry fields to a text file (ftp_config.txt) in the program directory when "Save" button is clicked.
        :param window:
        :return:
        '''
        with open(file_path, 'w') as f:
            f.write(FTP_domain.get() + '\n')
            f.write(FTP_ID.get() + '\n')
            f.write(FTP_PWD.get() + '\n')
            f.write(FTP_Folder.get() + '\n')

        okay = messagebox.showinfo(message='FTP settings have been saved to:  ' + file_path)
        if okay:
            window.lift(root)


    def FTP_Close(window):
        '''
        When "Close" button is clicked, FTP_settings dict is created to store all values for use by the program.
        :param window:
        :return:
        '''
        global FTP_settings

        FTP_settings = {'FTP_domain': FTP_domain.get(), 'FTP_ID': FTP_ID.get(), 'FTP_PWD': FTP_PWD.get(),
                        'FTP_Folder': FTP_Folder.get()}

        window.destroy()

    #  Create Buttons and Checkbuttons and assign related functions above to commands for each.
    button2=ttk.Button(FTP_setup_window, text='Save', command=lambda: FTP_Save(FTP_setup_window)).grid(row=19, column=0, pady=25)
    button1=ttk.Button(FTP_setup_window, text='Close', command=lambda: FTP_Close(FTP_setup_window)).grid(row=19, column=1, pady=10)
    button3 = ttk.Checkbutton(FTP_setup_window, text="Show field entries", variable=show_field,
                              command=lambda: FTP_Show(FTP_setup_window)).grid(row=15, column=0, padx=15, pady=15)
    button4 = ttk.Checkbutton(FTP_setup_window, text="Use saved settings", variable=saved_settings,
                              command=lambda: FTP_Saved(FTP_setup_window)).grid(row=15, column=1, padx=15, pady=15)

    FTP_setup_window.lift(root)
    FTP_setup_window.mainloop()


def SendFTP():
    '''
    Use Python FTP library to make a connection using FTP_settings acquired from Set_FTP() and send default filename:
    "index.html" to the designated account folder.
    :return:
    '''
    try:
        ftp = FTP(FTP_settings['FTP_domain'])
        ftp.login(user=FTP_settings['FTP_ID'], passwd=FTP_settings['FTP_PWD'])
        ftp.cwd(FTP_settings['FTP_Folder'])
        filename='index.html'
        ftp.storbinary('STOR '+filename, open(filename, 'rb'))
        ftp.quit()
    except:
        okay=messagebox.showerror(message='FTP connection cannot be made. Re-enter credentials')
        if okay:
            Set_FTP()


def BoardHTML(active_board):
    '''
    Create an HTML file (index.html) to use as spymaster key card on browser and send via FTP.
    :param active_board:
    :return:
    '''
    #  Create dictionary to translate colors stored in program game board as text to rgb values needed in HTML graphics statements.
    rgb = dict(Red='(255,100,125)',Blue='(0,200,255)',Yellow='(255,255,0)',Assassin='(0,0,0)')
    outfile = open('index.html', 'w')
    print('<!DOCTYPE html>', file = outfile)
    print('<html>', file = outfile)
    print('<body>', file = outfile)
    print('<svg width="720" height="500">', file = outfile)

    #  Define a 5x5 array of rectangles individually colored to match the agent, bystander, or assassin on the game board and label
    #  with corresponding codename text.
    for x in enumerate(range(10, 660, 130)):
        for y in enumerate(range(20, 370, 70)):
            print('<rect x="{}" y="{}" width="120" height="60" style="fill:rgb{};stroke-width:stroke:rgb(0,0,0)" />'.format(x[1],y[1],rgb[active_board[1,y[0],x[0]]]), file = outfile)
            print('</rect>', file = outfile)
            #  Because codeword text is black and Assassin card is black, for this one instance, change text color to white.
            if active_board[1,y[0],x[0]] == 'Assassin':
                fc = 'white'
            else:
                fc = 'black'
            print('<text x="{}" y="{}" fill="{}">{}</text>'.format(x[1]+5,y[1]+35,fc,active_board[0,y[0],x[0]].strip()), file = outfile)

    print('</svg>', file = outfile)
    print('</body>', file = outfile)
    print('</html>', file = outfile)
    outfile.close()

    SendFTP()


def BlankHTML():
    '''
    Before game starts and when game ends, clear game board display and send a short message to browser.
    :return:
    '''
    outfile = open('index.html', 'w')
    print('<!DOCTYPE html>', file = outfile)
    print('<html>', file = outfile)
    print('<body>', file = outfile)
    print('<heading>Wait for game to start and then refresh browser.', file = outfile)
    print('</heading>', file = outfile)
    print('</body>', file = outfile)
    print('</html>', file = outfile)
    outfile.close()
    SendFTP()

"""
*********************************************************************************************************************
(1) Create frame of root window which contains status information of game play (i.e., scores, elapsed time etc. . .).
(2) Initialize buttons to control game (i.e., start, pause/resume, game settings, etc. . .).
(3) Initialize spy/bystander picture cards with scanned images (resize based on current screen dimensions of display
    being used) stored in "Assets_dir."
*********************************************************************************************************************
"""

root = Tk()
text_blue_time = StringVar()
text_blue_spymaster_remain = StringVar()
text_blue_operative_remain = StringVar()
text_blue_time_remain = StringVar()
text_red_time = StringVar()
text_red_spymaster_remain = StringVar()
text_red_operative_remain = StringVar()
text_red_time_remain = StringVar()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
width = 1920.0                                #  default screen width/height stored images are based on.
height = 1200.0
width_resize = screen_width/width             #  calculate resize factor needed to correctly display on current screen.
height_resize = screen_height/height
frame_height = int(height_resize*600)
frame_width = int(width_resize*400)
root.state('zoomed')
frame = ttk.Frame(root)
frame.grid(row=0,column=0,sticky='ne')
frame.config(height=frame_height, width=frame_width, relief=GROOVE)

#  Use an average of horizontal/vertical resize factors to scale font and spacing of text.
font_size = round((width_resize + height_resize)/2*18)
padx_size = int(width_resize*5)
pady_size = round(height_resize*5)

#  Button text can only be modified using style parameters.
s = ttk.Style()
s.configure('my.TButton', font=('Courier', font_size))

#  Create "game" instance to provide access to control buttons, continuous real time update of time, scores, and
#  selected options from game settings.
game = Game_Control()

#  Create and initialize status display of team scores, contacts, and total time elapsed.
Label(frame, text='BLUE', foreground='blue', font =('Courier', font_size, 'bold')).grid(row=1,column=1,padx=3, pady=3)
Label(frame, text='RED', foreground='red', font =('Courier', font_size, 'bold')).grid(row=1,column=2,padx=3, pady=3)
Label(frame, text='Contacts', wraplength=210, font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=2,column=0,padx=5, pady=5)
Label(frame, text='   Time', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=8,column=0,padx=5,pady=5)
Label(frame, text='   Score', wraplength=210,font=('Courier', font_size, 'bold'),justify=RIGHT).grid(row=9,column=0,padx=5,pady=5)
Label(frame, text=str(game.blue_score), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=9,column=1)
Label(frame, text=str(game.red_score), foreground='red', font=('Courier',font_size, 'bold')).grid(row=9,column=2)
Label(frame, text=str(game.blue_contacts), foreground='blue', font=('Courier',font_size, 'bold')).grid(row=2,column=1)
Label(frame, text=str(game.red_contacts), foreground='red', font=('Courier',font_size, 'bold')).grid(row=2,column=2)

Label(frame, text='0', foreground='blue', font=('Courier', font_size, 'bold'),
              justify=RIGHT).grid(row=8, column=1, padx=5, pady=5)
Label(frame, text='0', foreground='red', font=('Courier', font_size, 'bold'),
              justify=RIGHT).grid(row=8, column=2, padx=5, pady=5)

#  Create game control buttons
#  The "Settings" button allows players to configure whether team time is tracked (and how), and to select other
#  optional game variants.
settings_btn = ttk.Button(frame,text = 'Settings', style='my.TButton', command=game.Settings)
settings_btn.grid(row=18, column=1, padx=padx_size, pady=pady_size)

#  The "Start Game" button initializes a new game board (5x5 array of codenames), implementing any additional options
#  and parameters selected in game settings.
start_game_btn = ttk.Button(frame,text = 'Start Game', style='my.TButton', command=game.New_Game)
start_game_btn.grid(row=12, column=0, padx=padx_size, pady=pady_size)

#  The "Pause/Resume" button allows game play to be suspended for an indefinite period and then resumed.
pause_resume_btn = ttk.Button(frame,text = 'Pause/Resume', style='my.TButton', command=game.Pause_Resume)
pause_resume_btn.grid(row=15, column=0, padx=padx_size, pady=pady_size)
pause_resume_btn.state(['disabled'])

#  The "next_turn_btn" actually displays the color of the team which takes control of the board when pressed.  It is
#  initialized here to "Red Turn" since at the start of a new session (consisting of multiple alternating team turns),
#  the Blue team always goes first.
next_turn_btn = ttk.Button(frame,text = 'Red Turn', style='my.TButton', command=game.Next_Turn)
next_turn_btn.grid(row=12, column=1, padx=padx_size, pady=pady_size)
next_turn_btn.state(['disabled'])

#  The "Help" button displays a PDF document which contains the supplementary rules to the original codenames game.
help_btn = ttk.Button(frame, text = 'Help', style='my.TButton', command=Game_Control.Open_File)
help_btn.grid(row=18, column=0)

#  Images used in the game are based on a width/height of 270x187 px for a screen resolution of 1920x1200.  New
#  dimensions are calculated based on the resize factors calculated above for the current screen size.
new_width = int(width_resize*270)
new_height = int(height_resize*185)

#  Cards dict stores unique names for each image used in the game and its value which is a TKinter PhotoImage object.
#  To populate this dict, scan the "Assets_dir" where the game program resides, resize only "gif" files using the
#  Python Image Library (PIL) and store the resulting image in a subdirectory (/resize).  Use this image's base filename
#  as the Cards dict key and set its value to the PhotoImage object of the resized image file.
movie_files = []
Cards = {}
Assets_dir = os.getcwd() + '\\Assets\\'
files = list(os.scandir(Assets_dir))
for file in files:
    file_ext = file.name[-3:]
    file_basename = file.name[:-4]

    if file_ext == 'gif':
        temp_image = PIL.Image.open(Assets_dir + file.name)
        temp_image = temp_image.resize((new_width, new_height), PIL.Image.Resampling.LANCZOS)
        temp_image.save(Assets_dir + r'/resize/' + file.name)
        Cards[file_basename] = PhotoImage(file=Assets_dir + r'/resize/' + file.name)

    if file_ext == 'mp4':
        movie_files.append(file_basename + '.' + file_ext)



#  The Python codenames game replaces the spy master key card with a dynamically updated electronic version which can
#  be displayed on any mobile device running a web browser.  Connection settings must be provided for an FTP account to
#  allow the electronic key card to be displayed within a specified location.
Set_FTP()
