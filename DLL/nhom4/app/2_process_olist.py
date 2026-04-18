# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, round as _round,
    to_timestamp, month, year, when, desc,
    datediff, coalesce, lit
)

# ============================================================
# KHỞI TẠO SPARK SESSION
# ============================================================
spark = SparkSession.builder \
    .appName("Olist_Processing_Nhom4") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

HDFS_RAW  = "hdfs://namenode:9000/data/raw/olist"
HDFS_OUT  = "hdfs://namenode:9000/data/processed/olist"

print("\n" + "="*55)
print("  NHÓM 4 – XỬ LÝ DỮ LIỆU OLIST BẰNG PYSPARK")
print("="*55)

# ============================================================
# BƯỚC A: ĐỌC DỮ LIỆU THÔ TỪ HDFS
# ============================================================
print("\n[A] Đọc dữ liệu từ HDFS...")

orders      = spark.read.csv(f"{HDFS_RAW}/olist_orders_dataset.csv",
                              header=True, inferSchema=True)
order_items = spark.read.csv(f"{HDFS_RAW}/olist_order_items_dataset.csv",
                              header=True, inferSchema=True)
payments    = spark.read.csv(f"{HDFS_RAW}/olist_order_payments_dataset.csv",
                              header=True, inferSchema=True)
reviews     = spark.read.csv(f"{HDFS_RAW}/olist_order_reviews_dataset.csv",
                              header=True, inferSchema=True)
customers   = spark.read.csv(f"{HDFS_RAW}/olist_customers_dataset.csv",
                              header=True, inferSchema=True)
products    = spark.read.csv(f"{HDFS_RAW}/olist_products_dataset.csv",
                              header=True, inferSchema=True)
sellers     = spark.read.csv(f"{HDFS_RAW}/olist_sellers_dataset.csv",
                              header=True, inferSchema=True)
category_translation = spark.read.csv(
    f"{HDFS_RAW}/product_category_name_translation.csv",
    header=True, inferSchema=True
)

print(f"   orders:      {orders.count():>7,} dòng")
print(f"   order_items: {order_items.count():>7,} dòng")
print(f"   payments:    {payments.count():>7,} dòng")
print(f"   reviews:     {reviews.count():>7,} dòng")
print(f"   customers:   {customers.count():>7,} dòng")
print(f"   products:    {products.count():>7,} dòng")

# ============================================================
# BƯỚC B: LÀM SẠCH DỮ LIỆU
# ============================================================
print("\n[B] Làm sạch dữ liệu...")

# B1: Loại bỏ dòng null ở cột quan trọng
orders_clean = orders.dropna(subset=["order_id", "customer_id", "order_status"])
print(f"   Sau dropna: {orders_clean.count():,} đơn hàng")

# B2: Chuyển cột timestamp sang đúng kiểu
orders_clean = orders_clean \
    .withColumn("order_purchase_timestamp",
                to_timestamp(col("order_purchase_timestamp"))) \
    .withColumn("order_delivered_customer_date",
                to_timestamp(col("order_delivered_customer_date"))) \
    .withColumn("order_estimated_delivery_date",
                to_timestamp(col("order_estimated_delivery_date")))

# B3: Thêm cột năm, tháng
orders_clean = orders_clean \
    .withColumn("year",  year(col("order_purchase_timestamp"))) \
    .withColumn("month", month(col("order_purchase_timestamp")))

# B4: Thêm cột số ngày giao hàng thực tế
orders_clean = orders_clean.withColumn(
    "delivery_days",
    datediff(
        col("order_delivered_customer_date"),
        col("order_purchase_timestamp")
    )
)

# B5: Thêm cột đánh giá giao hàng (đúng hạn hay trễ)
orders_clean = orders_clean.withColumn(
    "delivery_status",
    when(
        col("order_delivered_customer_date") <= col("order_estimated_delivery_date"),
        "on_time"
    ).otherwise("late")
)

# B6: Loại bỏ đơn hàng có delivery_days âm (lỗi data)
orders_clean = orders_clean.filter(
    col("delivery_days").isNull() | (col("delivery_days") >= 0)
)

# B7: Dịch tên danh mục sang tiếng Anh
products_translated = products.join(
    category_translation,
    on="product_category_name",
    how="left"
).withColumn(
    "category_en",
    coalesce(col("product_category_name_english"), col("product_category_name"))
)

print(f"   Sau làm sạch: {orders_clean.count():,} đơn hàng hợp lệ")
orders_clean.printSchema()

# ============================================================
# BƯỚC C: TỔNG HỢP DỮ LIỆU
# ============================================================
print("\n[C] Tổng hợp dữ liệu...")

