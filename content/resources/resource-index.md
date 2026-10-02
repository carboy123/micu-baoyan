---
title: "公共学习资源索引"
description: "按电子信息、嵌入式、自动化与计算机方向，选择项目维护方的开源仓库，从一个可复现的小实验开始。"
weight: 70
lastmod: 2026-10-03T00:00:00+08:00
params:
  status: published
  resourceCategory: "公共资源索引"
---
按方向选择一个资源，从能运行的小实验开始。本页收录 13 项项目维护方、芯片厂商或高校团队的资源，外部链接需联网访问。招生要求请查看[官方信息入口]({{< relref "resources/official.md" >}})。

## 按目标选起点

| 现在想解决的问题 | 可以先选 | 开始前应具备 |
| --- | --- | --- |
| 把电路想法画出来、做成板子 | [KiCad](#kicad) | 电路基础、认识常用器件 |
| 理解采样、滤波和频谱 | [GNU Radio](#gnu-radio)；有单片机基础后再看 [CMSIS-DSP](#cmsis-dsp) | 信号与系统、采样概念 |
| 把传感器和外设驱动起来 | [STM32CubeF4](#stm32cubef4) 或 [ESP-IDF](#esp-idf)，按手头芯片选择 | C 语言、GPIO 与串口基础 |
| 理解多个任务如何协作 | [FreeRTOS](#freertos)；有构建基础后再看 [Zephyr](#zephyr) | 能独立调试简单单片机程序 |
| 验证控制原理或机器人算法 | [python-control](#python-control) → [Modern Robotics](#modern-robotics)；需要节点通信时再看 [ROS 2](#ros2) | Python、线性代数、控制基础 |
| 做视觉、机器学习或系统实验 | [OpenCV](#opencv)、[PyTorch Tutorials](#pytorch)、[xv6](#xv6)，各选所需方向 | Python 或 C，以及对应基础课 |

开始前先看 README 和安装说明，确认教程版本、芯片与开发板相匹配。

## 电子电路与信号处理

{{< html >}}<span id="kicad原理图与-pcb-设计" aria-hidden="true"></span>{{< /html >}}

### KiCad：原理图与 PCB 设计 {#kicad}

[KiCad 官方 GitHub 镜像](https://github.com/KiCad/kicad-source-mirror) · [KiCad 10.0 中文入门](https://docs.kicad.org/10.0/zh/getting_started_in_kicad/getting_started_in_kicad.html)

用于原理图与 PCB 设计，需要电路和常用器件基础。可跟随中文入门完成一块 LED 接口板，练习封装分配、布线及规则检查。GitHub 为官方镜像，开发主仓库位于 GitLab。

{{< html >}}<span id="cmsis-dsp把信号算法放到-arm-芯片上" aria-hidden="true"></span>{{< /html >}}

### CMSIS-DSP：把信号算法放到 Arm 芯片上 {#cmsis-dsp}

[Arm 官方仓库](https://github.com/ARM-software/CMSIS-DSP) · [项目使用文档](https://arm-software.github.io/CMSIS-DSP/latest/index.html)

用于 Arm 平台的数字信号处理，需要 C 语言、采样与滤波基础；上板还需 Cortex-M 工程基础。从 FIR 滤波示例开始，比较测试信号处理前后的波形，也可先用项目的 Python 封装验证结果。

{{< html >}}<span id="gnu-radio用流图观察信号链路" aria-hidden="true"></span>{{< /html >}}

### GNU Radio：用流图观察信号链路 {#gnu-radio}

[GNU Radio 项目仓库](https://github.com/gnuradio/gnuradio)

用于通信与信号处理实验，需要理解采样率、频谱和滤波。可在 GNU Radio Companion 中连接信号源、滤波与显示模块，观察参数变化；使用合成信号即可开始，无需射频硬件。

## 嵌入式与实时系统

{{< html >}}<span id="stm32cubef4从官方外设示例建立工程基础" aria-hidden="true"></span>{{< /html >}}

### STM32CubeF4：从官方外设示例建立工程基础 {#stm32cubef4}

[STMicroelectronics 官方仓库](https://github.com/STMicroelectronics/STM32CubeF4)

用于 **STM32F4 系列**外设开发，需要 C 语言和基本开发板调试经验。从 `Projects` 中选择适配硬件的 GPIO 或 UART 示例，再尝试定时采样与串口输出；其他系列应使用对应软件包。

{{< html >}}<span id="esp-idfesp32-外设与物联网开发" aria-hidden="true"></span>{{< /html >}}

### ESP-IDF：ESP32 外设与物联网开发 {#esp-idf}

[Espressif 官方仓库](https://github.com/espressif/esp-idf) · [ESP32 中文快速入门](https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/get-started/index.html)

用于 ESP32 外设与物联网开发，需要 C 语言和串口基础。按手头芯片选择文档目标与稳定版本，先完成编译、烧录和串口监视，再运行 `examples` 中的传感器示例。

{{< html >}}<span id="freertos任务队列与同步" aria-hidden="true"></span>{{< /html >}}

### FreeRTOS：任务、队列与同步 {#freertos}

[FreeRTOS 内核仓库](https://github.com/FreeRTOS/FreeRTOS-Kernel) · [官方示例工程仓库](https://github.com/FreeRTOS/FreeRTOS)

用于任务调度、队列与同步，需要 C 语言、指针、中断和裸机调试基础。内核仓库不含完整入门工程，可从官方 `FreeRTOS/Demo` 选择适配示例，尝试用队列连接采样与输出两个任务。

{{< html >}}<span id="zephyr多平台嵌入式工程实践" aria-hidden="true"></span>{{< /html >}}

### Zephyr：多平台嵌入式工程实践 {#zephyr}

[Zephyr 项目仓库](https://github.com/zephyrproject-rtos/zephyr) · [项目入门指南](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)

用于多平台嵌入式开发，适合已有 C 语言、命令行和单片机调试基础的同学。按指南准备 `west` 与工具链，在受支持的开发板上运行 Blinky，再理解设备树和 Kconfig 配置。

## 自动化、控制与机器人

{{< html >}}<span id="python-control用计算实验理解控制系统" aria-hidden="true"></span>{{< /html >}}

### python-control：用计算实验理解控制系统 {#python-control}

[项目维护方仓库](https://github.com/python-control/python-control) · [项目示例文档](https://python-control.readthedocs.io/en/latest/examples.html)

用于控制系统建模与仿真，需要 Python、线性代数和反馈控制基础。可从二阶系统的阶跃响应开始，调整参数，观察超调量、调节时间与稳态误差的变化。

{{< html >}}<span id="modern-robotics机器人运动学与动力学" aria-hidden="true"></span>{{< /html >}}

### Modern Robotics：机器人运动学与动力学 {#modern-robotics}

[西北大学 NxRLab 教材配套代码](https://github.com/NxRLab/ModernRobotics) · [教材作者公开课程资源](https://modernrobotics.northwestern.edu/nu-gm-book-resource/)

用于学习机器人运动学与动力学，需要线性代数、坐标变换及 Python 或 MATLAB 基础。结合教材，用正运动学计算简单机械臂的末端位姿，再用手算特例核对；教学代码用于工程时仍需验证。

{{< html >}}<span id="ros-2-examples从节点通信开始组织机器人程序" aria-hidden="true"></span>{{< /html >}}

### ROS 2 examples：从节点通信开始组织机器人程序 {#ros2}

[ROS 2 官方示例仓库](https://github.com/ros2/examples)

用于机器人节点通信，需要 Python 或 C++、Linux 命令行基础。先运行 `rclpy` 或 `rclcpp` 的最小发布订阅示例，用一个节点发送模拟传感器数据、另一个节点接收；分支须匹配 ROS 2 发行版。

## 计算机、视觉与智能应用

{{< html >}}<span id="opencv从图像处理到视觉实验" aria-hidden="true"></span>{{< /html >}}

### OpenCV：从图像处理到视觉实验 {#opencv}

[OpenCV 项目仓库](https://github.com/opencv/opencv) · [项目 Python 教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

用于图像处理与视觉实验，需要 Python、NumPy 和基础线性代数。可从图像读写、阈值分割和轮廓处理开始，实现颜色目标定位，比较不同光照下的效果。

{{< html >}}<span id="pytorch-tutorials走完一次模型训练流程" aria-hidden="true"></span>{{< /html >}}

### PyTorch Tutorials：走完一次模型训练流程 {#pytorch}

[PyTorch 官方教程仓库](https://github.com/pytorch/tutorials) · [Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)

用于学习模型训练流程，需要 Python、线性代数、概率和导数基础。沿 Learn the Basics 完成一个小型分类示例，理解数据集、自动求导和优化，再改变一个参数比较结果。

{{< html >}}<span id="mit-xv6理解操作系统内部如何工作" aria-hidden="true"></span>{{< /html >}}

### MIT xv6：理解操作系统内部如何工作 {#xv6}

[MIT PDOS 的 xv6-riscv 仓库](https://github.com/mit-pdos/xv6-riscv) · [MIT 6.1810 课程入口](https://pdos.csail.mit.edu/6.1810/)

面向 RISC-V 的教学操作系统，适合已有 C 语言、指针、计算机组成与操作系统基础的同学。按仓库说明准备工具链和 QEMU，启动后从简单用户程序追踪到系统调用；课程与实验代码须匹配学期。

使用和分享项目时，请遵循原仓库的许可与署名要求，并准确说明自己的修改与贡献。
