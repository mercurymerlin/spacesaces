-- SpacesAces - SQL schema for game tree analysis
-- Copyright (C) 2024 John Barron <jbarronuk@gmail.com>
--
-- This file is part of SpacesAces.
--
-- SpacesAces is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- SpacesAces is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with SpacesAces.  If not, see <https://www.gnu.org/licenses/>.

CREATE TABLE "GameTree" (
    "StartState" 	INTEGER,
    "GameState"  	INTEGER NOT NULL,
    "Board"      	TEXT NOT NULL,
    "Score"      	INTEGER NOT NULL,
	"ActiveSpaces"	INTEGER NOT NULL,
	"TotLineLen"	INTEGER NOT NULL,
	"LineLenVal" 	REAL NOT NULL,	
	"GameOver" 	 	CHAR(1) NOT NULL DEFAULT '0',
    "DepthLvl"   	INTEGER NOT NULL,
    PRIMARY KEY("GameState")
);

CREATE INDEX idx_score ON GameTree(Score);
CREATE INDEX idx_depth ON GameTree(DepthLvl);
CREATE INDEX idx_start_state ON GameTree(StartState, GameState);
CREATE UNIQUE INDEX idx_unique_board ON GameTree(StartState, Board);

CREATE TABLE "Moves" (
    "StartState" 	INTEGER,
    "FromState" 	INTEGER NOT NULL,
    "ToState"   	INTEGER NOT NULL,
    "MoveFromRow"   INTEGER, 
    "MoveFromCol"   INTEGER,
    "MoveToRow"     INTEGER,    
    "MoveToCol"     INTEGER,	
    FOREIGN KEY("FromState") REFERENCES "GameTree"("GameState"),
    FOREIGN KEY("ToState") REFERENCES "GameTree"("GameState"),
    PRIMARY KEY("FromState", "ToState")
);

CREATE INDEX idx_movestate ON Moves(StartState, FromState);
CREATE INDEX idx_fromstate ON Moves(FromState, ToState);
CREATE INDEX idx_tostate ON Moves(ToState, FromState);