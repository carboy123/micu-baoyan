---
title: "公共学习资源索引"
description: "按电子信息、嵌入式、自动化与计算机方向，选择项目维护方的开源仓库，从一个可复现的小实验开始。"
weight: 70
lastmod: 2026-09-28
params:
  status: published
  resourceCategory: "公共资源索引"
---
**先选一个与你的基础和目标匹配的项目，完成一项小实验，再逐步扩展。** 本页收录 13 项由项目维护方、芯片厂商或高校团队公开维护的资源，外部仓库与文档需要联网访问。入口与用途核验日期：**2026-09-28**；下方的学习顺序与小产出是米醋编者建议。

这里的“官方”指项目维护方，并非招生主管部门。保研资格、报名日期和院校要求请查看[官方信息入口]({{< relref "resources/official.md" >}})。

## 按目标选起点

| 现在想解决的问题 | 可以先选 | 开始前应具备 |
| --- | --- | --- |
| 把电路想法画出来、做成板子 | KiCad | 电路基础、认识常用器件 |
| 理解采样、滤波和频谱 | GNU Radio；有单片机基础后再看 CMSIS-DSP | 信号与系统、采样概念 |
| 把传感器和外设驱动起来 | STM32CubeF4 或 ESP-IDF，按手头芯片选择 | C 语言、GPIO 与串口基础 |
| 理解多个任务如何协作 | FreeRTOS；有构建基础后再看 Zephyr | 能独立调试简单单片机程序 |
| 验证控制原理或机器人算法 | python-control → Modern Robotics；需要节点通信时再看 ROS 2 | Python、线性代数、控制基础 |
| 做视觉、机器学习或系统实验 | OpenCV、PyTorch Tutorials、xv6，各选所需方向 | Python 或 C，以及对应基础课 |

阅读仓库时先看 **README、支持的平台、安装说明和示例目录**，选择与教程一致的稳定版本。硬件项目要匹配芯片、开发板及工具链；框架源码较大时，可先按项目文档安装并运行一个示例。

## 电子电路与信号处理

### KiCad：原理图与 PCB 设计

