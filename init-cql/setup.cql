CREATE KEYSPACE IF NOT EXISTS my_keyspace
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE my_keyspace;

/* Might be a good idea to consult whether x and y are good candidate for a pk
   Shouldn't we make them integers? (0 to 300) ??
   lines */

CREATE TABLE IF NOT EXISTS cells (
  x TEXT,
  y TEXT,
  json_data TEXT,
  PRIMARY KEY (x, y)
);
