#!/bin/bash
echo "=== Cấu trúc thư mục output ==="
docker exec namenode hdfs dfs -ls /data/processed/olist/

echo ""
echo "=== Xem thử doanh thu theo tháng ==="
docker exec namenode hdfs dfs -cat \
  /data/processed/olist/stats_monthly/part-00000

echo ""
echo "=== Xem thử Top danh mục ==="
docker exec namenode hdfs dfs -cat \
  /data/processed/olist/stats_category/part-00000