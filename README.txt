README:
This project contains SQL scripts and python API for creating and maintianing a tournament database.

tournament.sql - Contains create scripts for the DB objects:
	1) tournament_db - Tournament database
	2) tournament - contains tournament related information. Each row represents a tournament, multiple tournaments can be held simoultenously. More columns can be added to hold more infromation about a tournament.
	3) players - contains player related information. Column player_tournamentId referres to  represent which tournament a player plays in, if null, then player has not signed up for any tournament. OMW contains opponent match win points for each player, helping in better ranking system
	4) matchdetails - contains all the match related details. Each row contains opponents ids, winner's id, bit columns representing if a match was draw (1) or if it's a bye win (1).
	5) vplayerstandings - it's a databse view that returns current player standing for a particular tournament, order by their wins and OMW points (DESC :)

tournament.py - Contains API to access and maintain tournament(s). Users of this API can:
	1) Create a new tournament
	2) Register a player in the database. If a valid torunament id is provided, this API will create a new player's record and associate her/him with the tournanemt. Otherwise, only a new player will be created in the database who has not entered in a tournament.
	3) Sign-up an existing player (who is not participating in tournament) with tournament which has not yet started yet (no matches have been played for that tournament).
	4) Get player standings for a particular tournament.
	5) Report a match result. This will create a new record in matchdetails table with the results provided to the API. If the match is a draw, no winner id will be added to the match record. This API can also be extended to report bye win. This API is configured to ingore a bye for OMW points and vPlayersStanding is already designed to take into account a bye win for ranking.
	6) Get an opponent pairing list using Swiss Pairing method.
	
tournament_test.py - Consists of test methods to call and verify each API's functionality.

How to run:
	Call createtournament function to create a tournament first and use it's id to run other operations for the tournament. Look at tournament_test.py for code examples
	 