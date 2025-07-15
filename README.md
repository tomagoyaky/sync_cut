# Sync Cut - 音视频转换工具

一个基于Python的音视频转换工具，支持MP4转MP3、MP3转文字等功能。

## 功能特性

- **MP4转MP3**: 将MP4视频文件转换为MP3音频文件，支持参数优化以获得最小文件大小
- **MP3转文字**: 支持两种引擎
  - **阿里云NLS**: 云端语音识别服务，识别准确度高，需要网络连接
  - **OpenAI Whisper**: 本地语音识别模型，离线可用，支持多种语言
- **Web界面**: 提供友好的Web界面进行文件上传和转换配置
- **实时进度**: 支持转换过程的实时进度显示
- **配置管理**: 灵活的配置管理系统
- **模型管理**: Whisper模型的下载、删除和状态管理

## 项目结构

```
sync_cut/
├── plugins/                    # 插件目录
│   ├── config.py              # 配置管理
│   ├── mp4_to_mp3/            # MP4转MP3模块
│   │   ├── mp4_to_mp3.py      # 转换逻辑
│   │   └── tools/             # FFmpeg工具
│   │       ├── ffmpeg.exe     # FFmpeg主程序
│   │       ├── ffprobe.exe    # 媒体信息工具
│   │       └── ffmpeg_utils.py # FFmpeg封装工具
│   ├── mp3_to_txt/            # MP3转文字模块
│   │   ├── mp3_to_txt.py      # 阿里云NLS转换逻辑
│   │   ├── whisper_convert.py # Whisper转换逻辑
│   │   └── manage_models.py   # 模型管理脚本
│   └── web_app/               # Web应用
│       ├── web_app.py         # Flask应用
│       └── templates/         # HTML模板
├── workspace/                 # 工作空间
│   ├── venv/                  # Python虚拟环境
│   ├── models/                # 模型文件
│   ├── logs/                  # 日志文件
│   ├── upload/                # 上传文件
│   ├── tmp/                   # 临时文件
│   └── status/                # 状态文件
├── tools/                     # 工具目录
├── demo.mp4                   # 示例视频文件
├── start.cmd                  # 启动脚本
├── config.yaml.example        # 配置文件模板
└── README.md                  # 说明文档
```

## 安装与配置

### 1. 环境要求

- Python 3.8+
- Windows 10/11 (批处理脚本)
- FFmpeg (已包含在项目中)

### 2. 快速开始

1. **运行启动脚本**：
   ```cmd
   start.cmd
   ```
   脚本会自动：
   - 创建虚拟环境
   - 安装依赖包
   - 启动Web服务

2. **访问Web界面**：
   打开浏览器访问 `http://localhost:5000`

### 3. 阿里云NLS配置

要使用MP3转文字功能，需要配置阿里云智能语音交互服务：

#### 3.1 获取阿里云访问密钥

