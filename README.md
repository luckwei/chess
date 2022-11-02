# CHESS

Building a Chess App with tkinter in Python

## About this project

I do love chess + I love coding so why not try practicing my Python skills relating to tkinter and OOP? The inspiration started out with seeing [ArjanCodes' chess refactoring video](https://youtu.be/n0i4SqjQdis) in my Subscriptions tab! OH btw **Hikaru** got me back into chess after around 5 years of not playing it, huge thanks!

So I challenged myself to try to code a version of Chess without watching the video and then come back to look at it when I decided I've done a fair bit of work.

## About Me

Hi I'm commonly known as **Luck** and I'm completing my Masters of Data Science but I have a passion for programming and creating mini projects in my spare time.
This is all done as part of a humble learning journey!

## Resources

[Chess Sprites by Cburnett](https://en.wikipedia.org/wiki/User:Cburnett/GFDL_images/Chess) (retrieved from WikiCommons)
[ArjanCodes' chess refactoring code](https://github.com/ArjanCodes/2022-chessroast)

## DEVELOPMENT LOG

> **29/10/22 CASTLING**
>
>As the title says! Might take longer till the next update!
>
>>**Game Logic**
>>
>>1. Castling is now possible! Logic was a tough one to implement! Trust me, it had 3/4 additional rules :)
>>
>>**Future developments planned**
>>
>> - To wrap things up, the promotion! By default Queen for now
>> - Implement checkmate if possible moves of current color == 0
>> - Implement check UI! Maybe implement hover UI for castling
>> - DRAWS: implement stalemate if possible moves == 0 but king currently checked
>> - SOUND?
>
> **28/10/22 Almost there**
>
> Game logic has been reset to normal chess, where the player can select their pieces and their moves, except.. for castling. UI is also slightly richer.
>
>>**Game Logic**
>>
>> - Implemented Legal Move checks! Very important and was indeed rather difficult in comparison.
>> - Back to normal chess, no priorities on captures over movement
>>
>> **UI/UX**
>>
>> - Removed invalid piece highlight for now for succinctness
>> - Selection feature implemented, click-click mode
>> - Highlights are also differing between capture, moving to light and moving to dark squares. Neat!
>
> **27/10/22 WOW Improvements**
> Game logic has been changed to -SerialKiller Chess- where pieces must prioritise capturing enemy pieces over usual movement. If multiple targets are available, kills one at random, same goes for movement.
>> **Game Logic**
>>
>> - All basic movements of all pieces (including the pesky pawn: en-passant)
>> - Applied almost all checking criteria (eg. avoid capturing own pieces, unable to move with obstruction)
>> - Board no longer jitters upon occassional piece movement and board reset, UI improvement!
>>
>> **UI/UX**
>>
>> - Hovering over pieces will show indicator of possible moves in white or unmovable pieces in red
>>
>> **Future developments**
>>
>> - General: Castling logic
>> - General: King checks
>> - Serial-Killer-Chess: Randomised kills could be weighted based on captured Piece Value
>> - Serial-Killer-Chess: Logic could be changed to 'must kill if any piece can' instead of each piece
>>
> **25/10/22 Update! Revamp**
>
>Refactored code based on inspiration for Uncle Arjan and developed till almost similar functionalities as the previous pitstop. I am actually learning so much about OOP, decoupling etc, this is good!
>
>> **Current functionalities**
>>
>> - Displays board and resets on 'q' key
>> - Basic chess piece movement (but RANDOM!)
>> - Accounts for turns
>> - Pieces can be captured (overwritten)
>>
>> **Main features to be developed**
>>
>> - King captured logic (I make the rules here and for now, I'll dictate the game is won when the king is CAPTURED)
>> - King check logic to prevent illegal (/pin) moves
>> - Pieces should not be able to jump over things (except ♞)
>> - Castling? ♔♖♚♜
>> - Pawn moves ugh (Em-peasant as Hikaru Nakamura would say)
>> - PROMOTING A PAWN UGHHHH I HATE PAWNS♟♟
>> - Unable to murder your own pieces (or maybe..)
>
> **22/10/22 Start of revamp**
> And right after this commit, despite being far off from a fully functioning chess game with all the logic inputted, I have decided to consult the video and see how different our solutions are. Pretty amazed and will take inspiration from here to refactor the chess and continue from then on again!
>
> **12/10/22 Get set, GO**
> By records, the project folder was created on this day