-- ============================================================
--  新闻资讯系统 - 数据库建表脚本
--  数据库：MySQL 8.0+
--  字符集：utf8mb4（支持中文和 emoji）
--
--  使用方法：
--     mysql -u root -p < schema.sql
--  或在 MySQL 客户端里：
--     source /path/to/schema.sql
--
--  ⚠️ 注意：Windows 下的 mysql.exe 默认用 GBK 编码读文件，
--     如果脚本里有中文（注释/初始数据），必须加下面这几行，
--     否则中文会变成乱码（如 "头条" 变成 "澶存潯"）。
-- ============================================================

SET NAMES utf8mb4;

-- 建库（如果已存在则跳过）
CREATE DATABASE IF NOT EXISTS `news_app`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE `news_app`;

-- ============================================================
--  建表顺序很重要：先建"被引用的表"，再建"引用别人的表"
--  这里顺序是：user / news_category → news → 其余
-- ============================================================

-- ------------------------------------------------------------
-- 1. 用户表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user` (
    `id`         int unsigned NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username`   varchar(50)  NOT NULL                COMMENT '用户名',
    `password`   varchar(255) NOT NULL                COMMENT '密码（加密存储）',
    `nickname`   varchar(50)           DEFAULT NULL   COMMENT '昵称',
    `avatar`     varchar(255)          DEFAULT NULL   COMMENT '头像URL',
    `gender`     enum('male','female','unknown') DEFAULT 'unknown' COMMENT '性别',
    `bio`        varchar(500)          DEFAULT NULL   COMMENT '个人简介',
    `phone`      varchar(20)           DEFAULT NULL   COMMENT '手机号',
    `created_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `username_UNIQUE` (`username`),   -- 用户名不能重复
    UNIQUE KEY `phone_UNIQUE` (`phone`)          -- 手机号不能重复
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户信息表';


-- ------------------------------------------------------------
-- 2. 新闻分类表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `news_category` (
    `id`         int unsigned NOT NULL AUTO_INCREMENT COMMENT '分类ID',
    `name`       varchar(50)  NOT NULL                COMMENT '分类名称',
    `sort_order` int          NOT NULL DEFAULT 0      COMMENT '排序顺序',
    `created_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `name_UNIQUE` (`name`)            -- 分类名不能重复
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='新闻分类表';


