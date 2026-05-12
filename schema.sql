-- ============================================================
--  Mobile Banking — Full Database Schema
--  Run this entire file in Railway's SQL editor
-- ============================================================
-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE user_profile (
    user_id           INT AUTO_INCREMENT PRIMARY KEY,
    first_name        VARCHAR(100) NOT NULL,
    last_name         VARCHAR(100) NOT NULL,
    phone_number      VARCHAR(20) UNIQUE NOT NULL,
    password          VARCHAR(255) NOT NULL,
    email             VARCHAR(150),
    dob               DATE,
    nid               VARCHAR(50),
    balance           DECIMAL(15,2) DEFAULT 0.00,
    transaction_limit DECIMAL(15,2) DEFAULT 10000.00,
    profile_pic       VARCHAR(255) DEFAULT 'default-profile-pic.jpg',
    points            INT DEFAULT 0,
    tier              VARCHAR(20) DEFAULT 'Bronze',
    status            VARCHAR(20) DEFAULT 'active'
);

-- ── Admin ──────────────────────────────────────────────────────
CREATE TABLE admin_profile (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    phone_number  VARCHAR(20) UNIQUE NOT NULL,
    password      VARCHAR(255) NOT NULL,
    email         VARCHAR(150),
    nid           VARCHAR(50),
    dob           DATE,
    status        VARCHAR(20) DEFAULT 'pending'
);

-- ── Notifications ──────────────────────────────────────────────
CREATE TABLE notifications (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT NOT NULL,
    alerts    TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── History ───────────────────────────────────────────────────
CREATE TABLE history (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type    VARCHAR(100),
    trx_id  VARCHAR(20),
    account VARCHAR(100),
    amount  DECIMAL(15,2),
    time    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Send Money (local) ────────────────────────────────────────
CREATE TABLE send_money (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phone_no VARCHAR(20),
    name    VARCHAR(200),
    amount  DECIMAL(15,2),
    trx_id  VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Send Money International ──────────────────────────────────
CREATE TABLE send_money_international (
    id                        INT AUTO_INCREMENT PRIMARY KEY,
    user_id                   INT NOT NULL,
    trx_id                    VARCHAR(20) UNIQUE,
    account_no                VARCHAR(50),
    receivers_name            VARCHAR(200),
    amount_in_bdt             DECIMAL(15,2),
    amount_in_selected_country DECIMAL(15,2),
    country                   VARCHAR(100),
    created_at                DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Temporary International Transfer ─────────────────────────
CREATE TABLE temporary_send_money_international (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    trx_id         VARCHAR(20),
    account_no     VARCHAR(50),
    receivers_name VARCHAR(200),
    amount         DECIMAL(15,2),
    country        VARCHAR(100),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Add Money via Bank ────────────────────────────────────────
CREATE TABLE add_money_bank (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    acc_no  VARCHAR(50),
    amount  DECIMAL(15,2),
    trx_id  VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Add Money via Card ────────────────────────────────────────
CREATE TABLE add_money_card (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    card_no VARCHAR(50),
    amount  DECIMAL(15,2),
    trx_id  VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Scheduled Transactions ────────────────────────────────────
CREATE TABLE schedule_transactions (
    schedule_id    INT AUTO_INCREMENT PRIMARY KEY,
    sender_id      INT NOT NULL,
    receiver_id    INT NOT NULL,
    amount         DECIMAL(15,2),
    scheduled_time DATETIME,
    status         VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (sender_id) REFERENCES user_profile(user_id),
    FOREIGN KEY (receiver_id) REFERENCES user_profile(user_id)
);

-- ── Investments (options) ─────────────────────────────────────
CREATE TABLE investment_ads (
    investment_id INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(200),
    roi           DECIMAL(5,2),
    duration      INT COMMENT 'duration in months'
);

-- ── Investments (user) ────────────────────────────────────────
CREATE TABLE investment_user (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    investment_id INT,
    trx_id        VARCHAR(20) UNIQUE,
    amount        DECIMAL(15,2),
    return_amount DECIMAL(15,2),
    period        INT COMMENT 'months',
    start_date    DATE,
    end_date      DATE,
    status        VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id),
    FOREIGN KEY (investment_id) REFERENCES investment_ads(investment_id)
);

-- ── Loans ─────────────────────────────────────────────────────
CREATE TABLE loans (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    trx_id        VARCHAR(20) UNIQUE,
    loan_amount   DECIMAL(15,2),
    interest_rate DECIMAL(5,2) DEFAULT 10.00,
    duration      INT COMMENT 'months',
    return_amount DECIMAL(15,2),
    status        VARCHAR(20) DEFAULT 'pending',
    remarks       TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Gift Cards ────────────────────────────────────────────────
CREATE TABLE gift_cards (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    card_no VARCHAR(50) UNIQUE,
    amount  DECIMAL(15,2),
    status  VARCHAR(20) DEFAULT 'active'
);

-- ── Pay Gas ───────────────────────────────────────────────────
CREATE TABLE pay_gas (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    name         VARCHAR(200),
    meter_no     VARCHAR(50),
    amount       DECIMAL(15,2),
    month        VARCHAR(20),
    multi_source VARCHAR(100),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Pay Electricity ───────────────────────────────────────────
CREATE TABLE pay_electricity (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    name         VARCHAR(200),
    meter_no     VARCHAR(50),
    amount       DECIMAL(15,2),
    month        VARCHAR(20),
    multi_source VARCHAR(100),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Pay WiFi ──────────────────────────────────────────────────
CREATE TABLE pay_wifi (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    name         VARCHAR(200),
    wifi_id      VARCHAR(50),
    amount       DECIMAL(15,2),
    month        VARCHAR(20),
    multi_source VARCHAR(100),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Messages ──────────────────────────────────────────────────
CREATE TABLE messages (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    sender_id    INT,
    recipient_id INT,
    message      TEXT,
    role         VARCHAR(20) DEFAULT 'user',
    timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Saved Contacts ────────────────────────────────────────────
CREATE TABLE saved_details (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name    VARCHAR(200),
    phone   VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
);

-- ── Admin Reports ─────────────────────────────────────────────
CREATE TABLE admin_reports (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    report_type VARCHAR(100),
    trx_id      VARCHAR(20),
    amount      DECIMAL(15,2),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Rewards (cashback tiers) ──────────────────────────────────
CREATE TABLE rewards (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    tier          VARCHAR(20) UNIQUE,
    cashback_rate DECIMAL(5,2)
);

-- Default reward tiers
INSERT INTO rewards (tier, cashback_rate) VALUES
    ('Bronze', 1.00),
    ('Silver', 2.00),
    ('Gold',   3.00);

-- ── Sample investment options ─────────────────────────────────
INSERT INTO investment_ads (name, roi, duration) VALUES
    ('Fixed Deposit 6M',  7.50,  6),
    ('Fixed Deposit 12M', 9.00, 12),
    ('Growth Plan 24M',  12.00, 24); 