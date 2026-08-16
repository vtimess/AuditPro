ALTER TABLE `ops_personnel`
  ADD COLUMN `chronic_disease` VARCHAR(32) NOT NULL DEFAULT '否' AFTER `education`;

UPDATE `ops_personnel`
SET `education` = '小学'
WHERE `education` IS NULL OR `education` = '';

UPDATE `ops_personnel`
SET `political_status` = '群众', `joined_party_at` = NULL
WHERE `political_status` IS NULL OR `political_status` = '' OR `political_status` = '群众';
