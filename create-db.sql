CREATE DATABASE IF NOT EXISTS musicapp;


USE musicapp;


DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS songs;


CREATE TABLE users
(
    userid       int not null AUTO_INCREMENT,
    username     varchar(64) not null,
    pwdhash      varchar(256) not null,
    PRIMARY KEY  (userid),
    UNIQUE       (username)
);


ALTER TABLE users AUTO_INCREMENT = 80001;  -- starting value


CREATE TABLE jobs
(
    jobid             int not null AUTO_INCREMENT,
    userid            int not null,
    status            varchar(256) not null,  -- uploaded, completed, error, processing...
    originaldatafile  varchar(256) not null,  -- original TXT filename from user
    datafilekey       varchar(256) not null,  -- TXT filename in S3 (bucketkey)
    emotion           varchar(256) default null,
    valence           float not null default 0.0,  -- computed valence
    energy            float not null default 0.0,  -- computed energy
    PRIMARY KEY (jobid),
    FOREIGN KEY (userid) REFERENCES users(userid),
    UNIQUE      (datafilekey)
);

ALTER TABLE jobs AUTO_INCREMENT = 1001;  -- starting value

CREATE TABLE songs
(
    songid       int not null AUTO_INCREMENT,
    userid       int not null,
    jobid        int not null,
    songname     varchar(256) not null,
    songartist   varchar(256) not null,
    songgenre    varchar(256) not null,
    PRIMARY KEY  (songid),
    FOREIGN KEY  (userid) REFERENCES users(userid),
    FOREIGN KEY  (jobid) REFERENCES jobs(jobid),
    UNIQUE       (songname)
);


--
-- Insert some users to start with:
-- 
-- PWD hashing: https://phppasswordhash.com/
--
INSERT INTO users(username, pwdhash)  -- pwd = abc123!!
            values('p_sarkar', '$2y$10$/8B5evVyaHF.hxVx0i6dUe2JpW89EZno/VISnsiD1xSh6ZQsNMtXK');


INSERT INTO users(username, pwdhash)  -- pwd = abc456!!
            values('e_ricci', '$2y$10$F.FBSF4zlas/RpHAxqsuF.YbryKNr53AcKBR3CbP2KsgZyMxOI2z2');


INSERT INTO users(username, pwdhash)  -- pwd = abc789!!
            values('l_chen', '$2y$10$GmIzRsGKP7bd9MqH.mErmuKvZQ013kPfkKbeUAHxar5bn1vu9.sdK');


-- insert job for testing
INSERT INTO jobs(userid, status, originaldatafile, datafilekey)
            values(80001, 'uploaded', 'test01.txt', 'musicapp/test01.txt');

--
-- creating user accounts for database access:
--
-- ref: https://dev.mysql.com/doc/refman/8.0/en/create-user.html
--


DROP USER IF EXISTS 'musicapp-read-only';
DROP USER IF EXISTS 'musicapp-read-write';


CREATE USER 'musicapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'musicapp-read-write' IDENTIFIED BY 'def456!!';


GRANT SELECT, SHOW VIEW ON musicapp.* 
      TO 'musicapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON musicapp.* 
      TO 'musicapp-read-write';
      
FLUSH PRIVILEGES;


--
-- done
--
