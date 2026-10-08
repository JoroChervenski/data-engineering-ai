from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

bronze = spark.read.table("bronze.orders")

silver = (
    bronze.dropDuplicates(["order_id"])
    .withColumn("order_date", F.to_date("order_date"))
    .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
)

silver.write.mode("overwrite").format("delta").saveAsTable("silver.orders")
