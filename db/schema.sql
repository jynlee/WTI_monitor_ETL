CREATE DATABASE IF NOT EXISTS exchange_rate
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE exchange_rate;

CREATE TABLE IF NOT EXISTS usd_krw_daily (
  trade_date  DATE           NOT NULL,
  usd_krw     DECIMAL(10,2)  NOT NULL,
  created_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS wti_daily (
  trade_date  DATE           NOT NULL,
  wti_usd     DECIMAL(10,2)  NOT NULL,
  created_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
