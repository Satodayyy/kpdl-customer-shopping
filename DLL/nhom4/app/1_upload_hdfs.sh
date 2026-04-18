#!/bin/bash
echo "=== Copy file vào container ==="
docker cp app/olist_data/. namenode:/tmp/olist/

echo "=== Tạo thư mục HDFS ==="
docker exec namenode hdfs dfs -mkdir -p /data/raw/olist

echo "=== Upload CSV lên HDFS ==="
docker exec namenode hdfs dfs -put /tmp/olist/*.csv /data/raw/olist/

echo "=== Kiểm tra ==="
docker exec namenode hdfs dfs -ls /data/raw/olist/