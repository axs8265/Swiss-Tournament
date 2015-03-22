#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament_db")


def deleteMatches():
    """Remove all the match records from the database."""
    conn = connect()
    cursor = conn.cursor()
    #Delete all the match data
    cursor.execute("DELETE FROM matchdetails")    
    conn.commit()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database."""
    conn = connect()
    cursor = conn.cursor()
    #Delete all records from player table
    cursor.execute("DELETE FROM players")
    conn.commit()
    conn.close()

def countPlayers():
    """Returns the number of players currently registered."""
    conn = connect()
    cursor = conn.cursor()
    #Count all the records from player table with valid tournament id, to get the count of all the registered players
    cursor.execute("SELECT COUNT(player_tournamentId) FROM players")
    count = cursor.fetchone()[0]
    conn.close()    
    return count

def createTournament(tournament_name):
    """Multiple tournaments are allowed. This function Creates new tournament in the database. This function needs to be called first before any
    and player can be registered
    Args:
      tournament_name: the name of the tournament_name. Name of the tournament needs not be unique.
    """    
    sql = "INSERT INTO tournament (tournament_name) VALUES (%s)  RETURNING tournament_id;"
    conn = connect()
    cursor = conn.cursor()
    if isinstance(tournament_name, str):
        cursor.execute(sql, (tournament_name,))
        conn.commit()
        t_id = cursor.fetchone()[0]
        conn.close()        
        return t_id
    else:
        #not a valid name
        return -1

def registerPlayer(name, tournament_id=-1):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
    
    If a valid tournament id is provided, a player rec will be created and assigned with the tournament. If a valid tournament id is not
    provided, then a new player record will still be created but not assigned to any tournament.

    Args:
      name: the player's full name (need not be unique).
      OPTIONAL - tournament_id: id of the tournament for which the player wants to register, since there can be more than one tournaments 
      going simultaneously. Not providing a tournament id will create a new player in database not signed up for any tournamnet.
    """    
    sql_insert = "INSERT INTO players (player_name, player_tournamentId, omw) VALUES (%s, %s, %s) RETURNING player_id; "
    
    #Get valid tournament_id (or None)
    t_id = validate_tournamentId(tournament_id)    
    if isinstance(name, str) and name != '':
        conn = connect()
        cursor = conn.cursor()
        #insert player into the database along with the tournament id (or None if a valid tournament name is not supplied)
        #The OMW will be zero initially
        cursor.execute(sql_insert, (name, t_id, 0,))        
        conn.commit()        
        p_id = cursor.fetchone()[0]
        conn.close()        
        return p_id
    else:
        #not a valid name
        return -1

def signupfortournament(player_id, tournament_id):
    """
    Sign-up a player to a tournament .

    Args:
        player_id: unique id of the player who is not signed up with any tournament
        tournament_id: the tournament id of a tournamnet which is not is progress alreay, i.e. no pairings have been done for the tournamnet
    """
    sql_update = "UPDATE players SET player_tournamentId = %s WHERE player_id = %s;"

    if validate_tournamentId(tournament_id) is None:
        print "Unable to sign-up. This tournament does not exists or alreay in progress"
        return

    if validate_playerId(player_id) is None:
        print "Unable to sign-up. This player does not exists or is already signed up with another tournament"
        return

    conn = connect()
    cursor = conn.cursor()
    cursor.execute(sql_update, (tournament_id, player_id))
    conn.commit()
    conn.close()

