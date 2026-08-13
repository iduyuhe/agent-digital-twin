# 无云本地运行栈 · 运行指南

> 结论先行：**不需要云服务器，直接在本地机器即可运行整套数字孪生 P1 原型。**
> 本目录把 OGG 几何内核、实时数据底座（MQTT + 时序库）、本地 LLM 智能层
> 打包成一个 docker-compose，装好 Docker 后一条命令拉起——**零公有云依赖**。

---

## 一、本地运行的三种形态（都不是"云"）

| 形态 | 适用阶段 | 说明 |
|---|---|---|
| **开发机 / 笔记本**（WSL2 + Docker Desktop，或 Linux 实体机） | 原型验证、W1/W2 开发 | 最快上手，验证整条链路可行性 |
| **工厂内网边缘服务器 / 工控机** | 现场试点 | 数据不出厂，最契合等保与"数据不出域" |
| **Linux 虚拟机**（本机或机房） | 预生产 | 与生产环境一致，便于迁移 |

> 关键区分："云"= 别人托管、按量计费、数据出域的基础设施；
> "本地"= 你自己的机器/内网设备。本栈全部跑在后者，华为云 IoT **非必需**。

---

## 二、最小环境要求

- **Docker**：Windows 装 Docker Desktop（启用 WSL2 后端）；Linux 装原生 Docker + docker-compose v2
- **内存**：≥ 8 GB（EMQX + IoTDB 约占 3–4 GB；OGG 编译另需 4 GB+）
- **磁盘**：≥ 20 GB 空闲（OGG/OCCT 源码 + 编译产物 + 镜像）
- **OGG 编译额外要求**：Linux 环境（容器内已满足），建议 ≥ 4 核
- **本地 LLM（可选）**：本机有 NVIDIA GPU 体验最佳；纯 CPU 可跑 7B/14B 量化模型但较慢

---

## 三、启动步骤

```bash
# 1. 进入本目录
cd P1_W1_开工脚手架/local-stack

# 2. 拉起数据底座（EMQX + IoTDB）
docker compose up -d

# 3. 验证本地连通
./verify_local.sh

# 4. 编译 OGG（进容器执行一键构建）
docker exec -it ogg-geometry-core bash /opt/build_ogg.sh
#   —— 脚本会自动 CMake 配置 → 编译 OCCT/OGG → 跑 hello_geometry（盒体→拓扑→STEP 导出）

# 5.（可选）启用本地 LLM
#   编辑 docker-compose.yml，取消 ollama 段注释，重新 up；
#   然后 ollama pull deepseek-r1:14b 或 qwen2.5:14b（量化版）
```

---

## 四、数据底座本地验证（MQTT → IoTDB）

1. 浏览器打开 EMQX 控制台 `http://localhost:18083`（默认 `admin/public`）
2. 用 WebSocket 客户端向主题 `twin/device/001` 发布一条 JSON：
   ```json
   {"ts": 1690000000000, "temp": 62.3, "rpm": 1480}
   ```
3. 在 IoTDB 建存储组并写入：
   ```sql
   CREATE DATABASE root.twin;
   INSERT INTO root.twin.device001(time, temp, rpm) VALUES (now(), 62.3, 1480);
   SELECT * FROM root.twin.device001;
   ```
4. 该时序流即驱动 OGG 几何模型增量更新 —— 完成"物理实体 → 孪生体"同步闭环（目标 ≤200ms）

---

## 五、诚实边界

- **OGG/OCCT 是大型 C++ 库**，首次编译耗时较长（数十分钟到小时级，视核数），首次建议在闲置机器上跑。
- 本栈在**你自己的机器**运行，不在本对话沙箱（沙箱已禁用 Docker/WSL 系统工具，无法代为实证）。
- 生产现场建议把 EMQX + IoTDB 部署在**工厂内网边缘服务器**，而非开发笔记本——架构不变，只是算力位置不同。
- 本地 LLM 为可选：若暂不需要智能层推理，注释掉 ollama 即可，不影响几何+数据底座闭环。
