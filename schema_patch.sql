-- Run this on Railway to add missing columns

-- messages: add is_read column
ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;

-- pay_gas: add installment columns
ALTER TABLE pay_gas ADD COLUMN IF NOT EXISTS installment INT DEFAULT NULL;
ALTER TABLE pay_gas ADD COLUMN IF NOT EXISTS due_1 DATE DEFAULT NULL;
ALTER TABLE pay_gas ADD COLUMN IF NOT EXISTS due_2 DATE DEFAULT NULL;
ALTER TABLE pay_gas ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'paid';

-- pay_wifi: add installment columns
ALTER TABLE pay_wifi ADD COLUMN IF NOT EXISTS installment INT DEFAULT NULL;
ALTER TABLE pay_wifi ADD COLUMN IF NOT EXISTS due_1 DATE DEFAULT NULL;
ALTER TABLE pay_wifi ADD COLUMN IF NOT EXISTS due_2 DATE DEFAULT NULL;
ALTER TABLE pay_wifi ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'paid';

-- pay_electricity: add installment columns
ALTER TABLE pay_electricity ADD COLUMN IF NOT EXISTS installment INT DEFAULT NULL;
ALTER TABLE pay_electricity ADD COLUMN IF NOT EXISTS due_1 DATE DEFAULT NULL;
ALTER TABLE pay_electricity ADD COLUMN IF NOT EXISTS due_2 DATE DEFAULT NULL;
ALTER TABLE pay_electricity ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'paid';

-- admin_profile: add unauthorized as default status for new signups
-- (change status default from 'pending' to 'unauthorized' to match approvals query)
ALTER TABLE admin_profile MODIFY COLUMN status VARCHAR(20) DEFAULT 'unauthorized';

-- schedule_transactions: add status column
ALTER TABLE schedule_transactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';
