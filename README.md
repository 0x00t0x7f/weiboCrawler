介绍
===================

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