[KiCad 官方 GitHub 镜像](https://github.com/KiCad/kicad-source-mirror) · [KiCad 10.0 中文入门](https://docs.kicad.org/10.0/zh/getting_started_in_kicad/getting_started_in_kicad.html)

- **适合方向**：电子信息、电子电路、硬件设计。**前置基础**：电路基础，能识别电阻、电容、接口及供电关系。
- **怎么开始**：跟随入门文档完成原理图、封装分配和 PCB 布线，理解电气规则检查与设计规则检查。GitHub 仓库是官方镜像，开发主仓库位于 GitLab；初学者可先使用软件和教程。
- **建议小产出**：一块简单 LED 或传感器接口板的工程文件、原理图、BOM，以及规则检查记录；说明每个主要器件的用途。

### CMSIS-DSP：把信号算法放到 Arm 芯片上

[Arm 官方仓库](https://github.com/ARM-software/CMSIS-DSP) · [项目使用文档](https://arm-software.github.io/CMSIS-DSP/latest/index.html)

- **适合方向**：电子信息、嵌入式信号处理。**前置基础**：C 语言、数组、采样与滤波；上板实践还需要 Cortex-M 工程基础。
- **怎么开始**：从库内的滤波或 FFT 示例选择一个，理解输入数据、采样率和输出含义。该库由 Arm 维护，面向 Cortex-M、Cortex-A；可先用项目的 Python 封装验证计算结果。
- **建议小产出**：对一组自建测试信号做 FIR 滤波，保存处理前后波形、参数和结果；有开发板时再记录运行时间与数值误差。

### GNU Radio：用流图观察信号链路

[GNU Radio 项目仓库](https://github.com/gnuradio/gnuradio)

- **适合方向**：通信、电子信息、数字信号处理。**前置基础**：正弦信号、采样率、频谱和基础滤波概念。
- **怎么开始**：从仓库 README 进入安装与文档入口，用 GNU Radio Companion 的图形化流图连接信号源、滤波模块和显示模块。先在电脑中使用合成信号，无需急着购买射频硬件。
- **建议小产出**：一份可运行的信号流图，展示改变采样率或滤波参数前后的波形与频谱，并解释观察到的变化。

## 嵌入式与实时系统

### STM32CubeF4：从官方外设示例建立工程基础

[STMicroelectronics 官方仓库](https://github.com/STMicroelectronics/STM32CubeF4)

- **适合方向**：嵌入式、测控、电子竞赛。**前置基础**：C 语言、GPIO、串口与开发板调试。
- **怎么开始**：这是 **STM32F4 系列**的软件包；在 `Projects` 中选择与开发板匹配的示例，从 GPIO、UART 逐步到定时器、ADC。使用其他系列芯片时，应从 ST 官方组织寻找对应软件包；按 README 准备子模块和工具链。
- **建议小产出**：一个定时采样并通过串口输出的程序，附引脚表、采样周期计算、串口数据和调试记录。

### ESP-IDF：ESP32 外设与物联网开发

[Espressif 官方仓库](https://github.com/espressif/esp-idf) · [ESP32 中文快速入门](https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/get-started/index.html)

- **适合方向**：嵌入式、物联网、智能硬件。**前置基础**：C 语言、串口与基本网络概念。
- **怎么开始**：依据手头芯片选择文档目标和稳定版本，完成环境配置、编译、烧录与串口监视，再从仓库 `examples` 选择外设或联网示例。
- **建议小产出**：一个定时读取传感器并输出时间戳的程序；需要联网时，再增加局域网内的数据传输，记录采样间隔和断连后的行为。

### FreeRTOS：任务、队列与同步

[FreeRTOS 内核仓库](https://github.com/FreeRTOS/FreeRTOS-Kernel) · [官方示例工程仓库](https://github.com/FreeRTOS/FreeRTOS)

- **适合方向**：嵌入式、自动化、实时软件。**前置基础**：C 语言、指针、中断，能调试简单裸机程序。
- **怎么开始**：内核仓库主要包含内核与移植文件；初学者从官方完整仓库的 `FreeRTOS/Demo` 选择适配硬件或模拟环境的工程，再理解任务调度、队列、信号量与互斥量。
- **建议小产出**：把采样与数据输出拆为两个任务，通过队列传递数据，记录任务周期、队列满时的处理及一次故障排查。

### Zephyr：多平台嵌入式工程实践

[Zephyr 项目仓库](https://github.com/zephyrproject-rtos/zephyr) · [项目入门指南](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)

- **适合方向**：嵌入式、物联网；适合已有单片机实践的同学。**前置基础**：C 语言、命令行、基本构建与调试经验。
- **怎么开始**：按指南准备 `west` 和工具链，选择受支持的开发板，先运行 Hello World 或 Blinky 示例，再逐步理解设备树、Kconfig 与驱动配置。
- **建议小产出**：在同一块板上完成 LED 控制和一个传感器读取示例，整理硬件配置、编译步骤和串口结果，能说明配置如何影响程序。

## 自动化、控制与机器人

### python-control：用计算实验理解控制系统

[项目维护方仓库](https://github.com/python-control/python-control) · [项目示例文档](https://python-control.readthedocs.io/en/latest/examples.html)

- **适合方向**：自动化、控制工程、测控。**前置基础**：Python、线性代数、传递函数与基础反馈控制。
- **怎么开始**：先做一阶或二阶系统的建模、阶跃响应和频率响应，再尝试反馈连接与参数调整。示例文档提供脚本和 Notebook，可按自己学过的课程主题选择。
- **建议小产出**：比较同一对象在几组参数下的响应，整理超调量、调节时间和稳态误差，并解释参数变化带来的影响。

### Modern Robotics：机器人运动学与动力学

[西北大学 NxRLab 教材配套代码](https://github.com/NxRLab/ModernRobotics) · [教材作者公开课程资源](https://modernrobotics.northwestern.edu/nu-gm-book-resource/)

- **适合方向**：机器人、自动化、机电系统。**前置基础**：线性代数、空间坐标变换，能使用 Python 或 MATLAB。
- **怎么开始**：结合教材章节学习旋转矩阵、齐次变换与正运动学，再阅读对应函数的输入、输出和示例。代码以教学可读性为目标，工程使用还需另做性能与可靠性验证。
- **建议小产出**：计算一个简单机械臂在多组关节角下的末端位姿，画出运动轨迹，并用手算的特例检查结果。

### ROS 2 examples：从节点通信开始组织机器人程序

[ROS 2 官方示例仓库](https://github.com/ros2/examples)

- **适合方向**：机器人、自动化、计算机交叉项目。**前置基础**：Python 或 C++、Linux 命令行，理解进程与消息的基本概念。
- **怎么开始**：从仓库 README 进入 ROS 2 教程，先学习节点、话题和发布订阅，再读 `rclpy` 或 `rclcpp` 的最小示例；仓库分支与所安装的 ROS 2 发行版保持一致。
- **建议小产出**：一个发布模拟传感器数据的节点和一个订阅处理节点，保存启动方式、消息定义与通信记录；基础通信跑通后再接入真实硬件。

## 计算机、视觉与智能应用

### OpenCV：从图像处理到视觉实验

[OpenCV 项目仓库](https://github.com/opencv/opencv) · [项目 Python 教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

- **适合方向**：计算机视觉、机器人感知、电子信息。**前置基础**：Python、NumPy 数组与基础线性代数。
- **怎么开始**：按教程完成图像读写、颜色空间、阈值分割和轮廓处理，再选择相机标定或特征匹配等专题。
- **建议小产出**：用自己采集的图片制作颜色目标定位程序，分别记录不同光照下的成功与失败样本，说明阈值选择与方法局限。

### PyTorch Tutorials：走完一次模型训练流程

[PyTorch 官方教程仓库](https://github.com/pytorch/tutorials) · [Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)

- **适合方向**：计算机、智能信息处理、视觉与感知。**前置基础**：Python、线性代数、概率与导数基础。
- **怎么开始**：沿入门教程理解张量、数据集、模型、自动求导、优化和保存加载，先运行一份小型分类示例，再一次只改变一个因素做对照。
- **建议小产出**：一份包含数据划分、环境版本、训练曲线、测试结果与失败样本的实验记录，明确哪些是教程原有内容、哪些是自己的修改。

### MIT xv6：理解操作系统内部如何工作

[MIT PDOS 的 xv6-riscv 仓库](https://github.com/mit-pdos/xv6-riscv) · [MIT 6.1810 课程入口](https://pdos.csail.mit.edu/6.1810/)

- **适合方向**：计算机系统、嵌入式系统软件；属于进阶入口。**前置基础**：熟练使用 C 语言和指针，学过计算机组成与操作系统，具备基础命令行能力。
- **怎么开始**：这是面向 RISC-V 的教学操作系统。按照仓库说明准备工具链和 QEMU，启动系统后，从一个简单用户程序追踪到系统调用入口；课程材料与实验代码应匹配相应学期。
- **建议小产出**：画出一次系统调用的关键执行路径，标注用户态、内核态及相关源码位置，附一份能够复现观察过程的运行记录。

## 把学习整理成能解释的经历

完成示例后，建议用[单个项目的讲解卡]({{< relref "resources/project-card.md" >}})留下四样东西：**要解决的问题、你实际修改的部分、验证结果、下一步改进**。同时记录仓库地址、版本、运行环境和参考许可，便于自己复现，也便于准确说明个人贡献。

本页只提供入口与原创导读，未将外部代码、课程或附件打包进本站；使用和分享这些项目时应遵循各仓库的许可与署名要求。本文已核对公开介绍与文档用途，未逐项安装、编译或实测所有硬件示例。