1. 登录 [阿里云控制台](https://ram.console.aliyun.com/manage/ak)
2. 创建或获取 AccessKey ID 和 AccessKey Secret

#### 3.2 创建NLS应用

1. 访问 [智能语音交互控制台](https://nls-portal.console.aliyun.com/applist)
2. 创建新应用，获取 App Key

#### 3.3 配置文件设置

1. 复制 `config.yaml.example` 为 `config.yaml`
2. 填入你的阿里云凭证：

```yaml
alibaba_nls:
  access_key_id: "YOUR_ACCESS_KEY_ID"
  access_key_secret: "YOUR_ACCESS_KEY_SECRET"
  app_key: "YOUR_NLS_APP_KEY"
  region: "cn-shanghai"
  endpoint: "https://nls-gateway.cn-shanghai.aliyuncs.com"
```

## 使用说明

### Web界面使用

1. **文件上传**: 在上传页面选择MP4或MP3文件
2. **选择转换类型**:
   - MP4转MP3: 将视频转换为音频
   - MP3转文字: 将音频转换为文字
   - MP4转文字: 完整流程，先转音频再转文字
3. **配置参数**: 在配置页面调整转换参数
4. **查看历史**: 在历史页面查看转换记录

### 命令行使用

#### MP4转MP3

```python
from plugins.mp4_to_mp3.mp4_to_mp3 import convert_mp4_to_mp3

def progress_callback(percent, message):
    print(f"Progress: {percent}% - {message}")

success, message, metadata = convert_mp4_to_mp3(
    "input.mp4", 
    "output.mp3", 
    progress_callback=progress_callback
)
```

#### MP3转文字

```python
from plugins.mp3_to_txt.mp3_to_txt import convert_mp3_to_txt

def progress_callback(percent, message):
    print(f"Progress: {percent}% - {message}")

success, message, metadata = convert_mp3_to_txt(
    "input.mp3", 
    "output.txt", 
    "output.srt",
    progress_callback=progress_callback
)
```

## 配置参数说明

### MP4转MP3参数

- `audio_bitrate`: 音频比特率 (默认: "64k")
- `audio_channels`: 声道数 (1=单声道, 2=立体声)
- `audio_sample_rate`: 采样率 (默认: 16000)
- `normalize_audio`: 音频标准化 (默认: true)
- `remove_silence`: 移除静音 (默认: true)

### MP3转文字参数

- `format`: 音频格式 (默认: "pcm")
- `sample_rate`: 采样率 (默认: 16000)
- `enable_punctuation_prediction`: 启用标点符号预测
- `enable_inverse_text_normalization`: 启用逆文本标准化
- `enable_voice_detection`: 启用语音活动检测
- `max_sentence_silence`: 最大句子静音时长 (毫秒)
- `chunk_size`: 音频块大小 (字节)

## 技术栈

- **后端**: Python 3.8+, Flask
- **音视频处理**: FFmpeg, MoviePy, PyDub
- **语音识别**: 阿里云智能语音交互 (NLS)
- **前端**: HTML5, CSS3, JavaScript
- **模板引擎**: Jinja2
- **配置管理**: YAML

## 故障排除

### 常见问题

1. **FFmpeg相关错误**:
   - 确保 `plugins/mp4_to_mp3/tools/` 目录下有 ffmpeg.exe 和 ffprobe.exe
   - 检查文件权限

2. **阿里云NLS连接失败**:
   - 检查网络连接
   - 验证AccessKey和AppKey是否正确
   - 确认账户余额和服务状态

3. **依赖安装失败**:
   - 使用管理员权限运行 start.cmd
   - 检查Python版本是否符合要求
   - 手动安装：`pip install -r plugins/requirements.txt`

4. **音频格式不支持**:
   - 确保输入文件格式正确
   - 检查文件是否损坏

### 日志查看

- Web应用日志: `workspace/logs/web_app.log`
- 转换日志: `workspace/logs/mp4_to_mp3_conversions.json`
- 识别日志: `workspace/logs/mp3_to_txt_conversions.json`

## 开发说明

### 项目架构

- 采用模块化设计，每个功能独立成包
- 使用工厂模式创建转换器实例
- 支持配置文件热加载
- 实现了进度回调机制

### 扩展开发

1. **添加新的转换器**:
   - 在 `plugins/` 下创建新模块
   - 实现标准的转换器接口
   - 在 `web_app.py` 中注册路由

2. **自定义FFmpeg参数**:
   - 修改 `plugins/mp4_to_mp3/tools/ffmpeg_utils.py`
   - 添加新的命令行参数

3. **扩展NLS功能**:
   - 修改 `plugins/mp3_to_txt/mp3_to_txt.py`
   - 添加新的识别参数或后处理逻辑

## 许可证

本项目采用 MIT 许可证。

## 支持

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 查看文档: [阿里云智能语音交互文档](https://help.aliyun.com/zh/isi/getting-started/start-here)

---

**注意**: 使用阿里云NLS服务需要付费，请根据使用量合理规划成本。 