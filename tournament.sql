-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

--Create the database
CREATE DATABASE tournament_db;

--Connect to the above database
\CONNECT tournament_db;

--Tournanment table create script
CREATE TABLE tournament (
tournament_id SERIAL PRIMARY KEY,
tournament_name VARCHAR
);

--Player table creat script. This table contains a foreign key reference to tournament table
CREATE TABLE players (
player_id SERIAL PRIMARY KEY,
player_name VARCHAR,
player_tournamentId INT,
OMW INT, --This column will hold the sum of the wins of all the opponents this player has defeated. initially it will 0 during registration
CONSTRAINT player_tournament_fk FOREIGN KEY (player_tournamentId) REFERENCES tournament (tournament_id) MATCH SIMPLE
);

--Matches table create script. This table contains a foreign key reference to tournament table
--This table will have a unique match ID (PK), torunament id (FK) for the that match belongs to winner's player id (initially null)
CREATE TABLE matchdetails (
match_id SERIAL PRIMARY KEY,
match_tournamentId INT,
first_opponentId INT,
second_opponentId INT,
winner_playerId INT,
match_draw BIT(1),
match_byewin BIT(1),
CONSTRAINT match_tournament_fk FOREIGN KEY (match_tournamentId) REFERENCES tournament (tournament_id) MATCH SIMPLE
);

--Add unique constraint to tournament name
ALTER TABLE tournament ADD CONSTRAINT unique_tournament_name UNIQUE (tournament_name);

--Create Player standings view
 SELECT p.player_id,
    p.player_name,
    sum(
        CASE
            WHEN m.winner_playerid = p.player_id OR m.match_byewin = '1' THEN 1
            ELSE 0
        END) AS won,
    count(m.match_id) AS played,
    p.omw,
    p.player_tournamentid
   FROM players p
     LEFT JOIN matchdetails m ON m.match_tournamentid = p.player_tournamentid AND (m.first_opponentid = p.player_id OR m.second_opponentid = p.player_id)
  WHERE p.player_tournamentid IS NOT NULL
  GROUP BY p.player_id, p.player_name
  ORDER BY sum(
        CASE
            WHEN m.winner_playerid = p.player_id OR m.match_byewin = '1' THEN 1
            ELSE 0
        END) DESC, p.omw DESC;		