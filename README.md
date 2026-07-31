# @小晚不在 · 公众号排版 Lite

仓库地址：https://github.com/cyberxiaowan/xiaowan-wechat-layout-skill

这是 @小晚不在 在实际制作公众号长文时，基于多轮截图反馈、手机端修改和真实发布复盘沉淀出的公开排版工作流。

## 实际效果示意

[![@小晚不在公众号排版 Skill 实际成品](docs/wechat-layout-showcase.jpg)](https://mp.weixin.qq.com/s/EKjNjihmkXBYgao16m5ztQ?scene=1)

上图是使用这套工作流反复修改后的实际成品。点击图片，或
[查看完整公众号文章](https://mp.weixin.qq.com/s/EKjNjihmkXBYgao16m5ztQ?scene=1)。

示意图仅用于展示排版效果；文章中的品牌图片版权归原品牌及原媒体所有。

它不会替你决定观点、文体和审美，也不会把所有文章强行套进同一种写稿结构。它会让 Codex 在排版时重点检查：

- 首屏是不是一个完整的信息单元；
- 大章节是否一眼可见；
- 横线、竖线、色块和外框是否过多；
- 标题有没有难看的 2～3 字孤行；
- 重点句是否只高亮了半句；
- 图片是否真的解释了正文；
- 多图是否在进入公众号前预先拼好；
- 粘贴到公众号后是否丢图、乱码或错位；
- 这次人工调整能否沉淀为下一次可复用的规则。

## 它与 gzh-design 的关系

本项目是一个工作流增强层，不包含公众号 HTML 排版引擎。

使用前需要安装甲木 × 摸鱼小李制作的
[gzh-design](https://github.com/isjiamu/gzh-design-skill)。本项目会调用它生成基础公众号 HTML，再加入 @小晚不在 从真实发布中沉淀的移动端检查、反馈路由和复盘流程。

## 安装

### 方式一：一条提示词安装两个 Skill

把下面整段复制给 Codex：

```text
请帮我安装并验证以下两个 Codex Skill：

1. gzh-design
   https://github.com/isjiamu/gzh-design-skill

2. xiaowan-wechat-layout-lite
   https://github.com/cyberxiaowan/xiaowan-wechat-layout-skill

要求：
- 先检查本机已安装的 Skills；
- 已存在且结构完整的 Skill 直接保留，不要覆盖；
- 缺少哪个就从对应的官方 GitHub 仓库安装哪个；
- 安装到 Codex 的 Skills 目录；
- 检查两个目录都包含有效的 SKILL.md；
- 告诉我安装结果，以及重新打开 Codex 任务后如何调用。
```

这样即使用户一个都没装，Codex 也会依次安装；已经装过
`gzh-design` 的用户只会补装 @小晚不在 的公开版。

### 方式二：Mac 一键安装

下载并解压仓库后，双击 `install.command`。

安装完成后，新开一个 Codex 任务即可使用。

## 调用

正文已经定稿：

```text
用 $xiaowan-wechat-layout-lite 排版这篇公众号文章。
正文已经定稿，不要改文字。先做手机端结构和图片证据表，
再生成可复制的 HTML，并检查 390px 预览和公众号粘贴稳定性。
```

已经有 HTML：

```text
用 $xiaowan-wechat-layout-lite 检查这份公众号 HTML。
只处理层级、断行、线条和图片规整问题，不要重做已确认的部分。
```

## 默认视觉起点

- 正文：`14px / #595757 / 1.9–2` 行距；
- 章节强调：赭金 `#b17816`；
- 背景：米白 `#fdfdf8`；
- 少线条、少外框，靠层级与留白组织文章；
- 重点覆盖完整语义；
- 图片预合成后再粘贴；
- 最终以公众号后台和手机预览为准。

这些是默认起点，不是要求所有人复制 @小晚不在 的视觉。请换成自己的头像、IP、署名、配色和内容资产。

## 关于写稿

这个公开版专注于排版，不承诺用一套逻辑写所有公众号文章。

品牌案例、教程、个人复盘、访谈和观点文，需要不同的选题、论证与语言方法。若正文尚未完成，请先使用适合该文体的写作 Skill，或让 Codex只做结构整理；正文确认后再调用本 Skill 排版。

## 授权与致谢

- 排版底层：甲木 × 摸鱼小李的 `gzh-design`；
- 工作流整理与移动端规则：@小晚不在；
- 本项目采用 `AGPL-3.0-or-later`；
- 本项目不包含 `gzh-design` 源码，也不包含 @小晚不在 的私人文章、AI呀素材或业务资料。

详见 [NOTICE.md](NOTICE.md)。
