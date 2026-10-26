# 原启动器来源与兼容条件

核对日期：2026-10-26。只下载和静态分析公开文件，没有运行下载包中的程序。

## 已确认与实机一致的文件

原设备使用者记得文件来自 [Open RT 下载站](https://files.open-rt.party/)，但不记得具体包。对目录与文件做 SHA-256 比对后，确认以下包中的 `test.efi` 与此前实机读取的原文件完全一致：

- 目录：[Linux/Other/](https://files.open-rt.party/Linux/Other/)
- 原包：[surface-2-bootfiles+kernel.zip](https://files.open-rt.party/Linux/Other/surface-2-bootfiles%2Bkernel.zip)
- ZIP 大小：8,233,155 字节。
- ZIP SHA-256：`da49c0b228430508c57849fe4bb52b6aea56f14dc97602408e8d064e93c95eb9`。

| 包内文件 | 大小（字节） | SHA-256 / 特征 |
| --- | ---: | --- |
| `test.efi` | 31,232 | `7242d9fc88753f6464d5ab3dd830c22c395b14f1e41525c544939310b630e95b`；ARMNT `0x1c4`，Windows Boot Application 子系统 `16`；与实机文件一致 |
| `boot.efi` | 7,356,928 | `35858b2469078ba837d42acdb2e848d2db638620c50cb7ecdef0648e986db409`；ARM Thumb `0x1c2`，EFI Application 子系统 `10` |
| `tegra114-microsoft-surface-2.dtb` | 22,542 | `259d6eee616f4ef0ef3d1ca9373c49d099e959a7f12cb9cfa49f30bd5dde9aae`；仅为旧包身份记录，不用于本项目 7.0.1 |

包中还带有 `5.17.0-rc4-next-20220217-g21d89a4d51a7` 模块目录、Windows 启动文件、BCD 和字体。**不能把整个压缩包覆盖到已有双系统的 EFI 分区。** 本项目只将它作为原启动适配层的来源和身份依据，不重新分发包内文件，也不复制其中的 BCD。

实机已删除的旧内核未重新与包内 `boot.efi` 做逐字节比对；已确定的精确二进制身份是仍在使用的 `test.efi`，旧内核版本和参数方式则与该包相符。目录中文件的上传/修改日期不能当作原作者或构建版本证明。

## “不带参数”是什么意思

这里指 Windows 启动适配层没有给内核提供 EFI `LoadOptions`，不代表 Linux 不需要启动参数。

```text
Windows Boot Manager / 原 BCD
  → test.efi（Windows Boot Application）
  → EFI 分区根目录的 boot.efi（包含 Linux EFI stub）
  → Linux
```

此前对实机 `test.efi` 的二进制分析观察到：它装载 `\boot.efi`，并在调用内核入口前清空子映像 `LoadOptions`。旧 `boot.efi` 中可见 `cmdline.txt` 和读取文件参数的诊断字符串，旧源码也有对应的自读参数实现。旧包的参数文件为：

```text
dtb=tegra114-microsoft-surface-2.dtb root=/dev/mmcblk1p2 console=tty1 cpuidle.off=1 rootwait rw
```

因此，旧系统是在**内核的 EFI stub 中读取文本参数**。官方 7.0.1 包缺少这项旧式约定，直接把官方 `vmlinuz` 改名为 `boot.efi` 不足以保留启动能力。

本项目保留原 `test.efi`，只为新内核的 EFI stub 补上“外层参数为空时读文件”的能力。为了与旧文件区分，新参数固定放在 `surface-upgrade/stub-native/cmdline.txt`；它通过 `dtb=` 指向本项目修正后的 7.0.1 设备树。文件位置和参数例子见 [安装教程](install.md)。

## 同站另一套 UEFI 文件不能混为一谈

另有 [release/uefi_bootfiles/bootfiles.zip](https://files.open-rt.party/release/uefi_bootfiles/bootfiles.zip)，核对时为 10,354 字节，ZIP SHA-256 为 `104b3c74f91f8fef506d3a0d07522e8877450772d2f5d61dced772eed2e4e435`。其中：

- `efi/boot/bootarm.efi` 为 16,288 字节，SHA-256 `9b07aba3ac412e5e6055bd84a9c04bc5a4777e7f25a087f455ffc3d366ab7bba`。
- 其 PE 类型为 ARM Thumb EFI Application；字符串包含 `Windows RT Boot Shim :)`、`WindowsRTBootShimPkg`、`cmdline.txt` 和多个机型的 DTB 名称。
- 自带参数例子是 `root=/dev/<...> rootwait cpuidle.off=1`。

这些静态特征说明它与上面的 Windows Boot Application `test.efi` 是不同二进制、不同入口约定。**本项目没有实机测试这个新包，既不把它列为已验证替代品，也不把此前其他启动器的故障直接归因于它。** “同站下载”“文件也叫 EFI”或“都支持 txt”都不足以证明可以互换。

在本机的历史试验中，GRUB 路径曾出现数分钟等待和显示异常；跳过菜单改善了显示，直接沿用原 `test.efi` 加兼容 stub 后恢复几秒内出现 Linux 文字。等待和黑屏的全部固件原因尚未确定，不能仅凭现象断言都是菜单或显示硬件重置导致。这里发布的是已经验证的兼容路径，不是通用固件修复。

## 来源和再分发

Open RT 的 [站点说明](https://files.open-rt.party/.hidden/about.html) 将此站称为项目文件托管站，并提供镜像方法。这可以帮助定位下载来源，但不能替代每个文件自身的许可证或完整内核对应源码。核对的两个 ZIP 内均未看到独立的 LICENSE/COPYING 文件；这不等于其中所有文件都没有许可，也不构成统一再分发授权。

本仓库提供来源链接、校验值、自有补丁和构建工具，不捆绑 `test.efi`、Windows 启动文件、BCD、旧内核或第三方压缩包。已有正常双系统的使用者应优先保留自己可用的原适配层；仅拿到本仓库并不等于已经具备完整安装环境。

## English summary

The tested legacy shim is the 31,232-byte `test.efi` in Open RT's `Linux/Other/surface-2-bootfiles+kernel.zip`. Its SHA-256 matches the file retained on the tested Surface 2. It is a Windows Boot Application, loads `\boot.efi` and supplies no EFI LoadOptions. The legacy kernel EFI stub reads `cmdline.txt`; this toolkit restores that behavior for the pinned 7.0.1 payload, using a separate fixed parameter path. The smaller `release/uefi_bootfiles/bootfiles.zip` contains a different EFI application and has not been boot-tested by this project. Third-party binaries are linked and identified, not redistributed.
