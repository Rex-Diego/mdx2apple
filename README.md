# mdx2apple

将 MDX/MDD 格式词典转换为 macOS 原生词典格式的工具。

转换后可在 Dictionary.app 中使用，支持三指轻点查词、Spotlight 搜索等系统级功能。

## 使用方法

```bash
# 安装依赖
pip install readmdict lxml

# 转换词典
python build_apple_dict.py your_dictionary.mdx
```

转换完成后，将生成的 `.dictionary` 文件复制到 `~/Library/Dictionaries/`，然后在 Dictionary.app 偏好设置中启用。

## 示例

仓库中以 Etymonline 词源词典为例演示转换效果：

| 文件 | 说明 |
|------|------|
| `etym2023.mdx` | 示例词典数据 |
| `etym2023.mdd` | 示例资源文件 |
| `etym2023.css` | 示例样式表 |

## License

MIT
