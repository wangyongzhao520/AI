# 用户账号管理系统设计文档
# User Account Management System Design Document

## 目录 (Table of Contents)

1. [背景与目标](#背景与目标)
2. [系统架构概述](#系统架构概述)
3. [数据库表结构设计](#数据库表结构设计)
4. [数据迁移方案](#数据迁移方案)
5. [权限体系设计](#权限体系设计)
6. [实施建议](#实施建议)

---

## 背景与目标

### 系统背景

当前系统存在以下问题：
- 公司账号（`dealer_user`）与个人账号（`shop_instance_clerk`）分离
- 手机号可能存在重复（同一手机号对应公司账号+个人账号）
- 角色不区分经销商/门店作用域
- 缺乏统一的权限管理体系

### 设计目标

1. **多租户 B2B 架构**：支持多组织（经销商/门店）的独立数据和权限隔离
2. **多层级账号**：使用 Closure Table 实现组织层级（深度≤5）
3. **统一账号体系**：合并公司账号与个人账号，一个手机号对应一个账号
4. **灵活权限系统**：RBAC + 数据范围 + 字段策略
5. **角色分类与用户类型**：用于业务分类，不参与权限判断

---

## 系统架构概述

### 核心概念

```
账号 (Account) ─┬─> 用户档案 (User Profile)
               │
               └─> 多个组织成员身份 (Org Member)
                   └─> 多个角色 (Roles)
                       └─> 权限 (Permissions)
```

### 关键特性

- **账号唯一性**：手机号作为全局唯一登录标识
- **多身份支持**：一个账号可在多个组织中拥有不同身份
- **角色继承**：支持角色组合和权限继承
- **数据范围**：精细化控制数据访问范围（本人/本部门/本公司/全部）
- **字段策略**：控制特定字段的读写权限

---

## 数据库表结构设计

### 1. accounts - 统一登录账号表

```sql
-- 账号表：全局唯一的登录凭证
CREATE TABLE `accounts` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '账号ID',
  `phone` VARCHAR(20) NOT NULL COMMENT '手机号（全局唯一登录标识）',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '账号状态：0-禁用，1-正常，2-锁定',
  `last_login_at` DATETIME NULL COMMENT '最后登录时间',
  `last_login_ip` VARCHAR(45) NULL COMMENT '最后登录IP',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_phone` (`phone`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一登录账号表';
```

### 2. users - 用户档案表

```sql
-- 用户档案表：存储用户基本信息
CREATE TABLE `users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `account_id` BIGINT UNSIGNED NOT NULL COMMENT '关联账号ID',
  `real_name` VARCHAR(50) NULL COMMENT '真实姓名',
  `id_card` VARCHAR(20) NULL COMMENT '身份证号',
  `email` VARCHAR(100) NULL COMMENT '邮箱',
  `avatar` VARCHAR(255) NULL COMMENT '头像URL',
  `gender` TINYINT NULL COMMENT '性别：0-未知，1-男，2-女',
  `birth_date` DATE NULL COMMENT '出生日期',
  `address` VARCHAR(255) NULL COMMENT '地址',
  `user_type_id` INT UNSIGNED NULL COMMENT '用户类型ID（仅分类，不参与权限）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_id` (`account_id`),
  KEY `idx_real_name` (`real_name`),
  KEY `idx_user_type` (`user_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户档案表';
```

### 3. org_members - 成员身份表

```sql
-- 组织成员表：一个账号在不同组织中的身份
CREATE TABLE `org_members` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '成员身份ID',
  `account_id` BIGINT UNSIGNED NOT NULL COMMENT '账号ID',
  `org_type` VARCHAR(30) NOT NULL COMMENT '组织类型：shop-经销商，shop_instance-门店',
  `org_id` BIGINT UNSIGNED NOT NULL COMMENT '组织ID（shop_id 或 shop_instance_id）',
  `member_code` VARCHAR(50) NULL COMMENT '员工编号',
  `position` VARCHAR(50) NULL COMMENT '职位',
  `department` VARCHAR(100) NULL COMMENT '部门',
  `is_primary` TINYINT NOT NULL DEFAULT 0 COMMENT '是否主身份（默认登录身份）',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '成员状态：0-离职，1-在职，2-停用',
  `joined_at` DATETIME NULL COMMENT '加入时间',
  `left_at` DATETIME NULL COMMENT '离职时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_org` (`account_id`, `org_type`, `org_id`),
  KEY `idx_org` (`org_type`, `org_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织成员身份表';
```

### 4. member_roles - 成员角色分配表

```sql
-- 成员角色表：为成员身份分配角色
CREATE TABLE `member_roles` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `member_id` BIGINT UNSIGNED NOT NULL COMMENT '成员身份ID',
  `role_id` INT UNSIGNED NOT NULL COMMENT '角色ID',
  `granted_by` BIGINT UNSIGNED NULL COMMENT '授权人账号ID',
  `granted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expires_at` DATETIME NULL COMMENT '过期时间（NULL表示永久）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_member_role` (`member_id`, `role_id`),
  KEY `idx_role` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成员角色分配表';
```

### 5. roles - 角色表

```sql
-- 角色表：定义系统角色
CREATE TABLE `roles` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `code` VARCHAR(50) NOT NULL COMMENT '角色编码（唯一标识）',
  `name` VARCHAR(50) NOT NULL COMMENT '角色名称',
  `description` VARCHAR(255) NULL COMMENT '角色描述',
  `role_category_id` INT UNSIGNED NULL COMMENT '角色分类ID（仅分类，不参与权限）',
  `data_scope` TINYINT NOT NULL DEFAULT 1 COMMENT '数据范围：1-仅本人，2-本部门，3-本部门及下级，4-本公司，5-全部',
  `is_system` TINYINT NOT NULL DEFAULT 0 COMMENT '是否系统内置角色（不可删除）',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_category` (`role_category_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';
```

### 6. role_categories - 角色分类表

```sql
-- 角色分类表：用于角色的业务分类（不参与权限判断）
CREATE TABLE `role_categories` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `code` VARCHAR(30) NOT NULL COMMENT '分类编码',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `parent_id` INT UNSIGNED NULL COMMENT '父分类ID',
  `description` VARCHAR(255) NULL COMMENT '分类描述',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色分类表';
```

### 7. user_types - 用户类型表

```sql
-- 用户类型表：用于用户的业务分类（不参与权限判断）
CREATE TABLE `user_types` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '类型ID',
  `code` VARCHAR(30) NOT NULL COMMENT '类型编码',
  `name` VARCHAR(50) NOT NULL COMMENT '类型名称',
  `description` VARCHAR(255) NULL COMMENT '类型描述',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户类型表';
```

### 8. permissions - 权限表

```sql
-- 权限表：定义系统权限
CREATE TABLE `permissions` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '权限ID',
  `code` VARCHAR(100) NOT NULL COMMENT '权限编码（唯一标识）',
  `name` VARCHAR(50) NOT NULL COMMENT '权限名称',
  `type` VARCHAR(20) NOT NULL COMMENT '权限类型：menu-菜单，button-按钮，api-接口',
  `parent_id` INT UNSIGNED NULL COMMENT '父权限ID',
  `resource_path` VARCHAR(255) NULL COMMENT '资源路径（菜单路径/API路径）',
  `method` VARCHAR(10) NULL COMMENT 'HTTP方法（针对API权限）',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_parent` (`parent_id`),
  KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';
```

### 9. role_permissions - 角色权限关联表

```sql
-- 角色权限关联表：角色与权限的多对多关系
CREATE TABLE `role_permissions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_id` INT UNSIGNED NOT NULL COMMENT '角色ID',
  `permission_id` INT UNSIGNED NOT NULL COMMENT '权限ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_permission` (`role_id`, `permission_id`),
  KEY `idx_permission` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';
```

### 10. field_policies - 字段策略表

```sql
-- 字段策略表：控制特定字段的读写权限
CREATE TABLE `field_policies` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '策略ID',
  `role_id` INT UNSIGNED NOT NULL COMMENT '角色ID',
  `resource` VARCHAR(100) NOT NULL COMMENT '资源名称（如：user, order）',
  `field_name` VARCHAR(50) NOT NULL COMMENT '字段名称',
  `can_read` TINYINT NOT NULL DEFAULT 1 COMMENT '是否可读：0-否，1-是',
  `can_write` TINYINT NOT NULL DEFAULT 0 COMMENT '是否可写：0-否，1-是',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_resource_field` (`role_id`, `resource`, `field_name`),
  KEY `idx_resource` (`resource`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字段策略表';
```

### 11. org_hierarchy - 组织层级关系表（Closure Table）

```sql
-- 组织层级关系表：使用Closure Table实现组织树（深度≤5）
CREATE TABLE `org_hierarchy` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ancestor_type` VARCHAR(30) NOT NULL COMMENT '祖先组织类型',
  `ancestor_id` BIGINT UNSIGNED NOT NULL COMMENT '祖先组织ID',
  `descendant_type` VARCHAR(30) NOT NULL COMMENT '后代组织类型',
  `descendant_id` BIGINT UNSIGNED NOT NULL COMMENT '后代组织ID',
  `depth` TINYINT NOT NULL COMMENT '层级深度（0表示自己，1表示直接子级）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ancestor_descendant` (`ancestor_type`, `ancestor_id`, `descendant_type`, `descendant_id`),
  KEY `idx_ancestor` (`ancestor_type`, `ancestor_id`, `depth`),
  KEY `idx_descendant` (`descendant_type`, `descendant_id`),
  CONSTRAINT `chk_depth` CHECK (`depth` <= 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织层级关系表';
```

### 12. legacy_identity_map - 旧身份映射表

```sql
-- 旧身份映射表：用于数据迁移追溯
CREATE TABLE `legacy_identity_map` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `legacy_table` VARCHAR(50) NOT NULL COMMENT '原表名（dealer_user/shop_instance_clerk）',
  `legacy_id` BIGINT UNSIGNED NOT NULL COMMENT '原表记录ID',
  `account_id` BIGINT UNSIGNED NOT NULL COMMENT '新账号ID',
  `member_id` BIGINT UNSIGNED NULL COMMENT '成员身份ID',
  `migration_batch` VARCHAR(50) NULL COMMENT '迁移批次号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_legacy` (`legacy_table`, `legacy_id`),
  KEY `idx_account` (`account_id`),
  KEY `idx_member` (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='旧身份映射表';
```

---

## 数据迁移方案

### 迁移策略概述

1. **手机号冲突处理**：优先保留公司账号，个人账号合并为成员身份
2. **分批迁移**：先迁移经销商（dealer_user），再迁移店员（shop_instance_clerk）
3. **保留追溯**：所有迁移记录保存到 `legacy_identity_map`
4. **角色映射**：根据原业务角色映射到新角色体系

### 1. 从 dealer_user 迁移

```sql
-- 步骤1: 迁移到 accounts 表（公司账号）
INSERT INTO accounts (phone, password_hash, status, created_at, updated_at)
SELECT 
    du.phone,
    du.password_hash,
    CASE WHEN du.status = 1 THEN 1 ELSE 0 END as status,
    du.created_at,
    du.updated_at
FROM dealer_user du
WHERE du.phone IS NOT NULL 
  AND du.phone != ''
  AND NOT EXISTS (
      SELECT 1 FROM accounts a WHERE a.phone = du.phone
  );

-- 步骤2: 迁移到 users 表
INSERT INTO users (account_id, real_name, email, created_at, updated_at)
SELECT 
    a.id as account_id,
    du.real_name,
    du.email,
    du.created_at,
    du.updated_at
FROM dealer_user du
INNER JOIN accounts a ON a.phone = du.phone
WHERE NOT EXISTS (
    SELECT 1 FROM users u WHERE u.account_id = a.id
);

-- 步骤3: 迁移到 org_members 表（经销商身份）
INSERT INTO org_members (
    account_id, 
    org_type, 
    org_id, 
    member_code,
    position,
    is_primary,
    status,
    joined_at,
    created_at,
    updated_at
)
SELECT 
    a.id as account_id,
    'shop' as org_type,
    du.shop_id as org_id,
    du.employee_code as member_code,
    du.position,
    1 as is_primary,  -- 公司账号设为主身份
    CASE WHEN du.status = 1 THEN 1 ELSE 0 END as status,
    du.created_at as joined_at,
    du.created_at,
    du.updated_at
FROM dealer_user du
INNER JOIN accounts a ON a.phone = du.phone
WHERE du.shop_id IS NOT NULL;

-- 步骤4: 记录映射关系
INSERT INTO legacy_identity_map (
    legacy_table,
    legacy_id,
    account_id,
    member_id,
    migration_batch
)
SELECT 
    'dealer_user' as legacy_table,
    du.id as legacy_id,
    a.id as account_id,
    om.id as member_id,
    'batch_001_dealer_user' as migration_batch
FROM dealer_user du
INNER JOIN accounts a ON a.phone = du.phone
INNER JOIN org_members om ON om.account_id = a.id 
    AND om.org_type = 'shop' 
    AND om.org_id = du.shop_id;

-- 步骤5: 迁移角色（假设原有 dealer_user_role 关联表）
-- 需要先建立角色映射关系
INSERT INTO member_roles (member_id, role_id, granted_at)
SELECT 
    om.id as member_id,
    r.id as role_id,  -- 新角色ID
    dur.created_at as granted_at
FROM dealer_user du
INNER JOIN accounts a ON a.phone = du.phone
INNER JOIN org_members om ON om.account_id = a.id 
    AND om.org_type = 'shop' 
    AND om.org_id = du.shop_id
INNER JOIN dealer_user_role dur ON dur.user_id = du.id
INNER JOIN roles r ON r.code = CONCAT('DEALER_', dur.role_code);  -- 角色映射规则
```

### 2. 从 shop_instance_clerk 迁移

```sql
-- 步骤1: 迁移到 accounts 表（个人账号，处理手机号冲突）
INSERT INTO accounts (phone, password_hash, status, created_at, updated_at)
SELECT 
    sic.phone,
    sic.password_hash,
    CASE WHEN sic.status = 1 THEN 1 ELSE 0 END as status,
    sic.created_at,
    sic.updated_at
FROM shop_instance_clerk sic
WHERE sic.phone IS NOT NULL 
  AND sic.phone != ''
  AND NOT EXISTS (
      SELECT 1 FROM accounts a WHERE a.phone = sic.phone
  );

-- 步骤2: 迁移到 users 表（如果账号不存在用户档案）
INSERT INTO users (account_id, real_name, created_at, updated_at)
SELECT 
    a.id as account_id,
    sic.real_name,
    sic.created_at,
    sic.updated_at
FROM shop_instance_clerk sic
INNER JOIN accounts a ON a.phone = sic.phone
WHERE NOT EXISTS (
    SELECT 1 FROM users u WHERE u.account_id = a.id
);

-- 步骤3: 迁移到 org_members 表（门店身份）
-- 注意：同一账号可能在多个门店工作
INSERT INTO org_members (
    account_id, 
    org_type, 
    org_id, 
    member_code,
    position,
    is_primary,
    status,
    joined_at,
    created_at,
    updated_at
)
SELECT 
    a.id as account_id,
    'shop_instance' as org_type,
    sic.shop_instance_id as org_id,
    sic.employee_code as member_code,
    sic.position,
    CASE 
        -- 如果账号没有主身份，设置第一个门店为主身份
        WHEN NOT EXISTS (
            SELECT 1 FROM org_members om2 
            WHERE om2.account_id = a.id AND om2.is_primary = 1
        ) THEN 1
        ELSE 0
    END as is_primary,
    CASE WHEN sic.status = 1 THEN 1 ELSE 0 END as status,
    sic.created_at as joined_at,
    sic.created_at,
    sic.updated_at
FROM shop_instance_clerk sic
INNER JOIN accounts a ON a.phone = sic.phone
WHERE sic.shop_instance_id IS NOT NULL
  AND NOT EXISTS (
      -- 避免重复插入同一账号在同一门店的身份
      SELECT 1 FROM org_members om 
      WHERE om.account_id = a.id 
        AND om.org_type = 'shop_instance' 
        AND om.org_id = sic.shop_instance_id
  );

-- 步骤4: 记录映射关系
INSERT INTO legacy_identity_map (
    legacy_table,
    legacy_id,
    account_id,
    member_id,
    migration_batch
)
SELECT 
    'shop_instance_clerk' as legacy_table,
    sic.id as legacy_id,
    a.id as account_id,
    om.id as member_id,
    'batch_002_shop_clerk' as migration_batch
FROM shop_instance_clerk sic
INNER JOIN accounts a ON a.phone = sic.phone
INNER JOIN org_members om ON om.account_id = a.id 
    AND om.org_type = 'shop_instance' 
    AND om.org_id = sic.shop_instance_id;

-- 步骤5: 迁移角色
INSERT INTO member_roles (member_id, role_id, granted_at)
SELECT 
    om.id as member_id,
    r.id as role_id,
    sicr.created_at as granted_at
FROM shop_instance_clerk sic
INNER JOIN accounts a ON a.phone = sic.phone
INNER JOIN org_members om ON om.account_id = a.id 
    AND om.org_type = 'shop_instance' 
    AND om.org_id = sic.shop_instance_id
INNER JOIN shop_instance_clerk_role sicr ON sicr.clerk_id = sic.id
INNER JOIN roles r ON r.code = CONCAT('CLERK_', sicr.role_code);
```

### 3. 手机号冲突处理策略

```sql
-- 冲突检测查询：找出同一手机号同时存在于两个表的情况
SELECT 
    du.phone,
    COUNT(DISTINCT du.id) as dealer_count,
    COUNT(DISTINCT sic.id) as clerk_count,
    GROUP_CONCAT(DISTINCT du.id) as dealer_ids,
    GROUP_CONCAT(DISTINCT sic.id) as clerk_ids
FROM dealer_user du
INNER JOIN shop_instance_clerk sic ON sic.phone = du.phone
GROUP BY du.phone
HAVING COUNT(DISTINCT du.id) > 0 AND COUNT(DISTINCT sic.id) > 0;

-- 处理策略：
-- 1. 保留 dealer_user 的账号（公司账号优先级更高）
-- 2. shop_instance_clerk 只创建成员身份，不创建新账号
-- 3. 如果密码不同，记录到日志表，后续通知用户修改密码

-- 创建冲突日志表
CREATE TABLE `migration_conflicts` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `phone` VARCHAR(20) NOT NULL,
  `conflict_type` VARCHAR(50) NOT NULL COMMENT '冲突类型：phone_duplicate',
  `dealer_user_id` BIGINT UNSIGNED NULL,
  `clerk_id` BIGINT UNSIGNED NULL,
  `resolution` VARCHAR(100) NULL COMMENT '解决方案',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 记录冲突
INSERT INTO migration_conflicts (phone, conflict_type, dealer_user_id, clerk_id, resolution)
SELECT 
    du.phone,
    'phone_duplicate' as conflict_type,
    du.id as dealer_user_id,
    sic.id as clerk_id,
    'kept_dealer_user_account' as resolution
FROM dealer_user du
INNER JOIN shop_instance_clerk sic ON sic.phone = du.phone;
```

### 4. 迁移验证查询

```sql
-- 验证1: 检查所有旧用户是否都已迁移
SELECT 
    'dealer_user' as source_table,
    COUNT(*) as total_count,
    COUNT(lim.id) as migrated_count,
    COUNT(*) - COUNT(lim.id) as unmigrated_count
FROM dealer_user du
LEFT JOIN legacy_identity_map lim ON lim.legacy_table = 'dealer_user' 
    AND lim.legacy_id = du.id
UNION ALL
SELECT 
    'shop_instance_clerk' as source_table,
    COUNT(*) as total_count,
    COUNT(lim.id) as migrated_count,
    COUNT(*) - COUNT(lim.id) as unmigrated_count
FROM shop_instance_clerk sic
LEFT JOIN legacy_identity_map lim ON lim.legacy_table = 'shop_instance_clerk' 
    AND lim.legacy_id = sic.id;

-- 验证2: 检查账号数量
SELECT 
    COUNT(DISTINCT du.phone) + COUNT(DISTINCT sic.phone) as expected_accounts,
    (SELECT COUNT(*) FROM accounts) as actual_accounts
FROM dealer_user du
CROSS JOIN shop_instance_clerk sic;

-- 验证3: 检查成员身份数量
SELECT 
    COUNT(*) as expected_members,
    (SELECT COUNT(*) FROM org_members) as actual_members
FROM (
    SELECT shop_id as org_id FROM dealer_user WHERE shop_id IS NOT NULL
    UNION ALL
    SELECT shop_instance_id FROM shop_instance_clerk WHERE shop_instance_id IS NOT NULL
) t;
```

---

## 权限体系设计

### 1. 角色字典示例

```sql
-- 插入角色分类
INSERT INTO role_categories (code, name, description, sort_order) VALUES
('DEALER', '经销商角色', '经销商组织内的角色', 1),
('STORE', '门店角色', '门店内的角色', 2),
('SYSTEM', '系统角色', '系统级角色', 3);

-- 插入系统角色
INSERT INTO roles (code, name, description, role_category_id, data_scope, is_system, status, sort_order) VALUES
-- 经销商角色
('DEALER_ADMIN', '经销商管理员', '经销商的最高管理权限', 
    (SELECT id FROM role_categories WHERE code = 'DEALER'), 4, 1, 1, 1),
('DEALER_MANAGER', '经销商经理', '经销商的业务经理', 
    (SELECT id FROM role_categories WHERE code = 'DEALER'), 3, 1, 1, 2),
('DEALER_SUPERVISOR', '经销商主管', '经销商的部门主管', 
    (SELECT id FROM role_categories WHERE code = 'DEALER'), 2, 1, 1, 3),
('DEALER_STAFF', '经销商员工', '经销商的普通员工', 
    (SELECT id FROM role_categories WHERE code = 'DEALER'), 1, 1, 1, 4),

-- 门店角色
('STORE_MANAGER', '门店店长', '门店的最高管理权限', 
    (SELECT id FROM role_categories WHERE code = 'STORE'), 4, 1, 1, 11),
('STORE_SUPERVISOR', '门店主管', '门店的部门主管', 
    (SELECT id FROM role_categories WHERE code = 'STORE'), 2, 1, 1, 12),
('STORE_CLERK', '门店店员', '门店的普通店员', 
    (SELECT id FROM role_categories WHERE code = 'STORE'), 1, 1, 1, 13),
('STORE_CASHIER', '门店收银员', '门店收银员', 
    (SELECT id FROM role_categories WHERE code = 'STORE'), 1, 1, 1, 14),

-- 系统角色
('SUPER_ADMIN', '超级管理员', '系统超级管理员，拥有所有权限', 
    (SELECT id FROM role_categories WHERE code = 'SYSTEM'), 5, 1, 1, 100);
```

### 2. 权限码体系示例

```sql
-- 权限码命名规范：{模块}:{资源}:{操作}
-- 例如：dealer:order:create, store:inventory:read

-- 插入权限示例
INSERT INTO permissions (code, name, type, parent_id, resource_path, method, sort_order, status) VALUES
-- 一级菜单：经销商管理
(NULL, '经销商管理', 'menu', NULL, '/dealer', NULL, 1, 1),
-- 二级菜单：订单管理
(NULL, '订单管理', 'menu', (SELECT id FROM permissions WHERE code IS NULL AND name = '经销商管理'), '/dealer/orders', NULL, 11, 1),
-- 操作按钮
('dealer:order:create', '创建订单', 'button', (SELECT id FROM permissions WHERE code IS NULL AND name = '订单管理'), NULL, NULL, 111, 1),
('dealer:order:read', '查看订单', 'button', (SELECT id FROM permissions WHERE code IS NULL AND name = '订单管理'), NULL, NULL, 112, 1),
('dealer:order:update', '修改订单', 'button', (SELECT id FROM permissions WHERE code IS NULL AND name = '订单管理'), NULL, NULL, 113, 1),
('dealer:order:delete', '删除订单', 'button', (SELECT id FROM permissions WHERE code IS NULL AND name = '订单管理'), NULL, NULL, 114, 1),
('dealer:order:approve', '审批订单', 'button', (SELECT id FROM permissions WHERE code IS NULL AND name = '订单管理'), NULL, NULL, 115, 1),
-- API权限
('dealer:order:api:list', '订单列表API', 'api', NULL, '/api/dealer/orders', 'GET', 1111, 1),
('dealer:order:api:create', '创建订单API', 'api', NULL, '/api/dealer/orders', 'POST', 1112, 1),
('dealer:order:api:detail', '订单详情API', 'api', NULL, '/api/dealer/orders/:id', 'GET', 1113, 1),
('dealer:order:api:update', '更新订单API', 'api', NULL, '/api/dealer/orders/:id', 'PUT', 1114, 1),
('dealer:order:api:delete', '删除订单API', 'api', NULL, '/api/dealer/orders/:id', 'DELETE', 1115, 1);

-- 更多权限示例
INSERT INTO permissions (code, name, type, resource_path, method, sort_order, status) VALUES
-- 门店库存管理
('store:inventory:read', '查看库存', 'button', NULL, NULL, 201, 1),
('store:inventory:update', '调整库存', 'button', NULL, NULL, 202, 1),
('store:inventory:api:list', '库存列表API', 'api', '/api/store/inventory', 'GET', 2011, 1),
('store:inventory:api:adjust', '调整库存API', 'api', '/api/store/inventory/adjust', 'POST', 2012, 1),

-- 员工管理
('dealer:staff:read', '查看员工', 'button', NULL, NULL, 301, 1),
('dealer:staff:create', '添加员工', 'button', NULL, NULL, 302, 1),
('dealer:staff:update', '修改员工', 'button', NULL, NULL, 303, 1),
('dealer:staff:delete', '删除员工', 'button', NULL, NULL, 304, 1),
('dealer:staff:api:list', '员工列表API', 'api', '/api/dealer/staff', 'GET', 3011, 1),

-- 报表统计
('dealer:report:sales', '销售报表', 'menu', '/dealer/reports/sales', NULL, 401, 1),
('dealer:report:api:sales', '销售报表API', 'api', '/api/dealer/reports/sales', 'GET', 4011, 1);
```

### 3. 角色权限分配示例

```sql
-- 为经销商管理员分配权限（拥有所有经销商相关权限）
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'DEALER_ADMIN'),
    p.id
FROM permissions p
WHERE p.code LIKE 'dealer:%' OR p.name LIKE '经销商%';

-- 为门店店长分配权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'STORE_MANAGER'),
    p.id
FROM permissions p
WHERE p.code LIKE 'store:%' OR p.name LIKE '门店%';

-- 为门店店员分配基础权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'STORE_CLERK'),
    p.id
FROM permissions p
WHERE p.code IN (
    'store:inventory:read',
    'store:inventory:api:list',
    'store:order:create',
    'store:order:read'
);
```

### 4. 数据范围配置示例

数据范围通过 `roles.data_scope` 字段定义，在业务代码中根据该值动态构建查询条件：

```sql
-- 数据范围枚举值
-- 1: 仅本人数据 - 只能查看自己创建/负责的数据
-- 2: 本部门数据 - 可查看本部门所有人的数据
-- 3: 本部门及下级部门 - 可查看本部门及下级部门的数据
-- 4: 本公司/本店数据 - 可查看本组织内所有数据
-- 5: 全部数据 - 可查看跨组织的所有数据（仅超级管理员）

-- 示例：查询订单时根据数据范围过滤
-- 伪代码逻辑：
/*
IF data_scope = 1 THEN
    WHERE created_by = current_user_id
ELSE IF data_scope = 2 THEN
    WHERE created_by IN (
        SELECT account_id FROM org_members 
        WHERE org_id = current_user_org_id 
        AND department = current_user_department
    )
ELSE IF data_scope = 3 THEN
    WHERE created_by IN (
        SELECT account_id FROM org_members om
        WHERE om.org_id = current_user_org_id 
        AND (
            om.department = current_user_department
            OR om.department LIKE CONCAT(current_user_department, '/%')
        )
    )
ELSE IF data_scope = 4 THEN
    WHERE org_id = current_user_org_id
ELSE IF data_scope = 5 THEN
    -- 无过滤条件，查询所有数据
END IF
*/
```

### 5. 字段策略示例

```sql
-- 字段策略配置示例：控制敏感字段访问

-- 经销商管理员可以读写员工的所有字段
INSERT INTO field_policies (role_id, resource, field_name, can_read, can_write) VALUES
((SELECT id FROM roles WHERE code = 'DEALER_ADMIN'), 'staff', 'salary', 1, 1),
((SELECT id FROM roles WHERE code = 'DEALER_ADMIN'), 'staff', 'id_card', 1, 1),
((SELECT id FROM roles WHERE code = 'DEALER_ADMIN'), 'staff', 'phone', 1, 1);

-- 经销商主管可以读取但不能修改员工薪资
INSERT INTO field_policies (role_id, resource, field_name, can_read, can_write) VALUES
((SELECT id FROM roles WHERE code = 'DEALER_SUPERVISOR'), 'staff', 'salary', 1, 0),
((SELECT id FROM roles WHERE code = 'DEALER_SUPERVISOR'), 'staff', 'id_card', 1, 0);

-- 经销商普通员工不能访问薪资和身份证字段
INSERT INTO field_policies (role_id, resource, field_name, can_read, can_write) VALUES
((SELECT id FROM roles WHERE code = 'DEALER_STAFF'), 'staff', 'salary', 0, 0),
((SELECT id FROM roles WHERE code = 'DEALER_STAFF'), 'staff', 'id_card', 0, 0);

-- 门店店员可以读取但不能修改客户手机号
INSERT INTO field_policies (role_id, resource, field_name, can_read, can_write) VALUES
((SELECT id FROM roles WHERE code = 'STORE_CLERK'), 'customer', 'phone', 1, 0),
((SELECT id FROM roles WHERE code = 'STORE_CLERK'), 'customer', 'address', 1, 0);

-- 门店店长可以读写客户信息
INSERT INTO field_policies (role_id, resource, field_name, can_read, can_write) VALUES
((SELECT id FROM roles WHERE code = 'STORE_MANAGER'), 'customer', 'phone', 1, 1),
((SELECT id FROM roles WHERE code = 'STORE_MANAGER'), 'customer', 'address', 1, 1);
```

### 6. 用户类型示例

```sql
-- 用户类型（仅用于分类，不参与权限判断）
INSERT INTO user_types (code, name, description, sort_order) VALUES
('INTERNAL', '内部员工', '公司内部正式员工', 1),
('EXTERNAL', '外部人员', '外部合作伙伴或兼职人员', 2),
('CONTRACTOR', '承包商', '承包商或供应商人员', 3),
('VIP', 'VIP客户', '重要客户', 4),
('REGULAR', '普通客户', '普通客户', 5);
```

---

## 实施建议

### 1. 实施步骤

1. **准备阶段（1-2周）**
   - 创建新表结构（在测试环境）
   - 准备迁移脚本
   - 建立角色和权限字典
   - 设计API接口

2. **开发阶段（3-4周）**
   - 实现账号统一登录逻辑
   - 开发权限验证中间件
   - 实现数据范围过滤
   - 实现字段策略控制
   - 开发管理后台

3. **测试阶段（2周）**
   - 在测试环境执行迁移
   - 验证数据完整性
   - 测试权限控制
   - 性能测试

4. **迁移阶段（1周）**
   - 数据库备份
   - 执行生产环境迁移
   - 验证迁移结果
   - 通知用户

5. **切换上线（1天）**
   - 灰度发布
   - 监控异常
   - 应急回滚准备

### 2. 注意事项

1. **数据一致性**
   - 迁移前后数据完整性验证
   - 建立回滚机制
   - 保留旧表至少3个月

2. **性能优化**
   - 为关键查询字段添加索引
   - 权限检查结果缓存（Redis）
   - 使用分页查询大数据量

3. **安全考虑**
   - 敏感字段加密存储
   - 操作日志记录
   - 定期权限审计

4. **用户体验**
   - 提供旧系统到新系统的操作指南
   - 通知用户密码变更（如有冲突）
   - 保持界面一致性

### 3. 权限验证伪代码示例

```python
def check_permission(user_account_id, permission_code, resource_id=None):
    """
    检查用户是否有指定权限
    
    Args:
        user_account_id: 用户账号ID
        permission_code: 权限编码
        resource_id: 资源ID（用于数据范围检查）
    
    Returns:
        bool: 是否有权限
    """
    # 1. 获取用户当前身份
    current_member = get_current_member(user_account_id)
    if not current_member:
        return False
    
    # 2. 获取用户角色
    roles = get_member_roles(current_member.id)
    if not roles:
        return False
    
    # 3. 检查角色是否拥有该权限
    has_permission = False
    for role in roles:
        if check_role_permission(role.id, permission_code):
            has_permission = True
            break
    
    if not has_permission:
        return False
    
    # 4. 检查数据范围（如果提供了资源ID）
    if resource_id:
        for role in roles:
            if check_data_scope(role, current_member, resource_id):
                return True
        return False
    
    return True

def check_field_access(user_account_id, resource, field_name, access_type='read'):
    """
    检查用户是否可以访问特定字段
    
    Args:
        user_account_id: 用户账号ID
        resource: 资源名称
        field_name: 字段名称
        access_type: 访问类型（read/write）
    
    Returns:
        bool: 是否可以访问
    """
    current_member = get_current_member(user_account_id)
    roles = get_member_roles(current_member.id)
    
    for role in roles:
        policy = get_field_policy(role.id, resource, field_name)
        if policy:
            if access_type == 'read' and policy.can_read:
                return True
            if access_type == 'write' and policy.can_write:
                return True
    
    return False
```

### 4. API接口示例

```python
# 登录接口
POST /api/auth/login
{
    "phone": "13800138000",
    "password": "password123"
}

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "account": {
        "id": 1,
        "phone": "13800138000"
    },
    "identities": [  # 用户的多个身份
        {
            "member_id": 100,
            "org_type": "shop",
            "org_id": 1,
            "org_name": "XX经销商",
            "position": "经理",
            "is_primary": true,
            "roles": ["DEALER_MANAGER"]
        },
        {
            "member_id": 101,
            "org_type": "shop_instance",
            "org_id": 10,
            "org_name": "XX门店",
            "position": "店长",
            "is_primary": false,
            "roles": ["STORE_MANAGER"]
        }
    ]
}

# 切换身份接口
POST /api/auth/switch-identity
{
    "member_id": 101
}

# 获取当前用户权限接口
GET /api/auth/permissions

Response:
{
    "member_id": 100,
    "org_type": "shop",
    "org_id": 1,
    "roles": [
        {
            "code": "DEALER_MANAGER",
            "name": "经销商经理",
            "data_scope": 3
        }
    ],
    "permissions": [
        "dealer:order:create",
        "dealer:order:read",
        "dealer:order:update",
        "dealer:staff:read"
    ]
}
```

---

## 附录

### A. 关键表关系图

```
accounts (账号)
    ↓ 1:1
users (用户档案)

accounts (账号)
    ↓ 1:N
org_members (成员身份)
    ↓ N:M
roles (角色)
    ↓ N:M
permissions (权限)
```

### B. Closure Table 查询示例

```sql
-- 查询某个组织的所有下级组织
SELECT 
    oh.descendant_type,
    oh.descendant_id,
    oh.depth
FROM org_hierarchy oh
WHERE oh.ancestor_type = 'shop' 
  AND oh.ancestor_id = 1
  AND oh.depth > 0
ORDER BY oh.depth;

-- 查询某个组织的所有上级组织
SELECT 
    oh.ancestor_type,
    oh.ancestor_id,
    oh.depth
FROM org_hierarchy oh
WHERE oh.descendant_type = 'shop_instance' 
  AND oh.descendant_id = 10
  AND oh.depth > 0
ORDER BY oh.depth;

-- 添加组织关系（当添加门店到经销商时）
INSERT INTO org_hierarchy (ancestor_type, ancestor_id, descendant_type, descendant_id, depth)
VALUES 
    -- 自己到自己
    ('shop_instance', 10, 'shop_instance', 10, 0),
    -- 自己到父级
    ('shop', 1, 'shop_instance', 10, 1),
    -- 继承父级的所有祖先关系
    -- (需要查询父级的祖先并插入)
    ...;
```

### C. 索引优化建议

```sql
-- 账号表
CREATE INDEX idx_phone ON accounts(phone);
CREATE INDEX idx_status ON accounts(status);

-- 成员表
CREATE INDEX idx_account_id ON org_members(account_id);
CREATE INDEX idx_org ON org_members(org_type, org_id);
CREATE INDEX idx_status ON org_members(status);

-- 角色分配表
CREATE INDEX idx_member_id ON member_roles(member_id);
CREATE INDEX idx_role_id ON member_roles(role_id);
CREATE INDEX idx_expires ON member_roles(expires_at);

-- 权限表
CREATE INDEX idx_code ON permissions(code);
CREATE INDEX idx_type ON permissions(type);
CREATE INDEX idx_parent ON permissions(parent_id);

-- 组织层级表
CREATE INDEX idx_ancestor ON org_hierarchy(ancestor_type, ancestor_id, depth);
CREATE INDEX idx_descendant ON org_hierarchy(descendant_type, descendant_id);
```

### D. 常见问题

**Q1: 如何处理一个账号在多个组织中的权限？**

A: 用户登录后，系统返回所有身份列表，用户选择当前工作身份。后续所有操作基于当前身份的权限进行验证。可以通过切换身份接口切换到其他组织。

**Q2: 数据范围和字段策略如何结合使用？**

A: 数据范围控制用户能看到哪些记录，字段策略控制每条记录的哪些字段可见/可编辑。两者是独立的维度，需要同时满足。

**Q3: 如何处理跨组织的数据访问（如经销商查看门店数据）？**

A: 通过 org_hierarchy 表定义组织关系，在权限验证时，如果用户有上级组织的权限，可以访问下级组织的数据。具体实现需要在数据范围检查中加入层级关系判断。

**Q4: 角色和用户类型的区别是什么？**

A: 角色参与权限判断，决定用户能做什么；用户类型仅用于业务分类，如区分内部员工和外部人员，不直接影响权限。

**Q5: 如何实现临时授权？**

A: 在 member_roles 表中设置 expires_at 字段，到期后该角色自动失效。需要定时任务或在权限检查时判断过期时间。

---

## 更新日志

- **2026-02-06**: 初始版本，完成数据库设计、迁移方案和权限体系设计