/*
 Navicat Premium Data Transfer

 Source Server         : 127.0.0.1
 Source Server Type    : MySQL
 Source Server Version : 50639
 Source Host           : localhost:3306
 Source Schema         : weibo

 Target Server Type    : MySQL
 Target Server Version : 50639
 File Encoding         : 65001

 Date: 18/12/2018 16:44:16
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for weibo_discovery_person
-- ----------------------------
DROP TABLE IF EXISTS `weibo_discovery_person`;
CREATE TABLE `weibo_discovery_person`  (
  `url` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `classify` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`url`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Compact;

SET FOREIGN_KEY_CHECKS = 1;
