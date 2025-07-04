CREATE DATABASE IF NOT EXISTS kamisystem DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kamisystem;

CREATE TABLE IF NOT EXISTS cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prefix VARCHAR(16) NOT NULL COMMENT '卡密前缀',
    code VARCHAR(64) NOT NULL COMMENT '随机生成主体',
    full_code VARCHAR(128) NOT NULL UNIQUE COMMENT '完整卡密代码',
    used_at DATETIME DEFAULT NULL COMMENT '第一次使用时间',
    expire_at DATETIME DEFAULT NULL COMMENT '过期时间',
    machine_code VARCHAR(128) DEFAULT NULL COMMENT '绑定设备码',
    status ENUM('UNUSED', 'ACTIVE', 'EXPIRED') DEFAULT 'UNUSED' COMMENT '卡密状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_full_code (full_code),
    INDEX idx_status (status),
    INDEX idx_prefix (prefix),
    INDEX idx_machine_code (machine_code),
    INDEX idx_expire_at (expire_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='卡密表';

