#!/usr/bin/env bash
# 无云本地栈连通性验证（在已 docker compose up -d 后运行）
# 仅用 curl 做健康检查，不依赖外部 MQTT 客户端
set -e

echo "== 1. 容器状态 =="
docker ps --filter "name=twin-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || {
  echo "Docker 不可用或栈未启动。请先 'docker compose up -d'"
  exit 1
}

echo
echo "== 2. EMQX (MQTT 入口) 健康检查 :18083 =="
if curl -sf -m 5 http://localhost:18083/status >/dev/null 2>&1; then
  echo "  EMQX 可达 ✓"
else
  echo "  EMQX 未响应（可能在启动中，稍后重试）"
fi

echo
echo "== 3. IoTDB (时序库) REST 健康检查 :31999 =="
if curl -sf -m 5 http://localhost:31999/actuator/health >/dev/null 2>&1; then
  echo "  IoTDB 可达 ✓"
else
  echo "  IoTDB 未响应（可能在启动中，稍后重试）"
fi

echo
echo "== 4. 手动验证 MQTT→IoTDB 数据流（建议）=="
echo "  - 打开 EMQX 控制台 http://localhost:18083 （默认 admin/public）"
echo "  - 用 WebSocket 客户端向主题 'twin/device/001' 发一条 JSON 报文"
echo "  - 在 IoTDB 中建存储组 root.twin，写入该点位时序数据"
echo "  - 详见 README.md 第二节"
echo
echo "本地栈基础就绪。OGG 编译请执行："
echo "  docker exec -it ogg-geometry-core bash /opt/build_ogg.sh"
