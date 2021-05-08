-- データベース
CREATE DATABASE tradingbot;

-- テーブル
CREATE TABLE `entry` (`side` varchar(255) NOT NULL);

CREATE TABLE `execution_history` (
    `id` bigint unsigned NOT NULL AUTO_INCREMENT,
    `date` datetime(6) NOT NULL,
    `side` varchar(255) NOT NULL,
    `price` int unsigned NOT NULL,
    `size` decimal(65, 30) unsigned NOT NULL,
    PRIMARY KEY (`id`),
    KEY `execution_history1` (`date`)
);

CREATE TABLE `ohlcv_1min_bitflyer_spot` (
  `date` datetime NOT NULL,
  `open` int unsigned NOT NULL,
  `high` int unsigned NOT NULL,
  `low` int unsigned NOT NULL,
  `close` int unsigned NOT NULL,
  `volume` decimal(65,8) unsigned NOT NULL,
  KEY `ohlcv_1min_bitflyer_spot1` (`date`)
);

CREATE TABLE `ohlcv_1min_bitflyer_perp` (
  `date` datetime NOT NULL,
  `open` int unsigned NOT NULL,
  `high` int unsigned NOT NULL,
  `low` int unsigned NOT NULL,
  `close` int unsigned NOT NULL,
  `volume` decimal(65,8) unsigned NOT NULL,
  KEY `ohlcv_1min_bitflyer_perp1` (`date`)
);

CREATE TABLE `coinapi_key` (
  `key` varchar(255) NOT NULL,
  PRIMARY KEY (`key`)
);