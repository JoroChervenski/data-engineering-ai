from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

raw = spark.read.option("header", True).csv("Files/landing/orders/")
orders = raw.withColumn("_ingested_at", F.current_timestamp())

order_ids = [r["order_id"] for r in orders.select("order_id").collect()]
print(f"ingested {len(order_ids)} orders")

orders.write.mode("overwrite").format("delta").saveAsTable("bronze.orders")
