# 安装到现有 Surface 2 双系统

前提：你的 Surface 2 已经有可用的 Windows/Linux 双系统，原 `test.efi` 能直接启动旧 Linux。先确认能从 Windows 挂载 EFI 分区、恢复自己的可用启动文件。

原适配层已在 [Open RT 旧包](https://files.open-rt.party/Linux/Other/surface-2-bootfiles%2Bkernel.zip) 中找到，`test.efi` 与实机哈希一致。详见 [文件身份与两套启动器的区别](bootloader-origin.md)。这条下载链接用于定位原文件，不是整包安装指令；不要覆盖原 BCD，也不要换用未经本项目实机验证的另一套 `bootarm.efi`。

## 启动文件布局

构建后在 EFI 系统分区放置：

```text
boot.efi                                      ← out/surface2-compat.efi
surface-upgrade/stub-native/cmdline.txt          ← 自己核实后的启动参数
surface-upgrade/stub-native/surface2-microsd-fixed.dtb
```

`cmdline.txt` 必须为单行 ASCII 文本。以下是 microSD 根分区示例，`root=` 必须按你自己的分区修改：

```text
dtb=surface-upgrade/stub-native/surface2-microsd-fixed.dtb root=/dev/mmcblk1p2 console=tty1 cpuidle.off=1 rootwait=90 rw panic=20
```

兼容代码仅在外层未提供 EFI LoadOptions 时读取这个固定路径。正常引导器已经提供参数时，维持标准行为。

在 Linux 中用 `lsblk -f` 核实 EFI 分区和根分区；不同安装的编号可能不同。挂载 EFI 分区后，先保存自己当前可用的 `boot.efi`，再复制新 EFI、修正 DTB 和参数。`test.efi`、Windows Boot Manager 和 BCD 保持原来可用的版本。

此路径不依赖 GRUB。不要给同一内核混用旧 5.17 的整份设备树；本项目的 SD 修正基于指定 7.0.1 EFI DTB。

## 首次启动验证

从原双系统菜单选择 Linux。启动后核对 `uname -r`、`/proc/cmdline`、根分区、SSH 和实屏显示。EFI 文件能通过格式检查，不等于已经通过你的固件实机验证。

旧 `test.efi` 会清空子映像的 LoadOptions。旧内核通过定制代码自读 `cmdline.txt`；新标准 EFI stub 缺少这一约定，是直接替换官方 `vmlinuz` 时确定缺失的环节。本补丁补上该兼容行为。

新包默认把 microSD 引脚用于 UART-A，并禁用 SDMMC3。以 microSD 为根分区时，需要本项目的 SD 修正。

## 诊断版

构建时添加 `--diagnostic` 会打开 EFI 文件检查点。将生成的 4096 字节 `boot-stage.log` 放在同一 `surface-upgrade/stub-native/` 目录，供固件阶段原地更新。文件缺失或不可写时，诊断路径会返回错误。

阶段：01 进入 EFI stub；02/03 参数读取；04/05 内核空间分配；06 通用 stub；07/08 CPU 检查；09/0a 图形信息；0b/0c 设备树；0d 即将 ExitBootServices；0f 错误返回。所有文件写入均在退出固件服务之前。

日常版默认关闭这些文件写入。

## 恢复

若新文件未能启动，从 Windows 管理员命令提示符用 `mountvol S: /S` 挂载 EFI 分区，将你自己保存的可用启动文件复制回去，再用 `mountvol S: /D` 卸载。原版恢复文件由各使用者自行保留；本项目不捆绑第三方引导文件。

以后更新内核包时，需要同步构建匹配的启动映像、设备树与模块。直接用新下载的官方 `vmlinuz` 覆盖这个 `boot.efi` 会丢掉此处的兼容改动。
