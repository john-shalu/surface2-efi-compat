# 来源、许可与可发布范围

- Linux kernel：GNU GPL version 2 only；各文件以自身 SPDX 标识为准。[官方许可说明](https://docs.kernel.org/process/license-rules.html)。
- EFI stub 参考：[libre-tegra/linux 固定提交](https://codeberg.org/libre-tegra/linux/src/commit/bfffc6d6656e87f3de3aa4c09d852849081ef088)。
- 旧式文件参数约定参考：[Open-Surface-RT/grate-linux](https://github.com/Open-Surface-RT/grate-linux/blob/21d89a4d51a7/drivers/firmware/efi/libstub/file.c)。新实现适配当前 EFI API，并增加边界及资源清理处理。
- 原内核输入来自 postmarketOS 的 `linux-postmarketos-grate 7.0.1-r4`。指定哈希见 pins.json。包的来源曾通过受信任密钥签名的官方 APKINDEX、包控制摘要及数据摘要核对。
- microSD 的供电、SDMMC3 与 UART 引脚问题也由 zefr0g 在 [grate-driver/linux #141](https://github.com/grate-driver/linux/issues/141) 中报告；感谢其同型号实机研究。补丁基于 GPL-2.0 设备树文件。
- 原 Windows→EFI 适配程序：已通过 SHA-256 确认 [Open RT 旧启动包](https://files.open-rt.party/Linux/Other/surface-2-bootfiles%2Bkernel.zip) 的 `test.efi` 与实机一致；完整记录见 [原启动器来源](bootloader-origin.md)。下载来源已经核实，具体作者、源码映射及逐文件再分发授权仍未完全核实，因此只链接、不捆绑二进制。

本项目保存自己的启动兼容改动和构建配方，没有把原 7.0.1 内核主体冒称为重新编译的完整内核。参考源码的提交与预编译内核主体的来源在 pins.json / manifest 中分开记录。

可公开的材料：源码补丁、构建工具、配置、匿名实测结论和教程。不得把私钥、登录凭据、家庭网络地址、个人目录、设备原始日志及来源未核实的第三方 EFI 混入发布包。

当前提供源码版发布材料。若发布包含 Linux 内核的二进制，应按 GPLv2 核实相应的完整源码与构建材料；不能把“某个近似分支的链接”当作已经满足对应源码要求。