def playerStandings(tournament_id):
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Args:
        tournament_id: the tournament id for which player standings are required    
    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """    
    #Exit if valid tournament id is not provided
    if isinstance(tournament_id, int) and tournament_id > 0:
        sql_select  = "select player_id, player_name, (won :: int), (played :: int) from vplayerstandings where player_tournamentid = %d ;" % tournament_id
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(sql_select)
        standings = cursor.fetchall()
        conn.close()
        return standings
    else:
        return None


def reportMatch(winner, loser, tournament_id, isdraw=False):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
      OPTIONAL - isdraw: True if a match is a draw, else false
    """
    if not isinstance(isdraw, bool):
        isdraw = False
    
    isdrawbit = '1' if isdraw else '0'


    sql_insert = "INSERT INTO matchdetails (match_tournamentid, first_opponentid, second_opponentid, winner_playerid, match_draw, match_byewin) VALUES (%s, %s, %s, %s, %s, '0') RETURNING match_id;"

    sql_updateOMW = "UPDATE players AS p SET OMW = (Select COUNT(m.winner_playerId) FROM matchdetails m WHERE m.winner_playerId = %s and m.match_byewin <> '1') WHERE p.player_id = %s;"
    # check if valid ids are provided
    if isinstance(winner, int) and isinstance(loser, int) and isinstance(tournament_id, int):
        conn = connect()
        cursor = conn.cursor()
        if isdraw:
            cursor.execute(sql_insert, (tournament_id, winner, loser, None, isdrawbit))
        else:
            cursor.execute(sql_insert, (tournament_id, winner, loser, winner, isdrawbit))
            #Since match in not a draw, update OMW as well
            cursor.execute(sql_updateOMW, (loser, winner))
        conn.commit()
        conn.close()
 
 
def swissPairings(tournament_id):
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    #Exit if valid tournament id is not provided
    if isinstance(tournament_id, int) and tournament_id > 0:
        sql_select  = "SELECT player_id, player_name FROM vplayerstandings WHERE player_tournamentid = %d ;" % tournament_id
        insert_sql = "INSERT INTO matchdetails (match_tournamentid,first_opponentid,second_opponentid, match_draw, match_byewin) VALUES (%s, %s, %s, %s, %s);"
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(sql_select)
        standings = cursor.fetchall()
        conn.close()
        pairs = []
        #If the number of player are not even, add a dummy record
        if len(standings)%2 != 0:            
            dummy = (-1, "ByeWin")
            standings.append(dummy)            

        #The standing are already sorted by wins and omw (Bye Win will not get any OMW points)
        #Create matches for all the consecutive records
        accu = 0
        while accu < len(standings):
            opp1 = standings[accu]
            accu+=1            
            opp2 = standings[accu]
            #cursor.execute(insert_sql, (tournament_id, opp1, opp2, '0','0'))
            accu+=1
            pairs.append(opp1+opp2)

        return pairs
    else:
        return None


def validate_tournamentId(tournament_id):
    """Validates and returns a tournament id.
  
    If a value is provided by user, this function will validate if a tournament exist in the database with the Id. If no tournamnet id 
    is found matching this value, it returns None.    
    
    Args:        
        tournament_id: the id of a tournamnet which is not is progress i.e. no pairings have been done for the tournamnet

    Returns:
      Valid tournament id matching the value provided by user, otherwise None.
    """
    
    sql_select = "SELECT tournament_id FROM tournament WHERE tournament_id = %s AND tournament_id NOT IN (SELECT DISTINCT match_tournamentId FROM matchdetails);"
    t_id = None    

    if isinstance(tournament_id, int) and tournament_id != -1:
        conn = connect()
        cursor = conn.cursor()        
        cursor.execute(sql_select, (tournament_id,))        
        t_res = cursor.fetchone()        
        if t_res is not None:
            t_id = t_res[0]
    
    return t_id


def validate_playerId(player_id):
    """Validates and returns a player id.
  
    This function will validate if a player exist in the database with the Id. If no player id 
    is found matching this value, it returns None.     
    
    Args:        
        player_id: the id of a player who has not signed-up for a tournament

    Returns:
      Valid tournament id matching the value provided by user, otherwise None.
    """
    sql_select = "SELECT player_id FROM players p WHERE p.player_id = %s AND p.player_tournamentId IS NULL;"
    t_id = None    

    if isinstance(player_id, int):
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(sql_select, (player_id,))        
        t_res = cursor.fetchone()
        #validate if a tournament id has been returned by the query
        if t_res is not None:
            t_id = t_res[0]       

    return t_id