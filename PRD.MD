## 项目目录
- plugins
- tools
- workspace
    - venv
    - models
    - logs
    - upload
    - tmp
    - status
- demo.mp4
- start.cmd

## 功能描述
- 所有python代码和依赖文件都创建在plugins目录中
- start.cmd使用英文注释和输出
- start.cmd启动需要创建venv虚拟环境，升级pip、安装依赖，要避免使用状态文件，避免重复每次初始化安装

## 模块
### mp4_to_mp3
- 将mp4视频文件，转换为mp3
- 转换的mp3要求文件大小要求最小
- 转换过程的参数都需要可以配置

### mp3_to_txt
- 将mp3转换为txt和srt字幕文本
- 转换过程的参数都需要可以配置
- 使用阿里nls服务完成语音转文字

## web_app
- flask 生成的后台服务
- 增加上传，和转换配置界面