介绍
===================

  此项目主要目的是以一种更简单更快捷的方式爬取微博信息，并用于情感分析。不仅限于爬取评论，
接下来将会爬取个人信息以及其他相关的内容，可配置。
  和其他微博爬虫项目不同，此项目旨在使用更加简单的配置，容易移植的环境。同时对PY2和PY3有良好的支持
  项目在开始阶段，后续将会陆续push，如果你是个新手，也对此感兴趣，不妨 fork，我们一起来 complete it!


1、实现功能
-------------------
简单的使用代理爬取新浪微博用户特定的微博评论数据以及CCPL的数据。

2、流程图
-------------------
线程1（读）——代理——请求——解析——消息队列——线程2（写）——入库
![流程图加载失败！](https://github.com/kuingsamlee/weiboCommentCrawl/raw/master/flowsheet/flow01.png)

3、保存文件
-------------------
先处理微博被评论的时间和真实时间的关系，比如20分钟前、40秒前等..
然后分割大文件——按500条一个小文件保存。
![文件示例内容加载失败！](https://github.com/kuingsamlee/weiboCommentCrawl/raw/master/flowsheet/saved_file.png)

