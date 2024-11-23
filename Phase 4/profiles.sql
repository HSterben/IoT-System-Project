BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS profile (
  UserID INTEGER,
  RFID TEXT UNIQUE,
  Name TEXT,
  Temperature_Limit REAL,
  Humidity_Limit REAL,
  Light_Limit REAL,
  PRIMARY KEY(UserID)
);

--Inserting Profiles into the Database! #ILoveIoT
INSERT OR IGNORE INTO profile (UserID, RFID, Name, Temperature_Limit, Humidity_Limit, Light_Limit)
VALUES (1, '8D DF F6 30', 'Donald Trump', 23.5, 50, 1700);
INSERT OR IGNORE INTO profile (UserID, RFID, Name, Temperature_Limit, Humidity_Limit, Light_Limit)
VALUES (2, '7D DD FF 31', 'Ilan Trutner', 10, 60, 1300);
INSERT OR IGNORE INTO profile (UserID, RFID, Name, Temperature_Limit, Humidity_Limit, Light_Limit)
VALUES (3, 'ED 7C 06 31', 'Harry Potter', 20, 55, 500);
INSERT OR IGNORE INTO profile (UserID, RFID, Name, Temperature_Limit, Humidity_Limit, Light_Limit)
VALUES (4, 'ED 7C 06 32', 'Elvis Presley', 18, 45, 1000);

COMMIT;
