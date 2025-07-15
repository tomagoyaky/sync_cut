# Whisper 音频转文字功能

## 概述

本项目现在支持两种音频转文字引擎：
- **阿里云 NLS**：云端语音识别服务，识别准确度高，需要网络连接
- **OpenAI Whisper**：本地语音识别模型，离线可用，支持多种语言

## Whisper 功能特点

### 优势
- ✅ **离线处理**：无需网络连接，保护隐私
- ✅ **多语言支持**：支持中文、英语、日语、韩语等多种语言
- ✅ **高准确度**：OpenAI训练的先进模型
- ✅ **多种模型大小**：从39MB到1.5GB，适应不同需求
- ✅ **开源免费**：无需API密钥或付费

### 限制
- ❌ **需要本地计算资源**：较大模型需要更多内存和计算时间
- ❌ **首次使用需下载模型**：根据模型大小，下载时间不同
- ❌ **处理速度**：相比云端服务，本地处理可能较慢

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `openai-whisper`：Whisper核心库
- `torch`：PyTorch深度学习框架
- `torchaudio`：音频处理库
- `ffmpeg-python`：音频格式转换

### 2. 下载模型

使用模型管理脚本下载所需模型：

```bash
# 查看所有可用模型
python plugins/mp3_to_txt/manage_models.py list

# 下载推荐的base模型（74MB）
python plugins/mp3_to_txt/manage_models.py download base

# 下载更高质量的small模型（244MB）
python plugins/mp3_to_txt/manage_models.py download small
```

### 3. 模型选择建议

| 模型 | 大小 | 速度 | 准确性 | 推荐场景 |
|------|------|------|--------|----------|
| tiny | 39MB | 最快 | 基础 | 快速测试、低资源环境 |
| base | 74MB | 快 | 良好 | **推荐**，日常使用 |
| small | 244MB | 中等 | 更好 | 对准确性有要求的场景 |
| medium | 769MB | 慢 | 高 | 专业使用 |
| large | 1550MB | 最慢 | 最高 | 最佳质量需求 |

## 使用方法

### 1. Web界面使用

1. 打开 `http://localhost:7000/upload`
2. 选择音频或视频文件
3. 选择转换类型（MP3转文字 或 MP4转文字）
4. 在"转换引擎"下拉菜单中选择"OpenAI Whisper"
5. 点击"开始转换"

### 2. 命令行使用

```bash
# 直接使用Whisper转换器
python plugins/mp3_to_txt/whisper_convert.py input.mp3 output.txt output.srt

# 使用原有的mp3_to_txt.py（阿里云NLS）
python plugins/mp3_to_txt/mp3_to_txt.py input.mp3 output.txt output.srt
```

### 3. 配置设置

在Web界面的"配置设置"页面，可以调整Whisper参数：

- **模型大小**：选择适合的模型（tiny/base/small/medium/large）
- **识别语言**：指定语言或选择自动检测
- **计算设备**：CPU或GPU（如果支持CUDA）
- **详细输出**：是否显示详细的处理信息

## 模型管理

### 查看模型状态
```bash
# 查看所有模型状态
python plugins/mp3_to_txt/manage_models.py status

# 查看特定模型状态
python plugins/mp3_to_txt/manage_models.py status base
```

### 删除模型
```bash
# 删除特定模型
python plugins/mp3_to_txt/manage_models.py delete base

# 清理所有模型
python plugins/mp3_to_txt/manage_models.py clean
```

## 性能优化

### 1. GPU加速

如果系统支持CUDA，可以在配置中选择GPU设备：
```yaml
mp3_to_txt:
  whisper_device: "cuda"
```

### 2. 模型选择策略

- **开发测试**：使用tiny模型快速验证
- **日常使用**：使用base模型平衡速度和质量
- **专业场景**：使用medium或large模型获得最佳质量

### 3. 批处理优化

对于大量文件，建议：
1. 使用较小的模型进行批量处理
2. 在低峰时段进行转换
3. 监控系统资源使用情况

## 故障排除

### 常见问题

1. **模型下载失败**
   - 检查网络连接
   - 确保有足够的磁盘空间
   - 尝试重新下载

2. **内存不足**
   - 使用较小的模型（tiny/base）
   - 关闭其他应用程序
   - 增加系统内存

3. **CUDA错误**
   - 确认CUDA和PyTorch版本兼容
   - 降级到CPU模式
   - 更新显卡驱动

4. **音频格式不支持**
   - 检查音频文件格式
   - 使用FFmpeg转换格式
   - 确认文件未损坏

### 日志查看

Whisper转换日志保存在：
```
workspace/logs/whisper_conversions.json
```

## 技术细节

### 文件结构
```
plugins/mp3_to_txt/
├── mp3_to_txt.py          # 阿里云NLS转换器
├── whisper_convert.py     # Whisper转换器
├── manage_models.py       # 模型管理脚本
└── README_WHISPER.md      # 本文档
```

### 配置文件
```yaml
mp3_to_txt:
  # Whisper设置
  whisper_model_size: "base"
  whisper_language: "zh"
  whisper_device: "cpu"
  whisper_verbose: false
```

### API接口

转换API支持引擎选择：
```javascript
POST /api/convert
{
  "file": "audio.mp3",
  "conversion_type": "mp3_to_txt",
  "conversion_engine": "whisper"  // 或 "alibaba_nls"
}
```

## 更新日志

### v1.1.0
- ✅ 添加OpenAI Whisper支持
- ✅ 实现引擎选择功能
- ✅ 创建模型管理工具
- ✅ 更新Web界面
- ✅ 添加配置选项

## 贡献

欢迎提交Issue和Pull Request来改进Whisper功能！

## 许可证

本项目遵循MIT许可证。OpenAI Whisper遵循MIT许可证。 