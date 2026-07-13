# ************************************************************
# Sequel Ace SQL dump
# 版本号： 20100
#
# https://sequel-ace.com/
# https://github.com/Sequel-Ace/Sequel-Ace
#
# 主机: 10.0.49.17 (MySQL 5.7.28)
# 数据库: jove_ims
# 生成时间: 2026-07-10 05:16:20 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
SET NAMES utf8mb4;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE='NO_AUTO_VALUE_ON_ZERO', SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# 转储表 alembic_version
# ------------------------------------------------------------

DROP TABLE IF EXISTS `alembic_version`;

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



# 转储表 customer
# ------------------------------------------------------------

DROP TABLE IF EXISTS `customer`;

CREATE TABLE `customer` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '客户ID',
  `name` varchar(200) NOT NULL COMMENT '客户名称',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `weight` int(11) NOT NULL DEFAULT '0' COMMENT '权重，越高越靠前',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



# 转储表 inbound_order
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inbound_order`;

CREATE TABLE `inbound_order` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `order_no` varchar(30) NOT NULL COMMENT '入库单号，前缀 JIN-',
  `inbound_mode` varchar(20) NOT NULL COMMENT '入库方式：PROCUREMENT=采购入库，NON_PROCUREMENT=其他入库',
  `stock_condition` varchar(30) NOT NULL COMMENT '入库类型/库存属性',
  `partner_id` int(11) NOT NULL COMMENT '往来单位 ID',
  `related_outbound_order_id` bigint(20) DEFAULT NULL COMMENT '关联出库单 ID（其他入库/退货入库）',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `operation_status` varchar(30) NOT NULL COMMENT '操作状态：INITIATED/PICKING/CHECKING/COMPLETED/CANCELLED/FAILED',
  `total_qty` int(11) NOT NULL DEFAULT '0' COMMENT '入库商品总件数',
  `submitted_by` int(11) DEFAULT NULL COMMENT '提交审核人用户 ID',
  `reviewed_by` int(11) DEFAULT NULL COMMENT '审核通过人用户 ID',
  `submitted_at` datetime DEFAULT NULL COMMENT '提交审核时间',
  `reviewed_at` datetime DEFAULT NULL COMMENT '审核通过时间（流水统计口径）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_inbound_order_order_no` (`order_no`),
  KEY `related_outbound_order_id` (`related_outbound_order_id`),
  KEY `reviewed_by` (`reviewed_by`),
  KEY `submitted_by` (`submitted_by`),
  KEY `ix_inbound_order_operation_status` (`operation_status`),
  KEY `inbound_order_ibfk_1` (`partner_id`),
  CONSTRAINT `inbound_order_ibfk_1` FOREIGN KEY (`partner_id`) REFERENCES `partner` (`id`),
  CONSTRAINT `inbound_order_ibfk_2` FOREIGN KEY (`related_outbound_order_id`) REFERENCES `outbound_order` (`id`),
  CONSTRAINT `inbound_order_ibfk_3` FOREIGN KEY (`reviewed_by`) REFERENCES `sys_user` (`id`),
  CONSTRAINT `inbound_order_ibfk_4` FOREIGN KEY (`submitted_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单';



# 转储表 inbound_order_item
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inbound_order_item`;

CREATE TABLE `inbound_order_item` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `inbound_order_id` bigint(20) NOT NULL COMMENT '入库单 ID',
  `line_id` bigint(20) NOT NULL COMMENT '入库商品行 ID',
  `item_id` bigint(20) DEFAULT NULL COMMENT '审核通过后关联的 inventory_item.id',
  `item_sn` varchar(50) NOT NULL COMMENT '录入或系统生成的 SN',
  `sn_source` varchar(10) NOT NULL DEFAULT 'MANUAL' COMMENT 'SN 来源：MANUAL=人工录入，AUTO=系统生成',
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  KEY `line_id` (`line_id`),
  KEY `ix_inbound_order_item_inbound_order_id` (`inbound_order_id`),
  CONSTRAINT `inbound_order_item_ibfk_1` FOREIGN KEY (`inbound_order_id`) REFERENCES `inbound_order` (`id`),
  CONSTRAINT `inbound_order_item_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `inventory_item` (`id`),
  CONSTRAINT `inbound_order_item_ibfk_3` FOREIGN KEY (`line_id`) REFERENCES `inbound_order_line` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单单品 SN 绑定';



# 转储表 inbound_order_line
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inbound_order_line`;

CREATE TABLE `inbound_order_line` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `inbound_order_id` bigint(20) NOT NULL COMMENT '入库单 ID',
  `sku_id` int(11) NOT NULL COMMENT 'SKU ID',
  `quantity` int(11) NOT NULL COMMENT '该 SKU 入库件数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `unit_price` decimal(12,2) DEFAULT NULL COMMENT '采购单价',
  PRIMARY KEY (`id`),
  KEY `sku_id` (`sku_id`),
  KEY `ix_inbound_order_line_inbound_order_id` (`inbound_order_id`),
  CONSTRAINT `inbound_order_line_ibfk_1` FOREIGN KEY (`inbound_order_id`) REFERENCES `inbound_order` (`id`),
  CONSTRAINT `inbound_order_line_ibfk_2` FOREIGN KEY (`sku_id`) REFERENCES `product_sku` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单商品行（按 SKU 汇总）';



# 转储表 inventory_daily_summary
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inventory_daily_summary`;

CREATE TABLE `inventory_daily_summary` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `snapshot_date` date NOT NULL COMMENT '业务日期',
  `opening_in_stock_qty` int(11) DEFAULT NULL COMMENT '期初在库件数',
  `inbound_qty` int(11) NOT NULL DEFAULT '0' COMMENT '当日审核入库件数（全库合计）',
  `outbound_qty` int(11) NOT NULL DEFAULT '0' COMMENT '当日审核出库件数（全库合计）',
  `closing_in_stock_qty` int(11) NOT NULL COMMENT '期末在库件数',
  `closing_asset_amount` decimal(14,2) DEFAULT NULL COMMENT '期末在库资产金额',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_inventory_daily_summary_snapshot_date` (`snapshot_date`),
  KEY `ix_inventory_daily_summary_snapshot_date` (`snapshot_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存日汇总（全库级期初/期末与出入库合计）';



# 转储表 inventory_item
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inventory_item`;

CREATE TABLE `inventory_item` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `item_sn` varchar(50) NOT NULL COMMENT '商品 SN/Item ID，全局唯一',
  `sku_id` int(11) NOT NULL COMMENT '所属 SKU ID',
  `stock_status` varchar(30) NOT NULL COMMENT '库存状态：IN_STOCK/SOLD/SOLD_OFFLINE 等',
  `stock_condition` varchar(30) NOT NULL COMMENT '库存属性：NEW/各类 RETURNED_FROM_*',
  `operation_status` varchar(30) NOT NULL COMMENT '操作状态：INITIATED/PICKING/CHECKING/COMPLETED 等',
  `last_order_no` varchar(30) DEFAULT NULL COMMENT '最近关联出入库单号',
  `quantity` int(11) NOT NULL DEFAULT '1' COMMENT '数量，固定为 1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `unit_price` decimal(12,2) DEFAULT NULL COMMENT '采购单价',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_inventory_item_item_sn` (`item_sn`),
  KEY `ix_inventory_item_sku_id` (`sku_id`),
  KEY `ix_inventory_item_stock_status` (`stock_status`),
  CONSTRAINT `inventory_item_ibfk_1` FOREIGN KEY (`sku_id`) REFERENCES `product_sku` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存单品表（一物一码核心表）';



# 转储表 inventory_item_history
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inventory_item_history`;

CREATE TABLE `inventory_item_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `item_id` bigint(20) NOT NULL COMMENT '单品 ID',
  `event_type` varchar(30) NOT NULL COMMENT '事件类型：INBOUND/OUTBOUND/STATUS_CHANGE',
  `order_no` varchar(30) DEFAULT NULL COMMENT '关联出入库单号',
  `from_stock_status` varchar(30) DEFAULT NULL COMMENT '变更前库存状态',
  `to_stock_status` varchar(30) DEFAULT NULL COMMENT '变更后库存状态',
  `from_operation_status` varchar(30) DEFAULT NULL COMMENT '变更前操作状态',
  `to_operation_status` varchar(30) DEFAULT NULL COMMENT '变更后操作状态',
  `operator_id` int(11) DEFAULT NULL COMMENT '操作人用户 ID',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `operator_id` (`operator_id`),
  KEY `ix_inventory_item_history_item_id` (`item_id`),
  CONSTRAINT `inventory_item_history_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory_item` (`id`),
  CONSTRAINT `inventory_item_history_ibfk_2` FOREIGN KEY (`operator_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存单品变动轨迹';



# 转储表 inventory_item_snapshot
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inventory_item_snapshot`;

CREATE TABLE `inventory_item_snapshot` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `snapshot_at` datetime NOT NULL COMMENT '快照执行时间',
  `snapshot_date` date DEFAULT NULL COMMENT '快照业务日期',
  `snapshot_type` varchar(10) NOT NULL DEFAULT 'DAILY' COMMENT '快照类型：DAILY=日快照，MONTHLY=月快照',
  `item_id` bigint(20) NOT NULL COMMENT '原 inventory_item.id',
  `item_sn` varchar(50) NOT NULL COMMENT '商品 SN',
  `sku_id` int(11) NOT NULL COMMENT 'SKU ID',
  `stock_status` varchar(30) NOT NULL COMMENT '快照时库存状态',
  `stock_condition` varchar(30) NOT NULL COMMENT '快照时库存属性',
  `operation_status` varchar(30) NOT NULL COMMENT '快照时操作状态',
  `last_order_no` varchar(30) DEFAULT NULL COMMENT '快照时最近关联单号',
  `quantity` int(11) NOT NULL DEFAULT '1' COMMENT '数量，固定为 1',
  `snapshot_month` varchar(7) DEFAULT NULL COMMENT '快照所属月份，格式 YYYY-MM',
  `unit_price` decimal(12,2) DEFAULT NULL COMMENT '快照时采购单价',
  PRIMARY KEY (`id`),
  KEY `ix_inventory_item_snapshot_item_sn` (`item_sn`),
  KEY `ix_inventory_item_snapshot_snapshot_at` (`snapshot_at`),
  KEY `ix_inventory_item_snapshot_snapshot_month` (`snapshot_month`),
  KEY `ix_inventory_item_snapshot_snapshot_date` (`snapshot_date`),
  KEY `ix_inventory_item_snapshot_snapshot_type` (`snapshot_type`),
  KEY `ix_inventory_item_snapshot_date_type` (`snapshot_date`,`snapshot_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存单品快照（日快照/月快照）';



# 转储表 inventory_sku_daily_ledger
# ------------------------------------------------------------

DROP TABLE IF EXISTS `inventory_sku_daily_ledger`;

CREATE TABLE `inventory_sku_daily_ledger` (
  `snapshot_date` date NOT NULL COMMENT '业务日期',
  `sku_id` int(11) NOT NULL COMMENT 'SKU ID',
  `opening_in_stock_qty` int(11) DEFAULT NULL COMMENT '期初在库件数',
  `inbound_qty` int(11) NOT NULL DEFAULT '0' COMMENT '当日审核入库件数',
  `outbound_qty` int(11) NOT NULL DEFAULT '0' COMMENT '当日审核出库件数',
  `closing_in_stock_qty` int(11) NOT NULL COMMENT '期末在库件数',
  `closing_asset_amount` decimal(14,2) DEFAULT NULL COMMENT '期末在库资产金额',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `inbound_new` int(11) NOT NULL DEFAULT '0' COMMENT '入库-正常（采购入库）',
  `inbound_returned_from_sale` int(11) NOT NULL DEFAULT '0' COMMENT '入库-线上售出退回',
  `inbound_returned_from_sold_offline` int(11) NOT NULL DEFAULT '0' COMMENT '入库-线下售出退回',
  `inbound_returned_from_presold` int(11) NOT NULL DEFAULT '0' COMMENT '入库-准售出退回',
  `inbound_returned_from_gift` int(11) NOT NULL DEFAULT '0' COMMENT '入库-赠送退回',
  `inbound_returned_from_scrapped` int(11) NOT NULL DEFAULT '0' COMMENT '入库-损毁退回',
  `inbound_returned_from_rnd` int(11) NOT NULL DEFAULT '0' COMMENT '入库-研发退回',
  `inbound_returned_from_sample` int(11) NOT NULL DEFAULT '0' COMMENT '入库-样机退回',
  `inbound_returned_from_trial` int(11) NOT NULL DEFAULT '0' COMMENT '入库-试用退回',
  `inbound_returned_from_repair` int(11) NOT NULL DEFAULT '0' COMMENT '入库-维修退回',
  `outbound_sold` int(11) NOT NULL DEFAULT '0' COMMENT '出库-售出-线上',
  `outbound_rnd` int(11) NOT NULL DEFAULT '0' COMMENT '出库-研发',
  `outbound_gifted` int(11) NOT NULL DEFAULT '0' COMMENT '出库-赠送',
  `outbound_repair` int(11) NOT NULL DEFAULT '0' COMMENT '出库-维修',
  `outbound_presold` int(11) NOT NULL DEFAULT '0' COMMENT '出库-准售出',
  `outbound_scrapped` int(11) NOT NULL DEFAULT '0' COMMENT '出库-损毁',
  `outbound_sample` int(11) NOT NULL DEFAULT '0' COMMENT '出库-样机',
  `outbound_borrowed` int(11) NOT NULL DEFAULT '0' COMMENT '出库-借用',
  `outbound_trial` int(11) NOT NULL DEFAULT '0' COMMENT '出库-试用',
  `outbound_sold_offline` int(11) NOT NULL DEFAULT '0' COMMENT '出库-售出-线下',
  `outbound_dept_procurement` int(11) NOT NULL DEFAULT '0' COMMENT '出库-部门采购',
  `inbound_returned_from_dept_procurement` int(11) NOT NULL DEFAULT '0' COMMENT '入库-部门采购退回',
  PRIMARY KEY (`snapshot_date`,`sku_id`),
  KEY `sku_id` (`sku_id`),
  CONSTRAINT `inventory_sku_daily_ledger_ibfk_1` FOREIGN KEY (`sku_id`) REFERENCES `product_sku` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SKU 日库存流水（快照任务预生成，查询只读）';



# 转储表 outbound_order
# ------------------------------------------------------------

DROP TABLE IF EXISTS `outbound_order`;

CREATE TABLE `outbound_order` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `order_no` varchar(30) NOT NULL COMMENT '出库单号，前缀 JOUT-',
  `outbound_type` varchar(20) NOT NULL COMMENT '出库类型：SOLD/SOLD_OFFLINE/PRESOLD/GIFTED/SCRAPPED/RND/SAMPLE/TRIAL/REPAIR/BORROWED',
  `partner_id` int(11) NOT NULL COMMENT '往来单位 ID',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `operation_status` varchar(30) NOT NULL COMMENT '操作状态：INITIATED/PICKING/CHECKING/COMPLETED/CANCELLED/FAILED',
  `total_qty` int(11) NOT NULL DEFAULT '0' COMMENT '出库商品总件数',
  `submitted_by` int(11) DEFAULT NULL COMMENT '提交审核人用户 ID',
  `reviewed_by` int(11) DEFAULT NULL COMMENT '审核通过人用户 ID',
  `submitted_at` datetime DEFAULT NULL COMMENT '提交审核时间',
  `reviewed_at` datetime DEFAULT NULL COMMENT '审核通过时间（流水统计口径）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '客户名称',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_outbound_order_order_no` (`order_no`),
  KEY `reviewed_by` (`reviewed_by`),
  KEY `submitted_by` (`submitted_by`),
  KEY `ix_outbound_order_operation_status` (`operation_status`),
  KEY `outbound_order_ibfk_1` (`partner_id`),
  CONSTRAINT `outbound_order_ibfk_1` FOREIGN KEY (`partner_id`) REFERENCES `partner` (`id`),
  CONSTRAINT `outbound_order_ibfk_2` FOREIGN KEY (`reviewed_by`) REFERENCES `sys_user` (`id`),
  CONSTRAINT `outbound_order_ibfk_3` FOREIGN KEY (`submitted_by`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库单';



# 转储表 outbound_order_item
# ------------------------------------------------------------

DROP TABLE IF EXISTS `outbound_order_item`;

CREATE TABLE `outbound_order_item` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `outbound_order_id` bigint(20) NOT NULL COMMENT '出库单 ID',
  `item_id` bigint(20) NOT NULL COMMENT '库存单品 ID',
  `sku_id` int(11) NOT NULL COMMENT 'SKU ID',
  `quantity` int(11) NOT NULL DEFAULT '1' COMMENT '数量，固定为 1',
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  KEY `sku_id` (`sku_id`),
  KEY `ix_outbound_order_item_outbound_order_id` (`outbound_order_id`),
  CONSTRAINT `outbound_order_item_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory_item` (`id`),
  CONSTRAINT `outbound_order_item_ibfk_2` FOREIGN KEY (`outbound_order_id`) REFERENCES `outbound_order` (`id`),
  CONSTRAINT `outbound_order_item_ibfk_3` FOREIGN KEY (`sku_id`) REFERENCES `product_sku` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库单单品明细';



# 转储表 partner
# ------------------------------------------------------------

DROP TABLE IF EXISTS `partner`;

CREATE TABLE `partner` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '单位 ID',
  `name` varchar(200) NOT NULL COMMENT '单位名称',
  `group_id` int(11) NOT NULL COMMENT '所属分组 ID',
  `partner_type` smallint(6) NOT NULL COMMENT '单位类型：0=供应商&客户，1=客户，2=供应商',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `status` smallint(6) NOT NULL COMMENT '状态：1=启用，0=停用',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_partner_group_id` (`group_id`),
  CONSTRAINT `partner_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `partner_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='往来单位（供应商/客户）';



# 转储表 partner_group
# ------------------------------------------------------------

DROP TABLE IF EXISTS `partner_group`;

CREATE TABLE `partner_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分组 ID',
  `name` varchar(100) NOT NULL COMMENT '分组名称',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='往来单位分组';



# 转储表 product_category
# ------------------------------------------------------------

DROP TABLE IF EXISTS `product_category`;

CREATE TABLE `product_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分类 ID',
  `name` varchar(100) NOT NULL COMMENT '分类名称',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类';



# 转储表 product_sku
# ------------------------------------------------------------

DROP TABLE IF EXISTS `product_sku`;

CREATE TABLE `product_sku` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '商品 SKU ID',
  `name` varchar(200) NOT NULL COMMENT '商品名称',
  `category_id` int(11) NOT NULL COMMENT '所属分类 ID',
  `barcode` varchar(50) NOT NULL COMMENT '条码编码，如 NO00001',
  `sn_mode` varchar(10) NOT NULL COMMENT 'SN 录入模式：MANUAL=人工，AUTO=系统生成，BOTH=两者皆可',
  `status` smallint(6) NOT NULL COMMENT '状态：1=启用，0=停用',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `unit` varchar(20) DEFAULT NULL COMMENT '计量单位，如 个/张/份/副',
  PRIMARY KEY (`id`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `ix_product_sku_category_id` (`category_id`),
  CONSTRAINT `product_sku_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `product_category` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品 SKU（条码/SN 规则）';



# 转储表 sys_audit_log
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sys_audit_log`;

CREATE TABLE `sys_audit_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `operator_id` int(11) DEFAULT NULL COMMENT '操作人用户 ID',
  `operator_name` varchar(100) NOT NULL COMMENT '操作人账号/昵称快照',
  `action` varchar(30) NOT NULL COMMENT '操作类型：LOGIN/CREATE/UPDATE/DELETE/APPROVE 等',
  `module` varchar(30) NOT NULL COMMENT '业务模块：auth/inbound/outbound/inventory 等',
  `resource_type` varchar(50) DEFAULT NULL COMMENT '资源类型',
  `resource_id` varchar(100) DEFAULT NULL COMMENT '资源标识（如 ID、单号）',
  `resource_name` varchar(200) DEFAULT NULL COMMENT '资源名称或单号展示',
  `summary` varchar(500) NOT NULL COMMENT '操作摘要',
  `before_data` text COMMENT '变更前数据 JSON',
  `after_data` text COMMENT '变更后数据 JSON',
  `ip_address` varchar(45) DEFAULT NULL COMMENT '客户端 IP 地址',
  `created_at` datetime NOT NULL COMMENT '操作时间',
  PRIMARY KEY (`id`),
  KEY `ix_sys_audit_log_action` (`action`),
  KEY `ix_sys_audit_log_created_at` (`created_at`),
  KEY `ix_sys_audit_log_module` (`module`),
  KEY `ix_sys_audit_log_operator_id` (`operator_id`),
  KEY `ix_sys_audit_log_resource_id` (`resource_id`),
  CONSTRAINT `sys_audit_log_ibfk_1` FOREIGN KEY (`operator_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统审计日志';



# 转储表 sys_sequence
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sys_sequence`;

CREATE TABLE `sys_sequence` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `seq_type` varchar(10) NOT NULL COMMENT '序列类型：JIN=入库单，JOUT=出库单',
  `seq_date` varchar(8) NOT NULL COMMENT '业务日期，格式 YYYYMMDD',
  `current_value` int(11) NOT NULL COMMENT '当前已使用的最大序号',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_seq_type_date` (`seq_type`,`seq_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出入库单号按日递增序列';



# 转储表 sys_config
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sys_config`;

CREATE TABLE `sys_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `key` varchar(64) NOT NULL COMMENT '配置键',
  `value` text COMMENT '配置值',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `ix_sys_config_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

INSERT INTO `sys_config` (`key`, `value`) VALUES
  ('app_name', 'IMS'),
  ('app_subtitle', '一物一码库存管理系统');



# 转储表 sys_user
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sys_user`;

CREATE TABLE `sys_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username` varchar(50) NOT NULL COMMENT '登录账号',
  `password` varchar(255) NOT NULL COMMENT 'bcrypt 密码哈希',
  `nickname` varchar(100) DEFAULT NULL COMMENT '显示昵称',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像 URL',
  `status` smallint(6) NOT NULL COMMENT '状态：1=正常，0=禁用',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `role` varchar(20) NOT NULL DEFAULT 'STAFF' COMMENT '角色：ADMIN=管理员，STAFF=普通员工',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_user_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
