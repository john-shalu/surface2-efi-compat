# 已知 grate 内存泄漏：动画屏保触发

此问题独立于 EFI 启动兼容改动，当前启动构建配方不应用其候选修补。

## 实机复现

设备：Surface 2 / Tegra 4 / ARM32，XFCE + Xorg，自动屏保主题 popsquares。用户只需登录桌面，自动屏保就能提供持续图形负载。

| 内核 / 负载 | 时长 | dma_resv_get_fences 分配 | 观察到的对应释放 |
|---|---:|---:|---:|
| 原 5.17，动画屏保 | 8.006秒 | 7748 | 0 |
| 原 5.17，暂停动画 | 7.954秒 | 0 | 0 |
| 7.0.1，动画屏保 | 8.005秒 | 7815 | 0 |
| 7.0.1，空白屏保实际生效后 | 约8秒 | 0 | 0 |

旧内核15秒内 kmalloc-64 活跃对象增加14544个，约3.54 MiB/分钟。暂停/恢复动画后，增长随之停止/恢复。新版空白屏保实际生效后的30秒，活跃对象连续保持同一数值。

采样使用 kmem 分配/释放事件，按地址配对；上述各 CPU 的 overrun 和 dropped events 为0。其他缓存中的未配对对象不据此一概判为泄漏。

这些是内核小对象，不是固定预留显存。大量积累会耗尽 ARM32 低端内存，即使高端内存仍有空闲。已失去引用的数组不会随关闭动画自动释放，重启能清除既有积累。

## 对应源码

`drivers/gpu/drm/grate/uapi/job_v2.c` 的 `tegra_drm_get_bo_fences()` 接收 `dma_resv_get_fences()` 分配的指针数组。调度器消耗 fence 引用并将数量设为0，数组本身仍由任务拥有；正常任务清理和错误回退没有释放数组。

`drivers/dma-buf/dma-resv.c` 明确要求调用者释放返回的数组。7.0.1 参考代码中该遗漏仍存在。其现代接口在自身分配失败时会清空并释放数组，所以候选补丁只在正常清理及原有错误循环加入 `kfree(f->shared)`，不扩大错误循环。

候选见 [research/grate-fence-array-release-candidate.patch](../research/grate-fence-array-release-candidate.patch)。它尚未编译或安装；当前配置的图形驱动内置于内核，验证修复需要重编译内核主体和配套模块，并保留 EFI 兼容改动。

## 已验证的缓解

在自己的 XFCE 桌面会话运行：

```sh
xfconf-query -c xfce4-screensaver -p /saver/mode -s 0
xfce4-screensaver-command --cycle
```

模式0是空白，模式2是单一动画。不要改动 `/lock/enabled`。已经运行的动画可能需要正常切换一次才会结束；应确认 popsquares 进程消失，并观察分配斜率，而非仅看设置值。

恢复单一动画模式：`xfconf-query -c xfce4-screensaver -p /saver/mode -s 2`。这会重新引入已验证的触发负载。

空白屏保可以消除已确认的持续空闲负载；其他图形工作负载仍可能触发底层遗漏。

来源：[libre-tegra 固定参考代码](https://codeberg.org/libre-tegra/linux/src/commit/bfffc6d6656e87f3de3aa4c09d852849081ef088/drivers/gpu/drm/grate/uapi/job_v2.c)、[XFCE 屏保模式定义](https://github.com/xfce-mirror/xfce4-screensaver/blob/master/src/gs-prefs.h)。
