## Quick start

启动前端：

Run `npm i` to install the dependencies.

Run `npm run dev` to start the development server.

启动后端：

```shell
cd backend
python server.py
```

## TODO

还需要完善的地方：

导入导出：

1. 导出

    1) 题目编号目前还是沿用原来的，需要修改

    2) 导出目前直接下载latex格式的文档，后续可以提供在线预览编辑调格式比较好。需要网页端支持latex引擎

2. 导入

    1) 数据还是不是格式良好的，可能有缺损或者串行。导入后试卷数据如何结构化存储校验？

    2) AI后端迁移：

        1) 目前AI后端是Gemini，如果汇报也许支持豆包/GLM之类的国产AI会不会更好？

        2) 迁移后需要对齐效果之类的，回归一遍数据

    3) 标签：目前是AI随意生成的标签，后续如果有标签集合可以更新在prompt中，让AI reference to 已有语义标签

如果要汇报需要一定的可用性，目前除了搜索还行还完全不可直接用...！


### 一些想法
1. 为了提高导入导出质量，重新做SFT对齐是否有助于提高OCR效果？