-- ------------------------------------------------------------
-- 3. 新闻表（依赖 news_category）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `news` (
    `id`           int unsigned NOT NULL AUTO_INCREMENT COMMENT '新闻ID',
    `title`        varchar(255) NOT NULL                COMMENT '新闻标题',
    `description`  varchar(500)          DEFAULT NULL   COMMENT '新闻简介',
    `content`      text         NOT NULL                COMMENT '新闻内容',
    `image`        varchar(255)          DEFAULT NULL   COMMENT '封面图片URL',
    `author`       varchar(50)           DEFAULT NULL   COMMENT '作者',
    `category_id`  int unsigned NOT NULL                COMMENT '分类ID',
    `views`        int unsigned NOT NULL DEFAULT 0      COMMENT '浏览量',
    `publish_time` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    `created_at`   timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`   timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `fk_news_category_idx` (`category_id`),      -- 外键列要建索引
    KEY `idx_publish_time` (`publish_time` DESC),    -- 经常按发布时间倒序排
    CONSTRAINT `fk_news_category` FOREIGN KEY (`category_id`)
        REFERENCES `news_category` (`id`)
        ON DELETE RESTRICT      -- 分类下还有新闻时，不许删分类
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='新闻表';


-- ------------------------------------------------------------
-- 4. 用户令牌表（登录态，依赖 user）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_token` (
    `id`         int unsigned NOT NULL AUTO_INCREMENT COMMENT '令牌ID',
    `user_id`    int unsigned NOT NULL                COMMENT '用户ID',
    `token`      varchar(255) NOT NULL                COMMENT '令牌值',
    `expires_at` timestamp    NOT NULL                COMMENT '过期时间',
    `created_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `token_UNIQUE` (`token`),             -- token 不能重复
    KEY `fk_user_token_user_idx` (`user_id`),
    CONSTRAINT `fk_user_token_user` FOREIGN KEY (`user_id`)
        REFERENCES `user` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE          -- 用户没了，令牌也没意义
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户令牌表';


-- ------------------------------------------------------------
-- 5. 收藏表（依赖 user + news）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `favorite` (
    `id`         int unsigned NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
    `user_id`    int unsigned NOT NULL                COMMENT '用户ID',
    `news_id`    int unsigned NOT NULL                COMMENT '新闻ID',
    `created_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_news_unique` (`user_id`,`news_id`),  -- 同一用户对同一新闻只能收藏一次
    KEY `fk_favorite_user_idx` (`user_id`),
    KEY `fk_favorite_news_idx` (`news_id`),
    CONSTRAINT `fk_favorite_user` FOREIGN KEY (`user_id`)
        REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_favorite_news` FOREIGN KEY (`news_id`)
        REFERENCES `news` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='收藏表';


-- ------------------------------------------------------------
-- 6. 浏览历史表（依赖 user + news）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `history` (
    `id`        int unsigned NOT NULL AUTO_INCREMENT COMMENT '历史ID',
    `user_id`   int unsigned NOT NULL                COMMENT '用户ID',
    `news_id`   int unsigned NOT NULL                COMMENT '新闻ID',
    `view_time` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
    PRIMARY KEY (`id`),
    KEY `fk_history_user_idx` (`user_id`),
    KEY `fk_history_news_idx` (`news_id`),
    KEY `idx_view_time` (`view_time` DESC),
    CONSTRAINT `fk_history_user` FOREIGN KEY (`user_id`)
        REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_history_news` FOREIGN KEY (`news_id`)
        REFERENCES `news` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='浏览历史表';


-- ------------------------------------------------------------
-- 7. 相关新闻关联表（自关联：news 关联 news）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `related_news` (
    `id`              int unsigned NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    `news_id`         int unsigned NOT NULL                COMMENT '新闻ID',
    `related_news_id` int unsigned NOT NULL                COMMENT '相关新闻ID',
    `created_at`      timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `news_related_unique` (`news_id`,`related_news_id`),   -- 同一对关联只能有一条
    KEY `fk_related_news_news_idx` (`news_id`),
    KEY `fk_related_news_related_idx` (`related_news_id`),
    CONSTRAINT `fk_related_news_news` FOREIGN KEY (`news_id`)
        REFERENCES `news` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_related_news_related` FOREIGN KEY (`related_news_id`)
        REFERENCES `news` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='相关新闻关联表';


-- ------------------------------------------------------------
-- 8. AI 聊天记录表（依赖 user）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `ai_chat` (
    `id`         int unsigned NOT NULL AUTO_INCREMENT COMMENT '聊天记录ID',
    `user_id`    int unsigned NOT NULL                COMMENT '用户ID',
    `message`    text         NOT NULL                COMMENT '用户消息',
    `response`   text         NOT NULL                COMMENT 'AI回复',
    `created_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `fk_ai_chat_user_idx` (`user_id`),
    KEY `idx_created_at` (`created_at` DESC),
    CONSTRAINT `fk_ai_chat_user` FOREIGN KEY (`user_id`)
        REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI聊天记录表';


-- ============================================================
--  初始数据：新闻分类
-- ============================================================
INSERT INTO `news_category` (`name`, `sort_order`) VALUES
    ('头条', 1),
    ('社会', 2),
    ('国内', 3),
    ('国际', 4),
    ('娱乐', 5),
    ('体育', 6),
    ('科技', 7),
    ('经济', 8)
ON DUPLICATE KEY UPDATE `sort_order` = VALUES(`sort_order`);   -- 重复执行不会报错
