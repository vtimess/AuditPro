CREATE DATABASE IF NOT EXISTS `audit_pro`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `audit_pro`;

CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户主键',
  `openid` VARCHAR(64) NOT NULL COMMENT '微信 OpenID',
  `unionid` VARCHAR(64) NULL COMMENT '微信 UnionID',
  `real_name` VARCHAR(64) NOT NULL DEFAULT '微信用户' COMMENT '姓名',
  `avatar_url` VARCHAR(500) NULL COMMENT '头像地址',
  `mobile` VARCHAR(32) NULL COMMENT '手机号',
  `org_name` VARCHAR(128) NULL COMMENT '所属组织名称',
  `role_code` VARCHAR(32) NOT NULL DEFAULT 'ordinary_user' COMMENT '角色编码',
  `role_name` VARCHAR(32) NOT NULL DEFAULT '普通用户' COMMENT '角色名称',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '账号状态',
  `last_login_at` DATETIME NULL COMMENT '最后登录时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_user_openid` (`openid`),
  UNIQUE KEY `uk_sys_user_unionid` (`unionid`),
  KEY `idx_sys_user_status` (`status`),
  KEY `idx_sys_user_role_code` (`role_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小程序用户';

CREATE TABLE IF NOT EXISTS `sys_notification` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '消息主键',
  `user_id` BIGINT NOT NULL COMMENT '接收用户',
  `title` VARCHAR(120) NOT NULL COMMENT '标题',
  `content` TEXT NULL COMMENT '内容',
  `business_type` VARCHAR(32) NULL COMMENT '业务类型',
  `business_id` VARCHAR(64) NULL COMMENT '业务主键',
  `read_at` DATETIME NULL COMMENT '阅读时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_notification_user_read` (`user_id`, `read_at`, `created_at`),
  CONSTRAINT `fk_notification_user`
    FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='站内消息';

CREATE TABLE IF NOT EXISTS `ops_attendance_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '打卡记录主键',
  `user_id` BIGINT NOT NULL COMMENT '用户主键',
  `work_date` DATE NOT NULL COMMENT '考勤日期',
  `punch_type` VARCHAR(20) NOT NULL COMMENT 'check_in/check_out',
  `punched_at` DATETIME NOT NULL COMMENT '打卡时间',
  `latitude` DECIMAL(10,7) NULL COMMENT '纬度',
  `longitude` DECIMAL(10,7) NULL COMMENT '经度',
  `accuracy` DECIMAL(10,2) NULL COMMENT '定位精度（米）',
  `location_text` VARCHAR(255) NULL COMMENT '位置说明',
  `source` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT 'normal/supplement',
  `supplement_reason` TEXT NULL COMMENT '补卡原因',
  `review_status` VARCHAR(20) NOT NULL DEFAULT 'approved' COMMENT 'approved/pending/rejected',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_attendance_user_date` (`user_id`, `work_date`, `punched_at`),
  KEY `idx_attendance_review_status` (`review_status`),
  CONSTRAINT `fk_attendance_user`
    FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='上下班打卡及补卡记录';

CREATE TABLE IF NOT EXISTS `ops_police_registration` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_by` BIGINT NOT NULL,
  `person_name` VARCHAR(64) NOT NULL,
  `gender` VARCHAR(10) NOT NULL,
  `id_card_ciphertext` TEXT NOT NULL COMMENT '加密身份证号',
  `id_card_hash` VARCHAR(64) NOT NULL COMMENT '身份证查重摘要',
  `id_card_last4` VARCHAR(4) NOT NULL,
  `company_name` VARCHAR(160) NOT NULL,
  `region` VARCHAR(64) NOT NULL DEFAULT '镇江',
  `mobile` VARCHAR(32) NULL,
  `filing_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
  `filing_date` DATE NULL,
  `remarks` TEXT NULL,
  `record_status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`), UNIQUE KEY `uk_police_id_card_hash` (`id_card_hash`),
  KEY `idx_police_region_status` (`region`, `filing_status`),
  CONSTRAINT `fk_police_created_by` FOREIGN KEY (`created_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公安备案人员';

CREATE TABLE IF NOT EXISTS `ops_consumable_purchase` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_by` BIGINT NOT NULL,
  `category` VARCHAR(64) NOT NULL,
  `item_name` VARCHAR(120) NOT NULL,
  `quantity` DECIMAL(14,3) NOT NULL,
  `unit` VARCHAR(32) NOT NULL,
  `unit_price` DECIMAL(14,2) NOT NULL,
  `total_amount` DECIMAL(14,2) NOT NULL COMMENT '用户确认的最终总价',
  `is_manual_total` TINYINT(1) NOT NULL DEFAULT 0,
  `total_adjustment_reason` VARCHAR(500) NULL,
  `purchase_date` DATE NOT NULL,
  `supplier_name` VARCHAR(160) NULL,
  `invoice_number` VARCHAR(80) NULL,
  `region` VARCHAR(64) NOT NULL DEFAULT '镇江',
  `operator_name` VARCHAR(64) NOT NULL,
  `description` TEXT NULL,
  `record_status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`), KEY `idx_purchase_region_date` (`region`, `purchase_date`),
  CONSTRAINT `fk_purchase_created_by` FOREIGN KEY (`created_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='耗材采购台账';

CREATE TABLE IF NOT EXISTS `ops_safety_inspection` (
  `id` BIGINT NOT NULL AUTO_INCREMENT, `created_by` BIGINT NOT NULL,
  `inspection_project` VARCHAR(160) NOT NULL, `region` VARCHAR(64) NOT NULL DEFAULT '镇江',
  `inspection_area` VARCHAR(160) NOT NULL, `inspected_at` DATETIME NOT NULL,
  `inspectors` VARCHAR(255) NOT NULL, `location_text` VARCHAR(255) NULL, `weather` VARCHAR(64) NULL,
  `site_readiness` VARCHAR(20) NOT NULL, `environment_status` VARCHAR(20) NOT NULL DEFAULT 'normal',
  `equipment_status` VARCHAR(20) NOT NULL DEFAULT 'normal', `fire_status` VARCHAR(20) NOT NULL DEFAULT 'normal',
  `ppe_status` VARCHAR(20) NOT NULL DEFAULT 'normal', `work_order_status` VARCHAR(20) NOT NULL DEFAULT 'normal',
  `description` TEXT NULL, `record_status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`), KEY `idx_inspection_region_time` (`region`, `inspected_at`),
  CONSTRAINT `fk_inspection_created_by` FOREIGN KEY (`created_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='安全检查记录';

CREATE TABLE IF NOT EXISTS `ops_safety_hazard` (
  `id` BIGINT NOT NULL AUTO_INCREMENT, `inspection_id` BIGINT NOT NULL,
  `hazard_name` VARCHAR(160) NOT NULL, `category` VARCHAR(32) NOT NULL, `risk_level` VARCHAR(20) NOT NULL,
  `description` TEXT NOT NULL, `responsible_person` VARCHAR(64) NOT NULL,
  `rectification_deadline` DATE NOT NULL, `rectification_requirement` TEXT NOT NULL,
  `immediate_stop` TINYINT(1) NOT NULL DEFAULT 0, `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
  `rectification_description` TEXT NULL, `rectified_at` DATETIME NULL,
  `review_result` VARCHAR(20) NULL, `review_comment` TEXT NULL, `reviewed_by` BIGINT NULL, `reviewed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`), KEY `idx_hazard_status_deadline` (`status`, `rectification_deadline`),
  CONSTRAINT `fk_hazard_inspection` FOREIGN KEY (`inspection_id`) REFERENCES `ops_safety_inspection` (`id`),
  CONSTRAINT `fk_hazard_reviewed_by` FOREIGN KEY (`reviewed_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='安全危险点及整改复查';

CREATE TABLE IF NOT EXISTS `ops_business_attachment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT, `business_type` VARCHAR(32) NOT NULL, `business_id` BIGINT NOT NULL,
  `usage_type` VARCHAR(32) NOT NULL DEFAULT 'general', `file_name` VARCHAR(255) NOT NULL,
  `storage_path` VARCHAR(500) NOT NULL, `content_type` VARCHAR(100) NULL, `file_size` BIGINT NOT NULL,
  `uploaded_by` BIGINT NOT NULL, `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`), KEY `idx_attachment_business` (`business_type`, `business_id`),
  CONSTRAINT `fk_attachment_uploaded_by` FOREIGN KEY (`uploaded_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='业务附件';
