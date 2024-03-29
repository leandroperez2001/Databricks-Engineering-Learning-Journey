# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC # Activity by Traffic Lab
# MAGIC Process streaming data to display total active users by traffic source.
# MAGIC 
# MAGIC ##### Objectives
# MAGIC 1. Read data stream
# MAGIC 2. Get active users by traffic source
# MAGIC 3. Execute query with display() and plot results
# MAGIC 4. Execute the same streaming query with DataStreamWriter
# MAGIC 5. View results being updated in the query table
# MAGIC 6. List and stop all active streams
# MAGIC 
# MAGIC ##### Classes
# MAGIC - <a href="https://spark.apache.org/docs/latest/api/python/pyspark.sql.html?highlight=datastreamreader#pyspark.sql.streaming.DataStreamReader" target="_blank">DataStreamReader</a>
# MAGIC - <a href="https://spark.apache.org/docs/latest/api/python/pyspark.sql.html?highlight=datastreamwriter#pyspark.sql.streaming.DataStreamWriter" target="_blank">DataStreamWriter</a>
# MAGIC - <a href="https://spark.apache.org/docs/latest/api/python/pyspark.sql.html?highlight=streamingquery#pyspark.sql.streaming.StreamingQuery" target="_blank">StreamingQuery</a>
# MAGIC - <a href="https://spark.apache.org/docs/latest/api/python/pyspark.sql.html?highlight=streamingquerymanager#pyspark.sql.streaming.StreamingQueryManager" target="_blank">StreamingQueryManager</a>

# COMMAND ----------

# MAGIC %md ### Setup
# MAGIC Run the cells below to generate data and create the **`schema`** string needed for this lab.

# COMMAND ----------

# MAGIC %run ./Includes/Classroom-Setup

# COMMAND ----------

schema = "device STRING, ecommerce STRUCT<purchase_revenue_in_usd: DOUBLE, total_item_quantity: BIGINT, unique_items: BIGINT>, event_name STRING, event_previous_timestamp BIGINT, event_timestamp BIGINT, geo STRUCT<city: STRING, state: STRING>, items ARRAY<STRUCT<coupon: STRING, item_id: STRING, item_name: STRING, item_revenue_in_usd: DOUBLE, price_in_usd: DOUBLE, quantity: BIGINT>>, traffic_source STRING, user_first_touch_timestamp BIGINT, user_id STRING"

# COMMAND ----------

# MAGIC %md ### 1. Read data stream
# MAGIC - Use schema stored in **`schema`**
# MAGIC - Set to process 1 file per trigger
# MAGIC - Read from parquet with filepath stored in **`eventsPath`**
# MAGIC 
# MAGIC Assign the resulting DataFrame to **`df`**.

# COMMAND ----------

# ANSWER
df = (spark
      .readStream
      .schema(schema)
      .option("maxFilesPerTrigger", 1)
      .parquet(eventsPath)
     )

# COMMAND ----------

# MAGIC %md **CHECK YOUR WORK**

# COMMAND ----------

assert df.isStreaming
assert df.columns == ["device", "ecommerce", "event_name", "event_previous_timestamp", "event_timestamp", "geo", "items", "traffic_source", "user_first_touch_timestamp", "user_id"]

# COMMAND ----------

# MAGIC %md ### 2. Get active users by traffic source
# MAGIC - Set default shuffle partitions to number of cores on your cluster (not required, but runs faster)
# MAGIC - Group by **`traffic_source`**
# MAGIC   - Aggregate the approximate count of distinct users and alias with "active_users"
# MAGIC - Sort by **`traffic_source`**

# COMMAND ----------

# ANSWER
from pyspark.sql.functions import col, approx_count_distinct, count

spark.conf.set("spark.sql.shuffle.partitions", spark.sparkContext.defaultParallelism)

trafficDF = (df
             .groupBy("traffic_source")
             .agg(approx_count_distinct("user_id").alias("active_users"))
             .sort("traffic_source")
            )

# COMMAND ----------

# MAGIC %md **CHECK YOUR WORK**

# COMMAND ----------

assert str(trafficDF.schema) == "StructType(List(StructField(traffic_source,StringType,true),StructField(active_users,LongType,false)))"

# COMMAND ----------

# MAGIC %md ### 3. Execute query with display() and plot results
# MAGIC - Execute results for **`trafficDF`** using display()
# MAGIC - Plot the streaming query results as a bar graph

# COMMAND ----------

# ANSWER
display(trafficDF)

# COMMAND ----------

# MAGIC %md **CHECK YOUR WORK**
# MAGIC - You bar chart should plot `traffic_source` on the x-axis and `active_users` on the y-axis
# MAGIC - The top three traffic sources in descending order should be `google`, `facebook`, and `instagram`.

# COMMAND ----------

# MAGIC %md ### 4. Execute the same streaming query with DataStreamWriter
# MAGIC - Name the query "active_users_by_traffic"
# MAGIC - Set to "memory" format and "complete" output mode
# MAGIC - Set a trigger interval of 1 second

# COMMAND ----------

# ANSWER
trafficQuery = (trafficDF
                .writeStream
                .queryName("active_users_by_traffic_p")
                .format("memory")
                .outputMode("complete")
                .trigger(processingTime="1 second")
                .start()
               )

# COMMAND ----------

# MAGIC %md **CHECK YOUR WORK**

# COMMAND ----------

untilStreamIsReady("active_users_by_traffic")
assert trafficQuery.isActive
assert "active_users_by_traffic" in trafficQuery.name
assert trafficQuery.lastProgress["sink"]["description"] == "MemorySink"

# COMMAND ----------

# MAGIC %md ### 5. View results being updated in the query table
# MAGIC Run a query in a SQL cell to display the results from the **`active_users_by_traffic`** table

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ANSWER
# MAGIC SELECT * FROM active_users_by_traffic_p

# COMMAND ----------

# MAGIC %md **CHECK YOUR WORK**  
# MAGIC Your query should eventually result in the following values.
# MAGIC 
# MAGIC |traffic_source|active_users|
# MAGIC |---|---|
# MAGIC |direct|438886|
# MAGIC |email|281525|
# MAGIC |facebook|956769|
# MAGIC |google|1781961|
# MAGIC |instagram|530050|
# MAGIC |youtube|253321|

# COMMAND ----------

# MAGIC %md ### 6. List and stop all active streams
# MAGIC - Use SparkSession to get list of all active streams
# MAGIC - Iterate over the list and stop each query

# COMMAND ----------

# ANSWER
for s in spark.streams.active:
    print(s.name)
    s.stop()

# COMMAND ----------

# MAGIC %md **CHECK YOUR WORK**

# COMMAND ----------

assert not trafficQuery.isActive

# COMMAND ----------

# MAGIC %md ### Classroom Cleanup
# MAGIC Run the cell below to clean up resources.

# COMMAND ----------

# MAGIC %run ./Includes/Classroom-Cleanup

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC &copy; 2022 Databricks, Inc. All rights reserved.<br/>
# MAGIC Apache, Apache Spark, Spark and the Spark logo are trademarks of the <a href="https://www.apache.org/">Apache Software Foundation</a>.<br/>
# MAGIC <br/>
# MAGIC <a href="https://databricks.com/privacy-policy">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use">Terms of Use</a> | <a href="https://help.databricks.com/">Support</a>