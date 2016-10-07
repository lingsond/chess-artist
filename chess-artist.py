"""
A. Program name
Chess Artist

B. Program description
It is a python script that can annotate a chess pgn file with
static evaluation of an engine.

C. License notice
This program is free software, you can redistribute it and/or modify
it under the terms of the GPLv3 License as published by the
Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License (LICENSE)
along with this program, if not visit https://www.gnu.org/licenses/gpl.html

D. Dependent modules and/or programs
1. python-chess
https://pypi.python.org/pypi/python-chess

E. Programming language
1. Python v2.7.11
https://www.python.org/

F. Other
1. See also the README.txt for some useful informations.
"""

import subprocess
import os
import sys
import time
import chess
from chess import pgn

# Constants
APP_NAME = 'Chess Artist'
APP_VERSION = '0.1.0'
BOOK_MOVE_LIMIT = 30
BOOK_SEARCH_TIME = 200

def PrintProgram():
    """ Prints program name and version """
    print('%s %s\n' %(APP_NAME, APP_VERSION))
    
def DeleteFile(fn):
    """ Delete fn file """
    if os.path.isfile(fn):
        os.remove(fn)

def CheckFile(fn):
    """ Verify if fn is present or not.
        If file is not available the program will exit.
    """
    if not os.path.isfile(fn):
        print('Error! %s is missing' %(fn))
        sys.exit(1)   

def EvaluateOptions(opt):
    """ Convert opt list to dict and returns it """
    return dict([(k, v) for k, v in zip(opt[::2], opt[1::2])])

def GetOptionValue(opt, optName, var):
    """ Returns value of opt dict given the key """
    if opt.has_key(optName):
        var = opt.get(optName)
        if optName == '-staticeval':
            var = int(var)
    return var

