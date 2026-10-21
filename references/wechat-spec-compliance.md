# 微信平台合规门禁

本 Skill 产出的 HTML 最终要粘进公众号编辑器，因此必须符合官方的
[《微信公众平台编辑器插件开发规范》](https://developers.weixin.qq.com/doc/service/guide/product/plugin_spec.html)
（下称“官方规范 #章节”）。审美判断不能越过这条线：不符合规范的样式在编辑器里会被过滤、被改写，或在手机上直接消失。

官方同步的开源校验实现：`https://github.com/wechatjs/verify-article-structure-spec`（基于真实浏览器，覆盖需要实测布局的规则）。本文件是执行摘要，规则细节与冲突时以官方文档和官方校验结果为准。

## 优先级

1. 官方规范（平台硬约束，不可协商）；
2. 用户本次要求与已确认的个人风格卡；
3. 本 Skill 的通用判断；
4. `gzh-design` 主题默认值。

用户的要求与规范冲突时（例如“换成宋体”“整篇固定 750px 宽”），先说明后果，再按规范实现近似效果：用字重、字距、行高、字号和留白代替换字体；用百分比宽度、内边距和留白代替固定宽度。不要默默照做，也不要默默拒绝。

## 一、交付前的三道关

1. **静态校验（必做）**
   `<gzh-design>/scripts/validate_gzh_html.py <正文.html>`，ERROR 必须为 0；WARNING 逐条判断并在交付说明里交代（渐变压文字、定宽含文字、`line-height`、`<pre>`、半角标点）。
2. **官方实测（条件允许时做终验）**
   `git clone https://github.com/wechatjs/verify-article-structure-spec.git` → `cli/` 下 `npm install` → `npm run check ./article.html`。退出码 `0` 通过、`1` 有违规、`2` 执行异常。环境没有 Node/puppeteer 时，交付里写明“仅完成静态校验与真机检查”。
3. **真机与后台（必做）**
   375–390px 长截图 → 粘进公众号后台 → 手机打开并切一次深色模式。浏览器预览不等于公众号效果。

## 二、CSS 与结构红线（官方规范 #1 / #2 / #3）

| 规则 | 不要写 | 应该写 |
|---|---|---|
| 字体 #3 | 任何 `font-family`（含“只给中文加衬线”） | 不写，走平台默认字体栈；气质靠字重、字距、行高、字号、留白。等宽代码字体是唯一例外 |
| 标签与属性（粘贴） | `<div>`、`class`、`id`、`<style>`、`<script>`、`<link>` | 一律 `<section>` + 内联 `style`；脚本与按钮只留在预览壳 |
| 优先级 #4.5.2 | `!important` | 正常层叠；需要覆盖就用更具体的内联样式 |
| 宽度 #1.4 | 含文字的容器写死 `width: 586px` | `width: 100%` / `max-width: 100%`；表格列宽用百分比；`<img>` 加 `data-w`，样式用 `max-width: 100%; height: auto`（不用 `width: 100%`，小图会被拉糊） |
| 居中 #1.4.1 | 定宽 + 居中，大屏变左对齐 | 居中使用 `margin: 0 auto` + 百分比/max-width |
| 溢出 #1.4.2 | `margin-left: 294pt`、表头固定列宽 | 用内边距、百分比、`box-sizing: border-box` |
| 行高 #1.3 | `line-height: 0` 里包多行文字 | 行高 ≥ 字号；`line-height: 0` 只用于纯图片无缝拼接 |
| 高度 #1.5 | `height: 0` 或 `height: 1px` 里装文字 | 让容器由内容撑开；需要裁切时不得裁到文字 |
| 图片 #1.1 | `img` 设 `opacity: 0`，再用 SVG 背景图显示 | 图片就是 `<img>`，可替换、可编辑 |
| 光标 #1.2 | `caret-color: transparent` | 不设置 |
| 对齐 #1.6 | `text-align: start / end` | 只用 `left / center / right` |
| 动效 #1.7 | `<animate begin="touchstart">` | `begin="touchstart; click"`，或干脆不做 SVG 动画，避免微信端不触发 |
| 代码 #1.8 | 用 `<pre>` 包普通段落 | 正文用 `<section>`／`<p>`；`<pre>` 只包代码，并给 `white-space: pre-wrap; word-break: break-word`，或改用行内代码 |
| 嵌套 #2.1 | 同标签、同样式、单子节点套 10 层以上 | 精简中间层；让每一层都有实际样式职责（静态脚本不查这条，靠官方 CLI 或人工核对） |
| 行内容器 #2.2 | `<span leaf>` 里放 `section / p / div` | `leaf` 内只放文本、`span`、`strong`、`img` |
| 功能容器 #2.3 | 给普通容器加 `nodeleaf` | 只在官方指定组件容器上使用，不要手写 |

`data-ignore-width` 只豁免宽度检测，不豁免行高、高度、对齐等其他规则，并且会连同子树一起跳过——只在横向滚动、刻意的视觉裁切等场景使用，并在交付里写明理由。

## 三、图片与 base64

**结论先说**：base64 是「复制载体」，不是「发布形态」。公众号文章最终引用的图片必须落在 `mmbiz.qpic.cn`，编辑器会在保存／发布时处理或过滤 `data:` URI。因此：

- **优先级**：素材库／图床 `https` URL ＞ base64 ＞ 本地路径（禁止）。URL 版更轻、发布后能单独换图；base64 不依赖任何服务器，但体积涨约 33%，且发布后不可替换。
- **"图床能用"只能粘完才知道**：防盗链、按 UA 拦截、`http` 混用、链接过期，在本地浏览器里都看不出来。所以先用 URL，粘进后台逐张确认；破掉的再转 base64。
- **本地图片必须先处理**：复制时剪贴板传的是 HTML 字符串，不是图片字节。本地路径（`./a.jpg`、`/Users/...`、`file://`）粘进后台一定破图——微信取不到你磁盘上的文件。所以本地图只有两条出路：内嵌成 base64，或先上传拿到 `https` 地址。
- **两版交付**：
  - 内嵌版（复制用）：`python3 scripts/inline_images.py article.html` 默认内嵌本地图、保留 http(s)；粘完发现某张远程图破了，用 `--inline-remote` 重跑把远程图也抓下来内嵌（抓取失败只告警并保留 URL，本地抓不到不代表微信抓不到）；脚本默认**拒绝写出**任何仍含本地路径的文件，除非显式加 `--allow-local`；
  - 发布稳定版：图片用可访问 URL（素材库 / `mmbiz.qpic.cn`），作为 base64 被吞掉时的兜底。
- **粘贴后必须验证**：粘进后台后检查图片的 `src`。已变成 `mmbiz.qpic.cn` ＝ 转存成功；仍是 `data:image/...` 或显示空白 ＝ 编辑器没接住，改用素材库 URL，别直接发布。
- **体积**：base64 会让体积涨约 33%。单图压到 1–2MB 以内，单文件控制在 10MB 内（脚本默认上限）；超限先压缩或拼图，否则剪贴板和编辑器会卡。整篇图片多时，可分两批粘贴。
- **不替代素材库**：base64 无法单独替换某张图、无法带 `data-w` 之外的图片元信息，也不进入公众号素材管理；需要反复改图的封面、头图仍应上传素材库。
- **图片样式**：`max-width: 100%; height: auto; display: block; margin: 0 auto` + `data-w`（原图像素宽）。内嵌脚本会自动补 `data-w`、`max-width` 和 `height: auto`。
- **允许的例外**：极小图标（≤120px 的角标、分隔符）内嵌后体积可忽略，可以长期用 base64；正文照片不建议。

## 四、Dark Mode（官方规范 #4）

- **颜色**：正文与背景对比度 ≥ 4.5:1；≥18px 或加粗文字 ≥ 3:1。浅灰弱化文字（如 `#9ea096` 在米白底上只有约 2.6:1）不要用来承载成段正文或图注。
- **渐变**：文字与卡片的背景用纯色；渐变只用于下方没有文字的装饰块。暗色模式会把文字背景渐变压成纯色，中间调、透明叠加和格子纹理都会丢失。
- **结构**：多个文本共用一个背景时，背景写在公共容器上，不要逐个文本节点重复设置。
- **层级**：不要用绝对定位或变形把文字挪到没有嵌套关系的底色上；算法按深度优先顺序转换，视觉与结构必须一致。
- **图片**：不要用图片承载纯文本标题或正文；透明底图片里的黑色系元素在深色底上要仍然可辨。
- **SVG**：能改就用 `stroke="currentColor" fill="currentColor"`，或给一块跟随主题的底色。
- **豁免**：`data-no-dark`（单节点跳过转换）、`data-ignore-dm="low-contrast text-bg-gradient"` 只在深色模式实测确认无问题后局部使用，并写进交付说明。

## 五、本项目自己的结构约定

```text
根 <section style="width: 100%">
├─ 段落 <section>／<p>
│  └─ <span leaf=""> 行内内容（文本／span／strong／img）
├─ 图片 <section> → <img data-w="1080" style="max-width: 100%; height: auto; display: block; margin: 0 auto">
└─ 图片组：同一容器内并排，统一间距，不逐个加外边距
```

- 不手写编辑器私有属性（`leaf`、`nodeleaf`、`data-imgqrcoded`、`contenteditable` 等）；本项目只用 `data-w`、`data-ignore-width`、`data-no-dark`、`data-ignore-dm`。
- 预览壳只用于本地：`<button>`、`<script>`、`class`、`id` 都留在壳里，粘进公众号的必须是干净正文 `<section>`。校验只对干净正文跑，不对预览页跑。

## 六、交付时附一句合规结论

至少在交付里说明：

```text
静态度量：validate_gzh_html.py → ERROR 0；WARNING N 条（已逐条判断：……）
官方实测：verify-article-structure-spec → 退出码 0（或：环境无 Node，未跑）
图片：内嵌版 N 张 / 共 X MB；粘贴后已转存 mmbiz（或：仍为 data:，待换素材库 URL）
真机：375–390px 长截图正常；后台粘贴无丢图/乱码；深色模式已检查
豁免：data-ignore-width ×1（横向滚动代码块）
```

没有这一句，就不算完成排版。

规范持续更新：交付前顺手看一眼官方页面与 `verify-article-structure-spec` 的规则变更，别把旧结论当永久结论。
