-- データベース
CREATE DATABASE tradingbot;

-- テーブル
CREATE TABLE `entry` (
    `process_id` int NOT NULL AUTO_INCREMENT,
    `date` timestamp(6) NOT NULL,
    `side` varchar(255) NOT NULL,
    `price` int unsigned NOT NULL,
    PRIMARY KEY (`process_id`)
);

CREATE TABLE `position` (
    `side` varchar(255) NOT NULL,
    `size` float NOT NULL
);

CREATE TABLE `execution_history` (
    `id` bigint unsigned NOT NULL AUTO_INCREMENT,
    `date` datetime(6) NOT NULL,
    `side` varchar(255) NOT NULL,
    `price` int unsigned NOT NULL,
    `size` float unsigned NOT NULL,
    PRIMARY KEY (`id`),
    KEY `index_execution_history_1` (`date`)
);

CREATE TABLE `ticker` (
    `date` timestamp NOT NULL,
    `best_bid` int unsigned NOT NULL,
    `best_ask` int unsigned NOT NULL
);

insert into
    ticker
values
    (now(), 0, 0);

commit;