class Analyze(object):
    """ An object that will read and annotate games in a pgn file """
    def __init__(self, infn, outfn, eng, bookTypeOpt, useStaticEvalOpt):
        """ Initialize """
        self.infn = infn
        self.outfn = outfn
        self.eng = eng
        self.bookTypeOpt = bookTypeOpt
        self.useStaticEvalOpt = useStaticEvalOpt
        self.writeCnt = 0
        self.isCereMoveFound = False

    def UciToSanMove(self, pos, uciMove):
        """ Returns san move given uci move """
        board = chess.Board(pos)
        board.push(chess.Move.from_uci(uciMove))
        sanMove = board.san(board.pop())
        return sanMove

    def PrintEngineIdName(self):
        """ Prints engine id name """
        print('Engine name: %s' %(self.GetEngineIdName()))

    def WriteMoves(self, side, fmvn, sanMove, cereMove, staticEval):
        """ Write moves and comments to the output file """
        bookComment = 'cerebellum book'
        
        # Write the move and comments
        with open(self.outfn, 'a+') as f:
            self.writeCnt += 1

            # If side to move is white
            if side:
                if self.useStaticEvalOpt:
                    assert staticEval is not None, 'Error! static eval is not correct.'
                    if self.isCereMoveFound:
                        f.write('%d. %s {%+0.2f} (%d. %s {%s}) ' %(fmvn, sanMove, staticEval, fmvn, cereMove, bookComment))
                    else:
                        f.write('%d. %s {%+0.2f} ' %(fmvn, sanMove, staticEval))
                else:
                    if self.isCereMoveFound:
                        f.write('%d. %s (%d. %s {%s}) ' %(fmvn, sanMove, fmvn, cereMove, bookComment))
                    else:
                        f.write('%d. %s ' %(fmvn, sanMove))
                        
            # Else if side to move is black
            else:
                if self.useStaticEvalOpt:
                    assert staticEval is not None, 'Error! static eval is not correct.'
                    if self.isCereMoveFound:
                        f.write('%d... %s {%+0.2f} (%d... %s {%s}) ' %(fmvn, sanMove, staticEval, fmvn, cereMove, bookComment))
                    else:
                        f.write('%s {%+0.2f} ' %(sanMove, staticEval))
                else:
                    if self.isCereMoveFound:
                        f.write('%d... %s (%d... %s {%s}) ' %(fmvn, sanMove, fmvn, cereMove, bookComment))
                    else:
                        f.write('%s ' %(sanMove))

                # Format output, don't write in one long line.
                if self.isCereMoveFound:
                    if self.writeCnt >= 2:
                        self.writeCnt = 0
                        f.write('\n')
                elif self.useStaticEvalOpt:
                    if self.writeCnt >= 4:
                        self.writeCnt = 0
                        f.write('\n')
                else:
                    if self.writeCnt >= 10:
                        self.writeCnt = 0
                        f.write('\n')

    def GetEngineIdName(self):
        """ Returns the engine id name """
        engineIdName = self.eng[0:-4]

        # Run the engine
        p = subprocess.Popen(self.eng, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Send command to engine.
        p.stdin.write("uci\n")
        
        # Parse engine replies.
        for eline in iter(p.stdout.readline, ''):
            line = eline.strip()

            # Save id name.
            if 'id name ' in line:
                idName = line.split()
                engineIdName = ' '.join(idName[2:])            
            if "uciok" in line:           
                break
        p.stdin.write('quit\n')
        p.communicate()
        return engineIdName

    def GetCerebellumBookMove(self, pos):
        """ Returns a move from cerebellum book """
        # Run the engine.
        p = subprocess.Popen(self.eng, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Send command to engine.
        p.stdin.write("uci\n")

        # Parse engine replies.
        for eline in iter(p.stdout.readline, ''):
            line = eline.strip()
            if "uciok" in line:
                break

        # Set the path of Brainfish cerebellum book. Make sure the Brainfish engine,
        # the script and the cerebellum book are on the same directory.
        p.stdin.write("setoption name BookPath value Cerebellum_Light.bin\n")

        # Set threads to 1 just in case the default threads is changed in the future.
        p.stdin.write("setoption name Threads value 1\n")
                
        # Send command to engine.
        p.stdin.write("isready\n")
        
        # Parse engine replies.
        for eline in iter(p.stdout.readline, ''):
            line = eline.strip()
            if "readyok" in line:
                break
                
        # Send commands to engine.
        p.stdin.write("ucinewgame\n")
        p.stdin.write("position fen " + pos + "\n")

        # Hack: We will give a 100 ms movetime, if the engine does not consume
        # this amount of time, then it is using the cerebellum book. The value in 
        # BOOK_SEARCH_TIME can be tuned as it may probably differ from system to system.
        startTime = time.clock()
        endTime = None
        p.stdin.write("go movetime %d\n" %(BOOK_SEARCH_TIME))

        # Parse the output and extract the bestmove.
        for eline in iter(p.stdout.readline, ''):        
            line = eline.strip()
            if 'bestmove ' in line:
                moveLine = line.split()[1]
                bestMove = moveLine.strip()
                
                # Get the time now.
                endTime = time.clock()
                break
        p.stdin.write('quit\n')
        p.communicate()
        assert endTime is not None, 'Error! something is wrong in getting the cerebellum book move.'

        # Convert uci move to san move format.
        bestMove = self.UciToSanMove(pos, bestMove)

        # If it successfully gets the cerebellum book move, it has use only a small elapsed time.
        if 1000 * (endTime - startTime) < BOOK_SEARCH_TIME/4:
            # True indicates that the bestMove is from cerebellum book.
            return bestMove, True
        return bestMove, False

    def GetStaticEval(self, pos):
        """ Returns static eval by running the engine,
            setup position pos and send eval command.
        """
        score = -32000.0

        # Run the engine.
        p = subprocess.Popen(self.eng, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Send command to engine.
        p.stdin.write("uci\n")

        # Parse engine replies.
        for eline in iter(p.stdout.readline, ''):
            line = eline.strip()
            if "uciok" in line:
                break
                
        # Send command to engine.
        p.stdin.write("isready\n")
        
        # Parse engine replies.
        for eline in iter(p.stdout.readline, ''):
            line = eline.strip()
            if "readyok" in line:
                break
                
        # Send commands to engine.
        p.stdin.write("ucinewgame\n")
        p.stdin.write("position fen " + pos + "\n")
        p.stdin.write("eval\n")

        # Parse the output and extract the engine static eval.
        for eline in iter(p.stdout.readline, ''):        
            line = eline.strip()
            if 'Total Evaluation: ' in line:
                first = line.split('(')[0]
                score = float(first.split()[2])
                break
        p.stdin.write('quit\n')
        p.communicate()
        assert score != -32000.0, 'Error! something is wrong in static eval calculation.'
        return score

    def Annotate(self):
        """ Parse the pgn file and annotate the games """
        # Get engine id name for the Annotator tag.
        engIdName = self.GetEngineIdName()

        # Disable bookTypeOpt if engine is not Brainfish.
        if self.bookTypeOpt == 'cerebellum':
            brainFishEngine = self.GetEngineIdName()
            if 'Brainfish' not in brainFishEngine:
                self.bookTypeOpt = None
                print('\nWarning!! engine is not Brainfish, cerebellum book is disabled.\n')
        
        # Open the input pgn file
        pgnHandle = open(self.infn, 'r')

        # Read the input pgn file using the python-chess module.
        game = chess.pgn.read_game(pgnHandle)

        # Used for displaying progress in console.
        gameCnt = 0

        # Loop thru the games.
        while game:
            gameCnt += 1

            # Used for formatting the output.
            self.writeCnt = 0

            # Show progress in console.
            print('Annotating game %d...' %(gameCnt))

            # We don't access cere book if isCereEnd is true.
            isCereEnd = False

            # Save the tag section of the game.
            for key, value in game.headers.items():
                with open(self.outfn, 'a+') as f:
                    f.write('[%s \"%s\"]\n' %(key, value))

            # Write the annotator tag.
            with open(self.outfn, 'a+') as f:
                f.write('[Annotator "%s"]\n\n' %(engIdName))

            # Save result to be written later as game termination marker.
            res = game.headers['Result']

            # Loop thru the moves.
            gameNode = game        
            while gameNode.variations:
                side = gameNode.board().turn
                fmvn = gameNode.board().fullmove_number             
                nextNode = gameNode.variation(0)                      
                sanMove = nextNode.san()

                # Try to get a cerebellum book move.
                self.isCereMoveFound = False
                cereBookMove = None
                if self.bookTypeOpt == 'cerebellum':                    
                    if not isCereEnd:
                        # Use FEN before a move.
                        fenBeforeMove = gameNode.board().fen()
                        cereBookMove, self.isCereMoveFound = self.GetCerebellumBookMove(fenBeforeMove)

                    # End trying to find cerebellum book beyond BOOK_MOVE_LIMIT.
                    if not self.isCereMoveFound and fmvn > BOOK_MOVE_LIMIT:
                        isCereEnd = True

                # Use FEN after a move to get the static eval.
                staticEval = None
                if self.useStaticEvalOpt:
                    fenAfterMove = nextNode.board().fen()
                    staticEval = self.GetStaticEval(fenAfterMove)

                # Write moves and comments.
                self.WriteMoves(side, fmvn, sanMove, cereBookMove, staticEval)

                # Read the next position.
                gameNode = nextNode

            # Write the result and a space between games.
            with open(self.outfn, 'a') as f:
                f.write('%s\n\n' %(res))

            # Read the next game.
            game = chess.pgn.read_game(pgnHandle)

        # Close the file handle.
        pgnHandle.close()
        
def main(argv):
    """ start """
    PrintProgram()

    # Initialize
    inputFile = 'src.pgn'
    outputFile = 'out_src.pgn'
    engineName = 'engine.exe'
    bookTypeOption = None # [None, cerebellum, polyglot]
    useStaticEvalOption = 0
    cereBookFile = 'Cerebellum_Light.bin'
    
    # Evaluate the command line options.
    options = EvaluateOptions(argv)
    if len(options):
        inputFile = GetOptionValue(options, '-inpgn', inputFile)
        outputFile = GetOptionValue(options, '-outpgn', outputFile)
        engineName = GetOptionValue(options, '-eng', engineName)
        bookTypeOption = GetOptionValue(options, '-book', bookTypeOption)
        useStaticEvalOption = GetOptionValue(options, '-staticeval', useStaticEvalOption)

    # Verify presence of input pgn and engine file.
    CheckFile(inputFile)
    CheckFile(engineName)

    # Delete existing output file.
    DeleteFile(outputFile)
    
    # Disable use of cerebellum book when Cerebellum_Light.bin is missing.
    if bookTypeOption == 'cerebellum':
        if not os.path.isfile(cereBookFile):
            bookTypeOption = None
            print('Warning! cerebellum book is missing.')
            
    # Declare a variable g of class Analyze.
    g = Analyze(inputFile, outputFile, engineName, bookTypeOption, useStaticEvalOption)

    # Print engine id name.
    g.PrintEngineIdName()

    # Call method Annotate of class Analyze to annotate the game.
    g.Annotate()      

    print('Done!!\n')    

if __name__ == "__main__":
    main(sys.argv[1:])

