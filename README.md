# Surface 2 EFI compatibility for Linux 7.0.1

微软 **Surface 2 / Tegra 4 / ARM32** 的启动兼容补丁、构建工具和中文教程。

A source-only toolkit to rebuild the ARM32 EFI stub and decompressor around an unchanged, pinned Linux 7.0.1 kernel payload. It reuses an existing working Surface 2 boot shim and includes microSD fixes, build checks and an independently documented graphics memory leak.

适用于已经按本机要求关闭固件验证，并能通过原 `test.efi` 启动旧 Linux 的设备。保留这一层 Windows→EFI 适配程序，重建新内核前面的 EFI stub 和解压包装，让它在没有 EFI LoadOptions 时自己读取启动参数、取得 Surface 2 设备树，从原双系统菜单直接进入 7.0.1。

本项目重建的是 **启动和解压部分**；7.0.1 内核主体取自指定官方包，并逐字节保持不变。设备树另修正 microSD 的控制器、引脚与供电描述。实测绕过 GRUB 后恢复了几秒内出现 Linux 文字、正常进入图形登录的启动方式。

## 原启动器从哪里获得

已确认 [Open RT 的 surface-2-bootfiles+kernel.zip](https://files.open-rt.party/Linux/Other/surface-2-bootfiles%2Bkernel.zip) 内 `test.efi` 与实机保留文件哈希一致。这个适配层不向内核传递 EFI 参数，由旧内核自己读取 `cmdline.txt`；本项目为新内核恢复这一约定。站点较新的 `release/uefi_bootfiles/bootfiles.zip` 属于另一套实现，尚未由本项目实机验证。

具体文件身份、校验值、两套引导的区别与再分发边界见 [原启动器来源说明](docs/bootloader-origin.md)。原包含 Windows 启动文件和 BCD，不能整包覆盖已有双系统。

## 适用范围和实测

- 设备：Surface 2，Tegra114/Tegra 4；这是 ARM32 项目。
- 原输入：`linux-postmarketos-grate-7.0.1-r4.apk`，具体哈希见 [pins.json](pins.json)。构建工具拒绝其他版本输入。
- 源码参考：libre-tegra/linux `bfffc6d6656e87f3de3aa4c09d852849081ef088`。
- 实测：原双系统菜单、原 `test.efi`、原来的 Windows 启动环境，直启 7.0.1；图形登录、microSD 根分区、Wi-Fi、SSH 正常。
- H.264：CAVLC 测试样本的 V4L2 stateless 硬解输出与软件解码逐字节一致。这不代表浏览器或所有在线视频格式自动获得硬解。
- 内存：动画屏保仍可触发 grate 驱动的 fence 数组泄漏，详见 [已知内存问题](docs/memory-leak.md)。启动补丁没有修复它。

原始 Surface RT / Tegra 3、Surface Pro、ARM64 和其他内核版本需要各自验证。

## 文件

- `patches/0001-*`：EFI 参数兼容及可选诊断记录。
- `patches/0002-*`：参考源码的 microSD 修正。
- `tools/build_wrapper.py`：正常源码链接 EFI 包装，保留指定内核主体；不会安装启动文件。
- `tools/fix_microsd_dtb.py`：修正指定包的 EFI DTB，比较全部节点属性，确认修改只涉及 microSD。
- `tools/unpack_kernel_apk.py`：校验并提取指定公开输入，不安装包。
- `tests/`：格式及参数处理测试。

## 构建

使用 Linux 和 Python 3.10 以上。原生 ARM32 上可使用 GCC；x86 主机可使用 ARM32 Linux GCC 交叉工具链。构建路径使用不含空格和 shell 特殊字符的 ASCII 路径。内核构建还需要 make、patch、flex、bison、bc、perl、xz、OpenSSL 开发头文件；设备树工具需要 `dtc` 和 `fdtput`。2 GB 平板建议 `--jobs 1` 或 `--jobs 2`。

先在 `downloads/` 下载 [固定源码归档](https://codeberg.org/api/v1/repos/libre-tegra/linux/archive/bfffc6d6656e87f3de3aa4c09d852849081ef088.tar.gz) 和 [指定 APK](https://mirrors.tuna.tsinghua.edu.cn/postmarketOS/master/armv7/linux-postmarketos-grate-7.0.1-r4.apk)。按 `pins.json` 核对 SHA-256。旧版包从镜像消失时，应寻找可信归档并核对哈希。

```sh
mkdir -p build/linux build/input out
# 对 downloads/linux-source.tar.gz 核对 pins.json 中的 SHA-256 后解包
tar -xzf downloads/linux-source.tar.gz -C build/linux --strip-components=1
python3 tools/unpack_kernel_apk.py downloads/linux-postmarketos-grate-7.0.1-r4.apk --output build/input
python3 tools/build_wrapper.py --source build/linux --vmlinuz build/input/vmlinuz --output out --jobs 2
python3 tools/fix_microsd_dtb.py --dtb build/input/surface2-efi-original.dtb --output out
```

交叉编译时为 `build_wrapper.py` 增加 `--cross-compile arm-linux-gnueabihf-`。构建过程使用专用源码目录，应用 EFI 补丁，写入构建配置及解压后的 `Image`，并通过正常 Kbuild 链接生成 `out/surface2-compat.efi`。它不重编译内核主体或模块。

输出 `manifest.json` 会记录输入/输出哈希、内核主体一致性、ARM32 EFI 格式和启动元数据。参考实测工具链是 Alpine GCC 15.2.0。其他工具链的 EFI 文件哈希可能不同，需要独立实机验证。

## 安装与恢复

见 [安装教程](docs/install.md)。请先保留自己的可用启动文件，并确认 Windows 恢复方法。不要把 Surface 2 的 Windows 启动适配层当作通用 ARM EFI 文件替换。

## 许可证与二进制

源码和脚本按 GPL-2.0-only 提供，保留上游文件原有许可和版权；见 [LICENSE](LICENSE) 与 [来源和致谢](docs/sources-and-license.md)。本仓库只包含补丁、配置、工具和文档。

原 `test.efi`、旧内核、固件、系统镜像及设备日志不包含在仓库中。当前 APK 的 `.PKGINFO` 标记为 `commit=-dirty`，尚未证明整个内核二进制与某一源码提交完全对应。因此这里先提供本地构建配方；若进一步发布内核二进制，应核实并提供适用许可证所要求的对应源码与构建材料。
