# 个人 Manim 项目合集

此仓库是我个人的 Manim 动画项目合集。我使用的 Manim 版本是社区版 [Manim CE](https://www.manim.community/). 仓库根目录下基本上除 `public` 之外的文件夹，每个文件夹就是一个独立项目。`public` 文件夹中包含了一些我在自己项目中用到的自定义 `Mobject` 和辅助函数等。关于每个项目的具体介绍参见项目文件夹内的 `README` 文件 (虽然目前还没有)。

项目中用到的字体、音源等外部资源未包含于项目目录中，若想尝试自己渲染视频片段需注意。缺失外部资源可能会导致报错或文字显示异常。以下列出的是我在项目当中使用的部分外部资源：

* 字体
  * 由 [`@派对大魔王`](https://space.bilibili.com/316576469) 老师开发的“快去写作业”系列字体
    * 文本字体 [CEF Fonts CJK](https://github.com/Partyb0ssishere/cef-fonts-cjk)
    * 数学公式字体 [CEF Fonts Mathematique](https://github.com/Partyb0ssishere/cef-fonts-mathematique)
  * LaTeX 中 `ctex` 包附带的中文字体 Fandol 系列。该系列字体可以在 LaTeX 的字体目录下找到。由于程序中某些地方是以文本的形式调用这些字体的，因此会需要找到字体源文件并在系统中安装。在 LaTeX 文本中使用这些字体是无需安装的。
    * 宋体 FandolSong
    * 黑体 FandolHei
* 外部程序
  * `fluidsynth`: 用来将 `midi` 格式的音频转化为 `wav` 等波形音频格式，以便在场景中使用 `add_sound` 添加。安装好 `fluidsynth` 之后要在系统变量 `Path` 中添加可执行文件的路径，成功的标准是在命令行里输入 `fluidsynth` 并按回车不报错。
    * `fluidsynth` 要合成音频需要搭配一个 `sf2` 格式的音源使用。请在 `public/assets/` 目录下新建一个名为 `soundfont.toml` 的配置文件，并在文件内指定 `sf2` 音源路径
        
        ```toml
        soundfontPath = "path/to/your/soundfont.sf2"
        ```

