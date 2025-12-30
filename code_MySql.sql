CREATE DATABASE sae302;

CREATE USER 'maxgui'@'%' IDENTIFIED BY 'toto';
GRANT ALL PRIVILEGES ON sae302.* TO 'maxgui'@'%';

FLUSH PRIVILEGES;

USE sae302;
DROP TABLE routeur;

CREATE TABLE routeur (nom VARCHAR(50) PRIMARY KEY, adresse_ip VARCHAR(20), port INT,cle_pub_n TEXT, cle_pub_e TEXT, ping DATETIME);