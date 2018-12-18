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

 Date: 18/12/2018 16:44:25
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for weibo_post
-- ----------------------------
DROP TABLE IF EXISTS `weibo_post`;
CREATE TABLE `weibo_post`  (
  `weibo_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `post_time` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `from_client` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `weibo_comment` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`weibo_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 555061 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Compact;

SET FOREIGN_KEY_CHECKS = 1;
