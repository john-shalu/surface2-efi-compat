# 验证记录

- 原生 ARM32，Alpine GCC 15.2.0。
- 公布的 build_wrapper.py 已在设备执行，生成 EFI SHA-256 与已多次直启的日常版完全相同：`1cbe919472691478a1ca9dc3d8590e084e617cb705b2d2aa64ec2091a90b0c30`。
- 内核主体保持29,724,216字节，SHA-256 `5f2beb941f6fa76bcab8cb3094ace8d08313121d7278380e3e17bb389f993880`。
- 公布的 DTB 工具生成与实机可用树相同的 SHA-256：`834cadac624036f4c987071c07099d0d28d3de88b17d3425aceea9cf494a1f3d`，确认其他属性及保留内存不变。
- 参数读取逻辑测试：日志开启/关闭各12项，共24项。
- 格式校验测试：7项，覆盖伪XZ常量、无效元数据、越界和长度不符。
- 日常模式不调用 EFI 文件写入；诊断模式只在 ExitBootServices 前记录。

运行纯格式测试：

```sh
python3 -m unittest discover -s tests -v
```

在已应用 EFI 补丁的源码上运行逻辑测试：

```sh
python3 tools/check_compat_io.py --source build/linux
```

测试使用模拟 EFI 接口，不代替固件实机验证。不同 Surface 2 固件和工具链仍需独立测试。