# ── C1: Doanh thu theo tháng ─────────────────────────────────
df_monthly = orders_clean \
    .filter(col("order_status") == "delivered") \
    .join(payments, "order_id", "left") \
    .groupBy("year", "month") \
    .agg(
        count("order_id").alias("total_orders"),
        _round(_sum("payment_value"), 2).alias("total_revenue"),
        _round(avg("payment_value"), 2).alias("avg_order_value")
    ).orderBy("year", "month")

print("\n   === Doanh thu theo tháng ===")
df_monthly.show()

# ── C2: Top 10 danh mục sản phẩm ────────────────────────────
df_category = order_items \
    .join(products_translated, "product_id", "left") \
    .groupBy("category_en") \
    .agg(
        count("order_id").alias("total_sold"),
        _round(_sum("price"), 2).alias("total_revenue"),
        _round(avg("price"), 2).alias("avg_price")
    ).orderBy(desc("total_sold")) \
    .limit(10)

print("\n   === Top 10 danh mục bán chạy ===")
df_category.show()

# ── C3: Phân tích đánh giá theo tháng ───────────────────────
df_rating = reviews \
    .join(orders_clean.select("order_id", "year", "month"), "order_id", "inner") \
    .groupBy("year", "month") \
    .agg(
        _round(avg("review_score"), 2).alias("avg_rating"),
        count("review_id").alias("total_reviews"),
        count(when(col("review_score") >= 4, 1)).alias("positive_reviews"),
        count(when(col("review_score") <= 2, 1)).alias("negative_reviews")
    ).orderBy("year", "month")

print("\n   === Đánh giá theo tháng ===")
df_rating.show()

# ── C4: Phân tích phương thức thanh toán ────────────────────
df_payment = payments \
    .groupBy("payment_type") \
    .agg(
        count("order_id").alias("total_orders"),
        _round(_sum("payment_value"), 2).alias("total_value"),
        _round(avg("payment_installments"), 1).alias("avg_installments")
    ).orderBy(desc("total_orders"))

print("\n   === Phương thức thanh toán ===")
df_payment.show()

# ── C5: Phân tích giao hàng  ──────────────────────────────
df_delivery = orders_clean \
    .filter(col("order_status") == "delivered") \
    .filter(col("delivery_status").isNotNull()) \
    .groupBy("delivery_status") \
    .agg(
        count("*").alias("total_orders"),
        _round(avg("delivery_days"), 1).alias("avg_delivery_days")
    )

print("\n   === Phân tích giao hàng ===")
df_delivery.show()

# ── C6: Top 10 seller doanh thu cao nhất ────────────────────
df_top_seller = order_items \
    .join(sellers, "seller_id", "left") \
    .groupBy("seller_id", "seller_city", "seller_state") \
    .agg(
        count("order_id").alias("total_orders"),
        _round(_sum("price"), 2).alias("total_revenue")
    ).orderBy(desc("total_revenue")) \
    .limit(10)

print("\n   === Top 10 Seller ===")
df_top_seller.show()

# ============================================================
# BƯỚC D: LƯU KẾT QUẢ VÀO HDFS
# ============================================================
print("\n[D] Lưu kết quả vào HDFS...")

# Lưu dạng Parquet (tối ưu cho Spark, Nhóm 5 đọc nhanh hơn)
orders_clean.write.mode("overwrite").parquet(f"{HDFS_OUT}/clean_orders")

# Lưu kết quả tổng hợp dạng CSV (dễ đọc cho Nhóm 5 / Tableau)
df_monthly.write.mode("overwrite").csv(
    f"{HDFS_OUT}/stats_monthly", header=True)

df_category.write.mode("overwrite").csv(
    f"{HDFS_OUT}/stats_category", header=True)

df_rating.write.mode("overwrite").csv(
    f"{HDFS_OUT}/stats_rating", header=True)

df_payment.write.mode("overwrite").csv(
    f"{HDFS_OUT}/stats_payment", header=True)

df_delivery.write.mode("overwrite").csv(
    f"{HDFS_OUT}/stats_delivery", header=True)

df_top_seller.write.mode("overwrite").csv(
    f"{HDFS_OUT}/stats_top_seller", header=True)

print("\n HOÀN TẤT! Dữ liệu đã lưu vào:")
print(f"   {HDFS_OUT}/")
print("   ├── clean_orders/      (Parquet)")
print("   ├── stats_monthly/     (CSV)")
print("   ├── stats_category/    (CSV)")
print("   ├── stats_rating/      (CSV)")
print("   ├── stats_payment/     (CSV)")
print("   ├── stats_delivery/    (CSV)")
print("   └── stats_top_seller/  (CSV)")

spark.stop()