# 启动改动的边界

原链：Windows Boot Manager → 原 test.efi 手动装载 PE → 带定制 EFI stub 的旧内核 → 自读文件参数和 DTB。

当前链：同一原 test.efi → 正常源码链接的7.0.1 EFI 包装 → 自读固定路径参数 → 修正 Surface 2 EFI DTB → 原始7.0.1内核主体。

原 test.efi 会清空子映像的 LoadOptions。补丁仅在外层参数为空时读取兼容参数文件；正常加载器提供 LoadOptions 时维持标准行为。实现处理文件大小限制、分段短读、空文件、ASCII范围、CRLF结尾和UTF-16终止符，并关闭文件、卷句柄，失败时恢复参数和释放分配。

Surface 2 兼容配置显式启用后，自读参数路径采用面向已解锁设备的 dtb= 兼容策略；正常加载路径保持标准安全启动检查。自读的设备树必须声明 microsoft,surface-2。本机实测固件报告 SecureBoot disabled，因此没有走 unknown/开启状态例外。此配置不用于维护通用 Secure Boot 信任策略。

日常模式不写 EFI 文件。诊断模式在退出固件服务前向预分配文件记录阶段；ExitBootServices 成功后不访问固件文件系统。EFI_FILE_PROTOCOL.Write 的长度参数声明也修正为 UINTN 指针，以匹配实际协议。

包装由正常 Kbuild 链接生成，保留 ARM32 PE 入口、区段及解压元数据。没有在发布的内核映像中二进制追加入口区段，没有改动 Windows→EFI 的 CPU/MMU 切换代码，也没有加入 GRUB 文字菜单。

当前构建工具只接受固定7.0.1-r4输入。它比较解压后的全部内核主体、BSS大小、TEXT_OFFSET及解压分配区，并核对最终ARM32 EFI格式。源码基线用于构建包装，不冒称已经确定整个预编译主体的精确源码来源。
